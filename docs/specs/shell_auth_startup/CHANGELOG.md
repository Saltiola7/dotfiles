# Shell Auth Startup Changelog

## 2026-07-25

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
