# Changelog — DBSCTR V3 Lifecycle

## 2026-07-12 — V3.4 Isolation Automation

- Began automatic creation of upstream-based cycle branches and linked worktrees
  so dirty integration worktrees no longer block independent DBSCTR work.
- Kept unknown ahead commits blocked, retained low-level `start`, and limited
  cleanup to clean completed DBSCTR-owned worktrees whose commits reached target.
- Implemented `begin` with upstream refresh, configured remote/branch handling,
  deterministic branch/worktree creation, rollback on failed start, and JSON
  OpenCode handoff without touching dirty source files.
- Implemented 24-hour default retention and cleanup checks for DBSCTR ownership,
  completion, current/dirty/branch/HEAD state, recorded destination, refreshed
  target containment, and safe branch deletion.
- Validation: 33 helper tests and 226 full tests passed; compilation, diff check,
  chezmoi dry-run/apply, fresh-process smoke, and independent review passed.
- Exceptions: none. Release: not applicable. Deployment: helper and skill applied
  locally. Final Push target: `origin/main`.
- Gate Commits: `da4ddf8`, `2b4191a`.

## 2026-07-12 — V3.3 Worktree Registry

- Began the approved always-isolated cycle architecture with common Git state,
  one active cycle per worktree, globally unique cycle IDs, retained completed
  records, and serialized delivery targets.
- Kept worktree creation, handoff, reconciliation, retention, and cleanup in
  V3.4; V3.3 changes state ownership only.
- Implemented schema version `2` common Cycle Records, per-worktree active
  pointers, globally atomic cycle-ID reservation, worktree/delivery identity,
  canonical target locks, retained completion records, and resumable pointer
  cleanup.
- Validation: 28 helper tests and 220 full tests passed; compilation, diff check,
  chezmoi dry-run/apply, fresh-process skill smoke, and independent review passed.
- Exceptions: none. Release: not applicable. Deployment: helper and DBSCTR skill
  applied locally. Final Push target: `origin/main`.
- Gate Commits: `d444950`, `7d80d21`.

## 2026-07-12 — V3.2 Discovery And Roadmap

- Approved V3.2 protocol correctness: schema-versioned new records, explicit
  applicability plans, ordered gate passing, monotonic risk, and legacy V3.1
  completion without implicit migration.
- Approved always-isolated DBSCTR write cycles as the V3.3 direction, followed by
  worktree automation, OpenCode/Herdr integration, and report-only lifecycle
  reconciliation audit in separate milestones.
- Retained direct-upstream delivery and deferred PR delivery, automatic semantic
  rewriting, permanent worktree retention, and unproven plugin enforcement.

## 2026-07-12 — V3.2 Implementation

- Added schema version `1` Cycle Records with explicit JSON applicability plans,
  committed Engineering Profile identity, mandatory/delivery gate validation,
  and duplicate-key rejection.
- Enforced predecessor disposal before passing later gates while preserving
  immediate failure/unavailable evidence and legacy schema-less V3.1 transitions.
- Added monotonic `raise-risk` and equal-or-stricter `update-plan` transitions;
  stale profile identity blocks Gate Commit and Final Push.
- Added the approved V3.2–V3.6 roadmap and aligned DBSCTR, Discovery, templates,
  lifecycle contracts, and compatibility tests.
- Validation: 214 tests passed; Python compilation, `git diff --check`, OpenCode
  config resolution, chezmoi dry-run/apply, helper smoke, two fresh-process skill
  probes, and independent review passed.
- Exceptions: none. Release: not applicable. Deployment: managed helper and
  skills applied locally. Final Push target: `origin/main`.
- Gate Commits: `da65d0b`, `66df166`, `00c2950`.

## 2026-07-11 — Discovery

- Reached 97% confidence after reviewing DBSCTR V1/V2, Discovery2, QA, domain
  modules, OpenCode routing, tests, CI, Graphify, and current Python lifecycle
  standards.
- Selected a language-neutral core with first-class Python and Security modules
  and future language/framework extension points.
- Selected unversioned `/discovery`, `/dbsctr`, and `/qa` public commands.
- Authorized replacement of V1, source-only archival of V2, and removal of V2
  runtime skills and commands.
- Selected bounded-context Engineering Profile defaults with per-cycle overrides.
- Selected `routine`, `elevated`, and `critical` risk levels.
- Replaced mandatory phase commits with evidence checkpoints and repository-owned
  commit policy.
- Selected short normative modules with optional provider/tool references.
- Deferred public branding; DBSCTR V3 remains the working name with MethodWeave
  and RigorWeave recorded as candidates.
- Added behavior scenarios for unversioned routing, Engineering Profiles,
  risk-scaled gates, full lifecycle completion, capability-aware QA, progressive
  modules, V1/V2 migration, OpenCode handoff, and evidence checkpoints.
