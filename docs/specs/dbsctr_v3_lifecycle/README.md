# DBSCTR V3 Lifecycle

**Status:** V3.10 Product Intent and Web/UI implemented
**Discovery readiness:** Complete
**Created:** 2026-07-11

## Overview

DBSCTR V3 is an OpenCode-first, language-neutral software-engineering lifecycle.
It retains Domain, Behavior, Spec, Contract, Test-driven implementation, and
Refactor as its development kernel, then carries evidence through review,
release, deployment, operations, maintenance, and retirement when those gates
apply.

The public OpenCode entry points are `/discovery`, `/dbsctr`, and `/qa`.
OpenCode is the first harness because its skills, commands, todos, agents,
permissions, and Plan/Build separation should shape the workflow directly.
Future harnesses may implement adapters to the same artifacts and contracts.
The approved staged evolution through V3.10 is recorded in [`ROADMAP.md`](ROADMAP.md).

## Problem

DBSCTR2 provides a strong design-to-refactor workflow, but it does not model the
entire software lifecycle. It also treats configured QA tools as the available
evidence without distinguishing missing required capabilities, and its copied
domain modules mix general engineering outcomes with project-specific tools,
providers, budgets, and thresholds.

V1 is obsolete. V2 remains useful as source history but must not remain deployed
or exposed through public commands after V3 is available.

## Goals

- Make V3 the default lifecycle behind unversioned OpenCode skills and commands.
- Keep the core language-neutral and load language, framework, domain, and risk
  modules only when applicable.
- Add first-class Python and Security modules.
- Normalize Data, Cloud, ML/AI, and Analytics modules around outcomes and risk
  triggers rather than provider-specific mandates.
- Persist stable bounded-context defaults and per-cycle overrides in an
  Engineering Profile.
- Require every lifecycle gate to be passed, ruled out, deferred, or accepted as
  risk with explicit evidence.
- Let QA compare required capabilities with configured authorities without
  installing tools.
- Create coherent commits at sensible lifecycle gates and push once after the
  completed cycle passes all required evidence.
- Preserve source history for V2 without deploying it.

## Non-Goals

- Do not build an OpenCode plugin or independent workflow engine.
- Do not optimize prompts for hypothetical alternative harnesses at the expense
  of OpenCode integration.
- Do not prescribe one language, framework, CI provider, package manager,
  deployment platform, or observability backend.
- Do not require release, deployment, or operational gates when the Engineering
  Profile rules them out.
- Do not automatically install tools, publish artifacts, deploy systems, or
  perform other external writes.
- Do not select a new public brand during this implementation.

## Bounded Context

`dbsctr_v3_lifecycle` owns lifecycle discovery, development phases, gate
applicability, evidence continuity, module selection, QA capability coverage,
OpenCode integration, and V1/V2 migration.

Adjacent contexts:

- `quality_assurance`: executes configured authorities and reports capability
  gaps.
- `opencode_control_plane`: owns agents, permissions, providers, and command
  loading.
- `graph_aware_skill_routing`: supplies repository-routing hints.
- Project toolchains: own actual commands, baselines, suppressions, and policies.
- Release and deployment platforms: remain external systems requiring explicit
  authorization.

## Ubiquitous Language

| Term | Definition |
|---|---|
| DBSCTR V3 | The complete OpenCode-first lifecycle and its extension modules. |
| Development Kernel | Domain, Behavior, Spec, Contract, Test-driven implementation, and Refactor. |
| Engineering Profile | Stable bounded-context defaults plus current-cycle overrides that determine applicable modules, risks, and gates. |
| Lifecycle Cycle | One bounded change carried from discovery through every applicable completion gate. |
| Lifecycle Gate | A decision point with separate applicability, result, evidence, and optional exception. |
| Gate Ledger | Evidence table recording applicability, authority, result, owner, and expiry where relevant. |
| Capability Requirement | An outcome that needs evidence, independent of the tool used to prove it. |
| Capability Authority | The project-selected command or service whose result gates one concern. |
| Module | Progressive guidance loaded for an applicable language, framework, domain, or risk. |
| Normative Label | `REQUIRED`, `CONDITIONAL`, `PROJECT POLICY`, or `EXAMPLE`. |
| Risk Level | `routine`, `elevated`, or `critical`. |
| Delivery Intent | Local change, merge, release, or deployment. |
| Accepted Risk | A failed or unavailable requirement accepted with rationale, owner, and expiry. |
| OpenCode Adapter | Skills, commands, todos, agents, and permissions implementing the lifecycle in OpenCode. |
| V2 Archive | Source-only historical V2 skills that are excluded from deployment. |
| Gate Commit | Atomic commit containing one coherent gate increment; tiny adjacent gates may combine. |
| Final Push | One normal push of completed cycle commits to the recorded upstream after all required gates pass. |
| Push Readiness | Verified branch, upstream, clean worktree, passing evidence, and no unrelated pre-cycle commits included. |
| Cycle Record | Local operational state for one cycle, retained in the Git common directory and not treated as durable repository evidence. |
| Worktree Identity | Stable hash of a cycle worktree's canonical path, used to isolate its active pointer. |
| Delivery Target Lock | Nonblocking local lock serializing readiness checks and delivery to one upstream target. |
| Artifact Review | A recorded decision that README, BACKLOG, and CHANGELOG are accurate, including an explicit no-change reason where applicable. |
| Gate Applicability | Whether a gate is `required` or `not_applicable`, with rationale. |
| Gate Result | `pending`, `passed`, `failed`, `unavailable`, or `not_run`; separate from applicability. |
| Gate Exception | A user-approved `deferred` or `accepted_risk` disposition with owner and review condition. |
| Method Revision | The lifecycle contract revision loaded by the active process. |
| Applicability Plan | Explicit JSON input declaring the Engineering Profile and applicability of every gate for a new cycle. |
| Cycle Record Schema | Integer version for the serialized Cycle Record shape, independent of Method Revision. |
| Fixed-Commit Inspection | Read-only access to repository objects after resolving one immutable commit identity. |
| Evidence Envelope | Sanitized metadata plus an optional hash-addressed local sidecar proving a gate result. |
| Product Intent | Conditional product-facing context held in `PRODUCT.md` and referenced by an Engineering Profile. |

## Domain Model

### Entities

- **Bounded Context:** owns stable Engineering Profile defaults and lifecycle
  artifacts.
- **Lifecycle Cycle:** owns current change scope, overrides, selected modules,
  and Gate Ledger.
- **Lifecycle Gate:** owns applicability, required evidence, status, and owner.
- **Capability Requirement:** owns one engineering outcome and selected
  authority.
- **Module:** owns progressive domain guidance and optional references.
- **QA Run:** executes authorities for an affected scope and Engineering Profile.
- **Evidence Envelope:** retains bounded, sanitized gate evidence without secret
  or environment-value capture.
