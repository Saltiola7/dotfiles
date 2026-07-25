# Shell Auth Startup

## Engineering Profile

| Concern | Default |
| --- | --- |
| Deliverable and owner | Personal chezmoi shell configuration and single-user Atuin service; operator owned |
| Runtime | macOS arm64 workstations and Fedora arm64 Lima guests; Bash; Atuin `18.17.1` |
| Platform | Docker on Colima, SQLite WAL storage, and Tailscale Serve HTTPS |
| Interfaces | Chezmoi `machine_type`, shell startup files, Atuin `config.toml`, Compose, `/healthz`, and Atuin sync protocol |
| Compatibility | Existing macOS rendering remains unchanged; `machine_type=lmsh` receives the portable terminal subset |
| Trust/data | Shell commands, arguments, working directories, account sessions, and encryption keys are sensitive |
| Deployment | Test account before migration; preserve hosted history and key; close registration after cutover |
| Operations | Loopback container ingress, tailnet-only HTTPS, health checks, bounded client timeouts, cold SQLite backup and restore |
| Maintenance | Pin image and clients, review updates and accepted risks, retain rollback until restore is proven |
| Authorities | Chezmoi rendering, shell syntax, pytest contracts, Compose validation, health/sync probes, lifecycle audit, and independent review |

Current cycle `AUTH-009-atuin-self-host` is elevated-risk deployment work. The
security and cloud modules apply. Release is not applicable because this source
publishes no project artifact; Review/Integrate, Deploy, Operate, and
Maintain/Retire are required.

## Domain

Bounded context: shell authentication startup for interactive panes, agents, and status-bar plugins.

Entities:
- `LoginShell`: shell started by terminal, Herdr pane, or SSH.
- `SecretLoader`: sourceable `secret` command that exports credentials into current shell.
- `OnePasswordCommand`: `op` CLI command that can require app integration or biometric approval.
- `TemplateRenderer`: chezmoi render path that must not require live 1Password access.
- `HerdrPane`: restored or newly opened Herdr pane with `HERDR_ENV` set.
- `HerdrServer`: persistent pane owner configured by the external `dotfiles-ai` source and launched in the macOS Aqua bootstrap context.
- `ClockifyPoller`: SketchyBar plugin that checks current Clockify timer.
- `TerminalProfile`: portable Bash, Atuin, zoxide, and Starship configuration
  selected by chezmoi machine intent and operating system.
- `AtuinClient`: one machine-local history database, record store, encryption
  key, and authenticated sync session.
- `AtuinServer`: pinned single-user container accepting authenticated encrypted
  record synchronization.
- `AtuinStore`: SQLite WAL database in a persistent host directory outside Git.
- `TailnetEndpoint`: Tailscale-terminated HTTPS proxy to loopback-only server
  ingress.

Value objects:
- `CachedClockifyApiKey`: local API key file used by the poller.
- `OnePasswordSessionCache`: local token cache under `~/.cache/op/session`.
- `OnePasswordServiceAccountToken`: per-session token injected into SSH/Herdr environments as `OP_SERVICE_ACCOUNT_TOKEN`.
- `MacOSKeychainServiceToken`: local login-Keychain item that stores `OnePasswordServiceAccountToken` for Herdr panes.
- `ShellSecretsItem`: consolidated 1Password item containing every secret required by `SecretLoader`.
- `ShellSecretsVault`: non-Personal 1Password vault (`Automation`) containing `ShellSecretsItem` for service-account access.
- `InjectedSecretBundle`: JSON document produced by the `ShellSecretsItem` fetch.
- `OnePasswordItemId`: stable item UUID used to fetch a secret item without title search.
- `ProjectedSecretSet`: validated JSON object containing every scalar secret and file payload needed by the shell.
- `CommandTimeout`: maximum wall time for external auth calls.

Events:
- `LoginShellStarted`
- `SecretLoadRequested`
- `OnePasswordCommandTimedOut`
- `HerdrPaneRestored`
- `ClockifyPollSkipped`
- `HistoryRecordedLocally`
- `HistorySyncRequested`
- `AtuinServerUnavailable`
- `HostedHistoryMigrated`
- `AtuinRegistrationClosed`

