# AWS SSO Credentials Auto-Refresh Specification

**Status:** Stable
**Created:** 2026-04-28

## Overview

MGM work uses AWS IAM Identity Center (SSO) chained to Microsoft Entra ID for authentication. The `aws sso login` flow opens a browser tab, which redirects through `myapps.microsoft.com`, and completes silently when the Microsoft session cookie is still valid.

This spec automates re-acquiring the AWS SSO **refresh token** three times per day via a launchd LaunchAgent, so the AWS SDK can keep renewing short-lived access tokens without interaction throughout the work day. The schedule is chosen to overlap the refresh token's ~8-hour lifetime (slots ~7h59m apart) while staying inside an 08:00–23:00 window.

### Token model (important — don't confuse these)

The SSO cache at `~/.aws/sso/cache/*.json` contains **two** distinct expirations:

| Field | File | Typical lifetime | Who refreshes it |
|-------|------|-----------------|------------------|
| `accessToken.expiresAt` | session file (with `accessToken`) | ~1 hour | AWS SDKs (boto3, botocore) silently, using the refresh token |
| `refreshToken` (implicit) | same session file | ~8 hours (admin-configured SSO session duration) | Only a fresh `aws sso login` call |
| `registrationExpiresAt` | client registration file | ~90 days | `aws sso login` when it expires |

**Key insight.** `accessToken.expiresAt` flaps between ~60m and ~1m throughout a session — that's normal and does **not** indicate that the browser will pop. The AWS SDK quietly trades the refresh token for new access tokens during every Bedrock API call. The *refresh token's* expiry is what determines when a browser re-auth is actually needed, and that tracks the SSO session duration (~8h here).

`aws sso login` does not extend an existing session — it starts a **new** one with a new refresh token. Running it every ~7.99h establishes a fresh refresh token before the previous one expires, giving continuous silent coverage.

### Authentication chain

```
aws sso login
  └─> browser → AWS SSO portal (https://mgmri.awsapps.com/start)
        └─> redirects to myapps.microsoft.com
              ├─ Microsoft session valid → SSO completes silently, tab closes (2–4s)
              └─ Microsoft session expired → MFA prompt (15s+ including user tap)
```

The practical consequence: the **first** refresh of a given day (08:00) may require password + MFA; subsequent refreshes (15:59, 22:45) piggyback on the live Microsoft cookie and flash the browser for a split second without interaction. Microsoft session rolls overnight, so the cycle repeats each morning.

## File Map

| Path | Purpose |
|------|---------|
| `Library/LaunchAgents/com.mgm.aws-sso-login.plist.tmpl` | launchd agent definition — invokes the wrapper on a calendar schedule |
| `dot_local/bin/executable_aws-sso-refresh` | Bash wrapper — checks token expiry from `~/.aws/sso/cache/*.json`, fires `aws sso login`, notifies on expired |
| `run_onchange_load-aws-sso-launchagent.sh.tmpl` | Chezmoi hook — unloads + loads the LaunchAgent whenever the plist or wrapper script changes |
| `docs/specs/aws_creds.md` | This document (not applied to `~/`; tracked in repo only via `docs/` entry in `.chezmoiignore`) |

## Schedule

Three calendar slots:

| Slot | Local time | Gap since previous | Notes |
|------|-----------|-------------------|-------|
| A | 08:00 | (—) | First refresh of day. Microsoft session usually rolled overnight → interactive. |
| B | 15:59 | 7h59m | Silent refresh; Microsoft still valid. |
| C | 22:45 | 6h46m | Silent refresh; extends AWS token to ~06:45 next morning. |

The 7h59m A→B gap is intentional: it re-acquires a token just under the 8-hour expiry so there's no dead time.

### Why calendar slots instead of `StartInterval`

launchd offers two scheduling modes:

- `StartInterval` (seconds) — fires a fixed interval from agent load time; drifts across days, cannot be constrained to a window.
- `StartCalendarInterval` (hour/minute dicts) — calendar-anchored; can restrict to an 08–23 window.

The calendar form is used because "only during 08:00–23:00" is a hard requirement. True "every 7.99 hours" cadence is not expressible in `StartCalendarInterval`; the three fixed slots approximate it.

## Token Validity Check

The wrapper reads `~/.aws/sso/cache/*.json` and logs informational metadata — it does **not** gate the login call on any expiry check. Because `accessToken.expiresAt` fluctuates on a 1-hour cadence independent of whether the browser would actually pop, it's not a reliable predictor and has been demoted to pure observability.

What the wrapper logs as a pre-check line:

```
pre-check: access=<min>m refresh=<yes|no> client-reg=<days>d
```

