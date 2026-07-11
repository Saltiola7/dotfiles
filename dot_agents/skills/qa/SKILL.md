---
name: qa
description: >
  Repository-aware quality assurance. Use for DBSCTR2 touched-scope gates or
  explicit full audits covering quality, security, dependencies, and packaging.
---

# Quality Assurance

## Role

Own repository toolchain discovery, scoped DBSCTR2 gates, explicit full audits,
finding normalization, and safe-fix orchestration. Project instructions and
configured commands are authoritative; do not install tools just because this
skill supports them.

## Modes

- `scoped`: DBSCTR2 supplies touched files, imports, manifests, packages, tests,
  specs, and downstream contracts. Check only that affected scope. Existing
  findings outside it are unrelated noise: ignore them rather than failing the
  gate.
- `full`: run only when the user explicitly requests a full/repository-wide
  audit. Inventory all configured concerns and keep baselined debt visible.
- If mode or scope is ambiguous, ask one short question. Never silently expand a
  scoped run into a full audit.

## Discover The Toolchain

Read the repository's applicable `AGENTS.md`, manifests, lockfiles, task runners,
CI workflows, pre-commit configuration, and documented validation commands.
Build a compact profile of command, scope support, baseline/suppressions, and
authority for each configured concern:

- formatting and lint
- static typing
- tests and coverage
- code/application security
- dependencies, vulnerability scanning, and GitHub Dependabot alerts
- dead code and complexity
- documentation checks
- mutation testing
- build, packaging, and publish validation

Use only relevant configured concerns. A broad suppression is evidence of a
limited check, not proof that the suppressed code passed. If a configured tool
is unavailable, record the blocker and next-best validation; never report a
pass.

Choose one gating Concern Authority per concern from project policy and CI.
Overlapping tools may add context, but must not become duplicate or contradictory
gates. When the project declares JFrog Xray, use its configured `jf` audit/scan
commands as vulnerability authority and do not add `pip-audit`. Otherwise, for
Python use configured `pip-audit` against the resolved or locked dependencies as
the fallback. Fetch current-repository Dependabot alerts with authenticated `gh`
and treat them as normalized finding inputs, not a separate workflow.

## Execute

1. Establish mode, affected scope, repository state, and toolchain profile.
2. Select the minimum checks that cover the requested scope and concerns.
3. Run independent read-only checks concurrently when useful; serialize checks
   that write caches, generated files, lockfiles, or shared outputs.
4. Normalize each result to source, location, concern, severity, scope, and
   remediation state. Deduplicate by root cause, with the Concern Authority's
   result controlling gate status.
5. Report findings before editing. In scoped mode, omit unrelated noise from the
   gate; mention only blockers that prevent scope isolation.
6. Group actionable findings into ranked, collision-safe Fix Batches with exact
   ownership, safety class, expected files, and focused validation.

## Fix Safety

- `safe`: deterministic formatting or unambiguous tool-provided correction with
  no behavior, contract, schema, dependency, or policy change. Apply only after
  presenting the batch, then run focused validation.
- `review_required`: dependency changes, suspected dead code, security policy,
  mutation survivors, complexity redesign, broad typing changes, or any fix with
  uncertain semantics. Propose the batch and obtain review before editing.
- `escalate_dbsctr2`: behavior, contract, schema, orchestration, validation rule,
  or downstream-visible changes. Return the finding and scope to DBSCTR2.

Never auto-delete suspected dead code; verify declarations, references, dynamic
loading, public API use, and generated-code boundaries first. Do not broaden a
dependency update beyond the finding. Re-run the affected authority and focused
tests after every applied batch; stop if failures cannot be resolved safely
within scope.

## Subagents And Git

Delegate only independent work. Before a write subagent starts, provide an
Ownership Contract containing the concern/finding, files it may read and write,
off-limits files, collision risks, expected output, and validation command.
Subagents never stage, commit, or push. The orchestrator reviews and integrates
all diffs, validates the combined result, and alone stages and commits when the
task requests commits and repository rules permit them.

## Output

Report, in order:

1. Mode, affected scope, selected authorities, and unavailable checks.
2. Findings ordered by severity, with location, authority, scope, and status.
3. Fix Batches: applied safe changes, proposed risky work, and DBSCTR2
   escalations.
4. Validation commands and results, changed files, residual findings, and risks.

A scoped gate passes only when affected findings are resolved or explicitly
accepted and every required configured check ran. A full audit may complete with
debt, but must expose all findings and their disposition.
