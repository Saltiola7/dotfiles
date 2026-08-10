# Shell Auth Startup Changelog

## 2026-08-09

- Routed mise installs, uv-managed tools and Python runtimes, and PyCharm plugins
  through their supported paths under `/Volumes/ext/state`. Missing-sentinel
  startup preserves each tool's native fallback instead of creating an internal
  compatibility path.
- Reinstalled the exact uv tools externally and verified mise and uv activation.
  Live PyCharm file handles resolve its system and plugin state externally; its
  internal plugin directory is absent. Rollback state is retained in the 7.1 GiB
  `/Volumes/ext/archive/host-cleanup-20260809` bundle.
- Validation: 10 focused tests, shell syntax, rendered path checks, exact tool
  probes, PyCharm restart/file-handle checks, and disk accounting passed. Host
  free space reached 177 GiB. Implementation Gate Commit: `3ead600`. Intended
  Final Push: draft PR to `main`.

- Routed direct Lima, Colima, Docker images, and the Atuin named volume through
  native homes under `/Volumes/ext/state`. Sparse disk conversion passed
  `qemu-img compare`; personal and rebuilt MGM sandboxes run externally and the
  stopped MGM v1 rollback is archived externally.
- Reconstructed the empty Atuin server from the original key and surviving
  client stores. Host, personal, and MGM clients authenticate as `tommi` and
  converge on 17,157 encrypted records. Registration is closed, loopback and
  tailnet health pass, and a 9.6 MiB cold named-volume export passed an isolated
  restore health check.
- Replaced the failing Homebrew service with a sentinel-, mount-, and
  state-root-guarded LaunchAgent. A dependency-hashed onchange target reloads
  wrapper/plist changes; a live stop/bootstrap restart restored Atuin health.
- Pinned Atuin to its native client path despite scoped XDG overrides. Added
  explicit `idea.log.path` beside `idea.system.path`; live PyCharm opened the
  external log without the compatibility warning.
- Validation: 174 tests, shell/plist checks, sparse image comparison, both VM
  readiness gates, three-client sync, closed registration, cold restore, and
  LaunchAgent restart passed. Accepted risk `AUTH-014-AR1`; the 4.9 GiB internal
  Lima tree remains the retained rollback. Gate Commits: `3fc478e`, `d758f6a`,
  `c33b500`, `d007441`, `ce91840`.

- Routed validated Prefect and Codex homes through their native
  controls and PyCharm system state through custom properties. All settings are
  Mac-mini-only, sentinel-guarded, and excluded from teammate defaults.
- Preserved 802 Prefect runs; copied databases passed SQLite integrity checks,
  Prefect server health, Codex GUI file-handle checks, and PyCharm control
  restarts. A login controller reconciles GUI state at load, sentinel changes,
  and 60-second intervals while preserving unrelated inherited values.
- Deployed the shell profile and LaunchAgent, then moved internal rollback copies
  to `/Volumes/ext/state/archive/runtime-state-rollback-20260809`. Post-move
  activation remained external and reclaimed about 12 GiB internally.
- Validation: 173 tests, Bash/Zsh syntax, plist/render checks, SQLite integrity,
  launchd state, and post-move GUI/runtime smoke passed. Accepted risk:
  `AUTH-013-AR1`. Implementation Gate Commit: `0e3e9dc`.

- Routed Playwright, uv, pre-commit, npm, and Pulumi through their native path
  controls only when the existing external-state sentinel is present. Inherited
  managed values clear on the fallback path without overriding unrelated values.
- Copied Playwright browsers and Pulumi home to external storage while retaining
  internal rollback copies. Live path checks passed for all CLI tools, including
  a Playwright Chromium screenshot, uv package execution, npm cache verification,
  pre-commit database initialization, and Pulumi plugin inventory.
- Rolled back the attempted PyCharm properties migration after review found no
  sentinel-aware fallback. Prefect and Codex remain internal because their CLIs
  are unavailable for migration integrity tests. Host cleanup remains operator
  blocked by runtime filesystem policy and interactive `sudo`.