- **Product Intent:** owns users, outcomes, journeys, constraints, accessibility,
  trust boundaries, compatibility, and retirement for product-facing contexts.

### Value Objects

- Risk Level
- Gate Status
- Delivery Intent
- Validation Evidence
- Accepted Risk Record
- Module Applicability
- Normative Label

### Domain Events

- `EngineeringProfileEstablished`
- `CycleOverridesRecorded`
- `ModuleSelected`
- `GateRequired`
- `GateRuledOut`
- `CapabilityGapFound`
- `GatePassed`
- `RiskAccepted`
- `ReleaseApproved`
- `DeploymentVerified`
- `LifecycleCompleted`
- `CycleStarted`
- `ArtifactReviewed`
- `GateEvaluated`
- `GateExceptionApproved`
- `RiskRaised`
- `GateApplicabilityTightened`
- `CommitResolved`
- `EvidenceRecorded`
- `EvidenceWithheld`
- `ProductIntentSelected`

### Sources And Sinks

Sources include user intent, project instructions, existing specifications,
ADRs, manifests, lockfiles, CI, task runners, code, tests, Graphify output, and
configured quality authorities.

Sinks include updated specifications, backlogs, changelogs, code, tests,
packages, release evidence, deployment plans, operational evidence, maintenance
records, and retirement decisions. External writes remain approval-gated.

## Behavior Scenarios

### Feature: OpenCode Entry Points

**Scenario: Route lifecycle work to V3**
- Given OpenCode reads the managed global routing instructions
- When a request changes behavior, contracts, schemas, validation, services,
  pipelines, orchestration, or downstream-visible output
- Then OpenCode loads the unversioned `dbsctr` skill
- And it loads `discovery` first when intent or the bounded context is unclear

**Scenario: Invoke public commands**
- Given the managed commands are deployed
- When the user invokes `/discovery`, `/dbsctr`, or `/qa`
- Then the command loads the matching unversioned skill
- And no public V1, V2, or V3-numbered lifecycle command is exposed

### Feature: Engineering Profile

**Scenario: Reuse bounded-context defaults**
- Given a bounded context has an Engineering Profile
- When a Lifecycle Cycle begins
- Then stable deliverable, runtime, ownership, compatibility, and data defaults
  are reused
- And only current-cycle risk, delivery, scope, or gate overrides are added

**Scenario: Scale obligations by risk**
- Given a change is classified as routine, elevated, or critical
- When applicable gates and modules are selected
- Then evidence requirements increase only for relevant impact and trust
  boundaries
- And routine work is not burdened with unrelated release or operational gates

### Feature: Development And Completion

**Scenario: Execute the development kernel**
- Given intent and the Engineering Profile are adequate
- When implementation begins
- Then Domain, Behavior, Spec, Contract, Test-driven implementation, and Refactor
  execute in order
- And each phase consumes the prior phase's artifacts

**Scenario: Evaluate the complete lifecycle**
- Given the Development Kernel is complete
- When DBSCTR evaluates review, release, deployment, operations, maintenance, and
  retirement
- Then every gate receives evidence and a Gate Status
- And no gate is skipped silently

**Scenario: Prevent unauthorized delivery**
- Given release, deployment, or another external write is required
- When the user has not explicitly authorized that action
- Then DBSCTR prepares and validates the plan without performing the write
- And reports the approval needed to continue

### Feature: Capability-Aware QA

**Scenario: Run configured authorities**
- Given a Lifecycle Cycle supplies affected scope and an Engineering Profile
- When QA runs in scoped mode
- Then it executes the project-selected authority for each applicable configured
  concern
- And it does not install an unconfigured tool

**Scenario: Expose missing required capability**
- Given an applicable Capability Requirement has no available authority or
  equivalent evidence
- When QA evaluates the Gate Ledger
- Then it records a capability gap rather than a pass
- And completion requires remediation, deferral, or an Accepted Risk

### Feature: Progressive Modules

**Scenario: Load Python guidance only for Python work**
- Given source, manifests, or the Engineering Profile identify Python
- When DBSCTR selects modules
- Then it loads the Python module
- And a non-Python cycle does not inherit Python-specific requirements

**Scenario: Add a future language or framework module**
- Given a new module follows the common applicability and normative contract
- When its trigger matches a Lifecycle Cycle
- Then DBSCTR can load it without changing the Development Kernel

**Scenario: Keep examples non-normative**
- Given a module references a tool, provider, threshold, or budget
- When no Project Policy makes that choice authoritative
- Then the guidance is labeled EXAMPLE
- And it cannot fail a lifecycle gate merely because another implementation was
  selected

### Feature: Version Migration

**Scenario: Replace V1 with V3**
- Given unversioned V1 source currently deploys as `discovery` and `dbsctr`
- When V3 is deployed
- Then those unversioned paths contain V3
- And no V1 workflow remains active

**Scenario: Preserve V2 as source history only**
- Given V2 source remains useful for reference
- When migration completes
- Then V2 is stored beneath the documentation archive
- And V2 skills and commands are absent from deployed OpenCode paths

### Feature: OpenCode-Native State

**Scenario: Hand planning to implementation**
- Given Plan is read-only
- When discovery or architecture reaches implementation readiness
- Then Plan returns a Build Handoff containing scope, constraints, artifacts,
  validation, risks, unresolved decisions, and recommended Build agent
- And Build verifies source freshness before writing

**Scenario: Commit sensible gate increments**
- Given a lifecycle phase or completion gate finishes
- And its evidence passes
- When its changes form a coherent reviewable increment
- Then the primary stages only intended files and creates a Gate Commit
- And tiny adjacent gates may share one commit instead of creating noise

**Scenario: Push the completed cycle**
- Given every required gate passes and all Gate Commits exist
- And the current branch and upstream were recorded at cycle start
- When the worktree is clean and the push contains no unrelated pre-cycle commits
- Then the primary performs one normal Final Push without another confirmation
- And verifies the branch is synchronized with its upstream

**Scenario: Stop an unsafe automatic push**
- Given Final Push would include unrelated pre-cycle commits, lacks an upstream,
  requires force, or follows a failed DVC push
- When DBSCTR evaluates Push Readiness
- Then it stops before Git push
- And reports the exact approval or remediation required

**Scenario: Keep active state out of stable specifications**
- Given a Lifecycle Cycle begins
- When DBSCTR records its Git baseline, current gate, and evidence
- Then it stores that operational state beneath `.git/dbsctr/`
- And durable specifications contain only stable context and completed evidence

**Scenario: Review every lifecycle artifact without meaningless edits**
- Given a Lifecycle Cycle is active
- When its Artifact Review runs
- Then README, BACKLOG, and CHANGELOG are each marked reviewed
- And README changes only when durable domain, behavior, interface, contract,
  profile, or validation truth changed

