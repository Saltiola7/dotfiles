# Changelog — DBSCTR2 and Discovery2 Lifecycle

## 2026-07-10 Follow-Up: Plan And Build Agents

- Made native `Plan` on GPT-5.6 Sol medium the startup agent.
- Renamed the implementation primaries to `Build-GPT` and `Build-Claude`,
  disabled native `Build`, and removed the unused OpenCode Zen `opus` primary.
- Added explicit OpenAI reasoning and Bedrock thinking variants because the new
  model catalog entries otherwise exposed only `Default` in the TUI.
- Retargeted implementation commands and provider-affine routing to `Build-GPT`.
- Deployed the renamed agents, removed stale deployed primary files, and verified
  the resolved primary set, variants, command targets, and clean chezmoi status.
- Corrected Bedrock `medium` to Claude 4.8/5's native adaptive reasoning shape
  after the TUI continued to show the legacy fixed-budget override as `Default`.

## 2026-07-10 Implementation: Provider-Affine OpenCode Agents

- Added `gpt` on `openai/gpt-5.6-sol` and `opus-bedrock` on
  `amazon-bedrock/global.anthropic.claude-opus-4-8` as selectable primary
  agents, while preserving the existing `opus` primary.
- Added OpenAI Luna/Terra and Bedrock Sonnet 5 Explore, Scout, and Builder
  subagents with provider-local task permissions and Builder write boundaries.
- Removed fixed Sonnet 4.6 overrides from generic agents and added a generic
  inheriting Scout.
- Added native Bedrock provider configuration for the existing `us-west-2`
  profile and made `gpt` the startup default.
- Added phase-ledger, child evidence, same-provider fallback, and Plan-to-Build
  requirements to DBSCTR2 and global routing.
- Verified exact models through OpenCode runtime listings and Models.dev, parsed
  the rendered configuration, deployed through chezmoi, and completed a live
  Bedrock Explore route. OpenAI Explore launched correctly twice but did not
  return before timeout/abort; this remains a runtime follow-up.

## 2026-07-10 Discovery: Provider-Affine OpenCode Agents

- Reached 96% confidence after reviewing OpenCode's agents, commands,
  permissions, tools, references, plugins, SDK, server, config, and rules plus
  current GPT-5.6 and Claude Sonnet 5 prompting guidance.
- Selected OpenCode-native primary-agent switching for regular OpenAI and Amazon
  Bedrock use, with GPT-5.6 Sol as the startup default and generic model
  inheritance for other providers.
- Assigned GPT-5.6 Luna low to OpenAI Explore, GPT-5.6 Terra medium to OpenAI
  Scout and Builder, and Claude Sonnet 5 medium to Bedrock Explore, Scout, and
  Builder. Flagship GPT-5.6 Sol or Bedrock Opus retains orchestration.
- Required clear-benefit delegation, full routing visibility, one visible
  same-provider flagship fallback, and no silent cross-provider delegation.
- Required flagship review of delegated code while trusting source-backed
  Explore and Scout results unless uncertain, contradictory, or controlling a
  risky edit.
- Added OpenCode-native phase-ledger, Plan-to-Build handoff, child-session
  evidence, permission, snapshot, and session-diff requirements.
- Deferred Review, phase-specific agents, routing plugins, and a permanent model
  evaluation framework. Validation will use a small temporary scenario suite.
- Kept the existing `opus` primary during migration and ignored the unused
  Headroom provider; exact native Bedrock model identifiers remain a pre-build
  validation item.

## 2026-07-10 Follow-Up: QA Gate

- Replaced the standalone Dependabot skill, command, and DBSCTR2 gate with the
  repository-aware `qa` skill and thin `/qa` command.
- Scoped DBSCTR2 quality checks to affected code and dependencies while ignoring
  unrelated pre-existing findings.
- Kept Dependabot alerts as QA finding inputs rather than a separate workflow.
- Added Discovery2 toolchain-command, authority, and baseline discovery.

