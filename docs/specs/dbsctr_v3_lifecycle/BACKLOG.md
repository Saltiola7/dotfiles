# Backlog — DBSCTR V3 Lifecycle

Discovery readiness: complete.

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3.3-1 | Specify common cycle registry and worktree ownership | high | in_progress | V3.2-5 | lifecycle spec, roadmap | V3.2 records | no | Define concurrent state authority | M | Contract review |
| V3.3-2 | Add linked-worktree and target-lock tests | high | in_progress | V3.3-1 | helper tests | Git worktree behavior | no | Prove isolation and serialization | M | Temporary-Git tests |
| V3.3-3 | Implement common registry and delivery lock | high | in_progress | V3.3-2 | `dbsctrctl` | lifecycle contracts | no | Enable concurrent isolated cycles | L | Full helper suite |
| V3.3-4 | Align skills, deploy, and verify V3.3 | high | pending | V3.3-3 | skills and lifecycle artifacts | all V3.3 work | no | Complete cycle coherently | M | Full QA and smoke |
Future milestones V3.3–V3.6 are specified in `ROADMAP.md` and become active only
after their preceding milestone completes.

## Completed

| id | outcome | completed | commit |
|---|---|---|---|
| V3-1–V3-15 | Implement and deploy DBSCTR V3 lifecycle | 2026-07-11 | `3151772` |
| V3-16 | Automate Gate Commits and Final Push | 2026-07-11 | `f7b11ca` |
| V3.1-1–V3.1-5 | Add deterministic V3.1 cycles and OpenCode integration | 2026-07-12 | `c9827e0` |
| V3.2-1–V3.2-5 | Add planned, ordered, monotonic cycle transitions | 2026-07-12 | `da65d0b`, `66df166`, `00c2950` |

V3.2 implementation is complete. V3.3 worktree architecture is next; activate it
through a new discovery-ready cycle rather than expanding this completed one.
