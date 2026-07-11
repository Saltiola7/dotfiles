# DBSCTR2 and Discovery2 Lifecycle

## Overview

The bounded context is the v2 lifecycle for OpenCode-native DBSCTR and
Discovery skills. The system creates strict, prompt-guide-native workflows that
remain callable beside the existing v1 skills forever.

The v2 lifecycle optimizes for GPT-5.6 Sol and Claude Opus on Amazon Bedrock,
with provider-local GPT-5.6 Terra and Claude Sonnet 5 subagents.
It uses OpenCode-native agents, permissions, child sessions, todos, and recovery
while preserving the original `dbsctr` and `discovery` skills for explicit v1
use.

## Problem Statement

The existing skills are useful but predate newer model prompt guidance,
OpenCode-native command/config patterns, and practical subagent orchestration.
They also need stronger guidance for keeping specs, backlogs, changelogs, and
other artifacts current when implementation changes.

## Goals

- Add globally managed `dbsctr2` and `discovery2` skills.
- Add global `/dbsctr2`, `/discovery2`, and `/qa` thin wrapper commands.
- Add OpenCode-native routing through managed `~/.config/opencode/AGENTS.md`.
- Keep v1 `dbsctr` and `discovery` unchanged and callable forever.
- Copy foundational DBSCTR modules into DBSCTR2 and route domain-specific work to
  the v2 module files.
- Install Ponytail globally and make minimal correct work a hard principle.
- Make DBSCTR2 strict when selected by routing or explicit command.
- Make Discovery2 interview until at least 95% confidence in user intent.
- Allow write subagents where viable while orchestrator owns review, test, and commit.
- Compile backlogs that are safe for concurrent work.
- Keep OpenAI and Bedrock delegation within the active provider family.
- Use lower-cost Explore, Scout, and Builder agents only when delegation has a
  clear benefit, with visible same-provider flagship fallback.
- Make phase state and Plan-to-Build handoff explicit through OpenCode-native
  session features.

## Non-Goals

- Do not modify `~/.claude/CLAUDE.md`.
- Do not delete, rename, or deprecate v1 skills.
- Do not create provider-specific copies of DBSCTR2 or Discovery2.
- Do not add a routing plugin, permanent model benchmark framework, phase-specific
  agents, or a separate Review agent in this cycle.
- Do not modify Graphify package internals.

## Domain Model

| Term | Definition |
|---|---|
| V2 Lifecycle | Combined Discovery2 and DBSCTR2 workflow, routing, commands, and deployment artifacts. |
| Discovery2 | Requirements interview skill that extracts user intent to at least 95% confidence before a DBSCTR2 cycle. |
| DBSCTR2 | Strict six-phase implementation skill: Domain, Behavior, Spec, Contract, Test, Refactor. |
| DBSCTR2 Domain Module | V2 module file loaded before Domain for foundational contexts such as data, cloud/platform, ML/AI, or analytics reference scaffolding. |
| QA Skill | Repository-aware scoped quality gate and explicit full-audit workflow, including dependency alerts. |
| Orchestrator | Main agent running the skill, owning plan, file ownership, integration, validation, and commits. |
| Write Subagent | Subagent allowed to edit isolated files under an explicit ownership contract. |
| Ownership Contract | Per-task definition of files a subagent may write, files it may read, dependencies, collision risks, and validation. |
| Concurrent Backlog | Backlog structured so independent tasks can run in parallel without file collisions. |
| Phase Gate | Required checkpoint before moving to next DBSCTR2 phase or committing. |
| QA Gate | DBSCTR2 checkpoint that validates affected scope with project-configured tools while ignoring unrelated existing noise. |
| DVC Sync Gate | Required DBSCTR2 checkpoint in DVC repos that keeps tracked outputs, DVC metadata, and phase commits aligned. |
| Artifact Freshness | Requirement that existing specs, backlogs, changelogs, docs, contracts, and tests remain aligned with behavior changes. |
| Thin Command | Slash command that only loads the matching skill and passes `$ARGUMENTS`; source of truth remains in the skill. |
| OpenCode Routing | Managed `AGENTS.md` guidance that selects `dbsctr2` and `discovery2` in OpenCode sessions. |
| Ponytail Principle | Hard rule to avoid work, reuse existing artifacts/code, and make the minimum correct change. |
| Provider Family | OpenAI, Amazon Bedrock, or the provider of an arbitrarily selected model. Delegation must remain inside it. |
| Provider-Local Agent | Specialized subagent whose configured model belongs to the Build agent's provider family. |
| Plan | Startup primary using GPT-5.6 Sol medium with native read-only planning behavior; `Plan-GPT-Pro` is an optional quality-first planner. |
| Build Agent | `Build-GPT`, `Build-GPT-Pro`, or `Build-Claude`, selected explicitly for implementation. |
| Optimized Subagent | Lower-cost Explore, Scout, or Builder selected for a bounded task instead of the flagship. |
| Flagship Review | Parent review of delegated code before integration, final validation, staging, or commit. |
| Same-Provider Fallback | One visible retry with the provider's flagship after an optimized subagent fails. |
| Phase Ledger | Six OpenCode todos tracking Domain, Behavior, Spec, Contract, Test, and Refactor. |
| Build Handoff | Structured read-only Plan output that Build verifies before persisting artifacts or implementation. |