Glossary:
- **Startup-safe**: shell/profile path must not block on interactive auth or network credentials.
- **Fail-fast**: auth command exits with an error after a bounded timeout.
- **Poll loop**: recurring SketchyBar script execution driven by `update_freq`.
- **lmsh:** portable personal terminal profile shared by personal and MGM Lima
  guests; it does not imply a shared VM filesystem or client identity.
- **Cold backup:** complete copy of stopped SQLite config storage, including WAL
  companions when present.

## Behavior Scenarios

### Feature: Startup-safe Herdr panes

**Scenario: Restored Herdr pane starts without auth fanout**
- Given many `HerdrPane` instances are restored at once
- When each `LoginShell` starts
- Then no `SecretLoader` runs automatically
- And no `OnePasswordCommand` runs from shell startup

**Scenario: Herdr server starts in the GUI security context**
- Given the user has an active Aqua login session
- When the managed `HerdrServer` starts
- Then launchd runs it with `LimitLoadToSessionType=Aqua`
- And no credential is stored in its plist or environment configuration
- And restored `HerdrPane` processes can request the login-Keychain service token

### Feature: Fail-fast secret loading

**Scenario: OnePassword command hangs**
- Given `SecretLoadRequested` runs while `OnePasswordCommand` is wedged
- When an `op read` or session probe exceeds `CommandTimeout`
- Then `SecretLoader` fails fast
- And partial credential state is cleaned up

**Scenario: Secrets are loaded from one consolidated item**
- Given `SecretLoadRequested` runs with a valid 1Password session
- When `SecretLoader` resolves required secrets
- Then it fetches exactly one `ShellSecretsItem` by `OnePasswordItemId`
- And it projects them into one `ProjectedSecretSet`
- And it exports all required environment variables
- And it materializes required credential files
- And missing required values fail the whole load

**Scenario: SSH session uses injected service account token**
- Given `SecretLoadRequested` runs in an SSH `LoginShell`
- And `OnePasswordServiceAccountToken` is present in the environment
- When the token passes the session validity probe
- Then `SecretLoader` uses that token for the `ShellSecretsItem` fetch
- And no biometric session mint is attempted
- And no `OnePasswordSessionCache` is written

**Scenario: Herdr session uses Keychain-backed service account token**
- Given `SecretLoadRequested` runs in a `HerdrPane`
- And no `OnePasswordServiceAccountToken` is present in the environment
- And a `MacOSKeychainServiceToken` exists
- When the token passes the session validity probe
- Then `SecretLoader` uses that token for the `ShellSecretsItem` fetch
- And no biometric or delegated `op signin` is attempted
- And no `OnePasswordSessionCache` is read or written
- And the `ShellSecretsItem` fetch specifies `ShellSecretsVault`
- And `SecretLoader` sources sibling `op-session` directly instead of using shell command lookup

**Scenario: Herdr session lacks service account token**
- Given `SecretLoadRequested` runs in a `HerdrPane`
- And no `OnePasswordServiceAccountToken` is present in the environment
- And no `MacOSKeychainServiceToken` is available
- When `SecretLoader` resolves 1Password authentication
- Then it fails fast without calling `op signin`
- And it tells the user to configure a Keychain-backed `OP_SERVICE_ACCOUNT_TOKEN`

**Scenario: Herdr cannot read the Keychain service token**
- Given the Keychain item exists but macOS denies non-interactive access
- When `SecretLoader` resolves 1Password authentication
- Then it reports the Keychain failure without exposing the token
- And it provides Keychain Access guidance that trusts `/usr/bin/security`
- And it does not call delegated `op signin`

**Scenario: SSH session lacks service account token**
- Given `SecretLoadRequested` runs in an SSH `LoginShell`
- And no valid `OnePasswordSessionCache` is available
- And no `OnePasswordServiceAccountToken` is present in the environment
- When `SecretLoader` resolves 1Password authentication
- Then it fails fast without calling `op signin`
- And it tells the user to inject `OP_SERVICE_ACCOUNT_TOKEN`

