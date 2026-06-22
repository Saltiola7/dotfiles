# Shell Auth Startup Changelog

## 2026-06-22

- Created shell auth startup spec after RCA found stuck `op read` processes and Herdr auth fanout.
- Removed Herdr profile auto-hydration so restored panes do not run `secret` automatically.
- Added bounded 1Password CLI execution and session-cache locking for `secret` / `op-session`.
- Changed Clockify SketchyBar polling to use only cached/env API keys; poll loop no longer calls `op read`.
- Removed Databricks `onepasswordRead` template calls; `secret` now exports Databricks env vars.
- Verification: shell syntax checks passed; `secret` with `OP_TIMEOUT_SECONDS=2` failed fast in non-TTY.
