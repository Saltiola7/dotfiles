# Backlog — DBSCTR V3 Lifecycle

Discovery readiness: complete.

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3.4-1 | Specify automatic cycle isolation and cleanup | high | in_progress | V3.3-4 | lifecycle spec, roadmap | V3.3 registry | no | Remove dirty-main startup friction | M | Contract review |
| V3.4-2 | Implement `begin` and safe cleanup | high | in_progress | V3.4-1 | helper and tests | Git worktree behavior | no | Automate cycle execution workspace | L | Temporary-Git tests |
| V3.4-3 | Align skills, deploy, and verify V3.4 | high | pending | V3.4-2 | skills and lifecycle artifacts | all V3.4 work | no | Complete cycle coherently | M | Full QA and smoke |
Future milestones V3.3–V3.6 are specified in `ROADMAP.md` and become active only
after their preceding milestone completes.

## Completed

| id | outcome | completed | commit |
|---|---|---|---|
| V3-1–V3-15 | Implement and deploy DBSCTR V3 lifecycle | 2026-07-11 | `3151772` |
| V3-16 | Automate Gate Commits and Final Push | 2026-07-11 | `f7b11ca` |
| V3.1-1–V3.1-5 | Add deterministic V3.1 cycles and OpenCode integration | 2026-07-12 | `c9827e0` |
| V3.2-1–V3.2-5 | Add planned, ordered, monotonic cycle transitions | 2026-07-12 | `da65d0b`, `66df166`, `00c2950` |
| V3.3-1–V3.3-4 | Isolate concurrent worktree cycle state and delivery | 2026-07-12 | `d444950`, `7d80d21` |

V3.3 implementation is complete. V3.4 isolation automation is next; activate it
through a new cycle rather than expanding this completed one.
