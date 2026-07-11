---
name: dbsctr2
description: Use for behavior, domain, schema, API, service, orchestration, validation, or downstream-visible changes requiring the Domain, Behavior, Spec, Contract, Test, Refactor lifecycle.
trigger: /dbsctr2
---

# DBSCTR2

## Outcome

Deliver the requested change through Domain, Behavior, Spec, Contract, Test, and
Refactor. The orchestrator owns planning, file ownership, integration,
validation, phase commits, and artifact freshness.

Do not load for trivial, formatting-only, git-only, dependency-only,
documentation-only, or non-behavioral configuration changes unless explicitly
invoked. Never modify V1 `dbsctr` or `discovery` without explicit instruction.

## Start

1. Read applicable project instructions and matching `docs/specs/` artifacts.
2. Discover configured quality commands, authorities, and accepted baselines.
3. If `graphify-out/graph.json` exists, run one targeted query, then verify useful
   results against source.
4. Read applicable domain modules before Domain:
   - data pipelines, ETL, orchestration, warehouses, streams, lakes: `modules/data.md`
   - self-service analytics or semantic routing: `modules/data.md` and `modules/analytics_references.md`
   - infrastructure, cloud resources, deployment, scaling: `modules/cloud.md`
   - ML, LLMs, embeddings, evals, feature engineering: `modules/ml.md`
5. If no adequate matching spec exists or intent remains unclear, run
   `discovery2`. Resume only at 95% confidence with required artifacts written.

Search again only when a required interface, owner, contract, validation
command, or affected file remains unknown.

## Phase Gates

Complete phases in order. Each gate consumes the previous phase's artifact.
For non-trivial work, create six todos named Domain, Behavior, Spec, Contract,
Test, and Refactor. Keep exactly one active until all required gates complete.

### 1. Domain `[domain]`

Name the bounded context, glossary, entities, value objects, events, external
sources/sinks, applicable modules, and affected artifacts. Reuse and update an
existing spec rather than creating a duplicate.

### 2. Behavior `[behavior]`

Write implementation-free Given/When/Then scenarios using Domain terms. Cover
happy paths, edges, and failures. Resolve ambiguity that changes behavior with
the user.

### 3. Spec `[spec]`

Define concrete signatures, commands, config shapes, file targets, examples,
and a dependency-aware backlog. Map every interface to behavior and record
non-overlapping ownership when delegating.

### 4. Contract `[contract]`

Define relevant preconditions, postconditions, runtime invariants, schemas,
configuration rules, failure behavior, stale-artifact checks, and validation
commands. Apply domain-module contract extensions and validate OpenCode config
against its current schema when applicable.

### 5. Test `[test]`

Prefer tests before implementation when a harness exists. Implement the minimum
correct change, apply domain-module test/eval extensions, and run configured
checks. For config or skill changes, deploy and smoke-test. Record passed checks
and blockers with next-best evidence.

### 6. Refactor `[refactor]`

Remove duplication and stale notes, align names with the Domain, update backlog
and changelog, and preserve validation evidence. Finish with no known stale
artifact and only intended worktree changes.

Tiny adjacent phases may share a commit when their work is trivial and artifacts
remain clear. Skip commits for phases producing no file changes.

## Delegation

Delegate when independent, non-overlapping work justifies the overhead; start
independent subagents together. Do direct work when it fits one response.

Before a write subagent starts, specify its goal, readable and writable files,
off-limits paths, dependencies, collision risk, expected output, and validation.
Subagents edit only owned files and never stage or commit. The orchestrator
reviews diffs, resolves integration, validates, and alone commits.

Log the selected optimized agent and model. Child results must state the
question, inspected sources, findings, facts versus assumptions, validation,
blockers, uncertainty, and changed files. Trust sourced Explore and Scout output
unless uncertain, contradictory, or controlling a risky edit. Review every
Builder patch. If an optimized agent fails, report it and retry the task once by
continuing with the active same-provider flagship; never cross providers
silently.

## Plan To Build

Plan mode is read-only. Its final Build Handoff contains decisions, interfaces,
scope, contracts, validation, risks, unresolved questions, and inspected source
state without claiming writes occurred. Build verifies source and artifact
freshness before persisting it. OpenCode snapshots and session diffs aid
recovery; Git remains authoritative for integration and commits.

## Commit Gate

At every phase boundary:

1. Inspect status, diff, and recent log.
2. Run `qa` in scoped mode for touched files, dependencies, tests, specs,
   contracts, manifests, and direct downstream impact.
3. Treat relevant findings as failures or documented blockers. Ignore unrelated
   pre-existing findings. Safe deterministic remediation may stay in scope;
   behavior, contract, schema, orchestration, validation, or downstream changes
   remain in DBSCTR2.
4. In repositories with `.dvc/`, `*.dvc`, `dvc.yaml`, or `dvc.lock`, run
   `dvc status`. Update and stage DVC metadata only for outputs changed by this
   phase; report and exclude unrelated drift.
5. Stage only intended files and commit using the phase prefix.

If asked to push from a DVC repo, run `dvc push` before `git push`; stop if it
fails.

## Artifact And Config Contracts

Keep affected specs, backlogs, changelogs, tests, behavioral comments/docstrings,
commands, skills, agents, and config docs current.

For OpenCode changes, preserve its `$schema`, validate the rendered shape, keep
non-trivial prompts in files and slash commands thin, deploy with chezmoi when
managed there, and tell the user to restart OpenCode.

## Final Response

Lead with the outcome. Include phase commits, affected QA scope and validation,
residual risks, blockers, and restart requirements. Stop for unresolved bounded
context, overlapping ownership that cannot be serialized, or destructive,
irreversible, external, costly, or materially scope-expanding actions requiring
approval.