## 2026-06-25

### Domain

- Defined v2 lifecycle bounded context, domain terms, goals, non-goals, and
  external interfaces.
- Captured user decisions from Discovery interview: OpenCode-native routing,
  v1 permanence, strict DBSCTR2, Discovery2 95% confidence, Ponytail hard
  principle, write subagents under orchestrator control, and phase-gate commits.

### Behavior

- Added Given/When/Then scenarios for OpenCode routing, Discovery2 intent
  extraction, strict DBSCTR2 execution, stale-artifact prevention, phase-gate
  commits, concurrent backlog planning, write subagent ownership, Ponytail
  minimalism, and thin commands.

### Spec

- Added initial `discovery2` and `dbsctr2` skill interfaces with frontmatter,
  goals, success criteria, retrieval budgets, output contracts, and stop rules.
- Added thin global command wrappers for `/discovery2` and `/dbsctr2`.

### Contract

- Added managed OpenCode routing instructions in `AGENTS.md`.
- Added Ponytail to global OpenCode plugin config.
- Added Discovery2 confidence, DBSCTR2 artifact freshness, OpenCode config, and
  subagent safety contracts.

### Test

- Validated source OpenCode config JSON with `jq empty`.
- Deployed targeted v2 files with `chezmoi apply`.
- Verified deployed target files exist and read deployed skill/command/routing
  headers.
- Validated deployed OpenCode config JSON with `jq empty`.
- Confirmed `chezmoi status` returned clean output after targeted apply.

### Refactor

- Finalized backlog state after rollout.
- Left v1 skills untouched and recorded v2 as OpenCode-managed default routing.

## 2026-06-25 Follow-Up: DBSCTR2 DVC Sync

### Behavior

- Added DBSCTR2 behavior for DVC-aware phase commits and DVC-before-Git push
  sequencing.

### Contract

- Added DVC marker detection, DVC metadata commit coupling, graphify DVC artifact
  handling, unrelated-drift reporting, and push failure stop rules.

### Test

- Deployed updated DBSCTR2 skill with `chezmoi apply`.
- Verified deployed target contains the DVC Sync Gate, `dvc push` rule, and
  graphify DVC artifact rule.
- Confirmed `chezmoi status` returned clean output after deploy.

## 2026-06-26 Follow-Up: Dependabot Workflow

### Behavior

- Added a focused current-repo Dependabot remediation workflow.
- Added DBSCTR2 alert scoping so only alerts relevant to touched imports/usages
  are delegated, while unrelated alerts are summarized by severity.

### Spec

- Added `dependabot` skill and thin `/dependabot` command interface.

### Contract

- Added Dependabot gate and remediation contracts for authenticated `gh`, scoped
  alert context, patch/minor local remediation, major/breaking escalation to
  DBSCTR2, dependency-specific tests, artifact freshness, commits, and pushes.

### Test

- Deployed the `dependabot` skill, `/dependabot` command, updated `dbsctr2`, and
  updated OpenCode routing with targeted `chezmoi apply`.
- Verified deployed target text for the Dependabot workflow, DBSCTR2 gate, thin
  command wrapper, and routing rule.
- Confirmed `chezmoi status` returned clean output after deploy.

## 2026-07-03 Follow-Up: DBSCTR2 Domain Modules

### Domain

- Added DBSCTR2-owned domain modules for data engineering, cloud/platform/IaC,
  ML/AI, and analytics reference scaffolding.

### Behavior

- Added DBSCTR2 module routing so applicable modules are read before Phase 1
  Domain and their phase extensions are applied or explicitly ruled out.

### Spec

- Added the v2 module files under `dot_agents/skills/dbsctr2/modules/` and kept
  v1 modules intact for explicit v1 use.

### Contract

- Added the invariant that v2 module guidance must not depend on v1 `dbsctr`
  paths.
