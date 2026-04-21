# Dotfiles Management Specification

**Status:** Stable
**Updated:** 2026-04-20

## Architecture

All dotfiles are managed by [chezmoi](https://www.chezmoi.io/) from a single source directory.

- **Source of truth:** `~/.local/share/chezmoi/` (git repo → github.com/Saltiola7/dotfiles)
- **Chezmoi config:** `~/.config/chezmoi/chezmoi.toml`
- **Encryption key:** `~/.config/chezmoi/key.txt` (age, backed up in password manager)
- **Target:** `~/` (home directory)

## Machines

Two machines share this config, differentiated by `{{ .machine_type }}` in templates:

| Machine | Value | Notes |
|---------|-------|-------|
| Mac Mini M4 Pro | `mac-mini` | Primary workstation, source of truth for live configs |
| MacBook | `macbook` | Portable, set up via `chezmoi init --apply` |

The mac-mini live configs are always authoritative. Never overwrite them without confirmation.

## Secrets Management

### Strategy

Secrets are managed via **1Password CLI** (`op`). Two patterns are used depending on the use case:

| Pattern | When | Secrets on disk? |
|---------|------|-----------------|
| `op read` at shell startup | Environment variables (API keys) | No |
| `onepasswordRead` in chezmoi template | Config files that need secrets baked in | Yes (in target file, 0600 perms) |

### 1Password items

API keys and service credentials are stored as individual items in 1Password. Shell env vars are loaded via `op read` at startup; config file secrets use chezmoi's `onepasswordRead` template function.

### Shell secrets (runtime `op read`)

In `.common_profile`, API keys are fetched at every shell start:
```bash
export EXAMPLE_API_KEY="$(op read 'op://Vault/Item Name/field')"
```

No guard — shell startup fails if 1Password is locked. Unlock the app and open a new shell.

### Config file secrets (chezmoi `onepasswordRead`)

For files that require secrets baked in, use chezmoi's template function:
```
token = {{ onepasswordRead "op://Vault/Item Name/field" }}
```

These are resolved at `chezmoi apply` time. Re-run `chezmoi apply` after rotating secrets.

### Encryption (age)

Age encryption is still configured in chezmoi for any files that need it in the future. Currently no files use age encryption — all former encrypted files have been migrated to either 1Password-backed templates or de-encrypted (contained no real secrets).

## Shell Configuration

```
.common_profile    ← Shared config (PATH, env, aliases, secrets) for bash & zsh
.bashrc            ← Bash-specific (ble.sh, IntelliJ guard, sources .common_profile)
.zshrc             ← Zsh-specific (completions, sources .common_profile)
.bash_profile      ← Login shell → sources .bashrc
.zprofile          ← Zsh login → machine-specific PATHs
.profile           ← POSIX login shell fallback
```

Both `.bashrc` and `.zshrc` source `.common_profile` for shared behavior.

## Adding New Files

```bash
# Regular file
chezmoi add ~/.newconfig

# File with secrets → use a template with onepasswordRead
chezmoi add --template ~/.newconfig

# Machine-specific → add template attribute
chezmoi chattr +template ~/.newconfig
# Then use {{ if eq .machine_type "mac-mini" }} conditionals
```

## Adding a New Secret

1. Create item in 1Password (category: API Credential)
2. Choose the appropriate pattern:
   - **Env var needed by CLI tools** → add `op read` line to `.common_profile`
   - **Config file needs the value** → use `{{ onepasswordRead "op://..." }}` in a `.tmpl` file

## Deploying to a New Machine

```bash
# 1. Install prerequisites
brew install chezmoi age 1password-cli

# 2. Restore age key from 1Password
mkdir -p ~/.config/chezmoi
# Copy age key from password manager → ~/.config/chezmoi/key.txt
chmod 600 ~/.config/chezmoi/key.txt

# 3. Sign in to 1Password CLI
op signin

# 4. Initialize and apply
chezmoi init --apply https://github.com/Saltiola7/dotfiles
# When prompted: machine_type = "macbook"

# 5. Verify
chezmoi verify
```

## Daily Workflow

```bash
# Edit a managed file
chezmoi edit ~/.zshrc

# See what would change
chezmoi diff

# Apply source → home directory
chezmoi apply

# After editing, commit and push
cd ~/.local/share/chezmoi
git add -A && git commit -m "description" && git push
```

## Conventions

- File naming follows chezmoi conventions (`dot_`, `private_`, `.tmpl`, `.age`)
- `private_` prefix → file gets 0600 permissions
- `.tmpl` suffix → file is a Go template
- Templates use `{{ .chezmoi.homeDir }}` instead of hardcoded home paths
- `.chezmoiignore` excludes `.DS_Store`
- `gh/hosts.yml` is explicitly excluded (contains auth tokens managed by `gh` itself)

## What's NOT Managed

- `~/.config/chezmoi/chezmoi.toml` (machine-local config, not in git)
- `~/.config/chezmoi/key.txt` (encryption key, never in git)
- SSH keys (managed by 1Password agent)
- `gh` auth tokens (managed by `gh auth`)
- Any project-specific `.env` files
