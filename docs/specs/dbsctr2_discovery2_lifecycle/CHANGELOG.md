# Changelog — DBSCTR2 and Discovery2 Lifecycle

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
