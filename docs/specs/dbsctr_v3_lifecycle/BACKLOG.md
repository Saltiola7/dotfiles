# Backlog — DBSCTR V3 Lifecycle

Discovery readiness: complete.

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3.2-1 | Specify schema, applicability, order, and risk contracts | high | in_progress | - | lifecycle spec, roadmap, templates | approved discovery | no | Establish V3.2 authority | M | Contract review |
| V3.2-2 | Add V3.2 transition and legacy tests | high | pending | V3.2-1 | `tests/test_dbsctrctl.py`, lifecycle tests | helper and contracts | no | Preserve compatibility before implementation | M | Intended failures then pass |
| V3.2-3 | Implement V3.2 cycle transitions | high | pending | V3.2-2 | `dot_local/bin/executable_dbsctrctl` | tests and contracts | no | Enforce protocol deterministically | L | Temporary-Git tests |
| V3.2-4 | Align skills and templates | high | pending | V3.2-1 | DBSCTR/Discovery skills, templates | V3.2 contracts | yes, after V3.2-1 | Keep reasoning aligned | M | Lifecycle contracts and smoke |
| V3.2-5 | Integrate, deploy, and verify V3.2 | high | pending | V3.2-3, V3.2-4 | shared tests and lifecycle artifacts | all V3.2 work | no | Complete cycle coherently | M | Full QA, chezmoi, fresh-process smoke |

Future milestones V3.3–V3.6 are specified in `ROADMAP.md` and become active only
after their preceding milestone completes.

## Completed

| id | outcome | completed | commit |
|---|---|---|---|
| V3-1–V3-15 | Implement and deploy DBSCTR V3 lifecycle | 2026-07-11 | `3151772` |
| V3-16 | Automate Gate Commits and Final Push | 2026-07-11 | `f7b11ca` |
| V3.1-1–V3.1-5 | Add deterministic V3.1 cycles and OpenCode integration | 2026-07-12 | `c9827e0` |

V3.1 implementation is complete. Add an OpenCode plugin only after measured
helper bypass or compaction loss justifies ambient enforcement.