- Validation: 7 focused tests, Bash/Zsh render syntax, exact chezmoi deployment,
  Git diff checks, and independent review passed after rollback hardening.
  Accepted risk: `AUTH-011-AR1`. Release is not applicable. Final Push remains
  pending lifecycle completion. Implementation Gate Commit: `712e31e`.

## 2026-08-01

- Materialized GCP credentials in a private directory per loading shell and
  changed `_SECRETS_LOADED` to require both credential files before returning.
  Missing files now clear stale state and force full rematerialization; shell
  exit leaves inherited files valid for live child processes.
- Validation: focused secret-loader tests cover valid idempotency, missing-file
  reload, distinct shell paths, and child-shell cleanup isolation; Bash syntax
  and diff checks passed. Independent review findings on parent/child lifetime,
  EXIT-trap preservation, and stale docs were remediated; sandbox access blocked
  a final independent reread, while primary diff review passed. No Gate Exception
  or deployment. Implementation Gate Commit: `a8e0d9a`. Intended Final Push:
  draft PR to `main`.

## 2026-07-25

- Corrected the `lmsh` source boundary to deny all targets by default and allow
  only Bash/common profiles, Atuin and Starship configuration, and the pinned
  terminal installer.
- Validation: 169 tests, exact Linux chezmoi target inventory, shell rendering,
  both Lima guest dry-runs, terminal binary checks, and tailnet Atuin health
  passed. Independent review was unavailable because the reviewer sandbox could
  not read the cycle worktree; primary diff review passed with no new exception.
  Implementation Gate Commit: `4fdc25e`. Intended Final Push: `origin/main`.
- Added the portable `lmsh` Bash profile with pinned Atuin `18.17.1`, zoxide
  `0.9.8`, and Starship `1.26.0`; macOS shell rendering remains unchanged.
- Deployed a loopback-only Atuin `18.17.1` container through Tailscale Serve,
  migrated 16,229 hosted records with the preserved encryption key, logged both
  Lima clients into the same account, and closed registration.
- Replaced the initial macOS bind mount after SQLite WAL produced `disk I/O
  error`; the production store is a Docker named volume on Colima Linux storage.
- Validation: 168 tests, template/shell/TOML/Compose checks, disposable sync for
  both VMs, three-client production sync, denied registration, offline recovery,
  and isolated cold restore passed. Accepted risk `AUTH-009-AR1` remains owned
  by the operator through 2026-08-18. Implementation Gate Commit: `b44b1eb`.
  Intended Final Push: `origin/main`.

## 2026-07-13

- Transferred `op-session` and the Herdr Aqua LaunchAgent to the public
  `dotfiles-ai` source while retaining the personal `secret` bundle here.
- `secret` continues to source its installed sibling `op-session`; ownership is
  split by target without changing the runtime interface.

## 2026-06-22

- Created shell auth startup spec after RCA found stuck `op read` processes and Herdr auth fanout.
- Removed Herdr profile auto-hydration so restored panes do not run `secret` automatically.
- Added bounded 1Password CLI execution and session-cache locking for `secret` / `op-session`.
- Changed Clockify SketchyBar polling to use only cached/env API keys; poll loop no longer calls `op read`.
- Removed Databricks `onepasswordRead` template calls; `secret` now exports Databricks env vars.
- Verification: shell syntax checks passed; `secret` with `OP_TIMEOUT_SECONDS=2` failed fast in non-TTY.

## 2026-07-02

- Changed Herdr secret loading to use `OP_SERVICE_ACCOUNT_TOKEN` from the environment or macOS Keychain service `op-service-account-token` account `my`.
- Herdr panes now fail fast instead of attempting delegated desktop `op signin`.
- Added explicit `Automation` vault scoping for the `Shell Secrets` item fetch required by service accounts.
- Changed the default `ShellSecretsItem` id to the copied item in `Automation`.
- Changed `secret` to source sibling `op-session` directly so existing panes do not need `hash -r` after deploys.

## 2026-07-13

- Preserved actionable macOS Keychain errors while keeping service-account tokens out of output.
- Added Keychain Access repair guidance after `security -w` interactive input truncated the service-account token to 128 characters.
- Added a credential-free Aqua LaunchAgent after RCA found the headless persistent Herdr server could not access the login Keychain.
