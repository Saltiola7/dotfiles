# Changelog: Quality Assurance Skill

All notable changes to this bounded context.

## 2026-07-11 — DBSCTR V3 Capability Coverage

- Added optional Engineering Profile and Capability Requirement inputs.
- Added evidenced, missing, unavailable, failed, deferred, and accepted-risk
  capability statuses.
- Preserved configured-tool scoped/full behavior when no V3 profile is supplied.
- Retargeted active interfaces and escalation language to unversioned DBSCTR V3.
- Verified the V3 lifecycle contracts and a live `/qa` capability-status probe.

## 2026-07-10

### Added
- Discovery2 artifacts at 97% confidence.
- Domain model for scoped QA gates, full audits, toolchain discovery, concern
  authorities, finding normalization, and safe fix batches.
- Behavior scenarios and concurrent implementation backlog.
- Concrete skill, command, routing, project-management, and handoff interfaces.
- Contracts for scoped noise isolation, concern authorities, fix safety,
  validation evidence, subagents, and non-duplicated instructions.
- Global `qa` skill and thin `/qa` command.
- Chezmoi-managed project instructions and `seo-data-science` toolchain handoff.

### Decisions
- One `qa` skill replaces the standalone Dependabot skill and command.
- DBSCTR2 uses QA as a touched-scope gate and ignores unrelated tool noise.
- Explicit QA runs may inventory and reduce full-repository debt.
- Project tool configuration is deferred to a `seo-data-science` handoff spec.
- Chezmoi becomes canonical for the project-specific `AGENTS.md`.

### Changed
- DBSCTR2 now delegates affected-scope phase gates to QA.
- Discovery2 records project quality commands, authorities, and baselines.
- Global routing defaults to Ponytail and Caveman full modes and routes existing
  Graphify graphs before broad source search.

### Removed
- Standalone `dependabot` skill and `/dependabot` command; Dependabot alerts are
  now QA finding inputs.

### Verified
- Rendered OpenCode JSON parsed successfully.
- Targeted chezmoi apply deployed QA, updated DBSCTR2/Discovery2 and routing,
  removed standalone Dependabot surfaces, and synchronized project instructions.
- Chezmoi dry-run was idempotent and `chezmoi status` was clean.
- Restarted OpenCode successfully launched three concurrent ownership-isolated
  write subagents with the corrected model configuration.
- `seo-data-science` handoff Markdown passed diff checks; unrelated DVC drift and
  one unrelated high Dependabot alert remained out of scope.