**Scenario: Evaluate a required gate**
- Given a Lifecycle Gate has `required` applicability
- When its selected evidence passes
- Then its Gate Result becomes `passed`
- And applicability remains separate from the result

**Scenario: Handle a gate exception**
- Given a required Lifecycle Gate cannot pass
- When DBSCTR proposes deferral or Accepted Risk
- Then completion remains blocked until the user approves the Gate Exception
- And the exception records rationale, owner, and expiry or review condition

**Scenario: Scale evidence without skipping the kernel**
- Given a Lifecycle Cycle is routine, elevated, or critical
- When DBSCTR plans its artifacts and evidence
- Then all Development Kernel concerns are considered in dependency order
- And adjacent concerns may be compressed when existing artifacts and focused
  evidence already cover the change

### Feature: V3.2 Protocol Correctness

**Scenario: Start from an explicit applicability plan**
- Given a committed Engineering Profile and a plan defining every gate
- When a new Lifecycle Cycle starts
- Then the Cycle Record stores Method Revision `3.2`, schema version `1`, and the
  profile Git blob identity
- And mandatory or delivery-required gates cannot be ruled out

**Scenario: Preserve a legacy active cycle**
- Given an active schema-less V3.1 Cycle Record
- When its gates, commits, or Final Push continue
- Then V3.1 transition rules remain available without implicit migration

**Scenario: Enforce dependency order without hiding failure**
- Given an earlier required gate is not disposed
- When a later gate attempts to pass
- Then the transition is rejected
- But a later failure or unavailable authority may be recorded immediately

**Scenario: Tighten cycle rigor**
- Given new evidence raises risk or makes a previously inapplicable gate required
- When the primary records the stricter plan
- Then risk and applicability tighten and dependent passed gates reopen
- And neither risk nor applicability can loosen within the active cycle

### Feature: Approved V3.7–V3.10 Evolution

**Scenario: Inspect one committed repository state**
- Given a caller supplies a Git reference and repository-relative scope
- When fixed-commit inspection begins
- Then the reference resolves once and all reads use that immutable object ID
- And dirty overlay, traversal, repository escape, mutation, and unbounded output
  are excluded or rejected explicitly

**Scenario: Retain evidence without retaining secrets**
- Given a project-selected authority produces gate evidence
- When DBSCTR records an Evidence Envelope
- Then it stores sanitized invocation metadata and hash-addressed local output
- And environment values, stdin, resolved `op://` values, secret-bearing URLs,
  and unclassifiable output are never persisted

**Scenario: Reconcile semantic claims without mutation**
- Given lifecycle claims and evidence exist at one resolved commit
- When a semantic reconciliation audit runs
- Then it classifies each material claim against source and project policy
- And every remediation requires a separately approved context-scoped cycle

**Scenario: Load Product Intent conditionally**
- Given an Engineering Profile identifies product-facing behavior
- When Discovery selects durable product artifacts
- Then the selected authoritative artifact records the applicable Product Intent
- And Discovery creates `PRODUCT.md` only when no existing artifact satisfies it
- And non-product work receives no synthetic Product Intent

**Scenario: Load Web/UI guidance conditionally**
- Given an Engineering Profile identifies browser UI or frontend component work
- When DBSCTR selects modules
- Then the Web/UI module applies with WCAG 2.2 AA by default
- And non-browser product work receives no UI gates

## Engineering Profile

### Defaults

| Field | Value |
|---|---|
| Deliverable | OpenCode lifecycle skills, commands, routing, modules, and tests |
| Languages/frameworks | Language-neutral Markdown prompts; Python contract tests |
| Modules | Python, Security, Data, Cloud, ML/AI, Analytics, Web/UI |
| Runtime/platform support | OpenCode on the managed dotfiles environment; Python `>=3.12` test harness |
| Public compatibility | Unversioned `/discovery`, `/dbsctr`, and `/qa`; V1 removed; V2 source archived |
| Trust/data classification | Local configuration and public methodology; no sensitive application data |
| Operational owner | Dotfiles owner maintains deployment and OpenCode compatibility |

### Approved V3.1 Evolution

| Field | Value |
|---|---|
| Risk | Elevated: changes global workflow routing and deployed skill behavior |
| Delivery intent | Local deployment through chezmoi; no publication or remote deployment |
| Scope | Lifecycle skills/modules, QA, commands, routing, archive, specs, tests, CI |
| Overrides | Preserve public commands; add local cycle state, deterministic checks, artifact review, and safe Git actions without a plugin |

### V3.2 Cycle Overrides

| Field | Value |
|---|---|
| Risk | Elevated: changes serialized state and gate-transition contracts |
| Delivery intent | Deploy managed helper and skills locally after validation |
| Scope | Cycle schema, applicability plan, gate order, risk raising, compatibility, roadmap |
| Overrides | Preserve schema-less V3.1 completion; defer worktree registry and automation to V3.3/V3.4 |

### V3.6.2 Cycle Overrides

| Field | Value |
|---|---|
| Risk | Elevated: authorization boundary controls Git fetch/branch/worktree creation and optional Herdr launch |
| Delivery intent | Merge; local managed-config deployment remains orchestrator-owned after validation |
| Scope | `dbsctr_begin` authorization, narrow destructive-command prompts, Cycle Record Method Revision, compatibility evidence |
| Overrides | Keep public commands and schema unchanged; no helper runs when OpenCode denies or cancels begin authorization |

### Approved V3.7–V3.10 Evolution

| Field | Value |
|---|---|
| Risk | Elevated: introduces repository-read and evidence trust boundaries |
| Delivery intent | Separate isolated merge/deploy cycles per milestone |
| Scope | Fixed-commit inspection, evidence envelopes, semantic reconciliation, conditional Product Intent and Web/UI guidance |
| Overrides | Preserve public commands and compatibility; keep Graphify and Herdr runtime hygiene in separate cycles |

### V3.7 Cycle Overrides

| Field | Value |
|---|---|
| Risk | Elevated: adds a bounded repository-read trust boundary exposed to agents |
| Delivery intent | Merge and deploy the helper, skill, typed tool, and permission locally |
| Scope | Fixed-commit `read`, `tree`, `search`, and `object`; limits, compatibility, and runtime evidence |
| Overrides | Keep schema version 2 and public commands; exclude V3.8 evidence envelopes and runtime hygiene |

### V3.8 Cycle Overrides

| Field | Value |
|---|---|
| Risk | Elevated: executes project authorities and retains local evidence near Cycle Records |
| Delivery intent | Merge and deploy helper, skill, permission, and conditional Python reference locally |
| Scope | Schema-3 Evidence Envelopes, conservative output retention, Gate Commit binding, and cleanup coupling |
| Overrides | No typed write tool; no canonical URL retention without future committed allowlist policy; exclude V3.9 semantics |

### V3.9 Cycle Overrides

