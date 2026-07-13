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
3. Verify the bounded-context Engineering Profile. Run `discovery` when an
   unresolved question can materially change scope, behavior, interfaces,
   safety, delivery, or validation.
4. Record current affected scope, risk, delivery intent, applicable modules, and
   required capabilities.
5. Report Method Revision `3.10`. Use the typed `dbsctr_status` tool when available,
   otherwise `dbsctrctl status`, to resume the active Cycle
   Record. For a new write cycle, create an explicit JSON applicability plan
    bound to the committed Engineering Profile, then obtain authorization before `dbsctr_begin`;
    use typed `dbsctr_begin` or
   `dbsctrctl begin --plan PATH` to create an upstream-based branch/worktree and
   return its handoff. Use
   low-level `start` only in an already prepared clean cycle worktree. Create only
   actionable todos; adjacent kernel concerns may share one item when evidence is
   compact.

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
| Browser UI, product-facing web flow, frontend component, rendered user document | `modules/web.md` |

Modules use REQUIRED, CONDITIONAL, PROJECT POLICY, and EXAMPLE. Optional
provider/tool patterns live in `references/` and never gate a cycle by
themselves. A future language/framework module may extend phases and gates but
cannot reorder or weaken core evidence and safety contracts.
When Product Intent applies, read the Engineering Profile-selected artifact
(conventionally `docs/specs/<context>/PRODUCT.md`) before Domain and trace affected
journeys/outcomes through behavior, contracts, validation, and completion. Do not
invent that artifact for non-product work.

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

Consider phases in dependency order; each consumes the prior artifact. Iterate
back when examples or tests reveal a domain, behavior, interface, or contract
error. Routine work may compress adjacent artifacts when existing stable context
and focused evidence already cover them; no concern is skipped silently.

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

Enumerate Development Kernel and completion gates with separate dimensions:

- Gate Applicability: `required` or `not_applicable` with reason
- Gate Result: `pending`, `passed`, `failed`, `unavailable`, or `not_run`
- Gate Exception: user-approved `deferred` or `accepted_risk` with rationale,
  owner, and expiry or review condition

Missing or failed required evidence blocks completion unless a Gate Exception is
explicitly approved. The agent may propose but never approve an exception. An
unavailable preferred tool creates a capability gap, not a pass.

For new schema-versioned cycles, a gate passes only after every predecessor is
disposed. Record a failure or unavailable authority immediately even when an
earlier gate is open. New evidence may tighten applicability from
`not_applicable` to `required` and reopen dependent passed gates; applicability
and risk never loosen silently. Use `dbsctrctl update-plan --plan PATH` after a
committed Engineering Profile change and `dbsctrctl raise-risk --plan PATH` when
risk rises. Gate Commit and Final Push reject stale profile identity. Schema-less
V3.1 records continue under their legacy transition rules.

## Artifact Lifecycle

Every cycle reviews README, BACKLOG, and CHANGELOG. README holds stable truth and
changes only when durable domain, behavior, interface, contract, Engineering
Profile, or validation truth changes. BACKLOG has one live cycle item and moves
completed work to a concise Completed section. CHANGELOG gets one compact entry
at completion with outcome, validation, exceptions, commits, deployment, and
intended Final Push target. The Cycle Record and final response capture the
actual push result. Record each review with `dbsctrctl review-artifact`; validate with
`dbsctrctl check artifacts`. New Cycle Record state uses the Git common directory;
completed records remain there while each worktree has one active pointer.
Multiple sessions may resume one cycle, but one primary owns integration.
Delivery to the same upstream is serialized by the helper's target lock.
`begin` leaves a dirty source worktree untouched and blocks unknown ahead commits.
After completion, `cleanup` removes only a clean DBSCTR-owned worktree whose
commits reached target; retain successful worktrees for 24 hours by default and
never auto-remove failed or dirty work.
Typed OpenCode tools are argument-safe adapters over `dbsctrctl`, not another
state machine. `dbsctr_begin` asks once before helper execution; denial or
cancellation creates no branch, worktree, Cycle Record, fetch, or Herdr launch.
The `launch` argument defaults to `false`; when explicitly true in a Herdr pane,
the same authorization covers launching OpenCode in the new worktree. Herdr state
is presentation only and never gate evidence.

## Lifecycle Reconciliation Audit

