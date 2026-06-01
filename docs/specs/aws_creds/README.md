# AWS SSO Credentials Auto-Refresh Specification

**Status:** Stable
**Created:** 2026-04-28
**Last updated:** 2026-06-01

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

The wrapper reads `~/.aws/sso/cache/*.json` and logs informational metadata, then **uses STS as a gate** to decide whether to invoke `aws sso login`:

```
pre-check: access=<min>m refresh=<yes|no> client-reg=<days>d
```

- `access=<min>m` — minutes remaining on the short-lived access token (informational; will often be low, don't panic).
- `refresh=<yes|no>` — whether a refresh token exists in the cache. `yes` means the SDK can still silently renew access tokens for Bedrock calls.
- `client-reg=<days>d` — days remaining on the client registration (~90 day lifetime). If this ever gets close to zero, `aws sso login` will re-register automatically.

### STS gate (added 2026-05-26)

Original design ran `aws sso login` unconditionally on every scheduled slot, relying on the Microsoft session cookie to keep the browser flow silent. In practice the Microsoft session expires often enough that "silent" turned into "browser tab pops three times a day" — visible to the user and frequently failing with `pending authorization expired` because no human was present to approve.

The wrapper now gates on `aws sts get-caller-identity`:

| STS probe | Action |
|---|---|
| succeeds | **skip login**, trigger SketchyBar, exit 0 |
| fails | proceed with `aws sso login` |

#### Why STS is the only authority

An earlier revision combined STS with an "access token minutes remaining > 30m" guard, intending to proactively rotate the refresh token before it died. That guard was removed because the cached `accessToken.expiresAt` reflects the **short-lived (~1h) access token**, not the refresh token. On an idle machine where no SDK calls have happened for hours, the cached field can show negative minutes (e.g. `access=-372m`) while the refresh token is still healthy. The old guard sent those cases to the login branch and popped a browser unnecessarily.

Invoking `aws sts get-caller-identity` forces the SDK to either silently mint a new access token from the refresh token (proving liveness) or fail outright (proving the refresh token is genuinely dead). It is therefore both necessary and sufficient as the gate.

The proactive schedule (08:00 / 15:59 / 22:45) is unchanged — slots stay aligned to the 8h refresh token lifetime — but most slots are now no-ops when the SDK is already healthy.

### Browser-interaction detection (post-hoc)

Because the SSO cache doesn't expose the refresh token's actual expiry, when the wrapper *does* invoke `aws sso login` it cannot predict whether user interaction is required. It measures elapsed wall-clock time of the command:

| Elapsed | Interpretation | Notification |
|---------|---------------|--------------|
| < 15s | Microsoft session was live → silent passthrough | none (quiet log line) |
| ≥ 15s | MFA prompt was likely shown | "Browser MFA completed (Ns)" |
| non-zero exit | Auth failed | "SSO login failed (exit N)" |

The 15-second threshold is a heuristic. A silent OIDC flow on a warm machine completes in 2–4 seconds; anything with an MFA prompt includes the user's tap-to-approve latency (~3–10s on top of the silent baseline). 15s is a conservative middle ground.

## Behavior

### During a working day

With the STS gate in place:

- **08:00** fires → STS probe likely fails (refresh token expired overnight) → `aws sso login` runs → may require MFA if Microsoft session also rolled → fresh refresh token established.
- **15:59** fires → STS probe likely succeeds (refresh token still alive from 08:00 grant) → **skip**, no browser, no login.
- **22:45** fires → same: STS succeeds, skip. If the refresh token has actually died by now (rare; refresh tokens are ~8h and 22:45 is < 8h after 15:59), STS fails and a real login runs as backstop.
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

## SketchyBar Integration

**Added:** 2026-05-01

The SketchyBar status bar includes an AWS Bedrock token indicator that provides real-time visibility and automatic recovery.

### Indicator States

| Color | Label | Meaning |
|---|---|---|
| Green `#a6e3a1` | `15:59 ~6h` | Active. Activated at 15:59, ~6h estimated remaining. |
| Yellow `#f9e2af` | `15:59 ~3h` | Getting low (2-4h remaining) |
| Peach `#fab387` | `15:59 ~1h` | Low (1-2h remaining) |
| Red `#f38ba8` | `15:59 ~30m` | Very low (<1h remaining) |
| Yellow `#f9e2af` | `renew...` | Auto-recovery in progress |
| Green `#a6e3a1` | `renewed` | Silent recovery succeeded |
| Red `#f38ba8` | `auth` | Microsoft session expired, Zen Browser opened for manual re-auth |
| Gray `#6c7086` | `off` | Outside work hours (00:00-08:00) |

### Architecture: launchd + SketchyBar

```
launchd (proactive, scheduled):
  08:00, 15:59, 22:45 → aws-sso-refresh → aws sso login

SketchyBar (reactive, every 60s):
  aws sts get-caller-identity
    ├─ Success → parse log for login time → show countdown
    └─ Failure → token expired
         ├─ 00:00-08:00 → show "off", no recovery
         └─ 08:00-00:00 → try silent aws sso login (10s timeout)
              ├─ Success → show "renewed"
              └─ Failure → Microsoft session expired:
                   1. Background `aws sso login --profile X` (opens OIDC URL in Zen)
                   2. After 3s: 1Password autofill (Alt+. → Enter → Enter)
                   3. aws sso login polls its callback; exits when MS+AWS auth complete
                   4. On success: refresh epoch, warm STS, fire `aws_sso_refreshed`
                   5. macOS notification: "AWS SSO restored automatically"
                   6. Bar: red "auth" → green within 1s of bg success
```

**No overlap:** launchd handles proactive scheduled refreshes at fixed times. SketchyBar handles reactive recovery when the token actually expires between scheduled runs. The STS probe is the source of truth — the 8-hour countdown is an estimate that the probe corrects.

### Recovery flow internals

When the silent `aws sso login` (10s timeout) fails, the plugin enters the Microsoft-session-expired branch. It dispatches a single-flow background subshell driven by `aws sso login`'s own OIDC polling, so there are no fixed waits beyond a brief page-render delay.

| Step | Wait | Action |
|---|---|---|
| 1 | — | Background-start `aws sso login --profile $AWS_PROFILE`. The CLI generates an OIDC URL and calls `open` on it; Zen handles the URL and redirects through AWS SSO portal → Microsoft Entra → MS sign-in if the MS session is dead. |
| 2 | 3s | Wait for the OIDC redirect chain to land on the MS sign-in page. |
| 3 | — | Activate Zen. Send Alt+Period (1Password picker), Enter (fill MS form), 1.0s, Enter (submit). |
| 4 | — | `aws sso login` keeps polling its OIDC callback. As soon as MS auth completes (and the user clicks "Allow access" if prompted), the CLI exits 0. Default polling timeout is ~10 minutes, ample for MFA. |
| 5 | — | On success: delete `$BROWSER_LOCKFILE`, write `$LOGIN_EPOCH_FILE`, warm STS, post a notification, fire `sketchybar --trigger aws_sso_refreshed` so the bar flips green within 1s. |
| 6 | — | On failure (non-zero exit): leave `$BROWSER_LOCKFILE` in place; the 10-minute TTL prevents tight retry loops. |

**Why `aws sso login` is started first.** The CLI owns the browser tab — calling `open` on its own OIDC URL means Zen lands directly on the Microsoft sign-in page (or AWS "Allow access" if MS session is still valid). An older revision opened `myapps.microsoft.com` separately and then ran `aws sso login` afterward; that produced two distinct auth journeys back-to-back for one logical login. The current single-flow design uses the CLI's own browser-opening behavior so there is exactly one tab.

**Why there is no fixed MFA wait.** `aws sso login` polls its OIDC callback for ~10 minutes by default. As soon as MS auth + AWS "Allow access" complete, the callback fires and the CLI exits. A blind `sleep 30` was an earlier mistake that added pure dead time even when MS session was still valid (auth completes in 2-4s in that case). The new flow reads progress from the CLI itself via `wait "$AWS_LOGIN_PID"`.

The autofill keystroke sequence handles only the password-entry page; the "Pick an account" page (rare, only after explicit `aws sso logout`) requires a manual click. MFA latency is bounded by the user's Authenticator approval speed, not by a fixed timer.

`$BROWSER_LOCKFILE` (`/tmp/sketchybar_aws_browser_lock`) has a 10-minute TTL and is removed only on background success. While present, the section-3 lockfile gate keeps the bar at red `"auth"` and prevents repeat browser openings.

### Expected user-visible recovery time

| Scenario | Time from STS-failure detection to bar going green |
|---|---|
| MS session still valid (cookie alive) | ~5–10 seconds |
| MFA approval needed | ~10–30 seconds, bounded by user MFA tap latency |
| User AFK during recovery | bounded by `aws sso login`'s ~10min polling timeout, then the 10-minute lockfile cooldown |

### Files

| Path | Purpose |
|---|---|
| `private_dot_config/sketchybar/items/executable_aws_bedrock.sh` | SketchyBar item definition |
| `private_dot_config/sketchybar/plugins/executable_aws_bedrock.sh` | STS probe + log parsing + auto-recovery logic |

## Manual refresh

From any terminal:

```bash
awslogin   # alias for ~/.local/bin/aws-sso-refresh BedrockDeveloperAccess-302432775606
```

**Always prefer `awslogin` over raw `aws sso login`.** The wrapper:

- Probes STS first and skips the browser when the session is alive.
- Writes `/tmp/sketchybar_aws_login_epoch` so the bar countdown resets immediately on success.
- Triggers SketchyBar to update the indicator without waiting for the 60s tick.

Running `aws sso login --profile …` directly bypasses the last two — the bar can lag up to 60s behind a successful login.

The alias is defined in `dot_common_profile.tmpl` next to other aliases.

## Domain

### Bounded Context

AWS SSO credential lifecycle management — proactive refresh (launchd), reactive recovery (SketchyBar), and manual refresh (shell alias).

Adjacent contexts: SketchyBar UI (bar rendering), AeroSpace (window layout), 1Password (autofill), Microsoft Entra ID (upstream IdP).

### Entities

- **SSOSession** — the AWS SSO session containing access token + refresh token, identified by cache file path
- **RecoveryAttempt** — a single invocation of the background recovery flow, gated by lockfiles

### Value Objects

- **STSProbeResult** — success/failure of `aws sts get-caller-identity`
- **LockfileState** — presence + age of browser/recovery lockfiles
- **BarIndicator** — color + label text representing current credential state

### Domain Events

- `STSProbeFailed` — refresh token is dead, recovery needed
- `SilentLoginSucceeded` — 10s timeout login worked (MS session valid)
- `SilentLoginFailed` — MS session expired, interactive recovery needed
- `RecoveryStarted` — bg `aws sso login` launched, lockfile created
- `RecoveryCompleted` — bg login exited 0, bar goes green
- `RecoveryFailed` — bg login exited non-zero, lockfile TTL prevents retry
- `ScheduledRefreshFired` — launchd slot triggered (08:00/15:59/22:45)

### Ubiquitous Language

| Term | Definition |
|------|-----------|
| STS probe | `aws sts get-caller-identity` — forces SDK to use refresh token or fail |
| refresh token | ~8h token in SSO cache; only `aws sso login` renews it |
| access token | ~1h token; SDK renews silently from refresh token |
| silent login | `timeout 10 aws sso login` — succeeds only if MS session is alive |
| recovery flow | Full interactive: bg `aws sso login` + 1Password autofill + MFA |
| browser lockfile | `/tmp/sketchybar_aws_browser_lock` — 10min TTL, gates recovery retries |
| login epoch | `/tmp/sketchybar_aws_login_epoch` — unix timestamp of last successful login |
| bar tick | SketchyBar plugin runs every 60s (`update_freq=60`) |

## Behavior Scenarios

### Feature: Proactive Scheduled Refresh (launchd)

**Scenario: STS alive at scheduled slot**
- Given the launchd agent fires at 15:59
- And `aws sts get-caller-identity` succeeds
- When `aws-sso-refresh` runs
- Then it skips `aws sso login` entirely
- And triggers SketchyBar update
- And exits 0

**Scenario: STS dead at first slot of day**
- Given the launchd agent fires at 08:00
- And `aws sts get-caller-identity` fails (refresh token expired overnight)
- When `aws-sso-refresh` runs
- Then it invokes `aws sso login --profile BedrockDeveloperAccess-302432775606`
- And the browser opens for Microsoft auth + MFA

### Feature: Reactive Recovery (SketchyBar plugin)

**Scenario: STS alive during work hours**
- Given the bar tick fires between 08:00-00:00
- And `aws sts get-caller-identity` succeeds
- When the plugin evaluates
- Then bar shows green with countdown (e.g., "7h59m")
- And no recovery action is taken

**Scenario: STS dead, silent login succeeds**
- Given the bar tick fires between 08:00-00:00
- And `aws sts get-caller-identity` fails
- And Microsoft session cookie is still valid in Zen
- When the plugin attempts `timeout 10 aws sso login`
- Then the login completes within 10s (OIDC callback fires)
- And bar shows green "renewed"

**Scenario: STS dead, silent login fails, recovery launched**
- Given the bar tick fires between 08:00-00:00
- And `aws sts get-caller-identity` fails
- And `timeout 10 aws sso login` fails (MS session expired)
- And no browser lockfile exists (or TTL expired)
- When the plugin enters the recovery branch
- Then it backgrounds `aws sso login --profile X` (opens OIDC URL in Zen)
- And waits 3s for page render
- And fires 1Password autofill (Alt+Period → Enter → Enter)
- And `aws sso login` polls OIDC callback (~10min timeout)
- And bar shows red "auth"

**Scenario: Recovery succeeds (MFA approved)**
- Given a recovery attempt is running (`aws sso login` polling)
- When the user approves MFA in Microsoft Authenticator
- Then `aws sso login` exits 0
- And browser lockfile is deleted
- And login epoch file is updated
- And STS is warmed
- And macOS notification fires: "AWS SSO restored automatically"
- And `sketchybar --trigger aws_sso_refreshed` fires
- And bar flips green within 1s

**Scenario: Recovery fails (timeout or error)**
- Given a recovery attempt is running
- When `aws sso login` exits non-zero (polling timeout, network error)
- Then browser lockfile remains (10min TTL)
- And bar stays red "auth"
- And no retry until lockfile TTL expires

**Scenario: Lockfile prevents duplicate recovery**
- Given browser lockfile exists and is less than 10 minutes old
- When the bar tick fires and STS fails
- Then no recovery is attempted
- And bar stays red "auth"

**Scenario: Outside work hours**
- Given the bar tick fires between 00:00-08:00
- And `aws sts get-caller-identity` fails
- When the plugin evaluates
- Then bar shows gray "off"
- And no recovery action is taken

### Feature: Manual Refresh (shell alias)

**Scenario: awslogin when STS alive**
- Given user runs `awslogin` in terminal
- And STS probe succeeds
- When `aws-sso-refresh` runs
- Then it prints "session alive" and skips login
- And writes login epoch
- And triggers SketchyBar

**Scenario: awslogin when STS dead**
- Given user runs `awslogin` in terminal
- And STS probe fails
- When `aws-sso-refresh` runs
- Then it invokes `aws sso login` (opens browser)
- And waits for auth completion
- And writes login epoch on success
- And triggers SketchyBar

## Contracts & Invariants

### Function: aws-sso-refresh (wrapper script)
- **Pre:** `$1` (profile name) is provided and exists in `~/.aws/config`
- **Pre:** `aws` CLI is available at `/usr/local/bin/aws`
- **Post:** On skip (STS alive): login epoch updated, SketchyBar triggered, exit 0
- **Post:** On login success: new refresh token in SSO cache, login epoch updated, exit 0
- **Post:** On login failure: exit non-zero, no epoch update

### Function: executable_aws_bedrock.sh (SketchyBar plugin)
- **Pre:** `$AWS_PROFILE` environment variable set in plugin context
- **Pre:** SketchyBar is running and `aws_bedrock` item exists
- **Post:** Bar label always reflects current state (countdown, "renew...", "auth", "off", "renewed")
- **Post:** At most one recovery subshell running at a time (browser lockfile gate)
- **Post:** On recovery success: epoch + STS warm + trigger fire all happen atomically in success branch

### Module: Recovery Flow (section 5 of plugin)
- **Invariant:** Browser lockfile exists IFF a recovery attempt is in progress or recently failed (10min TTL)
- **Invariant:** Only one `aws sso login` background process runs at a time per lockfile
- **Invariant:** Recovery branch never fires outside 08:00-00:00
- **Invariant:** 1Password autofill keystrokes fire only after `sleep 3` page-render delay

### Module: Countdown Display
- **Invariant:** Countdown is based on `login_epoch + 8h - now`, never on `accessToken.expiresAt`
- **Invariant:** Color thresholds: green (>4h), yellow (2-4h), peach (1-2h), red (<1h)