| Field | Value |
|---|---|
| Risk | Elevated: agent interpretation compares lifecycle claims with multiple authority levels |
| Delivery intent | Merge and deploy the semantic audit protocol and skill locally |
| Scope | Fixed-commit claim tracing, exact classifications, report schema, privacy, and remediation boundaries |
| Overrides | Reuse V3.7 inspection and V3.8 metadata; no new write tool, automatic remediation, or `/qa full` execution |

### V3.10 Cycle Overrides

| Field | Value |
|---|---|
| Risk | Elevated: changes Discovery artifacts and global Web/UI accessibility guidance |
| Delivery intent | Merge and deploy Discovery/DBSCTR skills, Web/UI module, and references locally |
| Scope | Conditional Product Intent, WCAG 2.2 AA outcomes, non-normative tool examples, and project-local MCP boundary |
| Overrides | Preserve project authorities; no synthetic Product Intent, mandatory frontend dependency, or global MCP configuration |

## Gate Ledger — V3.1 Completion

| Gate | Capability | Applicability | Result | Authority/evidence | Exception | Owner |
|---|---|---|---|---|---|---|
| Domain | Bounded context and language | required | passed | V3.1 specification | - | Primary |
| Behavior | Observable lifecycle scenarios | required | passed | V3.1 scenarios | - | Primary |
| Spec | Interfaces and collision-safe backlog | required | passed | README and BACKLOG | - | Primary |
| Contract | Profile, gate, module, QA, migration invariants | required | passed | V3.1 contracts | - | Primary |
| Test-driven implementation | Failing then passing lifecycle contracts | required | passed | Intended failures; 206 tests | - | Primary |
| Refactor | No stale runtime surfaces or active docs | required | passed | Diff and artifact review | - | Primary |
| Review/Integrate | Integrated diff review | required | passed | Primary review; reviewer-openai no findings | - | Primary |
| Release | Publish a versioned external artifact | not_applicable | not_run | No release requested | - | User |
| Deploy | Apply managed skills and commands locally | required | passed | Chezmoi apply/status | - | Primary |
| Operate | Verify new OpenCode processes load V3.1 | required | passed | Live command and reviewer probes | - | Primary |
| Maintain/Retire | Keep V3.1 maintainable and compatible | required | passed | Compatibility and CI contracts | - | Primary |

## Gate Ledger — V3.2 Completion

| Gate | Capability | Applicability | Result | Authority/evidence | Exception | Owner |
|---|---|---|---|---|---|---|
| Domain | Planned lifecycle vocabulary and roadmap | required | passed | V3.2 specification and roadmap | - | Primary |
| Behavior | Planned, ordered, monotonic transitions | required | passed | V3.2 scenarios | - | Primary |
| Spec | Plan, CLI, schema, and compatibility interfaces | required | passed | README and BACKLOG | - | Primary |
| Contract | Applicability, order, risk, profile, legacy invariants | required | passed | V3.2 contracts | - | Primary |
| Test-driven implementation | Intended failures then passing transitions | required | passed | 23 helper tests; 214 total | - | Primary |
| Refactor | Review findings resolved minimally | required | passed | Profile, JSON, and object-format fixes | - | Primary |
| Review/Integrate | Integrated independent review | required | passed | reviewer-openai: No findings | - | Primary |
| Release | Publish external artifact | not_applicable | not_run | No release requested | - | User |
| Deploy | Apply managed helper and skills locally | required | passed | Chezmoi dry-run/apply | - | Primary |
| Operate | Verify fresh OpenCode processes | required | passed | DBSCTR and Discovery probes | - | Primary |
| Maintain/Retire | Preserve supported cycle compatibility | required | passed | V3.1 and unknown-schema tests | - | Primary |

## Architecture

```text
OpenCode AGENTS routing
  ├─ /discovery → discovery skill
  │    └─ Engineering Profile + DBSCTR-ready artifacts
  ├─ /dbsctr → dbsctr skill
  │    ├─ Development Kernel
  │    ├─ applicable modules and references
  │    └─ completion gates + Gate Ledger
  └─ /qa → qa skill
       └─ configured authorities + optional capability profile

Stable state: docs/specs/<bounded_context>/README.md
Development history: BACKLOG.md, CHANGELOG.md, tests, commits, and CI
Active cycle state: .git/dbsctr/<cycle>.json plus OpenCode todos
Integration authority: Git
```

Skills own reasoning and orchestration. Thin commands expose stable entry points.
Project instructions and configured tools remain authoritative. A future harness
adapter must implement these contracts rather than copy OpenCode-specific prompt
mechanics.

## Engineering Profile Shape

The matching bounded-context README contains this compact shape:

```markdown
## Engineering Profile

### Defaults
| Field | Value |
|---|---|
| Deliverable | library, CLI, application, service, pipeline, ML system, IaC, docs/config |
| Languages/frameworks | project values |
| Modules | selected module names |
| Runtime/platform support | supported versions and environments |
| Public compatibility | API/schema/CLI/data compatibility policy |
| Trust/data classification | boundaries and sensitivity |
| Operational owner | accountable owner or not applicable |

### Cycle Overrides
| Field | Value |
|---|---|
| Risk | routine, elevated, critical |
| Delivery intent | local, merge, release, deploy |
| Scope | affected artifacts and downstreams |
| Overrides | only values differing from defaults |

## Gate Ledger
| Gate | Capability | Applicability | Result | Authority/evidence | Exception | Owner |
|---|---|---|---|---|---|---|
```

## Module Layout

```text
dot_agents/skills/dbsctr/
  SKILL.md
  modules/
    python.md
    security.md
    data.md
    cloud.md
    ml.md
    analytics.md
    web.md
  references/
    data.md
    cloud.md
    ml.md
    analytics.md
    python.md
    semantic-audit.md
    web.md
```

Each module contains applicability, Engineering Profile extensions, vocabulary,
required outcomes, conditional controls, validation capabilities, and
delivery/operations/retirement obligations. References contain non-normative
tool and provider examples and load only when useful.

## Interfaces

| Interface | Purpose | Behaviors |
|---|---|---|
| `dot_agents/skills/discovery/SKILL.md` | V3 intent discovery and Engineering Profile creation | Engineering Profile, OpenCode-native state |
| `dot_agents/skills/dbsctr/SKILL.md` | V3 development kernel and completion-gate orchestration | Development and completion, progressive modules |
| `dot_agents/skills/dbsctr/modules/*.md` | Language, domain, and risk extensions | Progressive modules |
| `dot_agents/skills/dbsctr/references/*.md` | Optional non-normative examples | Keep examples non-normative |
| `docs/specs/<context>/PRODUCT.md` | Conditional durable Product Intent | Product-facing users, outcomes, journeys, constraints, and obligations |
| `dot_agents/skills/qa/SKILL.md` | Scoped/full QA plus optional capability coverage | Capability-aware QA |
| `private_dot_config/opencode/commands/{discovery,dbsctr,qa}.md` | Stable public command surfaces | Public commands |
| `private_dot_config/opencode/AGENTS.md` | Default V3 routing and execution policy | Route lifecycle work to V3 |
| `docs/archive/opencode/skills/v2/**` | Non-deployed V2 source history | Preserve V2 as source history only |
| `.chezmoiremove` | Remove deployed V2 skills and commands | Version migration |
| `tests/test_dbsctr_lifecycle.py` | Deterministic lifecycle and migration contracts | All static contracts |
| `.github/workflows/test.yml` | Run contract tests when lifecycle sources change | Integration validation |

