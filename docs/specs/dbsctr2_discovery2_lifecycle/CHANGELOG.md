# Changelog — DBSCTR2 and Discovery2 Lifecycle

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
