# DBSCTR2 Domain Module: Data Engineering

**Applies when:** Task involves data pipelines, ETL/ELT, orchestration (Prefect), warehouse writes
(ClickHouse/BigQuery/DuckDB), streaming, batch exports, or data lake operations (GCS/Parquet).

This module extends Phases 1, 4, and 5 of core DBSCTR2 with data-engineering-specific patterns.

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

### Canonical Entity Resolution

The dominant analytics-agent failure is **concept↔entity ambiguity**: a concept
("revenue for product X", "active users") maps to dozens of plausible tables with
subtly different definitions, and the consumer cannot tell which is correct. Attack
this in the Domain phase, before any logic exists.

- **One canonical dataset per concept.** Name the single source-of-truth table,
  column, and metric definition. Aggressively deprecate near-duplicates — mark them
  in the glossary, don't leave them as silent alternatives.
- **Physical rollups derive mechanically.** Caches and aggregates still matter for
  cost/performance, but they must derive from the canonical model, never coexist as
  competing definitions.
- **Disambiguation glossary.** Every ambiguous term gets a single governed
  definition plus the exact filters/lookback that define it. Example below.

```
## Entity Disambiguation
- "active user": event in {login, query, export} within trailing 28 days;
  EXCLUDE fraud-flagged accounts; identity = stable_user_id (NOT session_id, which inflates)
- "revenue": fct_revenue_daily.net_usd (post-refund); deprecated alt = stg_billing.amount (gross)
- "the Q2 launch" → resolve via business-context source; ambiguous, must clarify
```

This glossary IS a deliverable (Phase 4 delivery contract) — the consumer agent
needs it at query time, not just the authoring engineer.

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
    clicks: int             # >= 0; clicks <= impressions enforced at load-time (TypedDict can't)
    search_features: list[str]  # subset of ALLOWED_FEATURES