## OpenCode Execution Interfaces

- `/discovery $ARGUMENTS` loads `discovery` and creates or updates the matching
  artifacts after no unresolved question can materially change implementation.
- `/dbsctr $ARGUMENTS` loads `dbsctr`, verifies the Engineering Profile, creates
  actionable todos, and evaluates completion gates. Cycle state and safe Git
  actions use `dbsctrctl`.
- `/qa $ARGUMENTS` loads `qa`; DBSCTR supplies affected scope and required
  capabilities, while an explicit user request may run a full audit.
- Plan remains read-only and produces a Build Handoff. Build verifies freshness,
  owns integration, and alone invokes safe Gate Commit or Final Push operations.

## Contracts And Invariants

### Engineering Profile Contract

- **Pre:** Discovery can name the bounded context or continues interviewing.
- **Pre:** Existing project instructions, specs, ADRs, manifests, CI, and
  configured validation have been inspected.
- **Post:** Defaults record deliverable, languages/frameworks, modules,
  runtime/platform support, compatibility, trust/data classification, and owner.
- **Post:** Current-cycle overrides record risk, delivery intent, affected scope,
  and only values that differ from defaults.
- **Invariant:** Missing information that changes gate applicability prevents a
  profile from being declared ready.
- **Invariant:** Stable defaults are updated once rather than copied into every
  cycle.

### Risk Contract

- `routine`: localized and reversible, with no material public compatibility,
  sensitive-data, production, security-boundary, money, or safety impact.
- `elevated`: affects a public interface, migration, external integration,
  production deployment, sensitive data, material performance/reliability, or a
  security boundary.
- `critical`: can cause irreversible loss, broad outage, regulated exposure,
  authentication/authorization failure, material financial impact, or safety
  harm.
- **Invariant:** Risk may be raised by new evidence but never lowered silently.
- **Invariant:** Critical work requires explicit rollback/recovery evidence and
  independent review where a reviewer is available.

### Gate Ledger Contract

- **Pre:** Every Development Kernel and completion gate is enumerated.
- **Post:** Each gate records capability, applicability, result, authority or
  evidence, and owner.
- Applicability is exactly `required` or `not_applicable`; the latter requires a
  reason tied to the Engineering Profile and has result `not_run`.
- Result is exactly `pending`, `passed`, `failed`, `unavailable`, or `not_run`.
- A Gate Exception is `deferred` or `accepted_risk` and requires explicit user
  approval, rationale, owner, and expiry or review condition.
- **Invariant:** A required gate with missing or failed evidence blocks lifecycle
  completion unless an approved Gate Exception disposes it.
- **Invariant:** No gate is omitted because its preferred tool is unavailable.
- A missing Capability Authority is represented as an `unavailable` Gate Result
  with evidence; `pending` never qualifies for a Gate Exception.

### Artifact Lifecycle Contract

- Every cycle has one BACKLOG item before implementation and updates its state as
  work progresses.
- README, BACKLOG, and CHANGELOG each receive an Artifact Review before completion.
- Applicable Product Intent is reviewed when affected; it is not a fourth
  universal lifecycle artifact and does not alter the helper's fixed reviews.
- README changes only when durable truth changes; a no-change review is valid.
- Completed backlog work moves to a concise Completed section with date and commit.
- Every completed cycle receives one compact CHANGELOG entry with outcome,
  evidence, exceptions, commits, deployment, and intended Final Push target.
- The actual Final Push result is written to the local Cycle Record and final
  response because it cannot truthfully appear in a commit made before that push.
- Active Cycle Records stay beneath `.git/dbsctr/`; they are not portable or
  durable authority.

### Readiness And Scaling Contract

- Discovery is ready when no unresolved question can materially change scope,
  behavior, interfaces, safety, delivery, or validation; percentages are
  descriptive only.
- Routine work may compress adjacent phase artifacts when existing durable
  context plus focused regression evidence covers them.
- Elevated work records explicit behavior, contracts, compatibility/recovery,
  and structured gate evidence where applicable.
- Critical work additionally requires independent review when available and
  explicit threat, recovery, staged-delivery, and operational acceptance evidence.

### Development Kernel Contract

- Domain, Behavior, Spec, Contract, Test-driven implementation, and Refactor run
  in order for non-trivial behavior changes.
- Tests or equivalent failing evidence precede implementation where a harness can
  express the behavior; exceptions are recorded rather than fabricated.
- Refactor begins only after affected behavior passes.
- Evidence checkpoints and coherent Gate Commits are mandatory when a gate
  changes files; gates with no changes create no commit.
- Direct and delegated changes receive final orchestrator review and affected-
  scope validation.

### Completion Gate Contract

- **Review/Integrate:** always evaluate diff coherence, scenario/contract
  traceability, migration impact, and configured CI requirements.
- **Release:** required only when producing or publishing a releasable artifact;
  records version, notes, compatibility, artifact identity, and approvals.
- **Deploy:** required only for delivery to an environment; records preview,
  migration order, health verification, rollback, and authorization.
- **Operate:** required for running systems; records ownership, health signals,
  logs/metrics/traces as applicable, alerts, incident path, and post-deploy check.
- **Maintain/Retire:** required for supported public or long-lived systems;
  records runtime/dependency EOL, vulnerability intake, deprecation, migration,
  retention, and decommission obligations.
- **Invariant:** planning a release or deployment does not authorize its external
  execution.

### QA Capability Contract

- **Pre:** QA receives mode, affected scope, configured Toolchain Profile, and
  optional Engineering Profile requirements.
- **Post:** Configured authorities run as today for V2-compatible calls without
  capability requirements.
- **Post:** V3 calls classify each applicable requirement as evidenced, missing,
  unavailable, failed, deferred, or accepted risk.
- **Invariant:** QA does not install tools or invent a pass from next-best
  evidence.
- **Invariant:** One project-selected authority gates each concern.
- **Invariant:** Unrelated pre-existing findings do not fail scoped work.

### Module Contract

