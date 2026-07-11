# Changelog — DBSCTR V3 Lifecycle

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
