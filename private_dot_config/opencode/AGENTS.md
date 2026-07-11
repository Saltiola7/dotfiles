# OpenCode Global Routing

## DBSCTR2 Default

Use `dbsctr2` by default for coding work that changes behavior, domain rules,
models, schemas, APIs, views, services, pipelines, orchestration, validation,
contracts, or downstream-visible output.

Skip DBSCTR2 for trivial edits, formatting-only work, git-only tasks,
dependency-only changes, and configuration with no behavior impact. Also skip it
when the user explicitly requests a lighter workflow.

When no matching spec exists in `docs/specs/`, or intent is unclear, load
`discovery2` first. Do not resume DBSCTR2 until Discovery2 reaches at least 95%
confidence and writes or updates the required artifacts.

If a change affects an existing spec, contract, test, backlog, or changelog,
update it in the same cycle. Stale artifacts are a failure.

## V1 Permanence

Keep these v1 commands unchanged and callable forever:
- `/dbsctr` loads `dbsctr`
- `/discovery` loads `discovery`

Do not rename, delete, or deprecate v1.

## Ponytail

Use `ponytail` full mode by default for coding work. Choose the lowest sufficient
rung: reuse existing code, then standard library or native platform features,
then installed dependencies, then the smallest correct change.

Do not simplify away validation, security, data-loss handling, accessibility,
or necessary tests.

## Caveman

Use `caveman` full mode by default for concise communication. Expand when
clarity, safety, user-requested explanation, discovery interviews, audit reports,
or complex tradeoffs require normal prose.

## Graphify

For codebase, architecture, or relationship questions, use an existing
`graphify-out/` graph first. Prefer its report, wiki, and graph queries before
raw searches, but treat source code, current specs, contracts, and configured
project instructions as authoritative when they disagree.

Update the graph after code changes when project instructions require it.

## Quality Assurance

Use `qa` as the DBSCTR2 quality gate for touched files, dependencies, tests,
specs, contracts, and directly affected code. Discover and run the repository's
configured tools; do not impose a universal toolchain or fail scoped work for
unrelated pre-existing findings.

Run a repository-wide QA audit only when the user explicitly requests a full
audit. Use one project-selected authority per concern, classify fixes before
editing, validate safe fixes, and return behavior-changing fixes to DBSCTR2.
Dependabot alerts are QA inputs, not a standalone routing workflow.

## Subagents

Use subagents only when independent ownership makes work faster or safer. Every
write subagent needs an explicit ownership contract naming writable paths and
off-limits scope. The orchestrator reviews and validates integrated work and is
the only agent that may stage or commit. Subagents never commit.
