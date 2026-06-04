# DBSCTR Domain Module: Data Engineering

**Applies when:** Task involves data pipelines, ETL/ELT, orchestration (Prefect), warehouse writes
(ClickHouse/BigQuery/DuckDB), streaming, batch exports, or data lake operations (GCS/Parquet).

This module extends Phases 1 and 4 of core DBSCTR with data-engineering-specific patterns.

---

## Phase 1 Extensions (Domain)

### Source/Sink Naming

Every external data boundary gets a name in the ubiquitous language. Common taxonomy:

| Role | Examples |
|------|----------|
| **Source** | BigQuery table, Kafka topic, API endpoint, GCS prefix, webhook |
| **Intermediate** | Staging table, dedup view, validated prefix |
| **Serve** | Production ClickHouse table, materialized view, Parquet partition |
| **Control** | Watermark table, manifest file, ExportLog, PipelineControl |

### Multi-Hop Lineage

Sketch full pipeline topology with freshness annotations:

```
source: searchconsole.searchdata_url_impression (BQ, daily partitioned)
  → transform: sp_export_gsc_data (stored procedure, hourly batch of 365 dates)
  → intermediate: gs://bucket/gsc/{YYYY-MM-DD}/export-*.parquet (GCS, partition-replace)
  → ingest: ClickPipes (continuous S3-compat)
  → serve: default.gsc (ClickHouse SharedMergeTree, partitioned toYYYYMM)
  control: PipelineControl.last_successful_date (watermark)
  freshness: source lags real-world by ~2 days (GSC delay); serve ≤ 1 hour behind source
```

### Watermark & Incremental State

Identify the state mechanism that makes the pipeline resumable:

| Pattern | When to use | Example |
|---------|-------------|---------|
| **Control table** (DB row with last_successful_date) | SQL-based batch export | `PipelineControl` |
| **Manifest comparison** (set diff: available − processed) | Object-store batch | Adobe: manifest dates vs processed dates |
| **Gap auto-detection** (query for missing ranges) | Self-healing backfill | GSC dedup: find missing date ranges in serve table |
| **Content hash** (hash of input → skip if unchanged) | Incremental updates, idempotent re-processing | Wiki builder: content hash change detection |
| **Prefix staging** (staging/ → ready/ promotion) | Multi-stage validation before downstream access | Akamai: staging prefix → ready prefix after audit |

Document which pattern you're using in the Domain phase. This becomes a contract in Phase 4.

### Hive Partitioning Convention

When writing to object storage (GCS/S3/local), declare partition keys:
```
output path: gs://bucket/crawl_data/date={YYYY-MM-DD}/crawl_type={mobile|desktop}/*.parquet
partition keys: [date, crawl_type]
```

### Pipeline Topology Types

Classify the pipeline topology early — it affects contract design:

| Type | Description | Contract implications |
|------|-------------|----------------------|
| **Fan-out** | 1 source → N outputs | Each output has its own volume/freshness contract |
| **Fan-in** | N sources → 1 output | Referential contracts across all inputs; staleness = max(source freshness) |
| **Sequential chain** | A → B → C | Freshness compounds; total latency = sum of stages |
| **Orchestrator** | Parent flow dispatches child flows | Pre-flight validation contract; error isolation per child |
| **Self-healing** | Detects own gaps, auto-backfills | Gap-detection query IS the contract check |

---

## Phase 4 Extensions (Contract)

### Source Schema Contracts

Declare expected schema as typed Python artifacts. Prefer:
- **Pydantic models** for API responses / structured data
- **TypedDict** for lightweight row schemas
- **Dataclass** for domain objects passed between tasks
- **Polars schema** (`pl.Schema({...})`) for DataFrame pipelines

Example:
```python
class GscRow(TypedDict):
    data_date: str          # ISO date, not null
    url: str                # not null, must match subdomain whitelist
    query: str              # not null (may be "(not provided)")
    impressions: int        # >= 0
    clicks: int             # >= 0, <= impressions
    search_features: list[str]  # subset of ALLOWED_FEATURES
```

### Volume Contracts

Detect silent data loss — a pipeline succeeding with 0 rows is worse than one that errors.

| Check | Implementation |
|-------|---------------|
| **Row count bounds** | Assert output rows within ±N% of rolling average |
| **Partition completeness** | All expected partitions present (no date gaps) |
| **Source/output ratio** | Output rows proportional to input (e.g., 90-110% after filter) |
| **Empty-batch halt** | If batch produces 0 rows, raise — don't silently succeed |

Tolerance bands should be configurable per-environment (tighter in prod, looser in dev).

### Freshness Contracts

| Pattern | Implementation |
|---------|---------------|
| **Watermark lag** | `max(serve.date) >= max(source.date) - allowed_lag` |
| **Wall-clock lag** | `now() - max(serve.updated_at) <= threshold` |
| **Readiness gate** | Check upstream signals completeness before starting (e.g., ExportLog) |
| **Schedule adherence** | If scheduled hourly, alert if >2 hours since last success |

