# Quality Assurance Skill

> **Ownership note (2026-07-13):** Active QA skill and OpenCode command source
> moved to `Saltiola7/dotfiles-ai`. Source paths below are historical unless
> explicitly described as deployed target paths.

**Status:** Experimental
**Created:** 2026-07-10
**Last updated:** 2026-07-10

## Overview

The `quality_assurance` bounded context defines one global `qa` skill for
repository-aware quality and security checks. It replaces the standalone
Dependabot workflow, provides a touched-scope DBSCTR gate, supports optional V3
Engineering Profile capability coverage, and retains an explicit full-repository
cleanup mode.

The skill discovers the repository's existing toolchain instead of imposing a
universal stack. It deduplicates findings across tools, ignores unrelated
pre-existing noise during scoped work, applies deterministic safe fixes, and
plans risky fixes before editing.

Initial Discovery2 confidence: **97%**. DBSCTR V3 capability extension approved
at 97% confidence on 2026-07-11.

## Problem Statement

Quality checks currently live across DBSCTR, Dependabot, project CI, task
runners, and project-specific instructions. Coding agents can miss configured
checks, run overlapping scanners, expand scope into unrelated debt, or treat a
passing but broadly suppressed tool such as mypy as complete evidence.

## Goals

- Add one global `qa` skill and thin `/qa` command.
- Replace standalone Dependabot routing and skill ownership with QA.
- Make QA a scoped DBSCTR gate for touched code and dependencies.
- Compare V3 Capability Requirements with available authorities and expose gaps.
- Keep explicit QA audits capable of inventorying and reducing repo-wide debt.
- Discover and use project-configured lint, typing, testing, coverage, security,
  dependency, dead-code, complexity, documentation, mutation, and packaging
  tools.
- Prefer one authority per concern and avoid duplicate gates.
- Manage the project-specific `seo-data-science/AGENTS.md` through chezmoi
  without repeating global instructions.
- Produce a project handoff spec for later `seo-data-science` toolchain work.

## Non-Goals

- Do not configure the `seo-data-science` Python toolchain in this cycle.
- Do not fix project-specific mypy debt in this cycle.
- Do not retain `/dependabot` or a standalone `dependabot` skill.
- Do not deploy archived V2 lifecycle skills or reintroduce versioned commands.
- Do not require every supported QA tool in every repository.
- Do not auto-delete suspected dead code or auto-apply risky security,
  dependency, mutation, or complexity changes.

## Architecture

```text
User or DBSCTR
  -> qa
    -> discover project instructions and configured tools
    -> select scoped gate or full audit
    -> run independent checks concurrently when safe
    -> normalize and deduplicate findings
    -> apply safe fixes or propose fix batches
    -> validate affected scope
```

## Domain

### Bounded Context

`quality_assurance` owns quality-tool discovery, check selection, finding
normalization, scoped gating, full audits, and safe-fix orchestration.

Adjacent contexts:

- `dbsctr`: delegates touched-scope quality gates and receives results.
- `discovery`: records Engineering Profile requirements, available validation,
  and repository constraints.
- `opencode_routing`: loads QA for explicit requests and DBSCTR gates.
- `project_toolchain`: repository-owned configuration remains authoritative.
- `supply_chain_security`: JFrog Xray, pip-audit, and GitHub Dependabot alerts
  are alternative or complementary inputs selected by repository policy.

### Entities

- **QA Run**: one scoped gate or full audit with selected checks and evidence.
- **QA Check**: one configured tool invocation for a quality concern.
- **Finding**: normalized issue with source, location, category, severity, and
  remediation state.
- **Fix Batch**: collision-safe set of related findings and validation commands.
- **Toolchain Profile**: discovered project tools, commands, baselines, and
  authorities.
- **Quality Baseline**: accepted pre-existing findings excluded from a scoped
  gate but visible in a full audit.

### Value Objects

- **Run Mode**: `scoped` or `full`.
- **Affected Scope**: touched files, imports, manifests, packages, tests, specs,
  and downstream contracts.
- **Fix Safety**: `safe`, `review_required`, or `escalate_dbsctr`.
- **Capability Status**: `evidenced`, `missing`, `unavailable`, `failed`,
  `deferred`, or `accepted_risk`.
- **Vulnerability Authority**: project-selected scanner such as JFrog Xray or
  pip-audit.
- **Validation Evidence**: command, result, scope, and residual risk.

### Domain Events

- `ToolchainDiscovered`
- `ScopedGateRequested`
- `FullAuditRequested`
- `FindingNormalized`
- `FindingSuppressedAsUnrelated`
- `SafeFixApplied`
- `FixBatchProposed`
- `BehaviorChangeEscalated`
- `QACompleted`

### Ubiquitous Language

| Term | Definition |
|---|---|
| Scoped Gate | QA run limited to touched behavior and directly affected code, dependencies, tests, and contracts. |
| Full Audit | Explicit periodic repository-wide inventory and debt-reduction run. |
| Unrelated Noise | Existing finding outside the Affected Scope; reported only in full mode. |
| Safe Fix | Deterministic change such as formatter or unambiguous linter output with focused validation. |
| Risky Fix | Dependency, dead-code, security, mutation, complexity, or broad typing change requiring a plan or DBSCTR. |
| Capability Gap | Applicable Engineering Profile requirement with no authority or equivalent evidence. |
| Concern Authority | Single preferred tool or service whose result gates a concern. |

## Behavior Scenarios

### Feature: Repository Toolchain Discovery

**Scenario: Use configured project tools**
- Given a repository defines quality commands in project instructions, manifests,
  CI, or task runners
- When QA starts
- Then it builds a Toolchain Profile from those sources
- And it does not install an unconfigured tool merely because QA supports it

