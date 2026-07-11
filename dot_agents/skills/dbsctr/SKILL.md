---
name: dbsctr
description: Deliver behavior and downstream-visible changes through the DBSCTR V3 development kernel and every applicable review, release, deployment, operations, maintenance, and retirement gate.
trigger: /dbsctr
---

# DBSCTR V3

## Outcome

Deliver the requested change through a language-neutral Development Kernel—
Domain, Behavior, Spec, Contract, Test-driven implementation, and Refactor—then
evaluate Review/Integrate, Release, Deploy, Operate, and Maintain/Retire. No gate
is skipped silently.

Use DBSCTR for behavior, domain, schema, API, service, pipeline, orchestration,
validation, contract, or downstream-visible changes. Skip trivial, formatting,
git-only, dependency-only, or non-behavioral configuration work unless invoked.

## Start

1. Read project instructions, matching specs/ADRs, configured validation, and
   relevant source. Reuse existing artifacts.
2. Check an existing Graphify graph before broad search; verify useful results
   against source and fall back when stale, weak, or irrelevant.
3. Verify the bounded-context Engineering Profile. Run `discovery` to 95%
   confidence when intent, ownership, risk, interfaces, or gate applicability is
   materially unclear.
4. Record current affected scope, risk, delivery intent, applicable modules, and
   required capabilities.
5. Create six Development Kernel todos with exactly one active until complete.

## Progressive Modules

Load only matching modules before Domain. Multiple modules may apply.

| Signal | Module |
|---|---|
| Python source, metadata, runtime, package, or service | `modules/python.md` |
| Elevated/critical security or sensitive-data impact | `modules/security.md` |
| Pipeline, ETL/ELT, stream, warehouse, lake, dataset | `modules/data.md` |
| Cloud, platform, IaC, network, deployment runtime | `modules/cloud.md` |
| Model, prompt, embedding, evaluation, ML/AI serving | `modules/ml.md` |
| Self-service analytics, semantic routing, governed answers | `modules/analytics.md` and, when data changes, `modules/data.md` |

Modules use REQUIRED, CONDITIONAL, PROJECT POLICY, and EXAMPLE. Optional
provider/tool patterns live in `references/` and never gate a cycle by
themselves. A future language/framework module may extend phases and gates but
cannot reorder or weaken core evidence and safety contracts.

## Engineering Profile And Risk

Use bounded-context defaults and record only cycle overrides. Risk is:

- `routine`: localized and reversible without material public, production,
  sensitive-data, security-boundary, money, or safety impact
- `elevated`: public compatibility, migration, external integration, production,
  sensitive data, material reliability/performance, or security-boundary impact
- `critical`: irreversible loss, broad outage, regulated exposure,
  authentication/authorization failure, material financial impact, or safety harm

Risk may rise with new evidence and never falls silently.

## Development Kernel

Complete phases in order; each consumes the prior artifact.

### 1. Domain

Name bounded/adjacent contexts, ubiquitous language, entities, values, events,
owners, sources/sinks, trust boundaries, applicable modules, and affected
artifacts. Update the matching spec.

### 2. Behavior

Write implementation-free Given/When/Then scenarios using Domain terms. Cover
happy paths, edges, failures, recovery, compatibility, abuse cases when
applicable, and downstream-visible outcomes. Resolve consequential ambiguity.

### 3. Spec

Define concrete interfaces, signatures, commands, config/schema shapes, files,
examples, migrations, architecture decisions, and a dependency-aware backlog.
Map each interface to behavior and assign non-overlapping ownership.

### 4. Contract

Define preconditions, postconditions, invariants, boundary validation, failure
semantics, compatibility, migration/rollback, security/reliability/observability
requirements, stale-artifact checks, and validation commands. Apply module
extensions.

### 5. Test-Driven Implementation

Create failing behavior or regression evidence before implementation when the
harness can express it. Confirm failure for the intended reason, implement the
minimum correct change, and obtain passing affected-scope evidence. Record why a
red check was impossible rather than fabricating one. Deploy and smoke-test
managed config or skills when applicable.

### 6. Refactor

With affected behavior passing, remove duplication and stale notes, simplify,
align names with Domain language, update docs/backlog/changelog, and preserve
contracts and evidence. Finish with only intended worktree changes.

## Gate Ledger

Enumerate Development Kernel and completion gates. Each receives exactly one
status:

- `required`: evidence must pass
- `not_applicable`: reason tied to the Engineering Profile
- `deferred`: owner and concrete follow-up
- `accepted_risk`: rationale, owner, and expiry or review condition

Missing or failed required evidence blocks completion. An unavailable preferred
tool creates a capability gap, not a pass.

## Completion Gates

### Review/Integrate

Always evaluate diff coherence, behavior/interface/contract/test traceability,
migration impact, direct downstreams, configured CI, and final orchestrator
review. Independent review is required for critical work when available.

### Release

Apply when producing or publishing a releasable artifact. Record version,
release notes, compatibility/migration, artifact identity, approvals, and
applicable provenance. Planning does not authorize publication.

### Deploy

Apply when changing an environment. Record preview/plan, ordering, migrations,
health evidence, rollback/recovery, owner, and approval. Never perform an
external deployment without explicit authorization.

### Operate

Apply to running systems. Record ownership, health/readiness, applicable logs,
metrics/traces, alerts, incident path, capacity/cost signals, and post-deploy
verification.

### Maintain/Retire

Apply to public or long-lived systems. Record runtime/dependency EOL,
vulnerability intake, support/deprecation, migration, retention, ownership
transfer, access removal, and decommission evidence.

## QA

At evidence checkpoints, call `qa` in scoped mode with touched files, imports,
manifests, packages, tests, specs, downstream contracts, and Engineering Profile
Capability Requirements. Use project-selected authorities; do not install tools.
Unrelated pre-existing findings do not fail scoped work. Explicit full audits
remain user-requested.

## Delegation And OpenCode

Delegate only independent work where benefit exceeds overhead. A write subagent
receives goal, readable/writable files, off-limits paths, dependencies,
collision risk, expected output, and validation. Subagents never stage, commit,
push, deploy, publish, or write outside approved paths. Log agent/model routes.

The primary reviews every Builder patch and owns integration, final validation,
deployment, staging, and commits. Trust sourced research unless uncertain,
contradictory, or controlling a risky edit. Retry a failed optimized route once
with the active same-provider flagship and never cross providers silently.

Plan is read-only and ends with a Build Handoff. Build verifies source and
artifact freshness before writing. Todos and child sessions hold current state;
specs and Git are durable authority.

## Evidence And Git

Evidence checkpoints are mandatory; phase commits are not. Inspect status/diff
and run minimum affected checks at each checkpoint. Follow repository commit
policy and commit only when requested or required by that policy. The primary
alone stages/commits. Never push without explicit request.

In DVC repositories, run `dvc status`; couple changed outputs with their metadata
and run `dvc push` before an explicitly requested Git push.

## Final Response

Lead with outcome. Include applicable modules and gates, validation evidence,
changed files, residual risks, blockers, accepted risks, deployment/restart
requirements, and commits if any. Stop for unresolved context, failed required
evidence, unsafe ownership overlap, or destructive, irreversible, external,
costly, or materially expanded action requiring approval.
