# Backlog — DBSCTR V3 Lifecycle

Discovery confidence: 97%.

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3-1 | Persist V3 domain and behavior | high | done | - | V3 lifecycle README and changelog | V1/V2 lifecycle, QA, Graphify | no | Establish shared intent | M | Artifact review |
| V3-2 | Define interfaces and contracts | high | done | V3-1 | V3 lifecycle README and backlog | approved discovery | no | Make implementation deterministic | M | Interface/scenario trace review |
| V3-3 | Add failing lifecycle contract tests | high | done | V3-2 | `tests/test_dbsctr_lifecycle.py`, CI workflow | interfaces and migration contracts | no | Prove expected migration before edits | M | 8 intended failures before implementation |
| V3-4 | Implement Discovery V3 | high | done | V3-3 | `dot_agents/skills/discovery/**` | V3 spec, project routing | yes | Create Engineering Profiles and artifacts | M | Static contracts and live skill load passed |
| V3-5 | Implement DBSCTR V3 core | high | done | V3-3 | `dot_agents/skills/dbsctr/SKILL.md` | V3 spec, module contract | yes | Add kernel and completion gates | L | Static contracts and live phase/gate probe passed |
| V3-6 | Extend QA capability mode | high | done | V3-3 | `dot_agents/skills/qa/SKILL.md`, QA spec | Engineering Profile contract | yes | Distinguish configured evidence from gaps | M | QA contracts and live statuses passed |
| V3-7 | Add Python and Security modules | high | done | V3-2 | `modules/python.md`, `modules/security.md` | standards research, module contract | yes | Add first language and risk extensions | M | Module schema tests passed |
| V3-8 | Normalize Data module | high | done | V3-2 | `modules/data.md`, `references/data.md` | current Data module | yes | Separate outcomes from implementation examples | M | Module schema and banned-mandate tests passed |
| V3-9 | Normalize Cloud module | high | done | V3-2 | `modules/cloud.md`, `references/cloud.md` | current Cloud module | yes | Make platform controls provider-neutral | M | Module schema and banned-mandate tests passed |
| V3-10 | Normalize ML module | high | done | V3-2 | `modules/ml.md`, `references/ml.md` | current ML module | yes | Derive thresholds from policy and evidence | M | Module schema and banned-threshold tests passed |
| V3-11 | Normalize Analytics module | high | done | V3-2 | `modules/analytics.md`, `references/analytics.md` | current Analytics module | yes | Generalize governance and review outcomes | M | Module schema and provenance tests passed |
| V3-12 | Migrate runtime surfaces | high | done | V3-4, V3-5, V3-6, V3-7, V3-8, V3-9, V3-10, V3-11 | commands, routing, archive, removals | all implemented skills | no | Make V3 default and remove V1/V2 runtime | M | Source/deployed migration assertions passed |
| V3-13 | Refresh active downstream specs | medium | done | V3-12 | QA, control-plane, routing, prompting, analytics specs | final interfaces | no | Prevent stale active contracts | M | Independent reference audit remediated |
| V3-14 | Deploy and validate V3 | high | done | V3-12, V3-13 | deployed managed targets, validation evidence | all implementation | no | Prove runtime behavior | M | 185 tests, dry-run, apply, smoke probes, status passed |
| V3-15 | Finalize lifecycle artifacts | medium | done | V3-14 | V3 backlog, changelog, README | validation evidence | no | Close with no stale artifacts | S | Final diff and affected-scope QA passed |
| V3-16 | Automate sensible commits and final push | high | done | V3-15 | DBSCTR skill, routing, lifecycle contracts/tests | Git safety policy | no | Preserve coherent history and complete delivery without a second request | S | Intended failure, 186 tests, deployment, live smoke, Gate Commit, Final Push |

Tasks V3-4 through V3-11 own non-overlapping files and may run concurrently once
V3-3 fixes the shared contracts. The primary owns shared routing, migration,
integration, deployment, staging, and commits.
