# DBSCTR2 and Discovery2 Lifecycle

## Overview

The bounded context is the v2 lifecycle for OpenCode-native DBSCTR and
Discovery skills. The system creates strict, prompt-guide-native workflows that
remain callable beside the existing v1 skills forever.

The v2 lifecycle optimizes for current GPT-5.5 and Claude Opus 4.8 prompting
guidance, OpenCode global configuration, controlled subagent use, and stale-doc
prevention. It does not replace the original `dbsctr` or `discovery` skills.

## Problem Statement

The existing skills are useful but predate newer model prompt guidance,
OpenCode-native command/config patterns, and practical subagent orchestration.
They also need stronger guidance for keeping specs, backlogs, changelogs, and
other artifacts current when implementation changes.

## Goals

- Add globally managed `dbsctr2` and `discovery2` skills.
- Add global `/dbsctr2` and `/discovery2` thin wrapper commands.
- Add OpenCode-native routing through managed `~/.config/opencode/AGENTS.md`.
- Keep v1 `dbsctr` and `discovery` unchanged and callable forever.
- Install Ponytail globally and make minimal correct work a hard principle.
- Make DBSCTR2 strict when selected by routing or explicit command.
- Make Discovery2 interview until at least 95% confidence in user intent.
- Allow write subagents where viable while orchestrator owns review, test, and commit.
- Compile backlogs that are safe for concurrent work.

## Non-Goals

- Do not modify `~/.claude/CLAUDE.md`.
- Do not delete, rename, or deprecate v1 skills.
- Do not create model-specific v2 variants yet.
- Do not add custom OpenCode agents yet.
- Do not modify Graphify package internals.

## Domain Model

| Term | Definition |
|---|---|
| V2 Lifecycle | Combined Discovery2 and DBSCTR2 workflow, routing, commands, and deployment artifacts. |
| Discovery2 | Requirements interview skill that extracts user intent to at least 95% confidence before a DBSCTR2 cycle. |
| DBSCTR2 | Strict six-phase implementation skill: Domain, Behavior, Spec, Contract, Test, Refactor. |
| Orchestrator | Main agent running the skill, owning plan, file ownership, integration, validation, and commits. |
| Write Subagent | Subagent allowed to edit isolated files under an explicit ownership contract. |
| Ownership Contract | Per-task definition of files a subagent may write, files it may read, dependencies, collision risks, and validation. |
| Concurrent Backlog | Backlog structured so independent tasks can run in parallel without file collisions. |
| Phase Gate | Required checkpoint before moving to next DBSCTR2 phase or committing. |
| Artifact Freshness | Requirement that existing specs, backlogs, changelogs, docs, contracts, and tests remain aligned with behavior changes. |
| Thin Command | Slash command that only loads the matching skill and passes `$ARGUMENTS`; source of truth remains in the skill. |
| OpenCode Routing | Managed `AGENTS.md` guidance that selects `dbsctr2` and `discovery2` in OpenCode sessions. |
| Ponytail Principle | Hard rule to avoid work, reuse existing artifacts/code, and make the minimum correct change. |

## External Interfaces

| Interface | Purpose |
|---|---|
| `dot_agents/skills/dbsctr2/SKILL.md` | Source skill for DBSCTR2. |
| `dot_agents/skills/discovery2/SKILL.md` | Source skill for Discovery2. |
| `private_dot_config/opencode/commands/dbsctr2.md` | Global `/dbsctr2` command. |
| `private_dot_config/opencode/commands/discovery2.md` | Global `/discovery2` command. |
| `private_dot_config/opencode/AGENTS.md` | OpenCode-native routing instructions. |
| `private_dot_config/opencode/opencode.json.tmpl` | Global OpenCode config, including Ponytail plugin. |

## Prompt-Guidance Inputs

V2 skill prompts use outcome-first structure, success criteria, constraints,
output contracts, retrieval budgets, stop rules, and validation checks. They
avoid legacy process-heavy prompt stacks except for true invariants such as
phase order, artifact freshness, safety, and commit ownership.

## Routing Domain Rules

- OpenCode should route DBSCTR-required work to `dbsctr2` by default.
- If DBSCTR2 starts and no matching spec exists, it should auto-run Discovery2.
- Tiny unrelated edits do not require DBSCTR2 unless the user invokes it.
- If an edit changes behavior or existing artifacts, matching docs/specs/tests
  must be updated to avoid stale artifacts.
- Explicit `/dbsctr` and `/discovery` continue to load v1 skills.
