# OpenCode Global Routing

## Workflow

Use `dbsctr` for changes to behavior, domain rules, schemas, APIs, views,
services, pipelines, orchestration, validation, contracts, or downstream-visible
output. Skip it for trivial, formatting-only, git-only, dependency-only, and
non-behavioral configuration work, or when the user requests a lighter workflow.

If intent is unclear or no matching `docs/specs/` context exists, run
`discovery` until no unresolved question can materially change implementation before DBSCTR. Keep affected specs,
contracts, tests, backlogs, and changelogs current in the same cycle.

Use `qa` for DBSCTR touched-scope gates. Run repository-wide QA only when the
user explicitly requests it; Dependabot alerts are QA inputs.

Treat "DBSCTR audit" as a report-only lifecycle reconciliation audit at a fixed
commit unless the user explicitly requests updates. It inventories and traces
specs, profiles, backlogs, changelogs, decisions, tests, and source claims;
`/qa full` remains the separate configured-tool quality audit. Verified remediation
runs as context-scoped isolated DBSCTR cycles.

DBSCTR cycles create coherent Gate Commits after passing gate increments.
They perform one Final Push after every required gate passes. This standing
policy authorizes only a normal push to the cycle-start upstream. Stop and ask when the push lacks an
upstream, includes pre-cycle commits, changes destination, requires force, or
fails required Git/DVC evidence.

DVC synchronization is a separate external write: require confirmation for
`dvc push`, then record its evidence before Final Push.

## Execution

For requests to explain, review, diagnose, or plan, inspect relevant materials
and report the result without implementing unless requested. For requests to
change, build, or fix, make in-scope local changes and run non-destructive
validation without asking first.

Require confirmation before external writes, destructive or irreversible
actions, purchases, or material scope expansion. The DBSCTR Final Push above is
already confirmed by standing policy; other external writes still require it.

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

OpenAI Plan agents may use `explore-openai` and `scout-openai`; OpenAI Build
agents may also use `builder-openai`. `Build-Claude` may use only the matching
Bedrock agents. Log each optimized route. On failure, report it and retry once
by continuing directly with the same-provider flagship. Never cross providers
silently. For other selected models, use generic inheriting subagents.

Treat a graph as a routing hint, not a mandatory dependency. Check its recorded
commit and whether the query matches the task; fall back immediately when stale,
weak, or irrelevant. Source remains authoritative.

## Lifecycle Version

`/discovery` and `/dbsctr` load the unversioned DBSCTR V3 skills. V1 is removed.
V2 is retained only as source history under `docs/archive/` and is not deployed.
`/qa` remains available for explicit audits and DBSCTR capability gates.
