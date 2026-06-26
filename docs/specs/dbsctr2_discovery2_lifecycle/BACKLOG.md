# Backlog — DBSCTR2 and Discovery2 Lifecycle

## Active Tasks

None.

## Parallel Execution Guide

Tasks 3 and parts of task 4 can use write subagents only after the
orchestrator assigns non-overlapping file ownership. The orchestrator must
review all edits, run validation, and commit phase gates. Subagents never
commit.

## Completed Tasks

| ID | Title | Completed | Commit |
|---|---|---|---|
| 1 | Define v2 lifecycle domain | 2026-06-25 | `8993f76` |
| 2 | Add v2 workflow scenarios | 2026-06-25 | `ad524ee` |
| 3 | Add v2 skill and command interfaces | 2026-06-25 | `8b37fb1` |
| 4 | Add v2 routing and config contracts | 2026-06-25 | `15e902a` |
| 5 | Verify v2 deployment | 2026-06-25 | `9d40496` |
| 6 | Finalize lifecycle docs | 2026-06-25 | `e74ef01` |
| 7 | Add DBSCTR2 DVC sync gate | 2026-06-25 | `cafd07d` |
| 8 | Add Dependabot skill and DBSCTR2 gate | 2026-06-26 | `e2681bd` |
