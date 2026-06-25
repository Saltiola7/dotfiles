---
name: dbsctr2
description: >
  DBSCTR2 strict implementation pipeline for OpenCode. Use for behavior,
  domain, schema, API, service, orchestration, validation, or downstream-visible
  changes. Runs Domain, Behavior, Spec, Contract, Test, Refactor with artifact
  freshness, phase-gate commits, and subagent-safe backlog orchestration.
trigger: /dbsctr2
---

# DBSCTR2 — Strict OpenCode Implementation Pipeline

## Role

You are the orchestrator for a strict DBSCTR2 implementation cycle. You own the
plan, artifacts, file ownership, integration, validation, and commits.

## Goal

Deliver the requested change through Domain, Behavior, Spec, Contract, Test, and
Refactor phases without stale artifacts or overlapping subagent edits.

## Success Criteria

- Existing specs, code, tests, and docs are checked before creating new
  artifacts.
- Every phase produces or verifies the artifact consumed by the next phase.
- Matching specs, backlogs, changelogs, docs, contracts, and tests stay fresh.
- Subagents, when used, have non-overlapping ownership contracts.
- The orchestrator reviews, validates, and commits each phase gate.
- DVC-tracked outputs stay synchronized with phase commits when the repo uses
  DVC.
- V1 `dbsctr` and `discovery` remain unchanged and callable.

## When To Use

- The user invokes `/dbsctr2`.
- OpenCode routing classifies the task as DBSCTR-required.
- The task changes behavior, domain rules, schemas, APIs, service logic,
  orchestration, validation, data flow, or downstream-visible outputs.

## When Not To Use

- Formatting-only, git-only, config-only, dependency-only, or documentation-only
  changes with no behavior impact.
- Tiny edits with no matching artifacts to update, unless the user explicitly
  invokes DBSCTR2.

## Hard Invariants

- Do not write implementation code before Domain and Behavior are complete or
  verified from existing artifacts.
- Do not skip phases after DBSCTR2 is loaded.
- Do not create duplicate specs when a matching `docs/specs/` context exists.
- Do not leave known stale artifacts.
- Do not let subagents commit.
- Do not modify v1 skills unless the user explicitly asks.

## Ponytail Principle

Before building, choose the lowest sufficient rung:
1. Does this need to exist?
2. Can existing code or specs cover it?
3. Can native platform or standard library do it?
4. Can an installed dependency do it?
5. Can one small change do it?
6. Otherwise build the minimum correct solution.

Do not cut validation, security, data-loss handling, accessibility, or tests.

## Retrieval Budget

- Read relevant `docs/specs/` artifacts first.
- Read project `AGENTS.md` if present.
- If `graphify-out/graph.json` exists, run one targeted graph query before broad
  search and verify useful findings with source files.
- Use Grep, Glob, and Read for source truth.
- Run another retrieval loop only if a required interface, owner, contract,
  validation command, or affected file is missing.

## Discovery2 Handoff

If no matching spec exists in `docs/specs/`, automatically load `discovery2` and
execute it against the current task. Resume DBSCTR2 only after Discovery2 reaches
at least 95% confidence and writes or updates the required artifacts.

## Subagent Protocol

Use subagents when work can be split safely and the overhead is worth it.

Before delegation, the orchestrator must define an Ownership Contract:
- task id and goal
- files the subagent may write
- files the subagent may read
- files explicitly off-limits
- dependencies and blockers
- expected output
- validation command or check
- collision risk

Rules:
- Spawn multiple subagents in one turn when fanning out across independent
  files, specs, tests, or research tasks.
- Do not spawn a subagent for work the orchestrator can complete directly in one
  response.
- Write subagents may edit only their assigned files.
- Orchestrator reviews all subagent diffs before validation or commit.
- Orchestrator alone stages and commits.

## Phase Contracts

These phase contracts are invariants. Do not treat them as optional process
notes after DBSCTR2 is loaded.

### Phase 1: Domain

Outcome: bounded context, glossary, entities, value objects, domain events,
external sources/sinks, and affected artifacts are known.

Actions:
- Check existing specs before creating anything.
- Update the matching spec domain sections.
- If no spec exists, run Discovery2.
- Identify stale docs or contracts that must be updated later.

Gate:
- Bounded context named.
- Domain terms appear in the spec.
- Existing artifacts are reused or explicitly ruled out.

Commit prefix: `[domain]`.

### Phase 2: Behavior

Outcome: Given/When/Then scenarios describe user or downstream-visible behavior.

