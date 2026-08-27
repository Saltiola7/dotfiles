# Shell Auth Startup Backlog

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-019-yazi-terminal-file-manager | Install Yazi with portable shell cwd integration and Catppuccin Mocha | medium | active | none | Brewfile; shell templates; lmsh installer; Yazi config; terminal tests | shell auth startup profile; upstream Yazi docs | no | Shared shell and lifecycle artifacts require serial ownership | M | rendered shells; pytest; macOS and Fedora arm64 smoke |

## Completed

| id | outcome | completed | commit |
| --- | --- | --- | --- |
| AUTH-018-marimo-theme-source-root | Made the Mac mini external checkout authoritative, preserved the retired home clone's unique work, and applied pinned Catppuccin Mocha to marimo | 2026-08-26 | `03ad052`, `65a8283`, `59b9066` |
| AUTH-017-personal-source-root | Pinned the personal chezmoi source beneath each user's home independently of scoped XDG data | 2026-08-24 | `999d6f8` |
| AUTH-014-lima-atuin-recovery | Moved native Lima and Colima state externally, rebuilt shared Atuin sync from surviving clients, added guarded restart and cold restore, and reconciled PyCharm log routing | 2026-08-09 | `3fc478e..ce91840` |
| AUTH-001 through AUTH-008 | Startup-safe auth, polling, Keychain, and Herdr behavior | 2026-07-13 | `22c554e` baseline history |
| AUTH-009 | Tailnet-only self-hosted Atuin and portable lmsh terminal profile | 2026-07-25 | `b44b1eb`, `2cee8ea` |
| AUTH-010 | Deny-by-default lmsh source target boundary | 2026-07-25 | `4fdc25e` |
| AUTH-010-session-credentials | Session-isolated GCP credentials with stale-file rematerialization | 2026-08-01 | `a8e0d9a` |
| AUTH-011-cache-relocation | Routed supported CLI caches and Pulumi home through sentinel-guarded native paths; paused PyCharm, Prefect, and Codex | 2026-08-09 | `712e31e` |
| AUTH-013-runtime-state-relocation | Routed validated Prefect, Codex, and PyCharm state externally with team-safe defaults and runtime fallback | 2026-08-09 | `0e3e9dc` |
