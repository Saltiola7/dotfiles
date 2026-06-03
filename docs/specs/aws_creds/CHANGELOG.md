# Changelog: AWS SSO Credentials

All notable changes to the AWS SSO credential automation.

## [2026-06-01]

### Changed
- **Single-flow recovery** (commit `7a19462`): Replaced two-stage auth journey with single `aws sso login`-driven flow. CLI opens its own OIDC URL, 1Password autofills after 3s page render, CLI polls callback until MS auth completes. Removed `sleep 30` and redundant `myapps.microsoft.com` opener.

### Fixed
- Recovery no longer has ~108s worst-case delay. New flow: ~5-10s (MS session valid) or ~30-60s (MFA needed).

## [2026-05-31]

### Added
- **Background aws sso login** (commit `c40ef54`): After 1Password fills the Microsoft sign-in form, a background `aws sso login` now runs automatically. On success: deletes browser lockfile, refreshes login epoch, warms STS, fires `aws_sso_refreshed` trigger.

### Fixed
- Bar no longer stays red after MS auth completes — the missing `aws sso login` step was the root cause.

## [2026-05-28]

### Fixed
- **1Password autofill keystroke** (commit `1f64a2f`): Restored `Alt+Period` as picker trigger (was incorrectly changed to `Cmd+\` which is desktop-app-only). Added second `Enter` to submit the filled form after 1Password closes.
- **Superseded `Cmd+\` approach** (commit prior): `Cmd+\` is 1Password desktop app shortcut, not Firefox extension. Alt+Period is the correct Zen extension binding per `extension-settings.json`.

## [2026-05-27]

### Changed
- **STS-only gate** (commit `6d2f113`): Removed access-token-minutes guard from `aws-sso-refresh` wrapper. Cached `accessToken.expiresAt` reflects the short-lived (~1h) access token, not the refresh token — idle machines show "expired" while the refresh token is healthy. STS probe is now the sole gate (forces SDK to mint new access token or fail outright).

### Fixed
- Browser no longer pops at scheduled slots when the session is alive (was triggered by stale access token cache showing `-372m`).

## [2026-05-28]

### Added
- **`awslogin` shell alias** (commit `dfaf9b5`): alias for `aws-sso-refresh BedrockDeveloperAccess-302432775606`. Defined in `dot_common_profile.tmpl`.
- **GCP env cleanup** (commit `dfaf9b5`): `__cleanup_gcp_cache` now also unsets `GOOGLE_APPLICATION_CREDENTIALS`, `GWS_CONTENT_READER_CREDENTIALS`, `CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE`.

## [2026-05-01]

### Added
- **SketchyBar integration**: AWS Bedrock token indicator with color-coded countdown, auto-recovery on expiry, macOS notifications on state changes.

## [2026-04-28]

### Added
- **Initial implementation**: launchd LaunchAgent for 3x/day scheduled refresh (08:00/15:59/22:45). `aws-sso-refresh` wrapper script with token validity check. Chezmoi `run_onchange_` bootstrap.