- A module declares applicability triggers and Engineering Profile extensions.
- Normative guidance uses only REQUIRED, CONDITIONAL, PROJECT POLICY, or EXAMPLE.
- REQUIRED describes an outcome universal to the module's applicable context.
- CONDITIONAL names the exact risk or product-shape trigger.
- PROJECT POLICY cites the project artifact that makes a choice authoritative.
- EXAMPLE cannot gate a cycle.
- Provider/tool details and worked examples live in `references/` unless needed to
  state a concise interoperability contract.
- Numeric thresholds and budgets come from requirements, baselines, regulation,
  or ADRs; illustrative values remain examples.
- Future language/framework modules can extend phases and gates but cannot reorder
  or weaken the Development Kernel, safety boundaries, or evidence statuses.

### Python Module Contract

- Detect Python from the Engineering Profile, Python source, or standard project
  metadata; do not load it for unrelated repositories.
- Use project-selected tools first and prescribe no universal package manager,
  formatter, linter, test framework, or type checker.
- Cover runtime support, isolated/reproducible environments, dependency groups
  and lock authority, formatting/linting, typing, tests, security, packaging, CI,
  release, operations, and deprecation when applicable.
- Libraries use compatible runtime dependency ranges; applications may require
  exact deployment locks.
- Supported runtime claims are checked against CI evidence, including the oldest
  and newest supported stable Python where practical.
- Coverage is evidence, not a universal correctness threshold.

### Security Module Contract

- Baseline trust-boundary, secret, dependency, and unsafe-input considerations
  remain in the core.
- Load the Security module for elevated or critical security/data impact.
- Select controls by threat, impact, regulation, and project policy rather than a
  universal scanner list.
- Accepted security risk always has an owner and expiry/review condition.

### Migration Contract

- Unversioned `discovery` and `dbsctr` source paths become V3 in place.
- V1 content is removed with explicit user authorization.
- V2 source moves under `docs/archive/opencode/skills/v2/`, which is already
  excluded from chezmoi deployment through the repository's `docs/` rule.
- Versioned command sources and deployed V2 skills/commands are removed.
- Public `/discovery`, `/dbsctr`, and `/qa` commands remain thin and inherit the
  selected primary.
- Active specs and tests describe V3; historical changelog evidence may retain
  versioned names when clearly historical.

### OpenCode Adapter Contract

- Global routing selects unversioned V3 skills by default.
- Discovery and DBSCTR use OpenCode todos for current state and specs/Git for
  durable state.
- Plan performs no writes and ends with a Build Handoff.
- Write subagents receive non-overlapping ownership and never stage, commit,
  deploy, publish, or write outside approved paths.
- The primary reviews every Builder patch and owns integration and validation.
- No plugin is introduced until measured workflow failures justify it.
- The loaded Method Revision and active cycle are reported at DBSCTR entry.
- Raw Git writes remain permission-gated; narrowly allowed `dbsctrctl` actions
  perform deterministic checks before commit or push.
- Global `dbsctr_begin` permission is `ask`; Plan and reviewer agents deny it and
  selected Build agents allow it. `dbsctr_status` and `dbsctr_audit` remain allowed
  read-only tools.
- `dbsctr_begin` calls OpenCode `context.ask` once before any `beginCycle` helper
  execution. Denial or cancellation performs no fetch, branch, worktree, Cycle
  Record, or Herdr launch. `launch` defaults to `false`.
- `dbsctrctl cleanup*` and destructive Herdr commands ask explicitly; normal
  `herdr agent start` remains unchanged.

### Cycle Record Interface

`dbsctrctl` stores JSON beneath `.git/dbsctr/` with `method_revision`, independent
`schema_version`, `cycle_id`, `context`, `risk`, `delivery_intent`, committed
Engineering Profile identity, applicability plan, Git baseline, current state,
gates, Evidence Envelopes, Artifact Reviews, and created commits. Commands are `begin`, `start`,
`status`, `audit`, `review-artifact`, `set-applicability`, `set-gate`,
user-confirmed `approve-exception`, `record-dvc-push`, `record-evidence`, `raise-risk`,
`update-plan`, `check artifacts`, `gate-commit`, `final-push`, and `cleanup`.
`update-plan` rebinds a committed profile using an equal or stricter plan.
`gate-commit --gates ...` binds each commit to completed gates.

New cycles require `start --plan PATH`, where `-` reads JSON from stdin. The plan
names `docs/specs/<context>/README.md` and defines every gate as `required` or
reasoned `not_applicable`. The helper records the profile's committed Git blob.
Kernel gates and Review/Integrate are always required; release and deploy intents
require their matching completion gates.

For schema version `1`, a gate passes only after every predecessor is disposed.
Failures and unavailable authorities remain recordable out of order. Risk may
only rise through `raise-risk --plan`; its plan may tighten
`not_applicable` to `required` but cannot loosen applicability. Tightening or
reopening an earlier gate invalidates later passed gates. Schema-less V3.1 records
continue under legacy transitions and are never migrated implicitly.
Gate Commit and Final Push verify that the current profile blob still matches the
record; a committed profile change requires `update-plan` or `raise-risk` first.

Schema version `2`, shared by Method Revisions `3.3` through `3.7`, stores records beneath
`<git-common-dir>/dbsctr/cycles/`. Each worktree owns one pointer beneath
`worktrees/<worktree-id>/active`, so linked worktrees can run independent cycles
while cycle IDs remain globally unique. Records include worktree path, Git
directory, branch, base commit, creation authority, upstream, and lock identity.
schema-less/schema-1/schema-2 records remain readable without implicit rewriting.
Method Revision `3.8` creates schema version `3` records with an Evidence Envelope
collection; old records retain their original transition and evidence semantics.
Method Revisions `3.9` and `3.10` retain schema version `3`; new records use the
helper's single `CURRENT_METHOD_REVISION = "3.10"` constant.

Final Push acquires a nonblocking lock derived from push URL and upstream before
readiness evaluation and holds it through push verification and completion.
Contention fails without waiting or mutating cycle state. Completion removes only
the current worktree pointer and retains the completed common record.
Under that lock, Final Push refreshes the recorded remote branch and rejects target
advancement before changing cycle state or pushing. Reconciliation and renewed
validation remain explicit; conflicts are never resolved automatically.

Method Revision `3.4` adds `dbsctrctl begin` as the normal write-cycle entry.
It accepts the same context, risk, delivery intent, and plan as `start`, refreshes
the configured upstream, rejects unknown ahead commits, creates
`dbsctr/<context>/<cycle-id>` from that upstream beneath the DBSCTR state root,
sets the delivery upstream, starts the cycle, and returns a JSON OpenCode handoff.
Dirty source-worktree files are neither copied nor changed. `start` remains the
low-level command for an already prepared clean worktree.