When the user asks for a DBSCTR project/codebase audit, default to report-only.
Use typed `dbsctr_audit` or `dbsctrctl audit --commit HEAD --json` to pin committed
scope, inventory lifecycle triplets, expose excluded dirty overlay, and check
Graphify freshness. Then verify material claims against authoritative source and
classify confirmed drift, stale evidence, missing artifacts, authority conflicts,
historical content, and unverified claims. Do not treat graph inference as source.
Use typed `dbsctr_inspect` for bounded `read`, `tree`, `search`, and `object`
access to that resolved commit; never substitute filesystem reads that include
the dirty overlay.
For semantic reconciliation, load `references/semantic-audit.md`, keep the audit
on the resolved commit, apply its authority order and exact classifications, and
return its report shape. Evidence Envelope metadata may support a trace, but
withheld content remains unavailable. Private local references require explicit
authorization, a pinned commit, and non-public/non-authoritative treatment.

Keep this distinct from `/qa full`: lifecycle audit reconciles artifacts and
traceability; QA runs configured quality authorities. Do not write, archive,
execute external systems, or change statuses during report-only audit. When the
user explicitly approves remediation, turn verified findings into collision-safe
context batches and start each approved isolated DBSCTR cycle separately. Never infer
product/domain truth merely to make documents agree.

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

QA returns a human summary plus structured Gate Result evidence for each
applicable Capability Requirement.

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

For critical work, use an independent read-only reviewer when available. If no
reviewer is available, record a capability gap; do not silently waive review.

## Evidence And Git

At cycle start, use `dbsctrctl begin --plan PATH` to create isolation and record
schema version, committed Engineering Profile identity, explicit gate
applicability, HEAD, branch, upstream, worktree status, pre-cycle ahead commits,
Method Revision, gates, and Artifact Reviews. Use low-level `start` only for an
already prepared clean worktree. This baseline defines which commits the cycle
owns and whether an automatic Final Push can be safe.

Evidence checkpoints and coherent Gate Commits are mandatory when a gate changes
files. After one gate or a small adjacent gate group passes:

1. Inspect status, diff, and recent log.
2. Run affected-scope QA and required gate evidence.
3. Stage only intended files; never stage secrets, unrelated drift, or known
   failing required work.
4. Create one atomic Gate Commit with `dbsctrctl gate-commit --gates ...`; the
   helper rejects incomplete associated gates. Use the repository convention. Combine tiny
   adjacent gates when separate commits would add noise; skip gates with no file
   changes.
5. Verify the commit and remaining worktree state before continuing.

For schema-3 cycles, execute a project-selected authority through
`dbsctrctl record-evidence GATE --authority NAME [--path FILE ...] -- PROGRAM ...`.
This nested authority execution is permission-gated. The helper runs
an argument vector without a shell, stores only conservative metadata and safe
allowlisted output, withholds everything unclassified, and binds passing evidence
to the exact validated path/blob set and its Gate Commit. Do not place secrets in command arguments merely because the
record sanitizes them; use the project-owned secret wrapper and inherited process
environment. Gates with no file changes retain evidence only when its HEAD still
matches Final Push HEAD.

The primary alone stages, commits, and pushes. If hooks reject a commit, fix the
issue and create a new commit; never bypass hooks or rewrite published history.

After all required gates pass, perform one Final Push with `dbsctrctl final-push` to the recorded upstream
without another confirmation when the worktree is clean and only cycle-owned
commits are ahead. The user's standing DBSCTR policy authorizes this normal push.
Verify synchronization with the upstream and report pushed commit IDs.

Stop before push when HEAD is detached, no upstream exists, the destination
changed, pre-cycle ahead commits would be included, required evidence failed,
force would be needed, or repository policy requires another approval.
Never force-push automatically.

In DVC repositories, run `dvc status`, couple changed outputs with their metadata,
and obtain separate approval for `dvc push`. After it succeeds, use
`dbsctrctl record-dvc-push` to bind its evidence to current HEAD; never hide the
DVC external write inside standing Git-push authorization.

## Final Response

Lead with outcome. Include applicable modules and gates, validation evidence,
changed files, residual risks, blockers, accepted risks, deployment/restart
requirements, Gate Commits, and Final Push outcome. Stop for unresolved context, failed required
evidence, unsafe ownership overlap, or destructive, irreversible, external,
costly, or materially expanded action requiring approval.
