# ADR-001: Remove oh-my-openagent, adopt DBSCTR natively

## Status
Accepted

## Context

The project used `oh-my-openagent` (OMO) as an OpenCode plugin for:
- Boulder-based work tracking (`.sisyphus/` and `.omo/` directories)
- Automatic continuation hooks (fire prompts when session goes idle)
- Plan-based execution with final-wave verification

Problems encountered:
1. **Continuation loop bug**: archiving plan files to `done/` broke `getPlanProgress()` which uses `existsSync()` — returned `isComplete:false` for missing files, firing the continuation hook repeatedly on completed work.
2. **Dual state directories**: `.omo/` mirrored `.sisyphus/` content, causing confusion about which was authoritative.
3. **Subagent transport failures**: `task()` delegation broke with `Failed to create session: [object Object]` — 4 consecutive failures in one session with no recovery path.
4. **Opaque plan format**: OMO plans use a custom checkbox format that doesn't integrate with standard docs/specs/ workflow.
5. **Runtime coupling**: Plugin reads from disk paths that change when files are reorganized, creating silent failures.

## Decision

1. Disable OMO via `.chezmoidata.yaml` toggle (`omo_enabled: false`) — config remains for potential re-enable but plugin is not loaded.
2. Adopt DBSCTR methodology natively using `dot_agents/skills/dbsctr/SKILL.md` and `dot_agents/skills/discovery/SKILL.md` (chezmoi-managed).
3. Migrate valuable state from `.sisyphus/` plans/evidence/learnings into `docs/specs/` using DBSCTR's spec directory protocol (README + BACKLOG + CHANGELOG).
4. Delete `.omo/` and `.sisyphus/` runtime directories entirely.
5. Track work in `docs/specs/{context}/BACKLOG.md` instead of boulder.json.
6. Keep `.sisyphus/` and `.omo/` in `.gitignore` as safety net (in case OMO is re-enabled).

## Consequences

**Easier:**
- Single source of truth for specs, backlogs, and history (all in `docs/specs/`)
- No runtime state directories that break on file moves
- No continuation hook surprises
- Standard markdown files readable without plugin knowledge

**Harder:**
- No automatic "session went idle, continue working" prompts (must manually `/start-work` or use boulder-continuation from DBSCTR skill)
- No built-in elapsed-time tracking per task (can be added manually in CHANGELOG)
- Final-wave verification must be done manually or via explicit prompt (no auto-dispatch)

**Neutral:**
- Plan quality unchanged — DBSCTR skill produces equivalent or better structured plans
- Evidence gathering unchanged — can still store verification artifacts in docs/ or tests/