### Materialization Strategy

Choose one per output (see core SKILL.md for vocabulary). Data-specific guidance:

| Strategy | Best for | Idempotency | Backfill |
|----------|----------|-------------|----------|
| **Partition-replace** | Daily/hourly batch exports | Safe — replaces whole partition | Pass date_range param |
| **Incremental append** | Immutable event streams (logs, clicks) | Deduplicate on event_id | Replay from source with date filter |
| **Incremental merge** | Dimension tables, entity updates | UPSERT by key — safe to re-run | Full refresh from source |
| **Full-refresh** | Small lookup tables, config data | Drop + recreate — always safe | N/A (always full) |
| **Gap-fill** | Self-healing pipelines | Detect missing ranges, fill only gaps | Automatic — IS the backfill |

### Orchestration Contracts

When using Prefect (or equivalent):

| Contract | Rule |
|----------|------|
| **Task boundaries** | Each task is one logical unit of work with clear input→output |
| **Retry policy** | Declare retries + delay per task based on failure mode (network=retry, logic=don't) |
| **Concurrency** | Document max workers per resource (LLM rate limits, DB connections, API quotas) |
| **Cache policy** | Explicitly set `cache_policy=NONE` when tasks must always re-execute |
| **Pre-flight validation** | Orchestrator verifies connectivity + config before dispatching work |
| **Error isolation** | Child flow failure doesn't crash parent; parent collects status dicts |

### Storage-Format Contracts

| Format | Contract aspects |
|--------|-----------------|
| **Parquet** | Declare compression (zstd/snappy), row-group size, partition keys, schema evolution rules |
| **ClickHouse** | Declare engine (SharedMergeTree), partition key, ORDER BY, TTL if applicable |
| **BigQuery** | Declare partitioning, clustering, table expiry, authorized views |
| **GCS/S3** | Declare bucket lifecycle rules, IAM, HMAC for S3-compat (ClickPipes pattern) |

### Data Lineage Documentation

Use arrow notation in spec docs. Column-level for critical transforms:

```
## Lineage: gsc serve table

source: searchconsole.searchdata_url_impression
  .data_date → PASSTHROUGH → gsc.data_date
  .url → filter(subdomain_whitelist) → gsc.url
  .is_* (28 booleans) → collect_truthy() → gsc.search_features (array)
  .impressions → PASSTHROUGH → gsc.impressions
  .clicks → PASSTHROUGH → gsc.clicks
  .sum_position → PASSTHROUGH → gsc.sum_position

control: PipelineControl.last_successful_date → watermark for incremental range
```

---

## Rules (Data Engineering)

- Every pipeline output declares materialization strategy, freshness bound, and volume bound
- Watermark/state mechanism is documented in Phase 1 and enforced as a contract in Phase 4
- Batch size is a configurable parameter with a documented default and rationale
- Hive partition keys are declared upfront and never changed without a migration plan
- Schema evolution is explicit: additive (new nullable columns) OK; breaking changes require versioned output paths
- `cache_policy=NONE` is the default for tasks that depend on external state (DB queries, API calls)
- Pre-flight validation runs BEFORE any data movement — fail fast on bad config or unreachable services
- Dry-run / cost-estimation mode is required for pipelines that call paid APIs (LLM, SEMrush, etc.)
- Empty-result assertions prevent silent data loss from propagating downstream
- Typer CLI alongside Prefect: flows should be runnable both via Prefect deployment AND direct CLI invocation

---

## Worked Example: Batch Export Pipeline

A GSC data export illustrating all patterns:

```
# Domain (Phase 1)
Source: BigQuery searchconsole.searchdata_url_impression (daily partitioned)
Control: PipelineControl table (last_successful_date watermark)
Readiness: ExportLog (signals BQ partition is complete)
Output: GCS Parquet (hive: gsc/{YYYY-MM-DD}/export-*.parquet)
Downstream: ClickHouse default.gsc via ClickPipes (continuous)
Topology: Sequential chain with readiness gate
Freshness: Source lags real-world ~2 days; output ≤ 1h behind source

# Contracts (Phase 4)
Schema: GscExportRow(data_date, url, query, ..., search_features: list[str])
Volume: ~500K-2M rows/day; tolerance ±50% of 7-day avg; breach = halt + alert
Freshness: PipelineControl.last_successful_date < max(source.data_date) by ≤ 1 day
Materialization: Partition-replace (overwrite per date, multiple shards)
Idempotency: Safe to re-run — replaces entire date partition
Backfill: Set batch_size=365 to reprocess year; or pass explicit date range
Failure recovery: Incomplete partition invisible until full write; old data remains
Orchestration: Hourly scheduled query; retry on transient BQ errors; readiness gate prevents premature export
```
