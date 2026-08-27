# Shell Auth Startup Backlog

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-018-marimo-theme-source-root | Make the Mac mini external dotfiles checkout authoritative and apply Catppuccin Mocha to marimo | P2 | active | AUTH-017-personal-source-root | `.chezmoi.toml.tmpl`, marimo config/theme, source-root contract | machine type, upstream theme | no | source migration and deployment share one ordering boundary | S | pytest, chezmoi render, marimo config, browser CSS |

## Completed

| id | outcome | completed | commit |
| --- | --- | --- | --- |
| AUTH-017-personal-source-root | Pinned the personal chezmoi source beneath each user's home independently of scoped XDG data | 2026-08-24 | `999d6f8` |
| AUTH-014-lima-atuin-recovery | Moved native Lima and Colima state externally, rebuilt shared Atuin sync from surviving clients, added guarded restart and cold restore, and reconciled PyCharm log routing | 2026-08-09 | `3fc478e..ce91840` |
| AUTH-001 through AUTH-008 | Startup-safe auth, polling, Keychain, and Herdr behavior | 2026-07-13 | `22c554e` baseline history |
| AUTH-009 | Tailnet-only self-hosted Atuin and portable lmsh terminal profile | 2026-07-25 | `b44b1eb`, `2cee8ea` |
| AUTH-010 | Deny-by-default lmsh source target boundary | 2026-07-25 | `4fdc25e` |
| AUTH-010-session-credentials | Session-isolated GCP credentials with stale-file rematerialization | 2026-08-01 | `a8e0d9a` |
| AUTH-011-cache-relocation | Routed supported CLI caches and Pulumi home through sentinel-guarded native paths; paused PyCharm, Prefect, and Codex | 2026-08-09 | `712e31e` |
| AUTH-013-runtime-state-relocation | Routed validated Prefect, Codex, and PyCharm state externally with team-safe defaults and runtime fallback | 2026-08-09 | `0e3e9dc` |
