# Project Backlog

**Last updated:** 2026-06-01

Cross-cutting work tracker for the dotfiles project. Per-spec backlogs live in their respective `docs/specs/{context}/BACKLOG.md` files.

## Active

| # | Task | Spec | Priority | Status | Notes |
|---|------|------|----------|--------|-------|
| 1 | E2E validate single-flow AWS SSO recovery on real expiry | aws_creds | high | pending | Force-test via `aws sso logout` or wait for natural overnight expiry |
| 2 | Add Behavior Scenarios to astrovim.md | astrovim | low | backlog | Stable, two files customized, minimal benefit |
| 3 | Handle "Pick an account" MS page in autofill | aws_creds | low | pending | Only after explicit `aws sso logout` |
| 4 | Periodic auto-snapshot for kitty workspaces | kitty_pycharm | low | pending | launchd plist calling save-workspace.py |
| 5 | Add log rotation for AWS SSO logs | aws_creds | low | pending | ~/Library/Logs/aws-sso-login.{log,err.log} grow unbounded |
| 6 | Aerospace auto-route for kitty workspace windows | kitty_pycharm | low | pending | `on-window-detected` rules |

## Spec Index

| Spec | Format | Status |
|------|--------|--------|
| [aws_creds](specs/aws_creds/) | Directory (README + BACKLOG + CHANGELOG) | Stable |
| [kitty_pycharm](specs/kitty_pycharm/) | Directory (README + BACKLOG + CHANGELOG) | Experimental |
| [astrovim](specs/astrovim.md) | Flat file | Stable |
