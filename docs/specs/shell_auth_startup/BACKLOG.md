# Shell Auth Startup Backlog

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Completed

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-001 | Remove blocking auth from Herdr shell startup | P0 | done | none | shell startup | auth contracts | no | Prevent restore fanout | M | shell syntax |
| AUTH-002 | Make `secret` fail fast when `op` hangs | P0 | done | AUTH-001 | secret loader | 1Password CLI | no | Bound auth waits | M | timeout probe |
| AUTH-003 | Stop Clockify poll loop from calling `op` | P1 | done | none | Clockify poller | cached API key | yes | Avoid auth storms | S | static contract |
| AUTH-004 | Remove template-time 1Password reads from Databricks config | P1 | done | AUTH-002 | Databricks config | secret loader | yes | Keep apply noninteractive | S | render check |
| AUTH-005 | Use Keychain-backed 1Password service account token in Herdr | P0 | done | AUTH-002 | Herdr auth | Keychain and 1Password | no | Restore noninteractive access | L | auth probes |
| AUTH-006 | Avoid stale shell command lookup for `op-session` | P1 | done | AUTH-005 | secret loader | installed broker | yes | Select current broker | S | shell test |
| AUTH-007 | Preserve safe Keychain failure diagnostics and repair guidance | P1 | done | AUTH-005 | auth diagnostics | Keychain errors | yes | Actionable safe recovery | S | failure probes |
| AUTH-008 | Run persistent Herdr server in the Aqua security context | P0 | done | AUTH-005 | Herdr service | launchd context | no | Enable Keychain access | M | launchd smoke |
| AUTH-009 | Self-host portable Atuin history through tailnet-only SQLite service | P0 | done | none | terminal templates and Atuin service | Lima and Tailscale contracts | no | Share encrypted history | M | pytest, sync, offline, restore |
