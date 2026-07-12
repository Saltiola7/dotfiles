# Backlog — DBSCTR V3 Lifecycle

Discovery readiness: complete.

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3.6-1 | Specify lifecycle reconciliation audit semantics | high | in_progress | V3.5-4 | lifecycle spec, roadmap, routing | audit use cases | no | Separate lifecycle drift from QA | M | Contract review |
| V3.6-2 | Add fixed-commit audit inventory and tests | high | in_progress | V3.6-1 | helper, typed tool, tests | Git artifacts and graph metadata | no | Make structural drift deterministic | M | Temporary-Git tests |
| V3.6-3 | Align skill/routing, deploy, and verify audit | high | pending | V3.6-2 | skill, routing, lifecycle artifacts | all V3.6 work | no | Complete roadmap coherently | M | Full QA and real audit smoke |
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
| V3.4-1–V3.4-3 | Automate isolated cycle setup and safe cleanup | 2026-07-12 | `da4ddf8`, `2b4191a` |
| V3.5-1–V3.5-4 | Add typed OpenCode and Herdr execution adapters | 2026-07-12 | `d9a7363`, `9916235` |

V3.5 implementation is complete. V3.6 lifecycle reconciliation audit is next.
