# OpenCode Global Routing

## Workflow

Use `dbsctr2` for changes to behavior, domain rules, schemas, APIs, views,
services, pipelines, orchestration, validation, contracts, or downstream-visible
output. Skip it for trivial, formatting-only, git-only, dependency-only, and
non-behavioral configuration work, or when the user requests a lighter workflow.

If intent is unclear or no matching `docs/specs/` context exists, run
`discovery2` to at least 95% confidence before DBSCTR2. Keep affected specs,
contracts, tests, backlogs, and changelogs current in the same cycle.

Use `qa` for DBSCTR2 touched-scope gates. Run repository-wide QA only when the
user explicitly requests it; Dependabot alerts are QA inputs.

## Execution

For requests to explain, review, diagnose, or plan, inspect relevant materials
and report the result without implementing unless requested. For requests to
change, build, or fix, make in-scope local changes and run non-destructive
validation without asking first.

Require confirmation before external writes, destructive or irreversible
actions, purchases, or material scope expansion.

Use `ponytail` full for coding and choose the lowest sufficient implementation
rung. Never remove necessary validation, security, data-loss handling,
accessibility, or tests.

Use `caveman` full by default. Preserve conclusions, evidence, material caveats,
decisions, and next actions; trim introductions, repetition, generic reassurance,
and optional background first.

## Context And Delegation

For codebase or architecture questions, query an existing `graphify-out/` graph
before broad search, then verify useful results against authoritative source,
specs, contracts, and project instructions. Update the graph when project rules
require it.

Delegate only independent work when parallel ownership makes execution faster or
safer. Give each write subagent explicit writable paths and off-limits scope.
The orchestrator reviews and validates integrated work and alone stages or
commits; subagents never commit.

Use `explore-openai`, `scout-openai`, and `builder-openai` only from `Build-GPT`.
Use `explore-bedrock`, `scout-bedrock`, and `builder-bedrock` only from
`Build-Claude`. Log each optimized route. On failure, report it and retry once by
continuing directly with the same-provider flagship. Never cross providers
silently. For other selected models, use generic inheriting subagents.

## Compatibility

Keep `/dbsctr` and `/discovery` unchanged and callable forever. They load the V1
skills; do not rename, delete, deprecate, or modify them without explicit user
instruction.