**Scenario: Tool is unavailable**
- Given a configured QA Check cannot run in the current environment
- When QA executes it
- Then QA records the blocker and next-best validation
- And it does not claim the concern passed

### Feature: DBSCTR Scoped Gate

**Scenario: Gate only affected scope**
- Given DBSCTR supplies an Affected Scope and optional Engineering Profile
- When QA runs in scoped mode
- Then it selects checks relevant to that scope
- And unrelated pre-existing findings do not fail the DBSCTR cycle

**Scenario: Scoped finding requires behavior change**
- Given a finding cannot be fixed without changing behavior, contracts, schemas,
  or downstream-visible output
- When QA classifies the Fix Safety
- Then it escalates the fix to DBSCTR
- And it does not silently broaden the QA batch

### Feature: Full Quality Audit

**Scenario: Inventory repository debt**
- Given the user explicitly invokes `/qa` for a full audit
- When configured checks complete
- Then QA normalizes and deduplicates all findings
- And it ranks collision-safe Fix Batches before editing

**Scenario: Apply deterministic fixes**
- Given a Fix Batch contains only Safe Fix findings
- When QA applies the batch
- Then it runs focused validation
- And it reports the changed files and residual findings

**Scenario: Plan risky fixes**
- Given findings involve dependency changes, suspected dead code, custom security
  policy, mutation survivors, complexity redesign, or broad typing changes
- When QA creates Fix Batches
- Then it proposes the risky batch before editing
- And behavior-changing work is handed to DBSCTR

### Feature: Capability Coverage

**Scenario: Expose missing required evidence**
- Given the Engineering Profile marks a Capability Requirement applicable
- And no configured authority or project-approved evidence covers it
- When QA evaluates affected scope
- Then QA records a Capability Gap rather than a pass
- And lifecycle completion requires remediation, deferral, or accepted risk

**Scenario: Preserve calls without an Engineering Profile**
- Given QA is called without V3 Capability Requirements
- When configured checks run
- Then QA retains its configured-tool scoped or full behavior
- And it does not invent additional project policy

### Feature: Vulnerability Authority

**Scenario: Prefer project-declared Xray**
- Given project artifacts declare JFrog Xray as the vulnerability authority
- When QA evaluates dependencies or images
- Then it uses configured `jf` audit or scan commands
- And it does not add pip-audit as a competing gate

**Scenario: Use pip-audit fallback**
- Given no project vulnerability authority exists and pip-audit is configured
- When QA evaluates Python dependencies
- Then it audits the resolved or locked dependency set
- And GitHub Dependabot alerts remain finding inputs rather than a separate skill

### Feature: Concurrent Checks

**Scenario: Fan out independent checks**
- Given selected QA Checks have non-overlapping write ownership
- When concurrency reduces runtime or context
- Then the orchestrator delegates them with explicit ownership contracts
- And the orchestrator alone integrates, validates, stages, and commits

## Interfaces

| Interface | Purpose | Behaviors |
|---|---|---|
| `dot_agents/skills/qa/SKILL.md` | QA orchestration source of truth | All QA features |
| `private_dot_config/opencode/commands/qa.md` | Thin `/qa` command | Full audit and explicit scoped runs |
| `dot_agents/skills/dbsctr/SKILL.md` | Delegates scope and Capability Requirements | DBSCTR Scoped Gate |
| `dot_agents/skills/discovery/SKILL.md` | Captures Engineering Profile and Toolchain Profile inputs | Repository Toolchain Discovery |
| `private_dot_config/opencode/AGENTS.md` | Global skill routing and team standards | Toolchain discovery and scoped QA |
| `MGM/git/seo-data-science/AGENTS.md` | Chezmoi source for project adaptations | Project-specific routing only |
| `seo-data-science/docs/specs/toolchain/**` | Project implementation handoff | Tool evaluation and later rollout |

## Contracts & Invariants

- Project instructions and configured commands are authoritative for tool usage.
- QA must not fail a scoped gate for unrelated pre-existing findings.
- Full audit findings remain visible even when baselined.
- One Concern Authority gates each concern; overlapping tools may provide context
  but must not produce contradictory equal gates.
- QA must classify fixes before editing.
- Suspected dead code requires source verification before deletion.
- Safe fixes require focused validation.
- Behavior-changing fixes return to DBSCTR.
- Missing, unavailable, or failed required Capability Requirements prevent a
  scoped pass unless validly deferred or accepted as risk.
- Subagents never commit.
- Slash commands remain thin; skill files are workflow source of truth.
- Global and project `AGENTS.md` files must not duplicate the same standards.

## Validation Strategy

```bash
python -m json.tool private_dot_config/opencode/opencode.json.tmpl
chezmoi execute-template < private_dot_config/opencode/opencode.json.tmpl | python -m json.tool
chezmoi apply --dry-run --verbose
```

Validate deployed skill and command discovery after targeted `chezmoi apply`.
Restart OpenCode, then smoke-test `explore` subagent launch and `/qa` loading.

## Facts, Assumptions, And Risks

Facts:
- `seo-data-science` already uses Ruff, mypy, pytest, coverage, Hypothesis,
  pre-commit, uv, and Dependabot configuration.
- Its current mypy command passes while multiple modules use `ignore_errors`.
- JFrog Xray is specified as a future sole vulnerability authority.
- Current OpenCode `explore` delegation fails because its configured model ID is
  rejected.

Assumptions:
- OpenCode will reload global config and skills after restart.
- Chezmoi may manage a file inside an independently tracked Git repository.

Risks:
- Full audits can produce noisy findings; baseline and diff scoping are required.
- Chezmoi and project git can drift for the managed project `AGENTS.md`; drift is
  reconciled manually.
- Scanner overlap can create conflicting severity or exception policy unless the
  Concern Authority rule is enforced.