## External Interfaces

| Interface | Purpose |
|---|---|
| `dot_agents/skills/dbsctr2/SKILL.md` | Source skill for DBSCTR2. |
| `dot_agents/skills/dbsctr2/modules/data.md` | DBSCTR2 data engineering module. |
| `dot_agents/skills/dbsctr2/modules/cloud.md` | DBSCTR2 cloud/platform/IaC module. |
| `dot_agents/skills/dbsctr2/modules/ml.md` | DBSCTR2 ML/AI module. |
| `dot_agents/skills/dbsctr2/modules/analytics_references.md` | DBSCTR2 analytics reference scaffolding module. |
| `dot_agents/skills/discovery2/SKILL.md` | Source skill for Discovery2. |
| `dot_agents/skills/qa/SKILL.md` | Source skill for scoped quality gates and full audits. |
| `private_dot_config/opencode/commands/dbsctr2.md` | Global `/dbsctr2` command. |
| `private_dot_config/opencode/commands/discovery2.md` | Global `/discovery2` command. |
| `private_dot_config/opencode/commands/qa.md` | Global `/qa` command. |
| `private_dot_config/opencode/AGENTS.md` | OpenCode-native routing instructions. |
| `private_dot_config/opencode/opencode.json.tmpl` | Global OpenCode config, including Ponytail plugin. |
| `private_dot_config/opencode/agents/*.md` | Provider-local primary and subagent definitions when file-based prompts are needed. |

## Prompt-Guidance Inputs

V2 skill prompts use outcome-first structure, success criteria, constraints,
output contracts, retrieval budgets, stop rules, and validation checks. They
avoid legacy process-heavy prompt stacks except for true invariants such as
phase order, artifact freshness, safety, and commit ownership.

## Routing Domain Rules

- OpenCode should route DBSCTR-required work to `dbsctr2` by default.
- If DBSCTR2 starts and no matching spec exists, it should auto-run Discovery2.
- Tiny unrelated edits do not require DBSCTR2 unless the user invokes it.
- If an edit changes behavior or existing artifacts, matching docs/specs/tests
  must be updated to avoid stale artifacts.
- DBSCTR2 loads applicable v2 domain modules before Phase 1 Domain.
- Explicit `/dbsctr` and `/discovery` continue to load v1 skills.
- GPT and Bedrock flagship workflows use selectable OpenCode primary agents;
  OpenAI is the startup default and arbitrary providers use generic inheriting
  agents.
- Provider-local subagents are available globally; DBSCTR2 adds ownership,
  evidence, fallback, and phase-gate requirements.

## Contracts & Invariants

### OpenCode Routing Contract
- **Pre:** OpenCode reads managed `~/.config/opencode/AGENTS.md`.
- **Pre:** V1 skills remain installed and unchanged.
- **Post:** DBSCTR-required work routes to `dbsctr2` by default.
- **Post:** Explicit `/dbsctr` and `/discovery` still load v1.
- **Invariant:** `~/.claude/CLAUDE.md` is not modified by this v2 rollout.

### Discovery2 Confidence Contract
- **Pre:** Discovery2 has a bounded context or asks until it can name one.
- **Post:** Final artifacts are written only after at least 95% confidence, unless
  the user explicitly asks for a draft.
- **Invariant:** Requirements distinguish facts, assumptions, non-goals, and
  open risks.

