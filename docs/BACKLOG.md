# Project Backlog

**Last updated:** 2026-11-18

Cross-cutting work tracker for the dotfiles project. Per-spec backlogs live in their respective `docs/specs/{context}/BACKLOG.md` files.

## Active

| # | Task | Spec | Priority | Status | Notes |
|---|------|------|----------|--------|-------|
| 1 | Add Behavior Scenarios to astrovim.md | astrovim | low | backlog | Stable, two files customized, minimal benefit |
| 2 | Periodic auto-snapshot for kitty workspaces | kitty_pycharm | low | pending | launchd plist calling save-workspace.py |
| 3 | Aerospace auto-route for kitty workspace windows | kitty_pycharm | low | pending | `on-window-detected` rules |
| 4 | Implement mbp built-in keyboard layout (XKB `tis`, keyd layers, Touch Bar policy) | mbp_keyboard_layout | high | pending | Discovery 2026-11-18; spec README is normative |

## Spec Index

| Spec | Format | Status |
|------|--------|--------|
| [aws_creds](specs/aws_creds/) | Directory (README + BACKLOG + CHANGELOG) | Stable |
| [kitty_pycharm](specs/kitty_pycharm/) | Directory (README + BACKLOG + CHANGELOG) | Experimental |
| [mbp_keyboard_layout](specs/mbp_keyboard_layout/) | Directory (README + PROFILE + BACKLOG + CHANGELOG) | Draft |
| [astrovim](specs/astrovim.md) | Flat file | Stable |
