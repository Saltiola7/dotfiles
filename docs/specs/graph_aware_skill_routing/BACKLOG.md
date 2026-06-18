# Backlog: Graph-Aware Skill Routing

**Last updated:** 2026-06-18

## Active

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Add graph context gate to DBSCTR skill | high | done | Implemented in `dot_agents/skills/dbsctr/SKILL.md`. |
| 2 | Add graph context gate to Discovery skill | high | done | Implemented in `dot_agents/skills/discovery/SKILL.md`. |
| 3 | Install Graphify git hook for graph refresh | medium | done | `graphify hook install` completed; no OpenCode plugin added. |
| 4 | Verify skill instructions and hook status | medium | done | Hook status, graph query, targeted chezmoi apply, and git status checked. |

## Dependency Chain

1. Spec domain and behavior must exist before skill instructions change.
2. DBSCTR and Discovery skill edits can proceed after the shared graph context contract is documented.
3. Git hook install can happen independently of skill edits.
4. Verification runs after all edits and hook install.

## Parallel Execution Guide

Tasks that can be worked concurrently (no shared dependencies):
- 1 and 2 after the shared contract is documented.
- 3 after Graphify CLI availability is confirmed.

Tasks that must be sequential (shared models/contracts/migrations):
- Spec domain -> behavior -> contracts -> verification.
- 4 after 1, 2, and 3.

## Completed

| # | Task | Completed | Commit |
|---|------|-----------|--------|
| 1 | Add graph context gate to DBSCTR skill | 2026-06-18 | `4538e6c` |
| 2 | Add graph context gate to Discovery skill | 2026-06-18 | `4538e6c` |
| 3 | Install Graphify git hook for graph refresh | 2026-06-18 | `.git/hooks` local state |
| 4 | Verify skill instructions and hook status | 2026-06-18 | pending test commit |