```

> TypedDict declares shape, not cross-field invariants. `clicks <= impressions` and
> enum membership are asserted in a load-time check BEFORE transform logic (core
> SKILL.md Phase 4), not by the type.

### Semantic-Layer-First Contract

When the output is consumed by an analytics agent, a governed semantic layer
(compiled metric + dimension definitions) is the **mandatory-first** query path.
Raw SQL is the fallback, used only after semantic-layer coverage is shown absent.

| Rule | Detail |
|------|--------|
| **Structural routing** | The agent is instructed (by skill) to try the semantic layer first, every time |
| **Same number everywhere** | A metric resolves to one value across Slack, IDE, dashboards, agent sessions |
| **Humans own definitions** | LLM may draft documentation; a human owns the metric *definition*. Auto-generating definitions encodes the ambiguity it aims to remove (net-negative on evals) |
| **Don't bail early** | Pre-rebut the excuses agents use to skip the layer: "needs custom date filter" → time-dimension specs cover it; "needs a join" → the metric already encapsulates joins |

### Metadata-as-Product Contract

Coding agents perform well because codebases are legible (READMEs, types,
docstrings). Make the warehouse equally legible. For each governed table, maintain
with the same rigor as the transforms themselves:

- **Grain** — what one row represents
- **Scope / exclusions** — what's in, what's deliberately filtered out
- **Valid value ranges** — per column, where bounded
- **Lineage** — source → transform → output (arrow notation, below)
- **Ownership** — the team accountable for the model
- **Model tier** — canonical / derived / raw, so the agent prefers governed sources

Stale metadata is the common failure across all sources of truth. LLM drafts these
descriptions; humans curate and own.

### Provenance Footer Contract

Every agent-facing output carries a footer so the consumer can judge trust without
understanding the data model:

```
> Source: [semantic layer | governed table | raw exploration] ·
> Freshness: [MAX date in the data] · Owner: [owning team]
```

- **Post:** the footer is present on every agent-facing answer
- It doesn't make the answer more correct; it's the main mitigation for **silent
  failures** — a "raw table, freshness unknown" footer signals verify-before-forward

### Delivery Contract

A governed deliverable (canonical dataset definition, semantic metric, reference
doc, provenance schema) is useless if the consumer agent can't reach it. Each
deliverable declares **how it ships**. Principle: **colocate + auto-sync** — the
deliverable lives with what it describes and stays current via a defined trigger.

**Channel menu** (pick one or more per project; data-channel and context-channel
may differ):

| Channel | What ships | When to use | Sync trigger |
|---------|-----------|-------------|--------------|
| **Repo-embedded skill** (baseline, always present) | Reference docs + skill markdown in the data repo | Always — the floor; opencode-local reads these directly | CI-on-merge: schema PR must touch its doc |
| **MCP resources / tools** | Deliverables served over MCP | Hosted agents / cross-team platforms that consume via MCP | On-merge sync to MCP server |
| **Hive-partition sidecar** | Context shipped inside the data partition (`.../date=X/_context/` or a root `_manifest.json`) | Agent reads context alongside the data; pipeline owns delivery | Pipeline-run: regenerate + ship each run |
| **Git-context split** | Context in a git repo, data in a separate sink | When the orchestrator can't write context to the data sink (e.g., ClickHouse→ADLS data, but no ADLS write for context) | CI-on-merge for context repo |

- **Invariant:** every deliverable declares ≥1 delivery channel; the repo-embedded
  skill channel is always present
- **Invariant:** data-channel and context-channel are declared independently
- **Invariant:** the sync trigger is explicit (CI-on-merge | pipeline-run), never
  implicit framework behavior
- The exact channel set is a per-project decision — make it during Discovery, not
  by module default

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

## Phase 5 Extensions (Test)

Core Phase 5 uses pytest for deterministic code. Analytics-agent outputs are
**non-deterministic** (natural-language question → answer) with no compile-time
proof of correctness. Add evals alongside pytest: pytest tests the pipeline code;
evals test whether the agent maps questions to the right entity.

### Offline Evals

Question/answer pairs, run in CI. Like offline ML testing — they don't prove
online performance but catch obvious gaps.

| Source of evals | Detail |
|-----------------|--------|
| **Dashboard-based** | Auto-generated by the model (human-validated) from the most common stakeholder questions |
| **Long-tail** | Feed the model business context (roadmaps, table docs) → generate plausible questions across the domain |
| **Harvested corrections** | Every time a stakeholder corrects the agent in a thread, that correction is a candidate eval |

### Anti-Drift Anchoring

An eval written against live data goes stale the moment the number moves. Anchor it:

- Pin to a **snapshot date**, OR
- Write against a **stable fact table**, OR
- Have the grader judge the agent's **query**, not its number
- Wire the suite into CI so a PR touching a dependency re-runs affected evals

### Eval Results as Telemetry

Store each run as a warehouse row, not a test log: skill version, git SHA, model
ID, per-assertion pass/fail, token count, wall-clock. "Did that change help?"
becomes a query, and you catch slow regressions a single CI run misses.

### Launch Gates

A domain owner can't announce the agent to stakeholders until that domain's eval
slice clears a threshold (start ~90%). Forces reference-doc fixes before users see
failures. Offline accuracy target is ~100% (it means no obvious gaps, not zero
production errors).

### Ablation Discipline

Every structural skill decision (which sources to expose, whether a sub-agent earns
its latency, merging two skills) is decided by holding the eval set fixed and
varying one component.

- **Design for null results** — the most useful ablation may be negative. Raw
  grep-access to thousands of prior SQL files moved accuracy <1pt: the bottleneck
  was structure (question→entity), not access. Distill the corpus into reference
  docs; don't ship raw query history as a source of truth.
- **Ablate at PR granularity** — every meaningful skill edit gets a before/after
  run on the relevant eval slice, delta in the PR description. Catches the common
  case where a well-intentioned addition makes things worse.
- **Keep a "what didn't work" log** — negative results are cheap to record and stop
  the next person re-running the same experiment.

### Correction-Harvesting Loop

Close the loop: a scheduled agent scans stakeholder channels for correction language
("wrong table", "missing fraud filter"), drafts a one-line reference-doc fix, opens
a PR tagged to the domain owner. Keep the fix path boring (edit markdown, merge,
auto-sync). Same corrections feed back into the offline eval set.

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
- **One canonical dataset per concept**; near-duplicates carry a deprecation marker; rollups derive mechanically
- **Semantic-layer-first** for agent-consumed outputs; humans own metric definitions, LLM drafts docs only
- **Metadata is a product**: grain, scope, ranges, lineage, owner, tier maintained with transform-level rigor
- **Provenance footer** (source tier · freshness · owner) on every agent-facing answer
- **Every deliverable declares a delivery channel**; repo-embedded skill is the always-present baseline
- **Doc-model colocation**: a schema/model change PR MUST touch the reference doc describing it; a CI hook fails any reporting-model change that doesn't. Without this, skill docs drift ~95%→65% accuracy within a month.

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