- `access=<min>m` — minutes remaining on the short-lived access token (informational; will often be low, don't panic).
- `refresh=<yes|no>` — whether a refresh token exists in the cache. `yes` means the SDK can still silently renew access tokens for Bedrock calls.
- `client-reg=<days>d` — days remaining on the client registration (~90 day lifetime). If this ever gets close to zero, `aws sso login` will re-register automatically.

### Browser-interaction detection (post-hoc)

Because the SSO cache doesn't expose the refresh token's actual expiry, the wrapper **cannot predict** whether `aws sso login` will require user interaction. Instead it measures elapsed wall-clock time of the command:

| Elapsed | Interpretation | Notification |
|---------|---------------|--------------|
| < 15s | Microsoft session was live → silent passthrough | none (quiet log line) |
| ≥ 15s | MFA prompt was likely shown | "Browser MFA completed (Ns)" |
| non-zero exit | Auth failed | "SSO login failed (exit N)" |

The 15-second threshold is a heuristic. A silent OIDC flow on a warm machine completes in 2–4 seconds; anything with an MFA prompt includes the user's tap-to-approve latency (~3–10s on top of the silent baseline). 15s is a conservative middle ground.

## Behavior

### During a working day

- **08:00** fires → wrapper logs cache state → `aws sso login` likely requires MFA (Microsoft session rolled overnight) → elapsed ≥15s → notification pops → user taps MFA → fresh refresh token established.
- **15:59** fires → elapsed typically 2–4s → silent log line, no notification → refresh token rotated with ~8h validity.
- **22:45** fires → same as 15:59 → refresh token extends into early next morning.
- **Overnight**: AWS SDK continues to silently renew access tokens from the refresh token for Bedrock API calls until the refresh token itself expires. Microsoft session rolls at its own cadence.

### If the Mac is asleep at a scheduled time

launchd catches up missed `StartCalendarInterval` firings on wake by default. The agent will run once when the machine wakes, using whichever missed slot was most recent. No duplicate firings.

### If the user is AFK when the browser pops

The browser tab sits open awaiting Microsoft MFA. Harmless. The AWS token simply remains unrefreshed until the user returns and authenticates. Next scheduled slot tries again.

## Installation

### Automatic (via chezmoi)

Both machines (`mac-mini` and `macbook`) get identical configuration. On `chezmoi apply`:

1. `Library/LaunchAgents/com.mgm.aws-sso-login.plist` is rendered and written to `~/Library/LaunchAgents/`.
2. `.local/bin/aws-sso-refresh` is installed with 0755.
3. `run_onchange_load-aws-sso-launchagent.sh.tmpl` evaluates — if the plist or wrapper hash has changed, it unloads and reloads the agent.

### Manual (first-time verification)

```bash
# Preview what chezmoi will apply
chezmoi diff

# Apply
chezmoi apply

# Verify agent is loaded
launchctl list | grep aws-sso-login

# Test-fire the wrapper directly (bypass launchd)
~/.local/bin/aws-sso-refresh BedrockDeveloperAccess-302432775606

# Test-fire via launchd
launchctl start com.mgm.aws-sso-login

# Tail logs
tail -f ~/Library/Logs/aws-sso-login.log ~/Library/Logs/aws-sso-login.err.log
```

## Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.mgm.aws-sso-login.plist
rm ~/Library/LaunchAgents/com.mgm.aws-sso-login.plist
rm ~/.local/bin/aws-sso-refresh
# Then remove the source files from ~/.local/share/chezmoi and commit
```

## Why `run_onchange_` not `run_once_`

The bootstrap script uses chezmoi's `run_onchange_` prefix (matching the `run_onchange_install-npm-globals.sh.tmpl` pattern already in this repo) instead of `run_once_`. The script's source template includes the SHA-256 of the plist and wrapper files, so any edit to either triggers a re-run — automatically reloading the agent with the new definition. `run_once_` would install the agent on initial apply but silently ignore later plist edits, causing drift.

The reload is idempotent: `launchctl unload` ignores errors from an already-unloaded agent, then `launchctl load` registers the current definition.

## Gotchas

**Microsoft session cookies are per-browser.** If your default browser changes, the first SSO of the day in the new browser requires a fresh Microsoft login. Set a stable default browser.

**`aws sso login` is not the same as `aws configure sso`.** The latter is one-time profile setup; the former is token refresh. The LaunchAgent only calls the former. Initial profile configuration must be done manually once per machine.

**AWS CLI binary path is hardcoded.** The wrapper uses `/usr/local/bin/aws`. If you ever install the CLI to `/opt/homebrew/bin/aws` (Apple Silicon Homebrew default), update the wrapper. The plist's `EnvironmentVariables.PATH` covers both locations for the wrapper's own `$PATH`, but the wrapper hardcodes the `aws` path for defense against `$PATH` surprises.

**Logs grow unbounded.** The StandardOutPath / StandardErrorPath files at `~/Library/Logs/aws-sso-login.{log,err.log}` accumulate forever. Rotate manually or with `newsyslog` if they become inconvenient.

**First-run on a new machine** requires AWS CLI + `~/.aws/config` with the `BedrockDeveloperAccess-302432775606` profile set up. The `run_onchange_` script does not fail-hard if the agent load fails — it logs a warning — so chezmoi apply remains green even on machines that haven't yet been AWS-configured.

## Verification

```bash
# 1. Profile is configured
aws configure list-profiles | grep BedrockDeveloperAccess-302432775606

# 2. Agent is registered
launchctl list | grep com.mgm.aws-sso-login

# 3. Wrapper runs cleanly
~/.local/bin/aws-sso-refresh BedrockDeveloperAccess-302432775606

# 4. Token is valid after refresh
aws sts get-caller-identity --profile BedrockDeveloperAccess-302432775606
```
