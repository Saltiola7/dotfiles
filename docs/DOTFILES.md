# Dotfiles Management Specification

**Status:** Stable
**Updated:** 2026-04-21

## Architecture

All dotfiles are managed by [chezmoi](https://www.chezmoi.io/) from a single source directory.

- **Source of truth:** `~/.local/share/chezmoi/` (git repo → github.com/Saltiola7/dotfiles)
- **Chezmoi config:** `~/.config/chezmoi/chezmoi.toml`
- **Encryption key:** `~/.config/chezmoi/key.txt` (age, backed up in 1Password)
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
| `secret` function (lazy `op read`) | Environment variables (API keys) — loaded on demand, not at shell start | No |
| `onepasswordRead` in chezmoi template | Config files that need secrets baked in | Yes (in target file, 0600 perms) |

### 1Password items

| Item | Vault | Usage |
|------|-------|-------|
| Gemini API Key | Personal | Shell env (`$GEMINI_API_KEY`) via `secret` |
| Google AI API Key | Personal | Shell env (`$GOOGLE_GENERATIVE_AI_API_KEY`) via `secret` |
| OpenAI API Key | Personal | Shell env (`$OPENAI_API_KEY`) via `secret` |
| AWS Bedrock | Personal | Shell env (`$AWS_PROFILE`, `$AWS_REGION`) via `secret` |
| ClickHouse Cloud | Personal | `ch` alias fetches host inline at invocation |
| Databricks | Personal | `.databrickscfg` template (host + token) |

### Shell secrets (lazy-loaded `op read`)

In `.common_profile`, API keys are **not** loaded at shell startup. Call `secret` to load them on demand:

```bash
secret   # prompts once for Touch ID, exports all API keys into the current session
```

Secrets are cached for the lifetime of the shell session via `_SECRETS_LOADED` guard — subsequent calls print "Secrets already loaded." without re-prompting.

**Keys loaded by `secret`:**
- `$GEMINI_API_KEY` / `$GEMINI_DEEP_RESEARCH_API_KEY`
- `$GOOGLE_GENERATIVE_AI_API_KEY`
- `$OPENAI_API_KEY`
- `$AWS_PROFILE` / `$AWS_REGION`
- `$CLAUDE_CODE_USE_BEDROCK=1`

The ClickHouse alias (`ch`) fetches its host inline via `op read` at invocation time — no `secret` call needed.

### Config file secrets (chezmoi `onepasswordRead`)

For files that require secrets baked in (e.g., `.databrickscfg`), use chezmoi's template function:
```
token = {{ onepasswordRead "op://Personal/Databricks/credential" }}
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

1. Create item in 1Password (Personal vault, category: API Credential)
2. Choose the appropriate pattern:
   - **Env var needed by CLI tools** → add `op read` line inside the `secret()` function in `.common_profile`
   - **Config file needs the value** → use `{{ onepasswordRead "op://..." }}` in a `.tmpl` file
   - **Single command needs a value** → inline `$(op read '...')` directly in an alias (like `ch`)

## Deploying to a New Machine

```bash
# 1. Install prerequisites
brew install chezmoi age 1password-cli

# 2. Restore age key from 1Password
mkdir -p ~/.config/chezmoi
# Copy key from 1Password item "chezmoi age encryption key" → ~/.config/chezmoi/key.txt
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
- `private_` prefix → file gets 0600 permissions (files) / 0700 (directories)
- `.tmpl` suffix → file is a Go template
- Templates use `{{ .chezmoi.homeDir }}` instead of hardcoded `~` or `/Users/tis`
- `.chezmoiignore` excludes `.DS_Store` and `README.md`
- `gh/hosts.yml` is explicitly excluded (contains auth tokens managed by `gh` itself)
- `private_dot_ssh/` and `private_dot_boto` use `private_` prefix for restrictive permissions

## SSH Config

`~/.ssh/config` is managed via `private_dot_ssh/config.tmpl`. Security defaults applied to `Host *`:

```
StrictHostKeyChecking ask   # prompt on unknown hosts, never silently accept
HashKnownHosts yes          # obfuscate hostnames in known_hosts
ServerAliveInterval 60      # keepalive every 60s
ServerAliveCountMax 3       # disconnect after 3 missed keepalives
```

Authentication is handled entirely by the 1Password SSH agent (`IdentityAgent`). No private keys on disk.

## Kitty Remote Control Socket

Kitty's remote control socket is at `~/.local/share/kitty/control-socket` (Kitty appends `-{PID}` at startup, e.g. `control-socket-36767`). Workspace scripts discover it via glob:

```python
SOCKET_GLOB = os.path.expanduser("~/.local/share/kitty/control-socket-*")
```

The directory `~/.local/share/kitty/` must exist before Kitty starts. This is handled automatically by the chezmoi `run_once_create-kitty-socket-dir.sh` script on first `chezmoi apply`.

## What's NOT Managed

- `~/.config/chezmoi/chezmoi.toml` (machine-local config, not in git)
- `~/.config/chezmoi/key.txt` (encryption key, never in git)
- SSH keys (managed by 1Password agent)
- `gh` auth tokens (managed by `gh auth`)
- Any project-specific `.env` files
- `~/.atuin/` (self-installer artefact — atuin is now installed via Homebrew)
