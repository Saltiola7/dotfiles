# DBSCTR Lifecycle Roadmap

**Approved:** 2026-07-12
**Authority:** `README.md` owns current contracts; `BACKLOG.md` owns executable work.

## Decisions

- Every non-trivial DBSCTR write cycle uses one isolated branch and linked
  worktree. Multiple sessions may resume one cycle; worktrees are not permanent
  audit records.
- New cycles base on the verified target upstream. Local `main` is integration-
  only and may remain dirty.
- Cycle state ultimately lives beneath the Git common directory, with one active
  cycle per worktree and serialized delivery per target branch.
- Direct upstream remains the default delivery route. Pull-request delivery is
  deferred until its authorization and completion contracts are specified.
- Completed commits, lifecycle artifacts, CI, and retained Cycle Records are the
  durable track record. Successful worktrees are initially retained for 24 hours;
  failed or dirty worktrees are never removed automatically.
- Herdr is the execution and visibility plane; OpenCode is the worker runtime;
  DBSCTR remains the lifecycle and Git authority.
- Lifecycle reconciliation audits are report-only by default. Semantic artifact
  changes require explicit reconciliation and authoritative evidence.

## Milestones

### V3.2 — Protocol Correctness (complete)

- Version Cycle Record schemas independently from Method Revision.
- Require an explicit gate-applicability plan bound to an Engineering Profile.
- Enforce gate prerequisites while allowing failures to be recorded immediately.
- Allow risk and applicability to tighten, never loosen silently.
- Keep schema-less V3.1 records readable and completable under legacy rules.

### V3.3 — Worktree Architecture (complete)

- Move cycle registry to the Git common directory.
- Support multiple active cycles with one active cycle per worktree.
- Record worktree, branch, base, target, and integration ownership.
- Add target-branch locks and stale-base detection.

### V3.4 — Isolation Automation (complete)

- Add `dbsctrctl begin` to create cycle branch/worktree and start state.
- Add deterministic handoff, reconciliation, retention, and cleanup commands.
- Revalidate after target advancement; never resolve conflicts automatically.

### V3.5 — OpenCode And Herdr (in progress)

- Add typed OpenCode wrappers over stable `dbsctrctl` JSON interfaces.
- Launch or resume isolated OpenCode workspaces through Herdr when available.
- Surface cycle identity and status as non-authoritative UI metadata.
- Add a compaction/plugin adapter only after measured context-loss failures.

### V3.6 — Lifecycle Reconciliation Audit

- Inventory lifecycle artifacts and trace claims to source at a fixed commit.
- Classify confirmed drift, stale evidence, missing artifacts, authority conflicts,
  historical content, and unverified claims.
- Keep report-only audit distinct from repository-wide QA.
- Reconcile only mechanically proven drift by default; route semantic ambiguity
  through Discovery and context-specific DBSCTR cycles.

## Deferred

- Pull-request delivery and remote cycle branches.
- Automatic semantic rewriting of specifications.
- Permanent worktree retention.
- Herdr or OpenCode as lifecycle authority.
- New framework modules without repeated project evidence.
