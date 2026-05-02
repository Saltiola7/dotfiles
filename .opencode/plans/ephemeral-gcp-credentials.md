# Plan: Ephemeral GCP Service Account Credentials

## Goal
Make GCP SA credentials session-scoped (only active after calling `secret()`), remove all persistent SA credentials from disk.

## Changes

### 1. Edit `dot_common_profile.tmpl`

#### a) Add cleanup function before `secret()` (after line 88)
Insert a `__cleanup_gcp_cache` function that removes stale SA JSON files from `~/.cache/gcp/`, and call it at shell startup to handle cases where a previous shell was killed without the EXIT trap firing.

#### b) Add gcloud env vars inside `secret()` (after GOOGLE_CLOUD_PROJECT export)
- `CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE` → makes gcloud CLI use the ephemeral SA JSON
- `CLOUDSDK_ACTIVE_CONFIG_NAME=sa-dev-admin` → makes starship prompt show the SA config

#### c) Add EXIT trap inside `secret()` (before final echo)
Register `trap '__cleanup_gcp_cache' EXIT` so the JSON files are deleted when the shell exits.

### 2. Edit `dot_xonshrc.tmpl`
Apply equivalent changes to the xonsh `_load_secrets()` function:
- Add cleanup function at module level
- Add `CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE` and `CLOUDSDK_ACTIVE_CONFIG_NAME` env vars
- Add atexit handler for cleanup

### 3. One-time manual commands (user runs these)
```bash
# Remove SA credentials from gcloud's persistent store
gcloud auth revoke sa-dev-admin@enterprise-seo-tools.iam.gserviceaccount.com

# Switch active configuration to 'default' (personal account)
gcloud config configurations activate default

# Clean up stale cache files
rm -f ~/.cache/gcp/enterprise-seo-tools-sa.json
rm -f ~/.cache/gcp/gws-content-reader-key.json
rm -f ~/.cache/gcp/gws_content_reader_credentials.json
```

## Verification
After applying changes via `chezmoi apply`:
1. Open new shell → gcloud prompt should show `default` config (personal account), NOT the SA
2. Run `secret` → gcloud prompt should switch to show the SA
3. Exit shell → `ls ~/.cache/gcp/` should show no JSON files (cleanup trap fired)
4. Open new shell again → no stale files (startup cleanup ran)
