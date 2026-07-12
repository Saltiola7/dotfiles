# DBSCTR V3 Lifecycle

**Status:** V3.3 implemented; V3.4 in progress
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
The approved staged evolution through V3.6 is recorded in [`ROADMAP.md`](ROADMAP.md).

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

## Engineering Profile

### Defaults

| Field | Value |
|---|---|
| Deliverable | OpenCode lifecycle skills, commands, routing, modules, and tests |
| Languages/frameworks | Language-neutral Markdown prompts; Python contract tests |
| Modules | Python, Security, Data, Cloud, ML/AI, Analytics |
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
  references/
    data.md
    cloud.md
    ml.md
    analytics.md
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

### Cycle Record Interface

`dbsctrctl` stores JSON beneath `.git/dbsctr/` with `method_revision`, independent
`schema_version`, `cycle_id`, `context`, `risk`, `delivery_intent`, committed
Engineering Profile identity, applicability plan, Git baseline, current state,
gates, Artifact Reviews, and created commits. Commands are `start`, `status`,
`review-artifact`, `set-applicability`, `set-gate`, user-confirmed
`approve-exception`, `raise-risk`, `check artifacts`, `gate-commit`, and
`final-push`; `update-plan` rebinds a committed profile using an equal or stricter
plan.
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

Schema version `2` / Method Revision `3.3` stores new records beneath
`<git-common-dir>/dbsctr/cycles/`. Each worktree owns one pointer beneath
`worktrees/<worktree-id>/active`, so linked worktrees can run independent cycles
while cycle IDs remain globally unique. Records include worktree path, Git
directory, branch, base commit, creation authority, upstream, and lock identity.
Schema version `1` and schema-less records remain readable from their original
worktree-private paths.

Final Push acquires a nonblocking lock derived from push URL and upstream before
readiness evaluation and holds it through push verification and completion.
Contention fails without waiting or mutating cycle state. Completion removes only
the current worktree pointer and retains the completed common record.

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
