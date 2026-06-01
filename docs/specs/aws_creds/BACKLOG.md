# Backlog: AWS SSO Credentials

**Last updated:** 2026-06-01

## Active

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | E2E validate single-flow recovery on real expiry | high | pending | Force-test via `aws sso logout` or wait for natural overnight expiry. Verify bar goes green in ~30-60s. |
| 2 | Handle "Pick an account" MS page in autofill | low | pending | Only appears after explicit `aws sso logout`. Currently requires manual click. Could detect via page title and inject account-selection keystroke. |
| 3 | Add log rotation for `~/Library/Logs/aws-sso-login.{log,err.log}` | low | pending | Files grow unbounded. Add `newsyslog` config or logrotate equivalent. |
| 4 | Consider shorter update_freq when bar is red | low | pending | Currently 60s detection lag. Could switch to 15s polling during recovery state. Adds CPU cost. |

## Parallel Execution Guide

All tasks are independent — can be worked in any order or concurrently.

## Completed

| # | Task | Completed | Commit |
|---|------|-----------|--------|
| — | STS-only gate (drop access-token-minutes guard) | 2026-05-27 | `6d2f113` |
| — | 1Password autofill: Alt+Period + double Enter | 2026-05-28 | `1f64a2f` |
| — | awslogin alias + GCP env cleanup | 2026-05-28 | `dfaf9b5` |
| — | Aerospace outer.top snap to bar | 2026-05-28 | `65b9d4c` |
| — | Background aws sso login after MS auth | 2026-05-31 | `c40ef54` |
| — | Single-flow recovery (drop sleep 30 + redundant browser) | 2026-06-01 | `7a19462` |