- Defined the OpenCode architecture, Engineering Profile and Gate Ledger shapes,
  module/reference layout, public interfaces, and dependency-aware backlog.
- Defined risk, gate, development, completion, QA capability, module, Python,
  Security, migration, and OpenCode adapter contracts plus configured validation
  authorities and smoke scenarios.

## 2026-07-11 — Implementation

- Replaced unversioned V1 Discovery and DBSCTR skills with V3 and retained `/qa`.
- Added Engineering Profile, Gate Ledger, risk classification, six-phase
  Development Kernel, and Review/Integrate, Release, Deploy, Operate, and
  Maintain/Retire gates.
- Added Python and Security modules and normalized Data, Cloud, ML/AI, and
  Analytics into provider-neutral modules with optional references.
- Archived complete V2 source beneath `docs/archive/opencode/skills/v2/` and
  removed V2 runtime skills and commands.
- Added unversioned `/discovery` and `/dbsctr` commands, retargeted global routing,
  and extended QA with optional capability coverage.
- Added deterministic lifecycle contracts and CI path coverage for skills,
  OpenCode routing, lifecycle specs, and chezmoi migration manifests.
- Extended the declared Python `>=3.12` CI matrix through current stable Python
  3.14 so runtime support claims have oldest/newest evidence.
- Corrected thin commands after initial runtime probes answered from memory; the
  commands now require skill-tool loading before execution.
- Updated active QA, control-plane, prompting, graph-routing, analytics, and V2
  historical specifications.
- Reviewed all delegated module patches and remediated an independent final audit
  covering stale active constraints and CI migration paths.

### Validation

- Initial focused lifecycle run failed all 8 tests for the intended missing V3
  surfaces.
- Focused lifecycle and control-plane tests passed: 15 tests.
- Full configured pytest suite passed: 185 tests.
- `git diff --check`, `opencode debug config`, and chezmoi dry-run passed.
- Chezmoi applied V3 and removed deployed V2; `chezmoi status` returned clean.
- Live `/discovery`, `/dbsctr`, and `/qa` probes loaded the exact skills and
  returned the required artifacts, phases/gates, and capability statuses.
- `graphify update .` rebuilt the code graph with 1,366 nodes and 1,557 edges.
- No release, remote deployment, push, stage, or commit was performed.

## 2026-07-11 — Automatic Git Lifecycle Follow-Up

- Approved coherent Gate Commits during DBSCTR cycles and one normal Final Push
  after all required gates pass.
- Required cycle-start branch/upstream/ahead-state capture, intended-file staging,
  passing affected evidence, a clean worktree, and post-push verification.
- Prohibited automatic force-push and unsafe pushes that include unrelated
  pre-cycle commits, lack an upstream, change destination, or follow failed DVC
  synchronization.
- Added and passed a deterministic Git-lifecycle contract; the full configured
  suite passed 186 tests.
- Deployed the updated skill/routing and verified a live `/dbsctr` probe reports
  Gate Commit, Final Push, and stop conditions from the loaded skill.

## 2026-07-12 — V3.1 Discovery

- Approved a compatible V3.1 evolution under existing public commands and paths.
- Separated Gate Applicability, Gate Result, and user-approved Gate Exception.
- Selected `.git/dbsctr/` for active, non-portable Cycle Records; specifications,
  tests, commits, and CI remain durable authority.
- Required every cycle to review README, maintain a live BACKLOG item, and append
  one compact CHANGELOG entry at completion without forcing meaningless README edits.
- Selected a dependency-free `dbsctrctl` for deterministic state, artifact,
  Gate Commit, and Final Push checks. Raw Git writes remain permission-gated.
- Deferred an OpenCode plugin until measured helper bypass or compaction loss
  justifies ambient enforcement.
- Approved a read-only OpenAI reviewer route and fresh-process runtime validation.

## 2026-07-12 — V3.1 Implementation

- Separated Gate Applicability, Gate Result, and user-approved Gate Exception in
  lifecycle artifacts, skills, templates, QA output, and deterministic state.
- Added `dbsctrctl` with clean-cycle start, artifact identity checks, gate
  evaluation, permission-gated exceptions, safe Gate Commits, destination-bound
  Final Push, idempotent finalization, and separately approved DVC evidence.
- Replaced percentage readiness with a material-question criterion and allowed
  risk-scaled artifact compression without silently skipping kernel concerns.
- Added a read-only OpenAI reviewer and narrow OpenCode permission rules that deny
  force-push and hook bypass while allowing validated helper Git actions.
- Validation: 206 configured tests passed before artifact closure; JSON rendering,
  `git diff --check`, chezmoi dry-run/apply/status, fresh skill probes, helper
  smoke, and reviewer delegation passed.
- Exceptions: none. Deployment: local chezmoi targets applied. Final Push target:
  recorded `origin/main`; actual result is reported after push.
- Gate Commit: `c9827e0`.
