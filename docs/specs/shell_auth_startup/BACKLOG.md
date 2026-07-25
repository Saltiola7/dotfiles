# Shell Auth Startup Backlog

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-010 | Enforce deny-by-default lmsh targets | P0 | active | AUTH-009 | `.chezmoiignore`, terminal profile contract and test | personal source target inventory | no | One policy boundary and its evidence must change atomically | S | exact allowlist test and Linux dry-run |

## Completed

| id | outcome | completed | commit |
| --- | --- | --- | --- |
| AUTH-001 through AUTH-008 | Startup-safe auth, polling, Keychain, and Herdr behavior | 2026-07-13 | `22c554e` baseline history |
| AUTH-009 | Tailnet-only self-hosted Atuin and portable lmsh terminal profile | 2026-07-25 | `b44b1eb`, `2cee8ea` |
