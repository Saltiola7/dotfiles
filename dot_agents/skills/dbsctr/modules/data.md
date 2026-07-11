# Data Module

## Applicability

Load this module for pipelines, ETL/ELT, streams, data stores, exports, data
lakes, warehouses, or changes to governed datasets and their consumers.

- **REQUIRED:** Record each source, intermediate, serving sink, and control state
  that the cycle affects.
- **REQUIRED:** Use these labels consistently: **REQUIRED** is universal when
  this module applies; **CONDITIONAL** applies only when its stated trigger is
  true; **PROJECT POLICY** is authoritative only when named project artifacts
  make it so; **EXAMPLE** is non-normative and cannot gate a cycle.

## Engineering Profile Extensions

- **REQUIRED:** Record data classification, accountable owner, sources and sinks,
  consumers, freshness expectation, materialization, recovery expectations, and
  compatibility commitments relevant to the bounded context.
- **REQUIRED:** For every governed dataset, record schema, row grain, ownership,
  scope/exclusions, and canonical or derived status.
- **CONDITIONAL:** When a concept has competing datasets or metrics, identify its
  canonical definition and deprecation or derivation path for alternatives.
- **PROJECT POLICY:** Record the project-selected authority for retention,
  privacy, quality, schema compatibility, and operational controls.

## Required Outcomes

- **REQUIRED:** Define lineage from source through transformations and control
  state to each sink; include column-level lineage where a critical transform
  makes correctness or compliance depend on it.
- **REQUIRED:** Define schema and grain before materializing an output, and name
  its owner and intended consumers.
- **REQUIRED:** Define data-quality, freshness, and volume expectations, including
  how missing, late, duplicate, malformed, or unexpectedly empty data is handled.
- **REQUIRED:** Select a materialization and idempotency strategy; document safe
  rerun behavior, incremental state, and a backfill path.
- **REQUIRED:** Define compatible schema evolution and a migration path for
  breaking changes.
- **REQUIRED:** Specify orchestration boundaries, failure classification, retry
  behavior, and state transitions needed for reliable execution.
- **REQUIRED:** Apply applicable privacy, access, retention, and deletion
  obligations to data and operational state.

## Conditional Controls

- **CONDITIONAL:** For scheduled, incremental, or multi-stage flows, define a
  watermark, manifest, content identity, or equivalent resumable control state.
- **CONDITIONAL:** For partitioned or distributed outputs, declare partitioning,
  completeness, atomic visibility, and recovery behavior.
- **CONDITIONAL:** For non-idempotent writes, paid upstreams, or irreversible
  mutations, require an approved replay, dry-run, or compensation strategy before
  execution.
- **CONDITIONAL:** For sensitive, regulated, or customer data, define access,
  minimization, retention, deletion, and audit controls under applicable policy.
- **CONDITIONAL:** For downstream agent, analytics, or public consumers, provide
  governed definitions and provenance sufficient to judge source, freshness, and
  ownership.
- **CONDITIONAL:** For a breaking schema, grain, or semantic change, version or
  migrate the output and communicate the compatibility window to consumers.
- **PROJECT POLICY:** Thresholds, schedules, storage formats, retry limits,
  delivery channels, and approval requirements come from requirements, baselines,
  regulation, or ADRs—not this module.

## Validation Capabilities

- **REQUIRED:** Obtain evidence for schema/grain conformance, lineage, quality,
  freshness, volume, idempotent reruns, and recovery appropriate to affected risk.
- **REQUIRED:** Validate source assumptions before data movement and verify sink
  state after successful work.
- **CONDITIONAL:** For orchestration changes, exercise transient failure, retry,
  resume, and backfill paths where feasible.
- **CONDITIONAL:** For schema evolution or privacy/retention changes, validate
  compatibility and policy controls with the project-selected authority.
- **PROJECT POLICY:** The Engineering Profile or Gate Ledger names the authority;
  absent authority is a capability gap, deferral, or accepted risk—not a pass.
- **EXAMPLE:** A small representative rerun may evidence idempotency when a full
  production replay is unsafe or unavailable.

## Lifecycle Obligations

- **REQUIRED:** Carry data contracts and validation evidence through the
  Development Kernel and record applicable lifecycle-gate status in the Gate
  Ledger.
- **REQUIRED:** Maintain observability for execution, data state, freshness, and
  failures sufficient for the accountable owner to detect and investigate loss or
  corruption.
- **REQUIRED:** Define recovery ownership and the safe response to partial writes,
  stale state, failed retries, and required backfills.
- **CONDITIONAL:** For long-lived, public, or regulated datasets, plan maintenance,
  deprecation, retention expiry, consumer migration, and retirement or secure
  disposal.
- **PROJECT POLICY:** Project artifacts determine record locations, review,
  release, deployment, and operational procedures; no repository-embedded skill
  or delivery channel is universally required.
- **EXAMPLE:** Optional provider and tool patterns are in
  [`references/data.md`](../references/data.md).