### DBSCTR2 Phase Contract
- **Pre:** DBSCTR2 is loaded by routing or explicit command.
- **Pre:** Foundational domain work is checked against `dbsctr2/modules/`.
- **Post:** Domain, Behavior, Spec, Contract, Test, and Refactor are executed or
  verified in order.
- **Post:** Applicable module extensions are applied in the matching phase.
- **Invariant:** Known stale artifacts make the cycle incomplete.

### DBSCTR2 Module Contract
- **Pre:** A task touches data engineering, analytics reference scaffolding,
  cloud/platform/IaC, or ML/AI work.
- **Post:** DBSCTR2 reads the matching module file from
  `dot_agents/skills/dbsctr2/modules/` before Phase 1 Domain.
- **Invariant:** V2 module guidance must not depend on v1 `dbsctr` paths.

### QA Gate Contract
- **Pre:** DBSCTR2 supplies touched files, dependencies, tests, specs, contracts,
  manifests, and direct downstream impact as compact affected scope.
- **Post:** QA runs relevant project-configured checks and records evidence.
- **Post:** Unrelated pre-existing findings do not fail or broaden the cycle.
- **Invariant:** Behavior, contract, schema, orchestration, or downstream-visible
  remediation remains in or escalates to DBSCTR2.

### QA Audit Contract
- **Pre:** `/qa` is explicitly invoked for a repository-wide audit.
- **Post:** Configured findings, including Dependabot alerts when available, are
  normalized, deduplicated, prioritized, and grouped into safe fix batches.
- **Invariant:** One project-selected authority gates each concern.
- **Invariant:** Risky or behavior-changing fixes are planned before editing.

### DVC Sync Contract
- **Pre:** A DBSCTR2 cycle runs in a repo containing `.dvc/`, `*.dvc`,
  `dvc.yaml`, or `dvc.lock`.
- **Post:** Phase commits that changed DVC-tracked outputs include the matching
  `.dvc` metadata or `dvc.lock` changes in the same Git commit.
- **Post:** When DBSCTR2 is asked to push Git refs, `dvc push` succeeds before
  `git push` runs.
- **Invariant:** `graphify-out/graph.json.dvc`, when present, is a normal DVC
  artifact.
- **Invariant:** Unrelated pre-existing DVC drift is reported and excluded unless
  the user includes it.

### Subagent Ownership Contract
- **Pre:** A write subagent has explicit owned write files, read files,
  off-limits files, validation, dependencies, and collision risks.
- **Post:** The Orchestrator reviews, validates, stages, and commits.
- **Invariant:** Subagents never commit.

### Provider-Affine Routing Contract
- **Pre:** The active primary is `Plan`, `Plan-GPT-Pro`, `Build-GPT`,
  `Build-GPT-Pro`, `Build-Claude`, or a generic primary with
  an arbitrarily selected model.
- **Post:** OpenAI Pro primaries use GPT-5.6 Sol Pro at medium effort and may
  delegate only to OpenAI-specialized agents; `Build-GPT` follows the same
  provider boundary;
  `Build-Claude` may delegate only to Amazon Bedrock-specialized agents.
- **Post:** Generic Explore, Scout, and General agents inherit the active model
  for other providers.
- **Invariant:** Delegation never crosses provider families silently.
- **Invariant:** `Plan` on OpenAI is the startup default; unavailable Bedrock access does
  not prevent OpenCode startup.
- **Invariant:** The unused OpenCode Zen `opus` primary and native `Build` agent
  are not selectable.

### Optimized Agent Contract
- **Pre:** Delegation has a clear scope, independent value, and expected output.
- **Post:** OpenAI Explore uses GPT-5.6 Terra at low effort; OpenAI Scout and
  Builder use GPT-5.6 Terra at medium effort.
- **Post:** Bedrock Explore, Scout, and Builder use Claude Sonnet 5 at medium
  effort; Bedrock Opus remains the parent orchestrator.
- **Post:** Explore and Scout are read-only and return concise source-backed
  evidence. Their output is trusted unless uncertain, contradictory, or directly
  controlling a risky edit.
- **Post:** Builders edit only owned files, run focused checks, and return the
  patch scope and evidence for Flagship Review.
- **Invariant:** Builders never stage, commit, push, deploy, perform external
  writes, expand scope, or declare lifecycle gates complete.

