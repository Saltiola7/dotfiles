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
- Project instruction and handoff ownership is maintained privately outside
  this repository.

### Decisions
- One `qa` skill replaces the standalone Dependabot skill and command.
- DBSCTR2 uses QA as a touched-scope gate and ignores unrelated tool noise.
- Explicit QA runs may inventory and reduce full-repository debt.
- Downstream tool configuration and project-specific instructions remain with
  their private project owner.

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
  and removed standalone Dependabot surfaces.
- Chezmoi dry-run was idempotent and `chezmoi status` was clean.
- Restarted OpenCode successfully launched three concurrent ownership-isolated
  write subagents with the corrected model configuration.
- Private downstream handoff evidence remains with its project owner;
  unrelated dependency and storage findings remained out of scope.