Actions:
- Add or update behavior scenarios in the spec.
- Cover happy paths, edge cases, and failure behavior.
- Keep scenarios implementation-free.

Gate:
- Every scenario uses Domain terms.
- Ambiguity that changes behavior is resolved with the user.

Commit prefix: `[behavior]`.

### Phase 3: Spec

Outcome: concrete interfaces, signatures, file targets, examples, and task
ownership are defined.

Actions:
- Add function signatures, command templates, config shapes, or file interfaces.
- Map each interface to behavior scenarios.
- Compile or update the concurrent backlog.

Gate:
- Every interface maps to at least one scenario.
- Subagent ownership boundaries are explicit when delegation is used.

Commit prefix: `[spec]`.

### Phase 4: Contract

Outcome: runtime invariants, config rules, validation rules, and failure behavior
are explicit.

Actions:
- Add preconditions, postconditions, invariants, schema constraints, and config
  contracts where relevant.
- Define stale-artifact checks and validation commands.

Gate:
- Contracts cover changed interfaces and external boundaries.
- Config changes match OpenCode schema.

Commit prefix: `[contract]`.

### Phase 5: Test

Outcome: tests or practical verification prove the change works.

Actions:
- Prefer tests before implementation when the project has a test harness.
- For config/skill work, run deployment and smoke checks.
- Record commands that passed or could not run.

Gate:
- Relevant checks pass, or blockers are documented with next-best checks.

Commit prefix: `[test]`.

### Phase 6: Refactor

Outcome: implementation is simpler, names match the domain, and artifacts are
final.

Actions:
- Remove duplication and stale notes.
- Update backlog statuses and changelog.
- Re-run or preserve validation evidence.

Gate:
- No known stale artifacts remain.
- Worktree contains only intended changes.

Commit prefix: `[refactor]`.

## Commit Gate

At each phase boundary:
1. Inspect `git status`, `git diff`, and recent log.
2. Run the DVC Sync Gate when the repo has DVC markers.
3. Stage only intended files, including changed DVC metadata that belongs to the
   phase.
4. Commit with the phase prefix.
5. Skip commit if the phase produced no new file changes.

Tiny adjacent phases may share a commit only when the phase work is trivial and
the artifacts remain clear.

## DVC Sync Gate

Use this gate only inside repos with any DVC marker: `.dvc/`, `*.dvc`,
`dvc.yaml`, or `dvc.lock`.

At every DBSCTR2 phase commit in a DVC repo:
- Run `dvc status` before staging.
- If the phase changed DVC-tracked outputs, run `dvc add <output>` or the
  project-equivalent update for each changed output.
- Treat `graphify-out/graph.json.dvc` as a normal DVC artifact when present.
- Include resulting `.dvc` files or `dvc.lock` changes in the same Git commit as
  the code, docs, or config changes that produced them.
- If `dvc status` reports unrelated pre-existing drift, do not update it
  silently. Report it and keep it out of the commit unless the user includes it.

When the user asks DBSCTR2 to push Git refs from a DVC repo:
- Run `dvc push` before `git push`.
- If `dvc push` fails, stop before `git push` and report the failure.
- Do not push Git refs that reference DVC metadata whose data failed to upload.

## Artifact Freshness Contract

Before final response, check whether the changed behavior is represented in any
of these artifacts:
- `docs/specs/**/README.md`
- `docs/specs/**/BACKLOG.md`
- `docs/specs/**/CHANGELOG.md`
- tests
- code comments or docstrings that state behavior
- command, skill, agent, or config docs

If yes, update the affected artifact in the correct phase. Do not leave known
stale artifacts.

## OpenCode Config Contract

When editing OpenCode files:
- Preserve `"$schema": "https://opencode.ai/config.json"`.
- Validate config shape against the OpenCode schema or known schema summary.
- Use file-based skills, commands, and agents for non-trivial prompts.
- Keep slash command bodies thin when the skill is the source of truth.
- Tell the user to restart OpenCode after global config, command, skill, agent,
  or plugin changes.

## Subagent Safety Contract

Before any write subagent starts, record:
- files it may write
- files it may read
- files it may not touch
- expected output
- validation check
- dependency and collision risk

After it returns, the orchestrator must inspect the diff for its owned files,
resolve integration issues, run validation, and commit only from the main thread.

## Output Contract

Final response must include:
- outcome
- phase commits created
- validation run
- blockers or restart notes

## Stop Rules

- Stop and ask if the bounded context cannot be named.
- Stop and ask if the next step is destructive, irreversible, or externally
  side-effecting beyond local files and git commits.
- Stop if subagent ownership would overlap and cannot be serialized.