### Fallback And Visibility Contract
- **Pre:** An optimized provider-local subagent launch fails or its model is
  unavailable.
- **Post:** The Orchestrator reports the intended agent and model, failure,
  same-provider flagship retry, and outcome.
- **Post:** One same-provider flagship retry occurs automatically before direct
  continuation or a blocker is reported.
- **Invariant:** Normal delegation emits a concise routing log; fallback is never
  silent and never crosses providers.

### OpenCode Session Contract
- **Pre:** DBSCTR2 begins a non-trivial lifecycle.
- **Post:** A six-item Phase Ledger has exactly one active phase until all gates
  complete.
- **Post:** Plan mode produces a Build Handoff without claiming writes occurred;
  Build verifies freshness before using it.
- **Post:** Child sessions report question, inspected sources, findings, facts
  versus assumptions, validation, blockers, uncertainty, and changed files.
- **Invariant:** OpenCode snapshots and session diffs support recovery but Git
  remains authoritative for integration and commits.

### OpenCode Config Contract
- **Pre:** `opencode.json.tmpl` preserves `$schema` and existing config.
- **Post:** Ponytail is listed in the global `plugin` array.
- **Post:** Sol, Terra, Bedrock Opus, and Bedrock Sonnet expose explicit
  configured variants used by their agents.
- **Invariant:** Slash command bodies are thin wrappers and skill files remain
  workflow source of truth.

## Verification Evidence

2026-06-25 checks:
- `jq empty private_dot_config/opencode/opencode.json.tmpl` passed.
- Targeted `chezmoi apply` deployed v2 skills, commands, `AGENTS.md`, and
  `opencode.json`.
- Target file existence and `jq empty ~/.config/opencode/opencode.json` passed.
- Deployed skill and command headers were read from target paths.
- `chezmoi status` returned clean output after targeted apply.

2026-06-26 checks:
- Targeted `chezmoi apply` deployed `dependabot`, updated `dbsctr2`, updated
  `/dependabot`, and updated OpenCode routing.
- Deployed target checks found the Dependabot workflow, DBSCTR2 Dependabot Gate,
  thin command wrapper, and routing rule.
- `chezmoi status` returned clean output after targeted apply.

2026-07-03 checks:
- Targeted `chezmoi apply ~/.agents/skills/dbsctr2` deployed the updated DBSCTR2
  skill and v2 module directory.
- Deployed target checks found `data.md`, `cloud.md`, `ml.md`, and
  `analytics_references.md` under `~/.agents/skills/dbsctr2/modules/`.
- Deployed DBSCTR2 skill text contains the Domain Modules routing table and
  Phase 1 module loading action.

2026-07-10 provider-affine checks:
- `opencode models` and a temporary native Bedrock provider configuration
  confirmed the OpenAI Sol/Luna/Terra and Bedrock Opus 4.8/Sonnet 5 identifiers.
- `jq empty`, `git diff --check`, `chezmoi apply --dry-run --verbose`, targeted
  `chezmoi apply`, and `opencode debug config` passed.
- Rendered assertions confirmed startup defaults, provider-local task
  permissions, Builder command denials, and generic model inheritance.
- A live `opus-bedrock` to `explore-bedrock` route returned the expected source
  value. `gpt` launched `explore-openai` twice, but the child did not return
  before timeout/abort; configuration and permission checks still passed.
- `chezmoi status` returned clean output after deployment.
- Follow-up resolved-config assertions confirmed native `Plan` as default,
  disabled native `Build`, exact `Build-GPT` and `Build-Claude` names, removal of
  legacy primaries, case-sensitive command targets, and explicit provider
  variants for all configured OpenAI and Bedrock agents.
- Bedrock `medium` uses adaptive reasoning with `maxReasoningEffort: medium` and
  summarized display, matching OpenCode's runtime model metadata.

## Behavior Scenarios

### Feature: OpenCode Routing

**Scenario: Route DBSCTR-required work to DBSCTR2**
- Given an OpenCode session with managed routing instructions
- And a user asks for a change that introduces user-observable behavior,
  service logic, data schema, orchestration, validation, or domain constraints
- When the Orchestrator classifies the task
- Then it loads `dbsctr2` by default
- And it does not load v1 `dbsctr` unless the user explicitly invokes `/dbsctr`

