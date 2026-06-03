# Backlog: Kitty-PyCharm Workspace Integration

**Last updated:** 2026-06-01

## Active

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Periodic auto-snapshot via launchd | low | pending | plist that calls `save-workspace.py` every N minutes |
| 2 | Session switcher keybinding | low | pending | Map a key to switch between workspaces quickly |
| 3 | Aerospace integration for auto-routing | low | pending | `on-window-detected` rules to route workspace OS windows to specific AeroSpace workspaces |
| 4 | Fix tab_bar_filter for remote-control workspaces | low | pending | Currently no effect since workspaces aren't formal Kitty sessions |

## Parallel Execution Guide

All tasks are independent — can be worked in any order or concurrently.

## Completed

| # | Task | Completed | Commit |
|---|------|-----------|--------|
| — | Initial implementation (v1) | 2026-04-20 | (multiple) |
| — | kitty-query.py consolidation (PEP 723, typer CLI) | 2026-04-20 | (multiple) |
| — | 160 unit tests | 2026-04-20 | (multiple) |
| — | Snapshot save/restore system | 2026-04-20 | (multiple) |
| — | OpenCode session resumption with map/seed | 2026-04-20 | (multiple) |
| — | Pane tab move keymaps | 2026-05-15 | `a24bfb4`, `bc9b6dc` |
