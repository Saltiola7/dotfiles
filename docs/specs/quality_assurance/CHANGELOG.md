# Changelog: Quality Assurance Skill

All notable changes to this bounded context.

## 2026-07-10

### Added
- Discovery2 artifacts at 97% confidence.
- Domain model for scoped QA gates, full audits, toolchain discovery, concern
  authorities, finding normalization, and safe fix batches.
- Behavior scenarios and concurrent implementation backlog.

### Decisions
- One `qa` skill replaces the standalone Dependabot skill and command.
- DBSCTR2 uses QA as a touched-scope gate and ignores unrelated tool noise.
- Explicit QA runs may inventory and reduce full-repository debt.
- Project tool configuration is deferred to a `seo-data-science` handoff spec.
- Chezmoi becomes canonical for the project-specific `AGENTS.md`.
