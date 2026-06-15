# OpenCode Personal Account Setup Specification

**Status:** Stable
**Created:** 2026-04-27
**Last updated:** 2026-06-15

## Overview

This shell uses Claude Code in two contexts:

1. **Work** — global `claude` and `opencode` invocations route through AWS Bedrock, driven by `CLAUDE_CODE_USE_BEDROCK=1` and `AWS_PROFILE` env vars set in the shell profile.
2. **Personal** — `claude-personal` and `opencode-personal` wrappers strip the Bedrock environment, isolate Claude Code's auth into a dedicated config directory, and route OpenCode through a local Meridian proxy that talks to the Claude Pro subscription via the Claude Agent SDK.

Both contexts coexist on the same machine without interfering. Switching is a matter of which command you type.

## Domain

### Bounded Context

**OpenCode Provider Configuration** — manages the set of AI providers and models available in the
OpenCode TUI, including compression layers and local model routing.

Adjacent contexts: AWS Bedrock auth (SSO-managed, external), LM Studio (local inference server,
external), Headroom compression proxy (local service, managed by this context).

### Entities

- **Provider** — named AI provider registered in `opencode.json`; has an id, npm package, baseURL, and a model registry
- **Compressed Provider** — a Provider whose baseURL points at the Headroom proxy instead of a cloud API directly
- **HeadroomProxy** — the local headroom-ai proxy process; runs at `127.0.0.1:8787`; backend = Bedrock; always-on via launchd
- **LaunchAgent** — macOS launchd user agent managing the HeadroomProxy lifecycle
- **ModelEntry** — a named model within a provider's registry, with context/output limits

### Value Objects

- **ProxyEndpoint** — `http://127.0.0.1:8787/v1` — the stable local address of HeadroomProxy
- **ModelId** — the exact string opencode sends as the `model` field (e.g. `global.anthropic.claude-sonnet-4-6`); must match what Bedrock accepts verbatim
- **CompressionMode** — `optimize | audit | passthrough`; controls headroom-ai pipeline aggressiveness
- **SavingsRatio** — float 0–1; ratio of tokens saved vs uncompressed baseline; observable at `GET /stats`

### Domain Events

- `HeadroomProxyStarted` — launchd launched headroom-ai proxy; `/health` returns 200
- `HeadroomProxyStopped` — proxy process exited (SSO expiry, crash, manual stop)
- `CompressionToggled` — user switched between `amazon-bedrock/*` (raw) and `headroom/*` (compressed) model in opencode TUI
- `SSOTokenExpired` — `AWS_PROFILE` SSO cache expired; HeadroomProxy returns 403/5xx to opencode
- `LocalModelRegistryUpdated` — LM Studio model entries in opencode.json refreshed to match running server

### Ubiquitous Language

| Term | Definition |
|------|-----------|
| **compression toggle** | Switching opencode's active model between a raw Bedrock provider entry and a headroom-prefixed entry to enable/disable compression |
| **raw model** | Model entry under `amazon-bedrock` provider — routes native Bedrock SDK, no compression |
| **compressed model** | Model entry under `headroom` provider — routes via HeadroomProxy; same underlying LLM, compressed context |
| **HeadroomProxy** | The `headroom proxy --backend bedrock` process running at :8787; compresses Anthropic-format requests before forwarding to Bedrock via SigV4 |
| **LaunchAgent** | `~/Library/LaunchAgents/ai.headroom.proxy.plist` — the always-on launchd definition for HeadroomProxy |
| **SSO profile** | `BedrockDeveloperAccess-302432775606` — the AWS named profile used by both native Bedrock and HeadroomProxy |
| **local model** | Model served by LM Studio on `:1234`; registered under `lmstudio` provider in opencode.json |
| **model-id passthrough** | HeadroomProxy forwards the `model` field in the request body to Bedrock unchanged; no translation table |
| **savings ratio** | Fraction of tokens compressed away; visible at `http://127.0.0.1:8787/stats` |

## File Map

| Path | Purpose |
|------|---------|
| `dot_local/bin/executable_opencode-personal` | Wrapper: unsets Bedrock env, sets Meridian profile, launches OpenCode against the Anthropic provider |
| `dot_local/bin/executable_claude-personal` | Wrapper: unsets Bedrock env, sets `CLAUDE_CONFIG_DIR` to the personal profile, launches Claude Code |
| `private_dot_config/opencode/opencode.json.tmpl` | OpenCode config — declares Bedrock (work, default), Anthropic-via-Meridian, LM Studio, Moonshot, Google, and Headroom providers; loads `opencode-with-claude` plugin |
| `private_dot_config/meridian/profiles.json.tmpl` | Meridian profile registry — points the `personal` profile at an isolated `CLAUDE_CONFIG_DIR` (templated on `{{ "{{ .chezmoi.homeDir }}" }}`) |
| `private_dot_config/meridian/sdk-features.json` | Meridian SDK feature toggles for OpenCode: memory, auto-dream, full CLAUDE.md |
| `Library/LaunchAgents/ai.headroom.proxy.plist` | LaunchAgent definition: always-on HeadroomProxy, `--backend bedrock --region us-west-2`, env `AWS_PROFILE` |
| `npm-global-packages.txt` | Plain text list of npm packages installed globally |
| `run_onchange_install-npm-globals.sh.tmpl` | Chezmoi run-on-change script that `npm install -g`s anything in the package list when the file's hash changes |