**Scenario: Skip DBSCTR2 for tiny unrelated edits**
- Given an OpenCode session with managed routing instructions
- And a user asks for a formatting, config-only, git-only, or trivial edit that
  does not affect behavior or artifacts
- When the Orchestrator classifies the task
- Then it may proceed without DBSCTR2
- And it must still update existing artifacts if the edit changes documented behavior

**Scenario: Preserve v1 explicit commands**
- Given the v1 skills remain installed
- When the user invokes `/dbsctr` or `/discovery`
- Then OpenCode loads the v1 skill requested by the user
- And the v2 routing guidance does not rename, delete, or deprecate v1

### Feature: Discovery2 Intent Extraction

**Scenario: Auto-run Discovery2 when DBSCTR2 has no spec**
- Given DBSCTR2 starts for a bounded context
- And no matching spec exists in `docs/specs/`
- When the Orchestrator reaches the spec check
- Then it loads `discovery2` automatically
- And it interviews until it has at least 95% confidence in the user's actual intent

**Scenario: Produce DBSCTR2-ready artifacts**
- Given Discovery2 reaches at least 95% confidence
- When it writes output artifacts
- Then it creates or updates `README.md`, `BACKLOG.md`, and `CHANGELOG.md`
- And the backlog includes dependencies, ownership boundaries, read/write scopes,
  parallel-safety, validation, and reason for each task

### Feature: Strict DBSCTR2 Execution

**Scenario: Load applicable DBSCTR2 domain modules**
- Given DBSCTR2 is loaded for foundational domain work
- And the task matches data engineering, analytics reference scaffolding,
  cloud/platform/IaC, or ML/AI signals
- When the Orchestrator starts Phase 1 Domain
- Then it reads the matching module from `dot_agents/skills/dbsctr2/modules/`
- And it applies the module's phase extensions or explicitly rules them out

**Scenario: Execute all DBSCTR2 phases when selected**
- Given DBSCTR2 is loaded by routing or explicit command
- When implementation work begins
- Then the Orchestrator executes Domain, Behavior, Spec, Contract, Test, and Refactor in order
- And it does not skip a phase
- And it may combine tiny adjacent phase commits only when the artifacts remain clear

**Scenario: Prevent stale artifacts**
- Given existing specs, backlogs, changelogs, docs, contracts, or tests describe the changed area
- When DBSCTR2 changes behavior or implementation details represented by those artifacts
- Then it updates the affected artifacts in the matching phase
- And it treats stale artifacts as an incomplete cycle

**Scenario: Commit phase gates**
- Given a DBSCTR2 phase produces file changes
- When the phase gate passes
- Then the Orchestrator stages only intended files
- And commits with the phase prefix format
- And subagents never commit

**Scenario: Gate affected scope with QA**
- Given DBSCTR2 has touched code, dependencies, tests, or artifacts
- When the Orchestrator reaches a phase gate
- Then it delegates compact affected scope to `qa`
- And QA runs only relevant project-configured checks

**Scenario: Ignore unrelated quality noise**
- Given configured tools report findings outside the affected scope
- When QA returns phase-gate evidence
- Then unrelated findings do not fail or broaden the DBSCTR2 cycle
- And an explicit full QA audit remains available to inventory that debt

**Scenario: Sync DVC metadata with phase commits**
- Given DBSCTR2 runs in a repo with `.dvc/`, `*.dvc`, `dvc.yaml`, or `dvc.lock`
- And the phase changed DVC-tracked outputs
- When the Orchestrator reaches the phase commit gate
- Then it runs `dvc status`
- And updates matching DVC metadata for outputs changed by the phase
- And includes that metadata in the same Git commit as the code or docs that
  produced the output

**Scenario: Push DVC data before Git refs**
- Given DBSCTR2 is asked to push from a DVC repo
- When the Orchestrator prepares to push Git refs
- Then it runs `dvc push` first
- And it stops before `git push` if DVC data upload fails

### Feature: Concurrent Backlog and Subagents

**Scenario: Assign write subagents safely**
- Given DBSCTR2 has independent tasks or files
- When the Orchestrator delegates work to write subagents
- Then each delegated task has an Ownership Contract
- And no two write subagents write the same file unless explicitly serialized
- And the Orchestrator reviews, integrates, validates, and commits the result

