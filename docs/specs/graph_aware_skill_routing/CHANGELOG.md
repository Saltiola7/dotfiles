# Changelog — Graph-Aware Skill Routing

## 2026-06-18

### Added
- Created `graph_aware_skill_routing` spec, backlog, and changelog.
- Added Graph Context Gate and Impact Check requirements for DBSCTR.
- Added Graph Context Gate requirements for Discovery.
- Installed Graphify post-commit and post-checkout git hooks with `graphify hook install`.
- Ignored hook-generated `graphify-out/` artifacts in git.

### Verified
- `graphify hook status` reports post-commit and post-checkout installed.
- `graphify query "graph aware skill routing" --budget 300` returns scoped graph nodes.
- `graphify affected "dot_agents/skills/dbsctr/SKILL.md" --depth 1` returned no unique node match and remained non-blocking by contract.
- `chezmoi apply /Users/tis/.agents/skills/dbsctr/SKILL.md /Users/tis/.agents/skills/discovery/SKILL.md` applied the skill changes.
- `rtk git status --short` reports only the pre-existing `dot_local/bin/executable_secret` modification.

### ADRs
- No new ADR. Existing ADR-001 supports native DBSCTR and no opaque runtime plugin dependency.
