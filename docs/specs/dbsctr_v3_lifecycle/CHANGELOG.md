# Changelog — DBSCTR V3 Lifecycle

## 2026-07-12 — V3.10 Product Intent And Web/UI

- Added conditional Product Intent discovery that reuses an authoritative product
  artifact and creates `PRODUCT.md` only when needed; non-product contexts receive
  no synthetic artifact.
- Added a generic Web/UI module with WCAG 2.2 AA defaults, browser trust-boundary
  outcomes, lifecycle obligations, and explicit semantic, keyboard, focus,
  contrast, zoom/reflow, target-size, error-state, and reduced-motion evidence.
- Added non-normative Playwright and Flowbite Pro references plus a strict
  project-local MCP boundary. Existing frameworks and project authorities remain
  authoritative; automated and visual evidence alone cannot prove conformance.
- Validation: 258 tests passed and 1 skipped; Python compile and `git diff --check`
  passed. Independent accessibility review findings were remediated and final
  review reported no findings.
- Gate Commit: `d0bc5bd`. Deployment: targeted local chezmoi apply completed;
  source/deployed identity, idempotent dry-run, and deployed fixed-commit helper
  smoke passed. Gate Exceptions: none. Intended Final Push: `origin/main`.

## 2026-07-12 — V3.9 Semantic Reconciliation

- Added a report-only semantic audit protocol after deterministic fixed-commit
  inventory, using bounded `dbsctr_inspect` claim traces and V3.8 metadata without
  reading withheld content.
- Defined exclusive precedence for consistent, confirmed drift, stale evidence,
  missing artifact, authority conflict, historical-but-unlabelled content,
  unverified claim, and out-of-scope classifications.
- Added explicit authority ordering, confidence/severity separation, deterministic
  inventory separation, complete report fields, and separately approved
  remediation-cycle proposals.
- Constrained private local references to explicitly authorized, commit-pinned,
  Git-object-only inspection; reports omit machine paths and mark references
  non-public and non-authoritative.
- Validation: 257 tests passed and 1 skipped; Python compile and `git diff --check`
  passed. Independent review findings were remediated and final review reported
  no findings.
- Gate Commit: `82dd3da`. Deployment: targeted local chezmoi apply completed;
  source/deployed identity, idempotent dry-run, deployed fixed-commit helper smoke,
  and fresh Plan skill/protocol probe passed. Gate Exceptions: none. Intended
  Final Push: `origin/main`.

## 2026-07-12 — V3.8 Evidence Envelopes

- Added schema-3 Cycle Records and permission-gated `record-evidence` execution
  with no shell, closed stdin, bounded process-group timeout/output, conservative
  argv metadata, and no environment serialization.
- Added explicit sidecar/withheld/no-content dispositions. Only strict allowlisted
  summaries reach private hash-addressed sidecars; arbitrary text, URLs, binary,
  suspected secrets, and unclassified output are withheld without raw digests.
- Bound envelopes to pre-commit HEAD and explicit path/blob identities; rechecked
  worktree, staged index, and committed tree before Gate Commit binding; rechecked
  envelope and sidecar integrity before Final Push.
- Coupled schema-3 evidence and record deletion through retryable permission-gated
  cleanup while preserving historical schema behavior.
- Added conditional Python guidance for project-owned `op://`/`op run` wrappers,
  lazy grouped Pydantic Settings, `SecretStr`, fake-value tests, and constrained
  credential files. Private local references remain non-public and non-authoritative.
- Validation: 256 tests passed and 1 skipped; Python compile and `git diff --check`
  passed. Builder output received primary integration review; independent security
  review findings were remediated and final review reported no findings.
- Gate Commit: `9fd353d`. Deployment: targeted local chezmoi apply completed;
  source/deployed identity, idempotent dry-run, fresh config resolution, and a
  deployed schema-3 sidecar smoke passed. Gate Exceptions: none. Intended Final
  Push: `origin/main`.

## 2026-07-12 — V3.7 Fixed-Commit Inspection

- Added dependency-free `dbsctrctl inspect` actions for bounded committed-file
  reads, tree pages, literal searches, and object metadata after resolving one
  immutable commit identity.
- Excluded dirty overlay from content while reporting bounded path metadata;
  rejected traversal and action mismatches; disabled Git replacement objects;
  bounded blobs, pages, excerpts, responses, and overlay reporting; and preserved
  UTF-8 boundaries.
- Added the read-only typed `dbsctr_inspect` OpenCode adapter and global allow
  permission, updated DBSCTR audit routing, and advanced new Cycle Records to
  Method Revision `3.7` without rewriting historical records.
- Validation: 243 tests passed and 1 skipped; Python compile, Bun tool build,
  `git diff --check`, real fixed-commit action smoke, and independent security
  review passed. Builder patch was reviewed and its initial bounds gaps were
  corrected before integration.
- Gate Commit: `4af8365`. Deployment: targeted local chezmoi apply completed;
  source/deployed identity, idempotent dry-run, fresh config resolution, deployed
  helper actions, and typed-tool execution passed. Gate Exceptions: none.
  Intended Final Push: `origin/main`.

## 2026-07-12 — V3.7–V3.10 Roadmap Approval

- Approved separate milestones for fixed-commit inspection, sanitized retained
  evidence, report-only semantic reconciliation, and conditional Product Intent
  plus Web/UI guidance.
- Selected Git-object-only reads with bounded output and traversal/overlay
  rejection; hash-addressed local evidence sidecars with conservative withholding;
  and permission-gated record/evidence cleanup.
