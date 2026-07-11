# Data Module Examples

These are **EXAMPLES**, not lifecycle requirements. Select tools, providers,
formats, and numeric tolerances through project policy.

## Providers and tools

- **EXAMPLE:** Prefect can orchestrate task retries, concurrency, and child-flow
  isolation; another scheduler can provide equivalent evidence.
- **EXAMPLE:** Typer or Click can expose a direct CLI for a flow; this is optional.
- **EXAMPLE:** BigQuery, ClickHouse, GCS, and object storage can be sources or
  sinks. Their partitioning, IAM, TTL, and write semantics are project choices.
- **EXAMPLE:** Pydantic, `TypedDict`, dataclasses, and Polars schemas can describe
  row shape. Cross-field invariants still need runtime validation.

## Patterns

- **EXAMPLE:** A daily partition-replace export records a successful-date
  watermark, writes a complete staging partition, validates it, then promotes it.
  Reprocessing the same date replaces the partition; an explicit date range
  backfills it.
- **EXAMPLE:** An immutable event stream appends with event-key deduplication;
  a mutable dimension merges by stable key; a small lookup fully refreshes.
- **EXAMPLE:** A serve model can publish provenance as source tier, maximum data
  time, and owner.

## Tolerances

- **EXAMPLE:** A project may compare output volume with a rolling baseline, halt
  empty batches, or bound source-to-sink lag. Numeric bands, schedules, batch
  sizes, retry counts, and cost budgets belong in requirements, baselines,
  regulation, or ADRs.