## Architecture

```
opencode TUI
  ├─ amazon-bedrock/global.*       → native Bedrock SDK (raw, uncompressed)
  ├─ headroom/global.*             → @ai-sdk/anthropic → http://127.0.0.1:8787/v1/messages
  │                                      │
  │                               HeadroomProxy (launchd, optimize, --backend bedrock)
  │                                      │  compress → SigV4 via AWS_PROFILE SSO
  │                                      ▼
  │                               AWS Bedrock (global.anthropic.claude-*)
  ├─ lmstudio/*                    → @ai-sdk/openai-compatible → http://127.0.0.1:1234/v1
  └─ (personal contexts below)    → opencode-with-claude / Meridian → Anthropic Claude Pro

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

## Behavior Scenarios

### Feature: Compression Toggle (Bedrock models)

**Scenario: User enables compression for Bedrock model**
- Given HeadroomProxy is running at `127.0.0.1:8787` (LaunchAgent active)
- And opencode shows both `amazon-bedrock/global.anthropic.claude-sonnet-4-6` and `headroom/global.anthropic.claude-sonnet-4-6` in model picker
- When user selects `headroom/global.anthropic.claude-sonnet-4-6`
- Then opencode routes requests via `@ai-sdk/anthropic` to `http://127.0.0.1:8787/v1/messages`
- And HeadroomProxy compresses context before forwarding to Bedrock
- And savings ratio becomes observable at `GET http://127.0.0.1:8787/stats`
- And opencode persists model choice in `~/.local/state/opencode/model.json` across restarts

**Scenario: User disables compression (switches back to raw)**
- Given user has `headroom/global.anthropic.claude-sonnet-4-6` active
- When user selects `amazon-bedrock/global.anthropic.claude-sonnet-4-6` in model picker
- Then opencode routes requests via native Bedrock SDK directly
- And no HeadroomProxy involvement — proxy can be down without impact

**Scenario: HeadroomProxy not running, user selects compressed model**
- Given LaunchAgent is stopped or SSO token expired
- When opencode sends request to `http://127.0.0.1:8787/v1/messages`
- Then opencode receives connection refused or 5xx
- And user sees an error in TUI (not a silent hang)
- And raw Bedrock models remain fully functional

### Feature: Compression Toggle (LM Studio models)

**Scenario: User enables compression for local LM Studio model**
- Given LM Studio server running at `127.0.0.1:1234`
- And HeadroomProxy running at `127.0.0.1:8787` with `--openai-api-url http://127.0.0.1:1234/v1`
- And opencode shows both `lmstudio/mistralai/devstral-small-2-2512` (raw) and `headroom-lmstudio/mistralai/devstral-small-2-2512` (compressed)
- When user selects compressed variant
- Then opencode routes via `@ai-sdk/openai-compatible` to `http://127.0.0.1:8787/v1`
- And HeadroomProxy compresses context then forwards to LM Studio
- And model-id passthrough delivers `mistralai/devstral-small-2-2512` to LM Studio unchanged

**Scenario: User uses raw LM Studio model (no compression)**
- Given LM Studio server running at `127.0.0.1:1234`
- When user selects `lmstudio/mistralai/devstral-small-2-2512`
- Then opencode routes directly to LM Studio via `http://127.0.0.1:1234/v1`
- And HeadroomProxy state irrelevant

### Feature: LM Studio Model Registry Refresh

**Scenario: opencode model list matches running LM Studio server**
- Given LM Studio serves `mistralai/devstral-small-2-2512` and `qwen/qwen3.6-35b-a3b` (verified via `/v1/models`)
- When `chezmoi apply` deploys updated `opencode.json.tmpl`
- Then both model IDs appear in opencode model picker under `lmstudio` provider
- And context/output limits match spec recommendations (devstral: 65536/8192, qwen: 32768/16384)

### Feature: HeadroomProxy Always-On Service

**Scenario: LaunchAgent starts HeadroomProxy on login**
- Given `~/Library/LaunchAgents/ai.headroom.proxy.plist` loaded in launchd
- And valid SSO token in `~/.aws/sso/cache` (user ran `aws sso login --profile BedrockDeveloperAccess-302432775606`)
- When user logs in to macOS session
- Then LaunchAgent starts `headroom proxy --backend bedrock --region us-west-2`
- And `GET http://127.0.0.1:8787/health` returns 200

**Scenario: LaunchAgent restarts proxy after crash**
- Given KeepAlive=true in plist
- When HeadroomProxy process exits unexpectedly
- Then launchd restarts it within seconds
- And `/health` returns 200 again

**Scenario: SSO token expires mid-session**
- Given HeadroomProxy running with expired SSO cache
- When opencode sends request via compressed model
- Then HeadroomProxy returns error (403 or 5xx from Bedrock)
- And user sees error in TUI
- And fix is: `aws sso login --profile BedrockDeveloperAccess-302432775606` then requests resume

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
