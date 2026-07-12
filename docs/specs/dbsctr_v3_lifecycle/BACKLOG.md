# Backlog — DBSCTR V3 Lifecycle

Discovery confidence: 97%.

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3.1-1 | Correct lifecycle semantics and artifact policy | high | done | - | V3 lifecycle spec, backlog, changelog, templates | V3 review and approved discovery | no | Establish shared contracts before code | M | Scenario and contract review passed |
| V3.1-2 | Add deterministic cycle helper and tests | high | done | V3.1-1 | `dot_local/bin/executable_dbsctrctl`, helper tests | lifecycle contracts | yes | Enforce state and Git safety | L | 15 temporary-Git tests passed |
| V3.1-3 | Update skills and structured QA integration | high | done | V3.1-1 | Discovery, DBSCTR, QA skills | lifecycle contracts | yes | Make reasoning match V3.1 | M | Skill contracts and runtime probes passed |
| V3.1-4 | Align OpenCode permissions and reviewer route | high | done | V3.1-1 | OpenCode config, reviewer agent, commands | helper interface | yes | Add technical boundaries and review capability | M | Config, permission, and reviewer smoke passed |
| V3.1-5 | Integrate, deploy, and verify V3.1 | high | pending | V3.1-2, V3.1-3, V3.1-4 | shared tests, deployed targets, lifecycle artifacts | all V3.1 work | no | Complete the cycle coherently | M | Full QA, chezmoi, fresh-process smoke |

## Completed

| id | outcome | completed | commit |
|---|---|---|---|
| V3-1–V3-15 | Implement and deploy DBSCTR V3 lifecycle | 2026-07-11 | `3151772` |
| V3-16 | Automate Gate Commits and Final Push | 2026-07-11 | `f7b11ca` |

V3.1-2 through V3.1-4 own non-overlapping files and may run concurrently after
V3.1-1. The primary owns shared tests, integration, deployment, staging, and Git.