- Kept DBSCTR out of secret retrieval. Approved conditional Python reference
  guidance for project-owned 1Password wrappers feeding lazy grouped Pydantic
  Settings with `SecretStr` and fake-value tests.
- Kept approved private local repositories non-public and non-authoritative.
  Selected WCAG 2.2 AA by default, non-normative Playwright/Flowbite Pro guidance,
  and project-local MCP only.
- Separated Graphify duplicate-registration cleanup and Herdr LaunchAgent
  reconciliation from the V3.7–V3.10 milestone sequence.
- Validation: 18 lifecycle tests passed; `git diff --check` passed; private
  reference identity was absent from durable artifacts; independent review
  findings were resolved, including conservative withholding of unsafe raw
  digests, summaries, and URLs.
- Gate Commit: `08cd102`. Deployment and operation: not applicable because this
  cycle changes repository documentation only. Gate Exceptions: none. Intended
  Final Push: `origin/main`.

## 2026-07-12 — V3.6.2 Permission And Revision Correctness

- Routed typed `dbsctr_begin` through OpenCode permission evaluation before any
  helper execution; Plan, reviewer, and Builder subagents deny it, selected Build
  agents allow it, and the global fallback asks.
- Prompt-gated DBSCTR cleanup and destructive Herdr commands while preserving
  normal Herdr agent launch behavior.
- New Cycle Records now report Method Revision `3.6` from one helper constant;
  historical records remain readable and are not rewritten.
- Validation: 235 tests passed and 1 skipped; Python compile, Bun tool build,
  `git diff --check`, focused chezmoi dry-run/apply/idempotence, deployed-file
  identity, and fresh `opencode debug config` passed.
- Independent review completed. Its Build-allow concern was rejected because the
  approved permission policy intentionally grants selected Build agents standing
  authorization while requiring every custom-tool call to evaluate policy.
- Gate Commit: `95ef8ba`. Deployment: targeted local chezmoi apply. Gate
  Exceptions: none. Intended Final Push: `origin/main`.

## 2026-07-12 — V3.6.1 Integrated Review Corrections

- Added target refresh and explicit stale-base rejection under the delivery lock
  before Final Push changes state.
- Made cycle worktree roots stable when `begin` is invoked from another linked
  worktree.
- Corrected Cycle Record schema/command documentation and narrowed roadmap claims
  to implemented deterministic inventory, explicit reconciliation, optional
  Herdr launch, and agent-driven semantic tracing.
- Validation: 37 helper tests and 233 full tests passed with one expected macOS
  filesystem skip; compilation, diff check, targeted chezmoi deployment, and a
  fresh exact-path independent review passed.
- Exceptions: none. Release: not applicable. Deployment: corrected helper applied
  locally. Final Push target: `origin/main`.
- Gate Commits: `02bcf34`, `1b75001`.

## 2026-07-12 — V3.6 Lifecycle Reconciliation Audit

- Began report-only lifecycle audits at a fixed Git commit, excluding dirty
  overlay from claims while keeping it visible to the operator.
- Separated deterministic lifecycle artifact/graph inventory from semantic
  source reconciliation and from `/qa` quality-tool execution.
- Kept all remediation explicit: structural or semantic updates start scoped
  DBSCTR cycles rather than mutating artifacts during audit.
- Implemented fixed-commit lifecycle triplet inventory, exact object-format-aware
  graph freshness, unverifiable metadata findings, byte-safe dirty-overlay
  reporting, and optional-lock-free Git reads.
- Added typed `dbsctr_audit`, routing and skill semantics, and explicit separation
  from `/qa full` and write-capable reconciliation cycles.
- Validation: 36 helper tests and 232 full tests passed with one expected macOS
  filesystem skip; Python/Bun build, diff check, config resolution, chezmoi
  dry-run/apply, real helper audit, typed-tool audit, and independent review
  passed. Live audit: 10 contexts, zero findings, zero dirty overlay at HEAD.
- Exceptions: none. Release: not applicable. Deployment: helper, skill, routing,
  config, runtime, and typed tool applied locally. Final Push target: `origin/main`.
- Gate Commits: `696971c`, `178bf26`.

## 2026-07-12 — V3.5 OpenCode And Herdr Integration

- Began typed OpenCode status/begin wrappers over authoritative `dbsctrctl` JSON
  and optional Herdr launch of the newly isolated OpenCode workspace.
- Kept DBSCTR authoritative for cycle state, gates, commits, and delivery; Herdr
  owns panes/session visibility only, and launch failure does not falsify cycle
  creation.
- Selected chezmoi management for stable Herdr preferences only, disabled pane
  history to avoid prompt/secret retention, and left generated integration and
  runtime state Herdr-owned.
- Implemented typed `dbsctr_status` and explicit-launch `dbsctr_begin` tools over
  a dependency-free argument-vector runtime; lifecycle state remains in
  `dbsctrctl`.
- Managed stable Herdr preferences, disabled pane history, refreshed the generated
  OpenCode integration from v4 to v8, and reloaded running Herdr configuration.
- Validation: 11 OpenCode control tests and 229 full tests passed; Bun build,
  config resolution, chezmoi dry-run/apply, real typed-status invocation,
  fresh-process skill smoke, and independent review passed.
- Exceptions: none. Release: not applicable. Deployment: OpenCode tools/config,
  Herdr preferences/integration, and DBSCTR skill applied locally. Final Push
  target: `origin/main`.
- Gate Commits: `d9a7363`, `9916235`.

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
