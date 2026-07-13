# DBSCTR Lifecycle Roadmap

**Approved:** 2026-07-12; extended through V3.10 on 2026-07-12
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
- Fixed-commit inspection excludes the filesystem overlay and rejects paths that
  escape repository scope.
- DBSCTR evidence never retains environment values, stdin, shell expansion
  results, resolved `op://` values, or output that cannot be classified safely.
- Private local reference repositories may inform development when approved but
  are neither public artifacts nor automatic sources of project truth.
- Product Intent and Web/UI guidance are conditional; project-selected tools and
  stronger accessibility policy remain authoritative.

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
- Add deterministic handoff, retention, and cleanup commands.
- Detect target advancement before push and require explicit reconciliation and
  renewed validation; never resolve conflicts automatically.

### V3.5 — OpenCode And Herdr (complete)

- Add typed OpenCode wrappers over stable `dbsctrctl` JSON interfaces.
- Optionally launch isolated OpenCode workspaces through Herdr when requested.
- Use Herdr's native integration for non-authoritative session identity/status.
- Add a compaction/plugin adapter only after measured context-loss failures.

### V3.6 — Lifecycle Reconciliation Audit (complete)

- Deterministically inventory lifecycle triplets and graph identity at a fixed
  commit, then direct the read-only DBSCTR agent to trace claims to source.
- Define agent classifications for confirmed drift, stale evidence, missing
  artifacts, authority conflicts, historical content, and unverified claims.
- Keep report-only audit distinct from repository-wide QA.
- Reconcile only mechanically proven drift by default; route semantic ambiguity
  through Discovery and context-specific DBSCTR cycles.

### V3.7 — Fixed-Commit Inspection (complete)

- Add one read-only helper and typed adapter with `read`, `tree`, `search`, and
  `object` actions over a once-resolved immutable Git object ID.
- Read Git objects rather than the filesystem; report dirty overlay separately.
- Reject absolute paths, traversal, invalid object types, and repository escape.
- Bound search and output, identify binary content, and make truncation and
  continuation explicit.
- Perform no checkout, fetch, index/worktree mutation, or shell interpolation.

### V3.8 — Evidence Envelopes (complete)

- Store evidence metadata in retained Cycle Records and sanitized large output
  in hash-addressed sidecars beneath `.git/dbsctr/evidence/<cycle-id>/`.
- Record authority, sanitized argument vector, HEAD, timestamps, result, safe
  digest, byte count, truncation, classified summary, canonical non-sensitive
  URLs, and sidecar/withheld disposition.
- Never persist inherited environment, environment values, stdin, shell
  expansion results, resolved `op://` values, or secret-bearing URLs.
- Apply the output classifier to summaries and URLs. Withhold output that cannot
  be classified safely; retain only byte count, result, and the withheld marker,
  because raw digests can disclose low-entropy secrets by candidate verification.
- Retain sidecars with completed records and remove both only through explicit,
  permission-gated cleanup.
- Add conditional Python reference guidance for project-owned 1Password wrappers
  feeding grouped lazy Pydantic Settings with `SecretStr`; DBSCTR never retrieves
  project secrets itself.

### V3.9 — Semantic Reconciliation (complete)

- Trace lifecycle claims at one V3.7-resolved commit and classify confirmed
  drift, stale evidence, missing artifacts, authority conflicts,
  historical-but-unlabelled content, unverified claims, consistency, and scope.
- Consume V3.8 evidence metadata without exposing withheld content.
- Keep audits report-only and distinct from `/qa full`; every remediation starts
  an explicitly approved context-scoped DBSCTR cycle.
- Treat source and project policy as authoritative over graph inference or
  approved private local reference repositories.

### V3.10 — Product Intent And Web/UI (complete)

- Add conditional `docs/specs/<context>/PRODUCT.md` for product-facing contexts;
  do not create synthetic product artifacts for libraries or infrastructure.
- Add a conditional Web/UI module with WCAG 2.2 AA as the default target unless
  stronger project policy applies.
- Require applicable keyboard, focus, semantics, contrast, zoom/reflow, error,
  and reduced-motion evidence; visual evidence cannot replace semantic checks.
- Keep Playwright and Flowbite Pro as non-normative references and prefer the
  existing project framework and authorities.
- Permit only applicable project-local MCP configuration; never create or modify
  global MCP configuration.

## Delivery Order

Persist this roadmap first, then deliver V3.7, V3.8, V3.9, and V3.10 as
separately approved isolated cycles. Resolve Graphify duplicate registration and
Herdr LaunchAgent ownership in separate bounded-context cycles rather than
folding runtime hygiene into these milestones.

## Deferred

- Pull-request delivery and remote cycle branches.
- Automatic semantic rewriting of specifications.
- Permanent worktree retention.
- Herdr or OpenCode as lifecycle authority.
- New framework modules without repeated project evidence.