**Scenario: Avoid subagents for local work**
- Given the Orchestrator can complete a small edit directly in one response
- When subagent overhead would exceed benefit
- Then it performs the work directly
- And it records no subagent requirement

### Feature: Provider-Affine OpenCode Agents

**Scenario: Start in native Plan**
- Given OpenCode starts without an explicit agent
- When the initial session opens
- Then native `Plan` is active on GPT-5.6 Sol at medium effort
- And implementation requires selecting `Build-GPT`, `Build-GPT-Pro`, or
  `Build-Claude`

**Scenario: Select quality-first OpenAI planning or implementation**
- Given difficult or high-risk work may benefit from additional model work
- When the user selects `Plan-GPT-Pro` or `Build-GPT-Pro`
- Then GPT-5.6 Sol runs in Pro mode at medium effort
- And the normal Plan and `Build-GPT` agents remain the defaults for routine work

**Scenario: Use optimized OpenAI agents**
- Given the `Build-GPT` primary runs GPT-5.6 Sol at medium effort
- When local research, external research, or bounded coding clearly benefits
  from delegation
- Then it invokes GPT-5.6 Terra Explore, Scout, or Builder at the configured
  effort
- And it does not invoke an Amazon Bedrock agent

**Scenario: Use optimized Bedrock agents**
- Given the `Build-Claude` primary runs Claude Opus through Amazon Bedrock
- When local research, external research, or bounded coding clearly benefits
  from delegation
- Then it invokes the matching Claude Sonnet 5 agent at medium effort
- And it does not invoke an OpenAI agent

**Scenario: Preserve arbitrary-provider behavior**
- Given the user selects a model outside the configured OpenAI and Bedrock
  primary workflows
- When the primary delegates work
- Then generic subagents inherit the active model
- And no provider-specific optimized agent is selected automatically

**Scenario: Review delegated code with the flagship**
- Given an optimized Builder changed explicitly owned files
- When the child session returns
- Then the flagship parent reviews the complete patch and integration impact
- And the parent owns final affected-scope validation, staging, and commits

**Scenario: Trust bounded research without duplicating it**
- Given Explore or Scout returns source-backed findings without uncertainty or
  contradiction
- When the parent consumes the result
- Then it does not repeat the full investigation
- And it checks only claims that directly control a risky edit or conflict with
  authoritative context

**Scenario: Report same-provider fallback**
- Given an optimized subagent fails to launch or its model is unavailable
- When the parent recovers
- Then it logs the failed agent and model and retries once with the same-provider
  flagship
- And it reports the retry outcome without crossing providers

### Feature: OpenCode-Native Lifecycle State

**Scenario: Track DBSCTR2 phases in todos**
- Given DBSCTR2 starts non-trivial work
- When lifecycle execution begins
- Then it creates Domain, Behavior, Spec, Contract, Test, and Refactor todos
- And exactly one phase is active until all required gates complete

**Scenario: Hand Plan work to Build**
- Given the active primary cannot write
- When planning reaches an implementation-ready result
- Then it returns a structured Build Handoff with decisions, interfaces, scope,
  contracts, validation, risks, and unresolved questions
- And Build verifies source and artifact freshness before persisting changes

### Feature: Ponytail Minimalism

**Scenario: Reuse before building**
- Given DBSCTR2 or Discovery2 considers a new artifact, abstraction, or implementation path
- When existing code, specs, native platform features, standard library, or installed dependencies can solve the problem
- Then the Orchestrator chooses the lowest sufficient rung
- And it does not cut validation, security, data-loss handling, accessibility, or tests

### Feature: Thin Commands

**Scenario: Execute thin wrapper command**
- Given the global `/dbsctr2`, `/discovery2`, or `/qa` command is invoked
- When OpenCode expands the command
- Then the command only instructs the agent to load the matching skill and execute it against `$ARGUMENTS`
- And all workflow source of truth remains in the skill file

### Feature: Quality Assurance

**Scenario: Run a full repository audit**
- Given the user explicitly invokes `/qa` for a full audit
- When configured checks and alert sources complete
- Then QA deduplicates findings and proposes collision-safe fix batches
- And deterministic safe fixes are validated before completion

**Scenario: Escalate behavior-changing remediation**
- Given a QA finding requires behavior, contract, schema, or orchestration changes
- When QA classifies the fix
- Then it returns the affected scope to DBSCTR2
- And it does not silently apply the change as quality cleanup
