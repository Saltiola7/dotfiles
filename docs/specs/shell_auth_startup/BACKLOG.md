# Shell Auth Startup Backlog

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-009 | Self-host portable Atuin history | P0 | active | none | shell templates, Atuin config/server, tests, this context | Lima and Tailscale contracts | no | Shared encrypted terminal history requires one migration and trust boundary | M | pytest, render, shell, Compose, health, sync, offline, restore |

## Completed

| ID | Task | Status |
| --- | --- | --- |
| AUTH-001 | Remove blocking auth from Herdr shell startup | done |
| AUTH-002 | Make `secret` fail fast when `op` hangs | done |
| AUTH-003 | Stop Clockify poll loop from calling `op` | done |
| AUTH-004 | Remove template-time 1Password reads from Databricks config | done |
| AUTH-005 | Use Keychain-backed 1Password service account token in Herdr | done |
| AUTH-006 | Avoid stale shell command lookup for `op-session` | done |
| AUTH-007 | Preserve safe Keychain failure diagnostics and repair guidance | done |
| AUTH-008 | Run persistent Herdr server in the Aqua security context | done |
