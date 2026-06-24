# Shell Auth Startup

## Domain

Bounded context: shell authentication startup for interactive panes, agents, and status-bar plugins.

Entities:
- `LoginShell`: shell started by terminal, Herdr pane, or SSH.
- `SecretLoader`: sourceable `secret` command that exports credentials into current shell.
- `OnePasswordCommand`: `op` CLI command that can require app integration or biometric approval.
- `TemplateRenderer`: chezmoi render path that must not require live 1Password access.
- `HerdrPane`: restored or newly opened Herdr pane with `HERDR_ENV` set.
- `ClockifyPoller`: SketchyBar plugin that checks current Clockify timer.

Value objects:
- `CachedClockifyApiKey`: local API key file used by the poller.
- `OnePasswordSessionCache`: local token cache under `~/.cache/op/session`.
- `InjectedSecretBundle`: JSON document produced by grouped 1Password item fetches.
- `OnePasswordItemId`: stable item UUID used to fetch a secret item without title search.
- `ProjectedSecretSet`: validated JSON object containing every scalar secret and file payload needed by the shell.
- `CommandTimeout`: maximum wall time for external auth calls.

Events:
- `LoginShellStarted`
- `SecretLoadRequested`
- `OnePasswordCommandTimedOut`
- `HerdrPaneRestored`
- `ClockifyPollSkipped`

Glossary:
- **Startup-safe**: shell/profile path must not block on interactive auth or network credentials.
- **Fail-fast**: auth command exits with an error after a bounded timeout.
- **Poll loop**: recurring SketchyBar script execution driven by `update_freq`.

## Behavior Scenarios

### Feature: Startup-safe Herdr panes

**Scenario: Restored Herdr pane starts without auth fanout**
- Given many `HerdrPane` instances are restored at once
- When each `LoginShell` starts
- Then no `SecretLoader` runs automatically
- And no `OnePasswordCommand` runs from shell startup

### Feature: Fail-fast secret loading

**Scenario: OnePassword command hangs**
- Given `SecretLoadRequested` runs while `OnePasswordCommand` is wedged
- When an `op read` or session probe exceeds `CommandTimeout`
- Then `SecretLoader` fails fast
- And partial credential state is cleaned up

**Scenario: Secrets are loaded as a grouped bundle**
- Given `SecretLoadRequested` runs with a valid 1Password session
- When `SecretLoader` resolves required secrets
- Then it fetches required items by `OnePasswordItemId`
- And it projects them into one `ProjectedSecretSet`
- And it exports all required environment variables
- And it materializes required credential files
- And missing required values fail the whole load

**Scenario: Cached session is stale**
- Given `SecretLoadRequested` reads a cached `OnePasswordSessionCache`
- When the cached token is expired or rejected
- Then the first required 1Password fetch fails fast
- And partial credential state is cleaned up

### Feature: Clockify polling without auth storm

**Scenario: Cached Clockify API key is missing**
- Given `ClockifyPoller` runs in its poll loop
- And no `CachedClockifyApiKey` exists
- When the poller checks Clockify state
- Then it does not call `OnePasswordCommand`
- And it hides the Clockify item

## Contracts & Invariants

### LoginShell
- **Invariant:** profile startup must not invoke `secret` automatically.
- **Invariant:** profile startup must not run `op` commands.

### TemplateRenderer
- **Invariant:** `chezmoi status` and `chezmoi apply` must not call template-time `onepasswordRead` for routine config files.

### SecretLoader
- **Pre:** `secret` is sourced, not executed.
- **Post:** every `op` command either returns successfully or fails within `CommandTimeout`.
- **Post:** failed secret loading unsets `_SECRETS_LOADED`.
- **Invariant:** secret values are parsed from `InjectedSecretBundle` as JSON, not shell-evaluated text.
- **Invariant:** 1Password items are fetched by `OnePasswordItemId`, not title lookup.
- **Invariant:** required fields are projected into `ProjectedSecretSet` by one JSON projection step before exports or file writes.
- **Invariant:** the grouped secret path requires `jq` for JSON field extraction.
- **Post:** all required secrets are non-empty before `_SECRETS_LOADED` is set.

### OnePasswordSessionCache
- **Invariant:** cached tokens may be reused without a separate vault-list preflight.
- **Post:** stale cached tokens are discovered by the required secret fetch path and fail fast through `CommandTimeout`.

### ClockifyPoller
- **Invariant:** recurring poll path reads `CachedClockifyApiKey` only.
- **Invariant:** recurring poll path never calls `op read`.
- **Post:** missing API key hides the Clockify item and exits successfully.

## Verification

- Shell syntax checks pass for edited scripts.
- Static search confirms no Herdr profile auto-`secret` block remains.
- Static search confirms Clockify poller has no `op read` call.
- Static search confirms Databricks config has no `onepasswordRead` call.
