# OpenCode Global Routing

## DBSCTR2 Default

Use `dbsctr2` by default for work that:
- creates or changes models, entities, data schemas, APIs, views, service logic,
  pipeline flows, tasks, orchestration, validation, business rules, domain
  constraints, user-visible behavior, or downstream-visible behavior
- changes behavior represented by existing specs, docs, contracts, or tests

When `dbsctr2` starts and no matching spec exists in `docs/specs/`, load
`discovery2` automatically and run it first. Resume DBSCTR2 only after
Discovery2 reaches at least 95% confidence and writes or updates the required
artifacts.

Do not use DBSCTR2 for tiny unrelated edits, formatting-only changes,
git-only tasks, dependency-only work, or config-only changes with no behavior
impact unless the user explicitly asks for DBSCTR2.

If a small change affects existing artifacts, update those artifacts. Stale docs
are a failure.

## V1 Permanence

Keep v1 skills unchanged and callable forever:
- `/dbsctr` loads `dbsctr`
- `/discovery` loads `discovery`

Do not rename, delete, or deprecate v1.

## Ponytail Principle

Before building, choose the lowest sufficient rung:
1. Does this need to exist?
2. Can existing code or specs cover it?
3. Can native platform or standard library do it?
4. Can an installed dependency do it?
5. Can one small change do it?
6. Otherwise build the minimum correct solution.

Do not cut validation, security, data-loss handling, accessibility, or tests.

## Subagents

Use subagents when they make work faster or safer through independent ownership.
Write subagents may edit files only under an explicit ownership contract.
The orchestrator reviews, validates, stages, and commits. Subagents never commit.
