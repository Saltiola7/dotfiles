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
- **HeadroomProxyBedrock** — headroom-ai proxy at `127.0.0.1:8787`; `--backend bedrock`; compresses Anthropic-format requests; always-on via launchd
- **HeadroomProxyLMStudio** — headroom-ai proxy at `127.0.0.1:8788`; default (anthropic) backend; `--openai-api-url http://127.0.0.1:1234/v1`; compresses OpenAI-format requests; always-on via launchd
- **LaunchAgent** — macOS launchd user agent managing a HeadroomProxy lifecycle; two instances: `ai.headroom.proxy.bedrock` and `ai.headroom.proxy.lmstudio`
- **ModelEntry** — a named model within a provider's registry, with context/output limits

### Value Objects

- **BedrockProxyEndpoint** — `http://127.0.0.1:8787/v1` — stable local address of HeadroomProxyBedrock
- **LMStudioProxyEndpoint** — `http://127.0.0.1:8788/v1` — stable local address of HeadroomProxyLMStudio
- **ModelId** — the exact string opencode sends as the `model` field (e.g. `global.anthropic.claude-sonnet-4-6`); must match what Bedrock accepts verbatim
- **CompressionMode** — `optimize | audit | passthrough`; controls headroom-ai pipeline aggressiveness
- **SavingsRatio** — float 0–1; ratio of tokens saved vs uncompressed baseline; observable at `GET /stats`

### Domain Events

- `HeadroomProxyBedrockStarted` — launchd launched HeadroomProxyBedrock; `:8787/health` returns 200
- `HeadroomProxyLMStudioStarted` — launchd launched HeadroomProxyLMStudio; `:8788/health` returns 200
- `HeadroomProxyStopped` — either proxy process exited (SSO expiry, crash, manual stop)
- `CompressionToggled` — user switched between `amazon-bedrock/*` (raw) and `headroom/*` (compressed) model in opencode TUI
- `SSOTokenExpired` — `AWS_PROFILE` SSO cache expired; HeadroomProxy returns 403/5xx to opencode
- `LocalModelRegistryUpdated` — LM Studio model entries in opencode.json refreshed to match running server

### Ubiquitous Language

| Term | Definition |
|------|-----------|
| **compression toggle** | Switching opencode's active model between a raw provider entry and a headroom-prefixed entry to enable/disable compression |
| **raw model** | Model entry under `amazon-bedrock` or `lmstudio` provider — routes directly, no compression |
| **compressed model** | Model entry under `headroom` or `headroom-lmstudio` provider — routes via a HeadroomProxy |
| **HeadroomProxyBedrock** | `headroom proxy --backend bedrock` at :8787; handles `/v1/messages`; SigV4 via SSO profile |
| **HeadroomProxyLMStudio** | `headroom proxy --openai-api-url http://127.0.0.1:1234/v1` at :8788; handles `/v1/chat/completions` |
| **LaunchAgent** | macOS launchd user agent (plist in `~/Library/LaunchAgents/`); two instances, one per proxy |
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
| `Library/LaunchAgents/ai.headroom.proxy.bedrock.plist` | LaunchAgent: HeadroomProxyBedrock always-on, `--backend bedrock --region us-west-2 --bedrock-profile ...` |
| `Library/LaunchAgents/ai.headroom.proxy.lmstudio.plist` | LaunchAgent: HeadroomProxyLMStudio always-on, `--openai-api-url http://127.0.0.1:1234/v1` |
| `npm-global-packages.txt` | Plain text list of npm packages installed globally |
| `run_onchange_install-npm-globals.sh.tmpl` | Chezmoi run-on-change script that `npm install -g`s anything in the package list when the file's hash changes |

## Architecture