**Scenario: Cached session is stale**
- Given `SecretLoadRequested` reads a cached `OnePasswordSessionCache`
- When the cached token is expired or rejected by the session validity probe
- Then `SecretLoader` mints one fresh `OnePasswordSessionCache` in a TTY shell
- And no grouped item fetch starts before the session is valid
- And partial credential state is cleaned up

**Scenario: Exported session is stale while a lock remains**
- Given `OnePasswordSessionEnv` contains a stale token
- And `OnePasswordSessionLock` remains from an earlier attempt
- When the session validity probe rejects the exported token
- Then `SecretLoader` discards the exported token
- And it force-mints one fresh `OnePasswordSessionCache` in a TTY shell
- And it removes the stale lock before minting

### Feature: Clockify polling without auth storm

**Scenario: Cached Clockify API key is missing**
- Given `ClockifyPoller` runs in its poll loop
- And no `CachedClockifyApiKey` exists
- When the poller checks Clockify state
- Then it does not call `OnePasswordCommand`
- And it hides the Clockify item

### Feature: Portable terminal profile

**Scenario: Lima shell starts with personal terminal behavior**
- Given a Linux machine has `machine_type=lmsh`
- When chezmoi applies the personal source and Bash starts
- Then only portable shell configuration is rendered
- And Atuin, zoxide, and Starship initialize only when installed
- And macOS applications, LaunchAgents, credential helpers, and private keys are
  not installed
- And shell startup performs no network authentication

### Feature: Private self-hosted history sync

**Scenario: Tailnet client reaches Atuin**
- Given the pinned Atuin container is healthy on Mac loopback
- When an authorized Mac or Lima client connects to the stable tailnet URL
- Then Tailscale terminates HTTPS and proxies to the loopback service
- And no LAN or public listener exposes the container

**Scenario: Server is unavailable**
- Given an authenticated client cannot reach the Atuin server
- When the shell records and searches history
- Then local capture and search continue
- And encrypted unsynchronized records remain durable locally
- And bounded network timeouts prevent an unbounded shell delay
- And a later successful sync reconciles missing record chains

**Scenario: Hosted history moves after isolated validation**
- Given a disposable account synchronized between the Mac and both Lima clients
- And the hosted client has completed a final sync and local backup
- When the operator preserves the existing encryption key, registers the local
  account, and changes the sync endpoint
- Then existing local encrypted records upload to the self-hosted server
- And a second client decrypts the same representative history
- And the hosted account remains available for rollback until restore is proven

**Scenario: Registration closes after migration**
- Given the production account exists and client sync passes
- When the server restarts with open registration disabled
- Then existing authenticated clients continue to sync
- And an unregistered client cannot create another account

**Scenario: SQLite store is recoverable**
- Given the server is stopped cleanly
- When the complete persistent config directory is copied and restored in
  isolation
- Then the restored `/healthz` succeeds
- And an authenticated client can synchronize without changing its encryption
  key

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
- **Invariant:** `ShellSecretsItem` is fetched by `OnePasswordItemId`, not title lookup.
- **Invariant:** `ShellSecretsItem` is fetched from `ShellSecretsVault` so service-account reads satisfy 1Password CLI vault scoping.
- **Invariant:** `SecretLoader` performs one secret item fetch per load after session validation.
- **Invariant:** required fields are projected into `ProjectedSecretSet` by one JSON projection step before exports or file writes.
- **Invariant:** the grouped secret path requires `jq` for JSON field extraction.
- **Invariant:** installed `SecretLoader` sources sibling `op-session` by path so stale shell command hashes cannot select an old broker.
- **Post:** all required secrets are non-empty before `_SECRETS_LOADED` is set.

