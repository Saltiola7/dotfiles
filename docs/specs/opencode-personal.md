# OpenCode Personal Account Setup Specification

**Status:** Stable
**Created:** 2026-04-27

## Overview

This shell uses Claude Code in two contexts:

1. **Work** — global `claude` and `opencode` invocations route through AWS Bedrock, driven by `CLAUDE_CODE_USE_BEDROCK=1` and `AWS_PROFILE` env vars set in the shell profile.
2. **Personal** — `claude-personal` and `opencode-personal` wrappers strip the Bedrock environment, isolate Claude Code's auth into a dedicated config directory, and route OpenCode through a local Meridian proxy that talks to the Claude Pro subscription via the Claude Agent SDK.

Both contexts coexist on the same machine without interfering. Switching is a matter of which command you type.

## File Map

| Path | Purpose |
|------|---------|
| `dot_local/bin/executable_opencode-personal` | Wrapper: unsets Bedrock env, sets Meridian profile, launches OpenCode against the Anthropic provider |
| `dot_local/bin/executable_claude-personal` | Wrapper: unsets Bedrock env, sets `CLAUDE_CONFIG_DIR` to the personal profile, launches Claude Code |
| `private_dot_config/opencode/opencode.json` | OpenCode config — declares Bedrock (work, default), Anthropic-via-Meridian, LM Studio, and Google providers; loads `opencode-with-claude` plugin |
| `private_dot_config/meridian/profiles.json.tmpl` | Meridian profile registry — points the `personal` profile at an isolated `CLAUDE_CONFIG_DIR` (templated on `{{ "{{ .chezmoi.homeDir }}" }}`) |
| `private_dot_config/meridian/sdk-features.json` | Meridian SDK feature toggles for OpenCode: memory, auto-dream, full CLAUDE.md |
| `npm-global-packages.txt` | Plain text list of npm packages installed globally |
| `run_onchange_install-npm-globals.sh.tmpl` | Chezmoi run-on-change script that `npm install -g`s anything in the package list when the file's hash changes |

## Architecture

```
┌──────────────────────┐                       ┌────────────────┐
│  opencode-personal   │  unset BEDROCK env    │     opencode   │
│  (wrapper script)    │ ────────────────────▶ │     (TUI)      │
└──────────────────────┘                       └───────┬────────┘
                                                       │
                                  loads plugin          │
                                  opencode-with-claude  │
                                                       ▼
                                               ┌────────────────┐
                                               │  embedded       │
                                               │  Meridian proxy │  127.0.0.1:3456
                                               │  (per-process)  │
                                               └───────┬────────┘
                                                       │
                                  reads profiles.json   │
                                  picks "personal"      │
                                                       ▼
                                               ┌────────────────┐
                                               │ Claude Agent    │
                                               │ SDK (CLAUDE_   │
                                               │ CONFIG_DIR     │
                                               │ override)       │
                                               └───────┬────────┘
                                                       │
                                                       ▼
                                                  Anthropic
                                                  (Claude Pro)
```

The `opencode-with-claude` npm package bundles `@rynfar/meridian` and starts an embedded proxy in-process when OpenCode launches. The proxy is bound to a local port, lives only as long as the OpenCode process, and is configured per-process via env vars set by the wrapper.

## Why Two Wrappers

`claude` and `opencode` both honor several environment variables that override config file settings:

- `CLAUDE_CODE_USE_BEDROCK=1` forces Claude Code into Bedrock mode regardless of OAuth state.
- `AWS_PROFILE` / `AWS_REGION` are inherited by the SDK subprocess Meridian spawns; if they're set, requests fail with "AWS region setting is missing" or hang.
- `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_*_MODEL` pin specific Bedrock model IDs (e.g. `us.anthropic.claude-opus-4-6-v1[1m]`) that aren't valid against the Anthropic API.

The wrappers `unset` all of those before exec'ing the underlying tool, so the personal context starts from a clean slate even when the shell profile has the work overrides exported.

`claude-personal` additionally sets `CLAUDE_CONFIG_DIR` so Claude Code reads/writes its `.claude.json` and OAuth tokens inside `~/.config/meridian/profiles/personal/` instead of `~/.claude/` (where the Bedrock-bound work config lives).

## Profile Mechanism

Meridian's "profile" concept is a named auth context: each profile is a `CLAUDE_CONFIG_DIR` under `~/.config/meridian/profiles/<name>/` containing its own `.claude.json` and OAuth tokens. The profile registry at `~/.config/meridian/profiles.json` lists known profiles by id.

When `opencode-personal` sets `MERIDIAN_DEFAULT_PROFILE=personal`, the embedded proxy spawns the Claude Agent SDK with `CLAUDE_CONFIG_DIR=<personal profile dir>`, so it authenticates against the Pro subscription instead of Bedrock.

Adding a new profile (e.g. a second personal account) is a one-time per-machine browser flow:

```bash
claude-personal auth login   # for an isolated personal-style profile
# or
meridian profile add <name>  # standalone, prompts for browser OAuth
```

The profile credentials live entirely under `~/.config/meridian/profiles/<name>/` and are not synced via chezmoi (they're machine-local OAuth tokens).

## SDK Feature Toggles

`sdk-features.json` enables three Claude Code features for the OpenCode adapter:

| Toggle | Value | Effect |
|--------|-------|--------|
| `memory` | `true` | Auto-memory: SDK reads/writes persistent memory across sessions |
| `autoDream` | `true` | Background memory consolidation between sessions |
| `claudeMd` | `"full"` | Loads both `~/.claude/CLAUDE.md` and `./CLAUDE.md` into the system prompt |

These toggles are read lazily on every Meridian request, so editing the file takes effect on the next OpenCode turn without restarting.

## Installation Workflow

`chezmoi apply` is sufficient on a fresh machine. The `run_onchange_install-npm-globals.sh.tmpl` script:

1. Embeds the SHA-256 of `npm-global-packages.txt` into a comment header.
2. Chezmoi only re-runs the script when that hash changes.
3. The script reads each non-comment line of the package list and runs `npm install -g <package>`. `npm install -g` is naturally idempotent.

After the first apply on a new machine:

```bash
claude-personal auth login    # one-time browser OAuth for personal profile
opencode-personal             # verify it boots and answers a turn
```

## Gotchas

**Don't run `meridian setup`.** It rewrites `~/.config/opencode/opencode.json` to add a Nix-store-style absolute path to the Meridian-bundled plugin. That conflicts with the chezmoi-managed config (which loads `opencode-with-claude` instead) and produces drift on every `chezmoi diff`. The two plugins overlap — `opencode-with-claude` already embeds Meridian.

**Personal profile auth is machine-local.** OAuth tokens in `~/.config/meridian/profiles/personal/` are not in the chezmoi source. Each new machine needs its own `claude-personal auth login`.

**Bedrock env vars stay in the shell profile.** They're not removed because the work workflow needs them globally. The personal wrappers strip them per-process. If you ever want to flip the default, move the `CLAUDE_CODE_USE_BEDROCK` export into a work-only wrapper instead.

**Model selection in `opencode-personal`.** The wrapper hardcodes `--model anthropic/claude-sonnet-4-6` to override the chezmoi-default Bedrock model. Pass any other `--model` to override at the CLI, or switch inside the OpenCode TUI.

## Verification

```bash
# Work context (default shell)
claude auth status
# → loggedIn: true, apiProvider: bedrock

# Personal context
claude-personal auth status
# → loggedIn: true, apiProvider: firstParty (or claude.ai)

# OpenCode personal — should answer "test" without hanging
opencode-personal
```
