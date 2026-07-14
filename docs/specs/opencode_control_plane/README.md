# OpenCode Control Plane

**Status:** Approved
**Discovery2 confidence:** 99%

## Engineering Profile

### Defaults

| Field | Value |
|---|---|
| Deliverable | Managed OpenCode providers, agents, commands, permissions, skills, and routing |
| Languages/frameworks | JSON/JSONC configuration, Markdown agent prompts, Python contract tests |
| Modules | ML/AI |
| Runtime/platform support | OpenCode in the managed macOS dotfiles environment; Python `>=3.12` tests |
| Public compatibility | Preserve native Plan-to-Build and provider-affine Build workflows; retire provider entries that current authentication cannot use |
| Trust/data classification | Local configuration and public provider metadata; credentials remain outside the repository |
| Operational owner | Dotfiles owner maintains deployment and OpenCode compatibility |

## Overview

The OpenCode control plane owns global providers, agents, commands, permissions,
skills, and Graphify routing. It keeps OpenAI and Amazon Bedrock workflows
provider-affine while removing unused Claude Code, Meridian, Headroom, and OMO
surfaces.

## Goals

- Keep native Plan and Build, plus provider-affine `Build-GPT` and `Build-Claude`.
- Keep direct Bedrock Claude and raw LM Studio models.
- Make workflow commands inherit the selected primary agent.
- Allow local Build commands by default while gating external or destructive writes.
- Give Builder subagents bounded write access without Git, deployment, or external paths.
- Install only OpenCode-compatible skills, once.
- Preserve Graphify CLI, skill, graph, hooks, and health-gated query-first routing.
- Remove Claude Code, Meridian, Headroom, OMO, and their runtime state completely.

## Non-goals

- No new orchestration framework, review agent, MCP server, or benchmark suite.
- No Graphify package changes.
- No removal of Bedrock Claude or raw LM Studio.
- No changes to V1 `dbsctr` or `discovery`.

## Ubiquitous Language

| Term | Meaning |
|---|---|
| Control Plane | Managed OpenCode config, agents, commands, permissions, skills, and routing. |
| Provider Affinity | Delegation remains inside the active primary's provider family. |
| Local Build Command | In-worktree command without external, destructive, deploy, publish, or Git-write effects. |
| Runtime Residue | Unmanaged config, package, service, authentication, cache, or backup from a removed integration. |
| Graph Health Gate | Freshness and relevance check before trusting a Graphify query. |

## Behavior

### Provider-neutral commands

Given any selected primary, when `/dbsctr`, `/discovery`, or `/qa` runs, then
the command uses that primary and does not force OpenAI.

### Plan and Build permissions

Given a Plan primary, edits are denied and Bash requires approval. Given a Build
primary, local commands run by default while known external, destructive,
deployment, publishing, and Git-write commands require approval.

### Native Plan-to-Build handoff

Given native Plan completes planning, its built-in exit path targets the native
`build` agent. Native Build therefore remains enabled. `Build-GPT` remains a
separate primary selected manually for OpenAI provider-affine Sol-to-Terra
orchestration; changing only the model does not change the active agent.

### Bounded Builder

Given a provider-local Builder subagent, it may edit owned in-worktree files and
run focused checks, but cannot use external directories, delegate, write Git
state, deploy, publish, or perform external writes.

### Provider affinity

Given an OpenAI primary, it delegates only to OpenAI optimized agents. Given
`Build-Claude`, it delegates only to Bedrock optimized agents. No fallback
crosses providers silently.

### ChatGPT OAuth model exposure

Given OpenAI uses ChatGPT OAuth, only models and reasoning-effort variants
supported by that route are exposed. Native Plan and `Build-GPT` use base
GPT-5.6 Sol with medium effort by default, while the user may select another
supported effort variant. No agent or provider override claims unavailable Pro
reasoning mode. The ChatGPT OAuth backend rejects base Sol requests containing
`reasoning.mode: "pro"` with `unsupported_value`. OpenAI Explore, Scout, and
Builder remain on GPT-5.6 Terra.

### Removed integrations

Given deployment completes, Claude Code, Meridian, Headroom, OMO, their wrappers,
providers, services, packages, skills, authentication, state, backups, and
historical project documentation are absent. Bedrock Claude remains available.

### Graphify preservation

Given an existing graph, architecture work checks graph freshness and relevance,
queries it when useful, verifies findings against source, and falls back to
source search when stale or weak. Full Graphify creation, update, query, and Git
hook behavior remains available without a duplicate project plugin.

## Contracts

- `$schema` remains `https://opencode.ai/config.json` and rendered config passes
  the current schema/runtime parser.
- Direct provider `anthropic` is denied; `amazon-bedrock` is not.
- Raw `lmstudio` remains configured; `headroom` and `headroom-lmstudio` do not.
- Native Plan remains the startup default and native Build stays enabled as the
  built-in Plan exit target.
- `gpt-5.6-sol-pro`, `Plan-GPT-Pro`, `Plan-GPT-Pro-Max`, and `Build-GPT-Pro`
  are absent while ChatGPT OAuth excludes Pro reasoning mode.
- Native Plan and `Build-GPT` resolve to `openai/gpt-5.6-sol` with `medium` as
  their default effort; OpenAI optimized subagents remain on Terra.
- Commands contain no fixed `agent` field.
- Skill names visible to OpenCode are unique.
- Unversioned lifecycle commands load DBSCTR V3; V1 is removed and V2 source is
  archived outside deployed skill paths.
- Runtime cleanup is irreversible and was explicitly approved.

## Validation Strategy

| Authority | Scope | Command | Availability |
|---|---|---|---|
| OpenCode parser | Resolved config and agents | `opencode debug config` | Required |
| JSON parser | Source/rendered config | `jq empty` | Required |
| Focused tests | Control-plane invariants | `pytest tests/test_opencode_control_plane.py` | Required |
| Chezmoi | Deployment and removals | dry-run, apply, status | Required |
| Graphify | Skill, hooks, query | version, hook status, targeted query | Required |
| Package/service inventory | Removed runtime | npm, pipx, launchctl, path checks | Required |

## Risks

- Bash patterns are guardrails, not an OS sandbox.
- Runtime deletion cannot be rolled back without reinstalling removed tools.
- Removing the duplicate Graphify project integration must not remove its global
  skill, graph, or hooks.
- OpenCode provider behavior may change across upgrades; focused contract tests
  prevent unsupported aliases from silently returning.
- OpenCode 1.17.20 cannot retarget native `plan_exit` to a custom primary;
  `Build-GPT` therefore requires manual selection and a new message.
