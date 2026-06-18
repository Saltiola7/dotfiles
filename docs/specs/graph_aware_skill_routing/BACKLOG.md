# Backlog: Graph-Aware Skill Routing

**Last updated:** 2026-06-18

## Active

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Add graph context gate to DBSCTR skill | high | pending | Requires spec domain and behavior. |
| 2 | Add graph context gate to Discovery skill | high | pending | Requires spec domain and behavior. |
| 3 | Install Graphify git hook for graph refresh | medium | pending | Use `graphify hook install`; no OpenCode plugin. |
| 4 | Verify skill instructions and hook status | medium | pending | Validate docs, skill wording, and hook state. |

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
