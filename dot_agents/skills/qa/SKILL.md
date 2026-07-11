---
name: qa
description: Use for DBSCTR2 touched-scope quality gates or explicit repository-wide audits covering configured quality, security, dependencies, and packaging checks.
---

# Quality Assurance

## Scope

- `scoped`: check only DBSCTR2's touched files, imports, manifests, packages,
  tests, specs, and downstream contracts. Ignore unrelated existing findings.
- `full`: inventory all configured concerns only when the user explicitly asks
  for a repository-wide audit; keep baselined debt visible.

Ask one short question if mode or affected scope is ambiguous. Never expand a
scoped gate silently.

## Toolchain

Read applicable project instructions, manifests, lockfiles, task runners, CI,
pre-commit config, and documented commands. For each configured concern, record
command, scope support, baseline/suppressions, and one project-selected gating
authority:

- format/lint, typing, tests/coverage, code/application security
- dependencies, vulnerability scans, and current Dependabot alerts
- dead code/complexity, docs, mutation, build/package/publish

Use only relevant configured concerns and do not install tools. Suppressions
limit evidence; they do not prove suppressed code passed. If a required tool is
unavailable, record the blocker and next-best check, never a pass.

Overlapping tools may provide context but not duplicate gates. Use configured
JFrog Xray as vulnerability authority when declared; otherwise use configured
`pip-audit` for resolved Python dependencies. Fetch current-repository
Dependabot alerts with authenticated `gh` and normalize them as findings.

## Execute

1. Establish mode, affected scope, repository state, and toolchain profile.
2. Select the minimum checks covering that scope and its concerns.
3. Run independent read-only checks concurrently; serialize checks sharing
   caches, generated files, lockfiles, or outputs.
4. Collect every issue that could cause incorrect behavior, failed validation,
   security exposure, or misleading output. Record uncertainty rather than
   filtering early; omit pure style and naming preferences unless configured as
   gates.
5. Verify each candidate, then normalize source, location, concern, severity,
   confidence, scope, and remediation state. Deduplicate by root cause; the
   concern authority controls gate status.
6. Report findings before editing. In scoped mode omit unrelated noise unless it
   prevents scope isolation.
7. Rank actionable findings into collision-safe Fix Batches with exact
   ownership, safety class, expected files, and focused validation.

## Fix Classes

- `safe`: deterministic formatting or unambiguous tool correction with no
  behavior, contract, schema, dependency, or policy change. Apply after
  presenting the batch, then validate.
- `review_required`: dependency changes, suspected dead code, security policy,
  mutation survivors, complexity redesign, broad typing, or uncertain semantics.
  Obtain review before editing.
- `escalate_dbsctr2`: behavior, contract, schema, orchestration, validation rule,
  or downstream-visible changes.

Never auto-delete suspected dead code; verify references, dynamic loading,
public APIs, and generated boundaries. Do not broaden dependency updates. Re-run
the affected authority and focused tests after each applied batch; stop when a
failure cannot be resolved safely in scope.

## Delegation And Git

Delegate only independent work. A write subagent receives its finding, readable
and writable files, off-limits paths, collision risk, expected output, and
validation. Subagents never stage, commit, or push. The orchestrator reviews,
integrates, validates, and alone performs requested git writes.

## Report

Lead with findings ordered by severity. Include mode and affected scope,
authorities and unavailable checks, each finding's location/confidence/status,
Fix Batches and escalations, validation results, changed files, and residual
risk.

A scoped gate passes only when affected findings are resolved or explicitly
accepted and all required configured checks ran. A full audit may complete with
debt but must expose every verified finding and disposition.