`dbsctrctl cleanup --cycle-id ID` retains successful worktrees for 24 hours by
default. Cleanup must run from another worktree and requires a completed record,
a clean cycle worktree, and proof that every cycle commit is contained in the
delivery target. `--now` waives only the retention delay. Failed, active, dirty,
missing-target, or current worktrees are never removed.
For schema-3 cycles, cleanup parks evidence with retryable state, removes it, and
then removes the retained Cycle Record. Schema-less/schema-1/schema-2 cleanup
continues retaining records.

Method Revision `3.5` exposes typed OpenCode tools `dbsctr_status` and
`dbsctr_begin`. They invoke the dependency-free helper with an argument vector in
the active worktree; they do not implement lifecycle transitions independently.
`dbsctr_begin` returns the authoritative handoff and, when explicitly enabled in
a Herdr pane, asks Herdr to start OpenCode in the new cycle worktree. Cycle
creation remains successful and visible when optional Herdr launch fails.

Herdr is an execution/visibility plane only. It never approves gates, interprets
agent status as evidence, commits, pushes, or removes worktrees. Chezmoi manages
stable `~/.config/herdr/config.toml` preferences with pane history disabled.
Herdr owns its generated OpenCode integration, sockets, sessions, logs, plugin
registry, and worktrees; those runtime files are not templated by chezmoi.

Method Revision `3.6` adds a report-only Lifecycle Reconciliation Audit. The
typed `dbsctr_audit` tool or `dbsctrctl audit --commit REF --json` resolves one Git commit,
inventories bounded-context README/BACKLOG/CHANGELOG triplets, checks
recorded Graphify freshness, and reports the current dirty overlay as excluded.
It reads committed blobs, never the overlay, and performs no mutation.

After deterministic inventory, DBSCTR may trace artifact claims to authoritative
source and classify confirmed drift, stale evidence, missing artifacts, authority
conflicts, historical-but-unlabelled content, and unverified claims. This audit
does not duplicate `/qa`: QA executes configured quality authorities, while the
lifecycle audit reconciles specifications, profiles, backlogs, changelogs,
decisions, tests, and implementation claims. A request to update or reconcile
findings starts explicit context-scoped DBSCTR cycles; audit alone never rewrites
semantic truth, archives files, executes external systems, commits, or pushes.

Method Revision `3.7` adds `dbsctrctl inspect` and typed `dbsctr_inspect` as
read-only, argument-vector adapters over one resolved Git commit. Inspection
never reads worktree content, mutates Git state, follows filesystem symlinks, or
silently emits binary, oversized, traversal-selected, or unbounded content.

### V3.7 Fixed-Commit Inspection Contract

- `dbsctrctl inspect --commit REF --action ACTION --json` and typed
  `dbsctr_inspect` expose `read`, `tree`, `search`, and `object` actions.
- A supplied ref resolves once to one immutable object ID; every result reports
  that identity and reads Git objects rather than the filesystem overlay. Git
  replacement objects are disabled so mutable replacement refs cannot alter the
  content represented by the reported identity.
- Absolute paths, `..`, traversal, repository escape, invalid object types,
  shell interpolation, checkout, fetch, and index/worktree mutation are rejected.
- Search and output have caller limits and hard caps. Truncation is explicit and
  continuable; binary content is identified rather than emitted as unbounded text.
- Dirty overlay remains visible as excluded context and cannot affect a result.
  Both sides of a rename are counted; retained paths are capped at 100 and 64
  KiB with total and truncation metadata.
- Project Policy limits are: paths 4,096 bytes; queries 256 bytes; blobs 4 MiB;
  read pages 32 KiB by default and 64 KiB maximum; tree pages 50 entries by
  default and 100 maximum; search pages 25 matches by default and 100 maximum;
  excerpts 1 KiB by default and 2 KiB maximum; serialized responses 128 KiB.
- Continuations are byte offsets for reads and deterministic numeric cursors for
  tree/search pages. Binary reads return metadata without content; oversized
  reads are rejected before content retrieval; search treats its query literally
  and skips binary/oversized blobs.
- Text pages and excerpts preserve UTF-8 boundaries while enforcing byte limits;
  offsets inside a multibyte character are rejected. Git stdout is streamed and
  stderr is drained independently so bounded reads cannot deadlock on diagnostics.

Method Revision `3.8` adds
`dbsctrctl record-evidence GATE --authority NAME [--path FILE ...] -- PROGRAM ...`.
The command asks before nested authority execution. It executes an
argument vector without a shell, closes stdin, inherits but never serializes the
process environment, applies a 120-second default/600-second hard timeout and 1
MiB raw-output cap, and terminates the whole process group on timeout or overflow.

### V3.8 Evidence Envelope Contract

- Cycle Records retain evidence metadata; sanitized large output resides in
  hash-addressed sidecars beneath
  `<git-common-dir>/dbsctr/evidence/<cycle-id>/<sha256>`.
- Metadata records evidence ID, cycle, gate, authority, sanitized argument
  vector, resolved HEAD, timestamps, result, digest when safe, observed byte
  count/lower-bound status, truncation, generated summary, an empty URL list, and
  explicit `sidecar`, `withheld`, or `no_content` disposition. URL retention waits
  for a future committed canonical allowlist policy.
- Evidence never records inherited environment, environment values, stdin, shell
  expansion results, resolved `op://` values, or secret-bearing URLs.
- Known secret forms are redacted before persistence. Summaries and URLs pass the
  same conservative classifier; URL userinfo, query, fragment, internal hosts,
  paths, account identifiers, and personal data are removed unless Project
  Policy explicitly marks a canonical value non-sensitive. Output that cannot be
  classified safely is withheld; only byte count, result, and withheld status
  remain because a raw digest can disclose low-entropy secrets by verification.
- Arbitrary UTF-8 is unclassified by default. Sidecars retain at most 256 KiB and
  only strict allowlisted evidence summaries such as `ok` or numeric test-result
  lines; everything else is withheld without a digest.
- Persisted invocation keeps a safe executable basename and option names while
  redacting positional values, scripts, paths, combined option values, short
  option payloads, URLs, and suspected credentials. Application secrets belong
  in the inherited environment supplied by the project-owned wrapper, never argv.
- Evidence is recorded under a per-cycle lock and binds explicit intended paths
  to their Git blob identities plus pre-commit HEAD. Gate Commit revalidates both
  worktree and staged-index identities before binding the evidence to its commit.
  Gates with no changed files require evidence at Final Push HEAD. Sidecar
  identity, owner, mode, size, and digest are revalidated before commit and push.
- New schema-3 gates reference stored Evidence IDs rather than arbitrary evidence
  text. Schema-less/schema-1/schema-2 records remain readable and completable.
- Evidence and completed Cycle Records share retention. Only explicit,
  permission-gated cleanup removes both; there is no automatic expiry.
- DBSCTR never retrieves project secrets. A project authority may use a
  project-owned 1Password wrapper. Conditional Python guidance may use committed
  `op://` templates, `op run`, grouped lazy Pydantic Settings, and `SecretStr`,
  unwrapping only at client trust boundaries. Tests use fake environment values,
  not real 1Password data. Required credential files use restrictive permissions,
  validation, cleanup, and documented residual exposure.