```
opencode TUI
  ├─ amazon-bedrock/global.*           → native Bedrock SDK (raw)
  ├─ headroom/global.*                 → @ai-sdk/anthropic → :8787/v1/messages
  │                                         │
  │                              HeadroomProxyBedrock (launchd ai.headroom.proxy.bedrock)
  │                              --backend bedrock --bedrock-profile BedrockDeveloperAccess-302432775606
  │                                         │ SigV4 (SSO cache)
  │                                         ▼
  │                              AWS Bedrock us-west-2
  │
  ├─ lmstudio/*                        → @ai-sdk/openai-compatible → :1234/v1 (raw)
  ├─ headroom-lmstudio/*               → @ai-sdk/openai-compatible → :8788/v1/chat/completions
  │                                         │
  │                              HeadroomProxyLMStudio (launchd ai.headroom.proxy.lmstudio)
  │                              --openai-api-url http://127.0.0.1:1234/v1
  │                                         │ HTTP passthrough
  │                                         ▼
  │                              LM Studio :1234
  └─ (personal contexts below)         → opencode-with-claude / Meridian → Anthropic Claude Pro

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

## Spec: Config Stubs

### opencode.json.tmpl — headroom provider (Bedrock upstream)

```jsonc
"headroom": {
  "npm": "@ai-sdk/anthropic",
  "name": "Headroom → Bedrock (compressed)",
  "options": { "baseURL": "http://127.0.0.1:8787/v1", "apiKey": "dummy" },
  "models": {
    "global.anthropic.claude-sonnet-4-6": {
      "name": "Sonnet 4.6 (compressed)",
      "limit": { "context": 200000, "output": 64000 }
    },
    "global.anthropic.claude-opus-4-8": {
      "name": "Opus 4.8 (compressed)",
      "limit": { "context": 200000, "output": 32000 }
    }
  }
}
```

Behaviors: "User enables compression for Bedrock model", "User disables compression"

### opencode.json.tmpl — headroom-lmstudio provider (LM Studio upstream)

```jsonc
"headroom-lmstudio": {
  "npm": "@ai-sdk/openai-compatible",
  "name": "Headroom → LM Studio (compressed)",
  "options": { "baseURL": "http://127.0.0.1:8788/v1" },
      "name": "Devstral Small 2 (compressed, local)",
      "limit": { "context": 65536, "output": 8192 }
    },
    "qwen/qwen3.6-35b-a3b": {
      "name": "Qwen3.6 35B A3B (compressed, local)",
      "limit": { "context": 32768, "output": 16384 }
    }
  }
}
```

Behaviors: "User enables compression for local LM Studio model"

### opencode.json.tmpl — lmstudio provider (updated model registry)

```jsonc
"lmstudio": {
  "npm": "@ai-sdk/openai-compatible",
  "name": "LM Studio (local)",
  "options": { "baseURL": "http://127.0.0.1:1234/v1" },
  "models": {
    "mistralai/devstral-small-2-2512": {
      "name": "Devstral Small 2 (MLX 4bit, local)",
      "limit": { "context": 65536, "output": 8192 }
    },
    "qwen/qwen3.6-35b-a3b": {
      "name": "Qwen3.6 35B A3B (MLX 4bit, local)",
      "limit": { "context": 32768, "output": 16384 }
    }
  }
}
```

Behaviors: "opencode model list matches running LM Studio server"

### LaunchAgent plists — two instances

**`~/Library/LaunchAgents/ai.headroom.proxy.bedrock.plist`** (port 8787, Bedrock upstream):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>          <string>ai.headroom.proxy.bedrock</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/tis/.local/bin/headroom</string>
    <string>proxy</string>
    <string>--backend</string>           <string>bedrock</string>
    <string>--bedrock-profile</string>   <string>BedrockDeveloperAccess-302432775606</string>
    <string>--region</string>            <string>us-west-2</string>
    <string>--port</string>              <string>8787</string>
    <string>--no-ccr-inject-tool</string>
    <string>--no-ccr-marker</string>
    <string>--no-ccr-proactive-expansion</string>
    <string>--no-telemetry</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>   <string>/Users/tis</string>
    <key>PATH</key>   <string>/Users/tis/.local/bin:/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>RunAtLoad</key>     <true/>
  <key>KeepAlive</key>     <true/>
  <key>StandardOutPath</key>  <string>/Users/tis/.headroom/proxy-bedrock.out.log</string>
  <key>StandardErrorPath</key><string>/Users/tis/.headroom/proxy-bedrock.err.log</string>
</dict>
</plist>
```

