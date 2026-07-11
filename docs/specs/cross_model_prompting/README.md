# Cross-Model Prompting

## Overview

OpenCode's managed routing and V2 skills must work predictably with both
GPT-5.6 and Claude Opus 4.8. The current prompts are correct but repeat several
rules, increasing context cost and making literal instruction conflicts harder
to detect.

Discovery2 confidence: 97%.

## Goals

- Keep one lean, model-neutral instruction core.
- Preserve DBSCTR2, Discovery2, and QA behavior while removing repetition.
- Use OpenCode model variants for model-specific effort defaults.
- Make autonomy, approval, evidence, delegation, and output boundaries explicit.
- Deploy all managed changes, including pending OpenAI timeouts, with chezmoi.

## Non-Goals

- Changing V1 `dbsctr` or `discovery`.
- Maintaining separate GPT and Opus copies of each skill.
- Optimizing for Sonnet, Kimi, or local models in this cycle.
- Adding an evaluation framework or provider plugin.

## Ubiquitous Language

- **Shared core:** model-neutral routing and workflow instructions.
- **Adapter:** an OpenCode primary agent selecting a model and effort variant.
- **Approval boundary:** action requiring confirmation because it is external,
  destructive, costly, or materially expands scope.
- **Evidence:** commands, source references, or findings supporting an outcome.
- **Finding pass:** high-recall issue collection before verification and ranking.

## Behavior

### Shared execution

Given either GPT-5.6 or Opus 4.8 is selected, when a managed V2 workflow runs,
then it follows the same goals, gates, safety boundaries, and output contract.

### Safe autonomy

Given the user requests a local change, when execution is non-destructive and
in scope, then the agent edits and validates without unnecessary approval.

Given an action is external, destructive, costly, or materially expands scope,
when the agent reaches that action, then it asks for confirmation first.

### Delegation

Given independent workstreams with non-overlapping ownership, when delegation
reduces time or risk, then the orchestrator starts them concurrently and retains
integration and commit ownership.

Given work is small or coupled, when delegation adds overhead or collision risk,
then the orchestrator completes it directly.

### QA recall

Given a review or audit, when findings are collected, then QA captures all
behavioral or validation issues before separately verifying, deduplicating,
ranking, and gating them.

### Deployment

Given source prompts and OpenCode configuration change, when validation passes,
then chezmoi applies them and deployed targets match source.

## Interfaces

- `private_dot_config/opencode/AGENTS.md`: global routing and cross-cutting policy.
- `dot_agents/skills/dbsctr2/SKILL.md`: strict implementation lifecycle.
- `dot_agents/skills/discovery2/SKILL.md`: intent discovery lifecycle.
- `dot_agents/skills/qa/SKILL.md`: scoped gates and full audits.
- `private_dot_config/opencode/opencode.json.tmpl`: model adapters and timeouts.
- V1 skill files remain byte-for-byte unchanged.

## Contracts

- State each normative rule once in its narrowest authoritative layer.
- Prefer positive outcome instructions; retain prohibitions only for safety or a
  demonstrated failure mode.
- Prompt text controls outcomes and boundaries; model variants control effort.
- `gpt` uses `openai/gpt-5.6` at `medium`; `opus` uses
  `opencode/claude-opus-4-8` at `xhigh`.
- Shared workflow skills must not contain provider-specific branching.
- Existing user changes in `opencode.json.tmpl` are preserved and deployed.

## Validation

- Parse rendered OpenCode JSON and validate it against the current schema.
- Confirm available model identifiers with `opencode models`.
- Compare prompt size and repeated normative phrases before and after.
- Run static scenario checks for autonomy, approval, delegation, QA recall, V1
  permanence, and deployment requirements.
- Run `chezmoi apply --dry-run --verbose`, targeted `chezmoi apply`, and
  `chezmoi status`.

## Risks

- Prompt reduction can accidentally weaken a gate; scenario and diff review
  mitigate this.
- OpenCode/provider variant semantics may evolve; schema validation confirms
  shape, while model behavior still requires representative use over time.