- Approved private local repositories may inform implementation research but are
  not public artifacts, distributable examples, or automatic project authority.

Method Revision `3.9` adds the semantic reconciliation protocol loaded by the
DBSCTR skill after deterministic `dbsctr_audit`. It uses `dbsctr_inspect` against
the already resolved commit and changes no helper transition or serialized
schema.

### V3.9 Semantic Reconciliation Contract

- Semantic reconciliation uses one V3.7-resolved commit and V3.8 metadata without
  exposing withheld content.
- Findings are confirmed drift, stale evidence, missing artifact, authority
  conflict, historical-but-unlabelled content, unverified claim, consistent, or
  out of scope.
- Every material claim receives one report-local ID, exact committed claim and
  evidence locations, authority level, relation, severity, confidence,
  rationale, uncertainty, and a separately approvable remediation-cycle scope.
- Classification uses deterministic precedence: out of scope, missing artifact,
  authority conflict, historical-but-unlabelled content, stale evidence,
  confirmed drift, consistent, then unverified claim. The first matching rule
  wins so classifications remain exclusive.
- Absence of contradiction is not consistency; missing proof is an unverified
  claim. Severity expresses impact independently from confidence.
- Source and project policy outrank graph inference and approved private local
  references. Uncertainty stays explicit.
- Authority order is explicit user intent and project policy/contracts/decisions;
  authoritative implementation/tests/schemas/manifests/configured CI; valid
  commit-bound Evidence Envelope metadata; lifecycle claims under review; then
  graph/private-reference hints. Equal-level unresolved disagreement is an
  authority conflict.
- Private local references require explicit authorization and a pinned commit.
  A separate helper inspection rooted in that repository uses bounded Git-object
  actions and excludes its overlay. Reports omit private machine paths and mark
  the reference `public=false` and `authoritative=false`; durable public artifacts
  do not copy private content.
- Reports identify mode, resolved commit, excluded overlay, contexts, counts by
  classification/severity, unchanged `inventory_findings`, complete semantic
  claim findings, and approved-reference metadata. Deterministic inventory
  findings remain separate from semantic ones.
- The audit remains report-only and distinct from `/qa full`. It never rewrites,
  changes status, commits, deploys, or cleans up; every remediation starts a
  separately approved context-scoped DBSCTR cycle.

Method Revision `3.10` adds conditional Product Intent discovery and Web/UI
module routing without changing Cycle Record schema or public commands.

### V3.10 Product Intent And Web/UI Contract

- Product-facing contexts may own `docs/specs/<context>/PRODUCT.md`, referenced
  by the Engineering Profile. It records users/stakeholders, problem and desired
  outcomes, non-goals, core journeys, success evidence, product constraints,
  accessibility, privacy/trust, compatibility, and retirement obligations.
- Product Intent stores durable outcomes rather than current cycle status,
  implementation design, or speculative feature lists. Existing authoritative
  product artifacts may satisfy the contract without duplication.
- Libraries, infrastructure, and internal tooling do not receive synthetic
  Product Intent unless their Engineering Profile establishes product-facing
  behavior.
- Browser UI, product-facing web flows, or frontend component work load the
  Web/UI module. WCAG 2.2 AA is the default accessibility target unless stronger
  Project Policy applies.
- Applicable evidence covers keyboard, focus, semantics, contrast, zoom/reflow,
  errors, and reduced motion. Visual evidence never replaces semantic or
  accessibility checks.
- Applicable WCAG 2.2 outcomes also include unobscured focus, non-drag
  alternatives, target sizing, consistent help, redundant-entry reduction, and
  accessible authentication. Automated tools alone never prove conformance.
- Existing project frameworks and authorities take precedence. Playwright and
  Flowbite Pro are non-normative references.
- MCP configuration is project-local and explicitly applicable; DBSCTR never
  creates or modifies user-global, machine-global, or unrelated-project MCP
  configuration. MCP output remains a hint verified against project source.

### Git Lifecycle Contract

- At cycle start, record HEAD, branch, upstream, worktree status, and any commits
  already ahead of upstream.
- After a gate or small adjacent gate group passes, inspect status/diff/log, run
  affected QA, stage only intended files, and create one coherent Gate Commit.
- Never commit secrets, unrelated changes, generated drift, or a knowingly
  failing required state.
- The primary alone stages, commits, and pushes; subagents never do.
- After all required gates pass, ensure the worktree is clean and perform one
  normal Final Push to the recorded upstream without another confirmation. The
  user's standing DBSCTR policy authorizes that normal push.
- Stop before push when there is no upstream, HEAD is detached, pre-cycle ahead
  commits would be included, force would be required, the destination changed,
  required evidence failed, or repository policy requires another approval.
- Never force-push automatically. If hooks reject a commit, fix the issue and
  create a new commit rather than bypassing hooks or amending published work.
- In a DVC repository, separately approved `dvc push` must succeed before Final
  Push; `record-dvc-push` binds the separately approved evidence to the current
  HEAD without hiding the external write.
- After push, verify the local branch is synchronized with its upstream and
  report commit IDs and push outcome.

## Validation Strategy

| Concern | Authority | Scope | Availability | Baseline |
|---|---|---|---|---|
| Lifecycle contracts | `uv run --group test pytest tests/test_dbsctr_lifecycle.py -q` | V3 skills, modules, commands, routing, archive | Available and passing | No accepted failures |
| Existing control plane | `uv run --group test pytest tests/test_opencode_control_plane.py -q` | Commands, providers, permissions, skill deployment | Available | Passing before V3 |
| Markdown/patch integrity | `git diff --check` | Touched artifacts | Available | No errors |
| Chezmoi rendering | `chezmoi apply --dry-run --verbose` | Managed targets | Available | Must be idempotent after apply |
| Runtime deployment | Targeted `chezmoi apply` and deployed-path inspection | V3 skills, commands, routing, removals | Available; external publication not involved | Targets match source |
| OpenCode loading | `opencode debug config` and command/skill smoke scenarios | Resolved config and workflow behavior | Available; restart required | No V1/V2 runtime routes |
| Graph freshness | `graphify update .` and commit comparison | Changed code/tests and routing graph | Available | Graph matched `eea73e3` before work |

Required smoke scenarios: routine Python library, elevated deployed service,
non-Python change, missing QA capability, read-only Plan handoff, explicit full
QA, and an unauthorized deployment that stops before external write.

## Naming Note

DBSCTR V3 remains the working name. `MethodWeave` and `RigorWeave` are candidate
future umbrella brands: MethodWeave emphasizes a connected engineering method;
RigorWeave emphasizes risk-scaled evidence and assurance. No command or artifact
depends on either candidate.
