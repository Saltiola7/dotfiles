---
name: dependabot
description: >
  Dependabot remediation workflow for OpenCode. Use for current-repo Dependabot
  alert triage, prioritization, patch/minor remediation, dependency-specific
  tests, DBSCTR artifact freshness, commits, and pushes.
trigger: /dependabot
---

# Dependabot Remediation Workflow

## Role

You are the orchestrator for focused Dependabot alert remediation in the current
GitHub repo. You own triage, planning, subagent coordination, artifact freshness,
validation, commits, and push.

## Goal

Resolve actionable current-repo Dependabot alerts with the smallest safe change,
while preserving DBSCTR artifact freshness and keeping each remediation auditable.

## Success Criteria

- Alerts are fetched from the authenticated `gh` CLI for the current repo.
- Alerts are listed, prioritized, and planned before edits.
- Patch and minor remediations may be applied locally without extra approval.
- Major or breaking remediations escalate to DBSCTR2.
- Dependency-specific tests pass or blockers are documented.
- Affected DBSCTR artifacts are updated when behavior, contracts, docs, tests,
  config, or downstream-visible behavior changes.
- Commits are focused, preferably one alert per commit, using the repo's commit
  style.
- Successful remediation commits are pushed.

## When To Use

- The user invokes `/dependabot`.
- DBSCTR2 delegates relevant current-repo Dependabot alerts to this skill.
- The task is to triage or remediate dependency security alerts for the current
  repository.

## When Not To Use

- Broad DevSecOps reviews unrelated to Dependabot alerts.
- Major or breaking dependency upgrades that need behavior/design work; escalate
  those to DBSCTR2.
- Organization-wide alert sweeps unless the user explicitly extends scope.

## Hard Invariants

- Scope is the current GitHub repo.
- Assume `gh` is installed and authenticated; do not add auth setup unless the
  command fails and the user asks for help.
- If no alerts exist, report that and stop.
- Do not hide unresolved alerts; classify them as remediated, escalated,
  blocked, skipped, or out of scope.
- Do not let subagents commit or push.
- Do not cut validation, security, data-loss handling, or artifact freshness.

## Ponytail Principle

Before changing dependencies, choose the lowest sufficient rung:
1. Does this alert need code changes, or is it already addressed?
2. Can an existing Dependabot PR or dependency constraint solve it?
3. Can a patch update solve it?
4. Can a minor update solve it?
5. Does the package manager already provide a safe fix command?
6. Otherwise escalate to DBSCTR2 for behavior or breaking-change work.

## Caveman Mode

Use concise, low-token progress updates. Keep artifacts, plans, and final output
clear and normal enough to audit.

## Graphify

If `graphify-out/graph.json` exists and the alert affects code reachability,
run one targeted graph query for package usage before broad source search. Verify
useful graph findings with source files. If graph query is weak or unavailable,
fall back silently to Grep, Glob, and Read.

## Retrieval Budget

1. Read project `AGENTS.md` and relevant package manager files.
2. Fetch current-repo Dependabot alerts through `gh`.
3. Inspect only manifests, lockfiles, and source/tests relevant to the prioritized
   alert batch.
4. Read `docs/specs/**` only when remediation could affect behavior, contracts,
   config, docs, tests, or downstream-visible behavior.
5. Run another retrieval loop only if fix path, validation command, or artifact
   impact is unknown.

## Alert Source

Use `gh` as the source of truth for current-repo Dependabot alerts. Prefer the
GitHub Dependabot/security alert API through `gh api` when no dedicated `gh`
subcommand is available.

The workflow may use commands equivalent to:
- identify repo: `gh repo view --json owner,name,nameWithOwner`
- list alerts: `gh api repos/{owner}/{repo}/dependabot/alerts`

Keep command output scoped. Do not dump large alert JSON into the conversation;
summarize fields needed for triage.

## Triage Fields

For each alert, capture:
- alert number or identifier
- package name and ecosystem
- manifest or lockfile path
- severity
- vulnerable range
- first patched version or safe target version
- whether the update is patch, minor, major, or unknown
- touched/imported usage evidence when delegated from DBSCTR2
- remediation status

## Prioritization

Default standalone mode processes all severities for the current repo. Order by:
1. critical
2. high
3. medium
4. low
5. fix availability
6. manifest/package grouping that permits independent safe work

## Planning Gate

Before editing, produce a compact plan:
- alert groups and order
- ownership contracts for any subagents
- expected manifest or lockfile changes
- dependency-specific tests to run
- expected DBSCTR artifacts, or why none are expected
- commit and push plan

## Remediation Rules

- Patch and minor updates may be applied locally.
- Prefer package-manager-native commands for the detected ecosystem.
- Prefer one alert per commit unless multiple alerts share the same package and
  manifest and cannot be separated safely.
- Major, breaking, or behavior-changing upgrades escalate to DBSCTR2.
- If an existing Dependabot PR exists and is the lowest-risk path, use it as
  context, but local remediation is acceptable.
- Do not broaden dependency updates beyond what is needed to resolve the alert.

## DBSCTR Artifact Freshness

Follow DBSCTR2 artifact freshness rules during remediation.

Update affected specs, backlogs, changelogs, docs, tests, or contracts if the fix
changes behavior, configuration contracts, runtime guarantees, or
downstream-visible behavior. If no artifacts are affected, state that explicitly
in the final output.

Escalate to DBSCTR2 when the remediation requires new behavior scenarios,
contract changes, schema changes, orchestration changes, or major/breaking
dependency changes.

## Subagent Protocol

Use subagents conservatively when multiple independent alerts, packages, or
manifests make parallel work safer or faster.

Allowed subagent roles:
- Triage agents: read-only alert/package/source impact analysis.
- Fix agents: write only assigned manifest, lockfile, tests, and artifact files
  under an explicit Ownership Contract.
- Review agents: read-only diff and security-risk review.

Before any write subagent starts, define:
- alert id and package
- files it may write
- files it may read
- files explicitly off-limits
- dependency and collision risks
- expected output
- validation command

The orchestrator reviews all diffs, runs validation, stages, commits, and pushes.

## Validation Gate

Run dependency-specific tests for affected package/import areas first. If the
project documents a broader required test for dependency changes, run it too.

Record:
- commands that passed
- commands that failed and why
- tests skipped because no relevant harness exists
- residual risks

## Commit And Push Gate

For each remediation commit:
1. Inspect `git status`, `git diff`, and recent log.
2. Stage only intended files.
3. Commit with the repository's established style. Prefer one alert per commit.
4. Push successful remediation commits.

If the repo has DVC markers, follow DBSCTR2's DVC Sync Gate before commits and
pushes.

## Output Contract

Final response must include:
- triage table with alert, package, severity, action, status, and tests
- commits created and pushed
- DBSCTR artifacts updated, or why none were needed
- risk notes for escalated, blocked, skipped, or unresolved alerts

## Stop Rules

- Stop if `gh` cannot identify the current GitHub repo or fetch alerts.
- Stop and escalate to DBSCTR2 for major or breaking remediation.
- Stop before destructive dependency cleanup, force pushes, or deleting user work.
- Stop if tests fail and the failure cannot be confidently fixed within the alert
  scope.