**`~/Library/LaunchAgents/ai.headroom.proxy.lmstudio.plist`** (port 8788, LM Studio upstream):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>          <string>ai.headroom.proxy.lmstudio</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/tis/.local/bin/headroom</string>
    <string>proxy</string>
    <string>--port</string>              <string>8788</string>
    <string>--openai-api-url</string>    <string>http://127.0.0.1:1234/v1</string>
    <string>--no-ccr-inject-tool</string>
    <string>--no-ccr-marker</string>
    <string>--no-ccr-proactive-expansion</string>
    <string>--no-telemetry</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>   <string>/Users/tis</string>
    <key>PATH</key>   <string>/Users/tis/.local/bin:/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>RunAtLoad</key>      <true/>
  <key>KeepAlive</key>      <true/>
  <key>StandardOutPath</key>  <string>/Users/tis/.headroom/proxy-lmstudio.out.log</string>
  <key>StandardErrorPath</key><string>/Users/tis/.headroom/proxy-lmstudio.err.log</string>
</dict>
</plist>
```

Key flags (both plists):
- `--no-ccr-inject-tool` + `--no-ccr-marker` + `--no-ccr-proactive-expansion` — headroom 0.25.0 has `UnboundLocalError: ccr_workspace_key` bug when CCR enabled; all three flags required to suppress it
- `HOME` env var — required so botocore can find `~/.aws/sso/cache` for SSO token resolution
- `--bedrock-profile` (bedrock plist only) — resolves SSO credentials without needing `AWS_PROFILE` env
- `--no-telemetry` — local-first

Behaviors: "LaunchAgent starts HeadroomProxy on login", "LaunchAgent restarts proxy after crash"

## Contracts & Invariants

### Provider: headroom (Bedrock upstream)
- **Pre:** HeadroomProxyBedrock running at `127.0.0.1:8787` (`GET /health` → `{"status":"healthy","config":{"backend":"bedrock",...}}`)
- **Pre:** SSO token valid in `~/.aws/sso/cache` for `BedrockDeveloperAccess-302432775606`
- **Post:** `/v1/messages` returns 200 with valid Anthropic-format response body
- **Invariant:** `apiKey: "dummy"` accepted; never forwarded to Bedrock
- **Invariant:** `model` field passed through to Bedrock unchanged (model-id passthrough — verified in PoC)

### Provider: headroom-lmstudio (LM Studio upstream)
- **Pre:** LM Studio server running at `127.0.0.1:1234`
- **Pre:** HeadroomProxyLMStudio running at `127.0.0.1:8788` (`GET /health` → 200)
- **Post:** `/v1/chat/completions` returns 200 with valid OpenAI-format response body
- **Invariant:** `model` field passed through to LM Studio unchanged (verified in PoC with `qwen/qwen3.6-35b-a3b`)
- **Invariant:** no `apiKey` needed in provider options (proxy requires no inbound auth)

### Provider: lmstudio (raw)
- **Invariant:** model IDs in `opencode.json` match IDs returned by `GET http://127.0.0.1:1234/v1/models` verbatim
- **Invariant:** `context` limit ≤ model's native window (devstral: 256768, qwen3.6-35b-a3b: 32768)

### LaunchAgent: ai.headroom.proxy.bedrock
- **Invariant:** `Label` = `ai.headroom.proxy.bedrock`
- **Invariant:** `HOME` env var set so botocore resolves `~/.aws/sso/cache`
- **Invariant:** CCR suppression flags all three present: `--no-ccr-inject-tool`, `--no-ccr-marker`, `--no-ccr-proactive-expansion` (headroom 0.25.0 bug — `UnboundLocalError: ccr_workspace_key`)
- **Invariant:** `KeepAlive = true`
- **Invariant:** `~/.headroom/` dir exists before plist loaded
- **Failure recovery:** restart loop on SSO expiry is harmless (fails fast to Bedrock 403); renew with `aws sso login --profile BedrockDeveloperAccess-302432775606`

### LaunchAgent: ai.headroom.proxy.lmstudio
- **Invariant:** `Label` = `ai.headroom.proxy.lmstudio`
- **Invariant:** CCR suppression flags all three present (same bug)
- **Invariant:** `KeepAlive = true`
- **Failure recovery:** if LM Studio not running, proxy starts but all requests return 503; harmless

### Data Contract: HeadroomProxy `/health` endpoint
- **Schema:** `{"status":"healthy","ready":true,"config":{"backend":...,...}}` — non-200 = not ready
- **Invariant:** `config.backend` = `"bedrock"` for :8787, `"anthropic"` for :8788
- **Invariant:** responds within 1s on healthy process