### OnePasswordSessionCache
- **Invariant:** cached tokens must pass one bounded validity probe before grouped item fetches start.
- **Invariant:** `OnePasswordServiceAccountToken` takes precedence over cached and biometric session paths.
- **Invariant:** `HerdrPane` uses `OnePasswordServiceAccountToken` from environment or `MacOSKeychainServiceToken` only; it must not call delegated desktop `op signin`.
- **Invariant:** `MacOSKeychainServiceToken` service/account values and `op-session` are managed by the machine-local `dotfiles-ai` configuration.
- **Invariant:** Keychain failures retain actionable diagnostics without printing credential values.
- **Invariant:** Keychain repair is explicit and interactive; `SecretLoader` never mutates Keychain ACLs.
- **Invariant:** repair guidance does not use `security -w` interactive input because it truncates the service-account token.
- **Invariant:** `HerdrServer` runs in the Aqua launchd domain without embedding credentials in its plist; this repository does not own that plist.
- **Invariant:** chezmoi deployment never stops an unmanaged `HerdrServer`; initial handoff is explicit or occurs at the next GUI login.
- **Post:** valid service account tokens must not call `op signin` or write `OnePasswordSessionCache`.
- **Post:** invalid service account tokens fail fast with a service-account-specific error.
- **Post:** SSH shells without a service account token must not attempt biometric or password-based `op signin`.
- **Post:** stale exported session tokens are discarded before a forced mint.
- **Post:** stale cached tokens are refreshed once in a TTY shell before parallel 1Password item fetches run.
- **Post:** non-TTY shells fail fast when no valid cached token is available.

### ClockifyPoller
- **Invariant:** recurring poll path reads `CachedClockifyApiKey` only.
- **Invariant:** recurring poll path never calls `op read`.
- **Post:** missing API key hides the Clockify item and exits successfully.

### TerminalProfile
- **Invariant:** `.chezmoi.os` expresses platform and `machine_type=lmsh`
  expresses Lima terminal intent.
- **Invariant:** macOS rendering remains byte-compatible outside intentional
  Atuin endpoint and daemon changes.
- **Invariant:** optional shell tools are command-guarded.
- **Invariant:** the lmsh target excludes SSH private keys, GitHub credentials,
  1Password integration, GUI applications, and macOS service configuration.

### AtuinServer
- **Invariant:** server and clients use pinned compatible Atuin `18.17.1`.
- **Invariant:** the container publishes only to `127.0.0.1`; Tailscale Serve is
  the only remote ingress.
- **Invariant:** the image is `ghcr.io/atuinsh/atuin:18.17.1` and the state URI is
  `sqlite:///config/atuin.db`.
- **Invariant:** open registration is an explicit temporary deployment override
  and defaults to false.
- **Invariant:** credentials, sessions, encryption keys, databases, and backups
  stay outside Git and command output.
- **Post:** successful migration retains the original encryption key and closes
  registration.

### AtuinClient
- **Invariant:** clients keep unique local host identity and databases; internal
  Atuin state is never copied between active clients.
- **Invariant:** the server address is tailnet HTTPS, automatic sync is bounded,
  and built-in secret filtering remains enabled.
- **Invariant:** `atuin key`, raw credential retrieval, and password-bearing
  commands are excluded from history collection.
- **Post:** remote failure does not prevent local history search or capture.

### Accepted Risk
- `AUTH-009-AR1`: the operator approved synchronizing MGM shell history through
  the same personal account, making work commands and paths decryptable on
  personal clients. End-to-end encryption, secret filters, tailnet-only ingress,
  and local credential isolation compensate but do not satisfy employer policy.
  Owner: operator. Review by 2026-08-18 or before connecting another work client.

## Verification

- Shell syntax checks pass for edited scripts.
- Static search confirms no Herdr profile auto-`secret` block remains.
- Static search confirms Clockify poller has no `op read` call.
- Static search confirms Databricks config has no `onepasswordRead` call.
- Pytest verifies lmsh exclusions, command guards, pinned assets, loopback-only
  Compose, closed-by-default registration, and bounded Atuin configuration.
- `docker compose config` validates the rendered service.
- Mac and both Lima clients resolve the tailnet endpoint and receive healthy
  HTTPS without a public or LAN listener.
- Disposable-account synchronization passes before production migration.
- Production validation compares representative history across two clients,
  verifies denied registration, exercises offline recovery, and restores one
  cold backup in isolation.
