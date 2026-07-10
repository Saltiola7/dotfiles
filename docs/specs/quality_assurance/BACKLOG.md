# Backlog: Quality Assurance Skill

**Last updated:** 2026-07-10

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| QA-1 | Define domain and behavior | high | done | - | `docs/specs/quality_assurance/README.md` | existing lifecycle specs and skills | no | Establish shared language and user-visible behavior | S | Spec review |
| QA-2 | Define interfaces and contracts | high | done | QA-1 | quality-assurance spec files | OpenCode schema and current skills | no | Make implementation targets and invariants explicit | S | Interface-to-scenario review |
| QA-3 | Repair OpenCode subagent routing | high | in_progress | QA-2 | `private_dot_config/opencode/opencode.json.tmpl` | available OpenCode models | yes | Restore requested concurrent analysis | S | Launch read-only explore subagent |
| QA-4 | Implement QA skill and command | high | pending | QA-2 | `dot_agents/skills/qa/**`, `private_dot_config/opencode/commands/qa.md` | current Dependabot skill and command | yes | Consolidate quality concerns under one workflow | M | Skill/command smoke checks |
| QA-5 | Integrate DBSCTR2 and Discovery2 | high | pending | QA-2 | `dot_agents/skills/dbsctr2/SKILL.md`, `dot_agents/skills/discovery2/SKILL.md` | QA skill interface | yes | Add scoped gate and toolchain discovery | M | Text contract checks |
| QA-6 | Replace global routing and remove Dependabot wrappers | high | pending | QA-2 | global `AGENTS.md`, Dependabot skill/command paths | QA interface and v1 invariants | yes | Make QA the single global quality route | S | Routing grep checks |
| QA-7 | Manage project AGENTS through chezmoi | high | pending | QA-2 | `MGM/git/seo-data-science/AGENTS.md` | current project `AGENTS.md` | yes | Preserve project adaptations without global duplication | S | `chezmoi diff` target |
| QA-8 | Write project toolchain handoff | high | pending | QA-2 | `seo-data-science/docs/specs/toolchain/**` | project configs, ADR-032, JFrog spec | yes | Defer project setup with evidence and decisions intact | M | Handoff completeness review |
| QA-9 | Deploy and validate | high | pending | QA-3, QA-4, QA-5, QA-6, QA-7 | deployed OpenCode and agent paths | all changed files | no | Prove configuration and workflow loading | M | Targeted apply and smoke checks |
| QA-10 | Finalize artifacts | medium | pending | QA-8, QA-9 | QA backlog and changelog | validation evidence | no | Remove stale status and record outcome | S | Final diff review |

## Parallel Execution Guide

After QA-2, QA-4 through QA-8 have non-overlapping primary ownership and may run
concurrently. QA-3 may also run independently if it preserves unrelated user
changes in the OpenCode config template. QA-9 and QA-10 are sequential final
integration tasks.