### Lineage
- `opencode req → HeadroomProxyBedrock :8787 compress → Bedrock invoke → opencode res`
- `opencode req → HeadroomProxyLMStudio :8788 compress → LM Studio :1234 → opencode res`
- `opencode req → amazon-bedrock SDK (native SigV4) → Bedrock invoke → opencode res`  ← raw

## Gotchas

**HeadroomProxy CCR bug (headroom 0.25.0).** `UnboundLocalError: cannot access local variable 'ccr_workspace_key'` fires on every request unless all three flags suppressed: `--no-ccr-inject-tool --no-ccr-marker --no-ccr-proactive-expansion`. Will be fixed upstream; remove flags when resolved.

**Two proxy instances required — one backend cannot serve both upstreams.** With `--backend bedrock`, headroom routes ALL `/v1/chat/completions` through litellm-bedrock, ignoring `--openai-api-url`. Separate process on :8788 (default anthropic backend) needed for LMStudio routing.

**`HOME` must be set in launchd plist.** launchd doesn't set `HOME` by default; botocore needs it to find `~/.aws/sso/cache`. Without it, SSO resolution fails silently.

**SSO token expiry.** HeadroomProxyBedrock holds no refresh logic. On expiry, Bedrock returns 403. Fix: `aws sso login --profile BedrockDeveloperAccess-302432775606`. launchd restart loop is harmless until renewed.

**LM Studio must be running for compressed local models.** `headroom-lmstudio/*` models return 503 if LM Studio is off. Raw `lmstudio/*` models have same requirement.

**Don't run `meridian setup`.** It rewrites `~/.config/opencode/opencode.json` to add a Nix-store-style absolute path to the Meridian-bundled plugin. That conflicts with the chezmoi-managed config (which loads `opencode-with-claude` instead) and produces drift on every `chezmoi diff`. The two plugins overlap — `opencode-with-claude` already embeds Meridian.

**Personal profile auth is machine-local.** OAuth tokens in `~/.config/meridian/profiles/personal/` are not in the chezmoi source. Each new machine needs its own `claude-personal auth login`.

**Bedrock env vars stay in the shell profile.** They're not removed because the work workflow needs them globally. The personal wrappers strip them per-process. If you ever want to flip the default, move the `CLAUDE_CODE_USE_BEDROCK` export into a work-only wrapper instead.

**Model selection in `opencode-personal`.** The wrapper hardcodes `--model anthropic/claude-sonnet-4-6` to override the chezmoi-default Bedrock model. Pass any other `--model` to override at the CLI, or switch inside the OpenCode TUI.

## Verification

```bash
# HeadroomProxyBedrock health (backend must be "bedrock")
curl -s http://127.0.0.1:8787/health | python3 -c "import sys,json; h=json.load(sys.stdin); print('bedrock proxy:', h['status'], h['config']['backend'])"

# HeadroomProxyLMStudio health
curl -s http://127.0.0.1:8788/health | python3 -c "import sys,json; h=json.load(sys.stdin); print('lmstudio proxy:', h['status'], h['config']['openai_api_url'])"

# Smoke test: Bedrock via headroom (Anthropic-format)
curl -s http://127.0.0.1:8787/v1/messages \
  -H "Content-Type: application/json" -H "x-api-key: dummy" \
  -d '{"model":"global.anthropic.claude-sonnet-4-6","max_tokens":32,"messages":[{"role":"user","content":"reply ok"}]}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['content'][0]['text'], '| model:', r['model'])"

# Smoke test: LM Studio via headroom (OpenAI-format)
curl -s http://127.0.0.1:8788/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3.6-35b-a3b","max_tokens":32,"messages":[{"role":"user","content":"reply ok"}]}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['choices'][0]['message']['content'][:40], '| model:', r['model'])"

# Compression stats
curl -s http://127.0.0.1:8787/stats | python3 -m json.tool

# LaunchAgent status
launchctl list ai.headroom.proxy.bedrock
launchctl list ai.headroom.proxy.lmstudio

# LM Studio models available
curl -s http://127.0.0.1:1234/v1/models | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"

# Work context (default shell)
claude auth status
# → loggedIn: true, apiProvider: bedrock

# Personal context
claude-personal auth status
# → loggedIn: true, apiProvider: firstParty (or claude.ai)

# OpenCode personal — should answer "test" without hanging
opencode-personal
```
