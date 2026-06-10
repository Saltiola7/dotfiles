# Backlog: analytics_agent_data

**Last updated:** 2026-06-10

## Active

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| — | all tasks complete | — | done | see Completed |

## Parallel Execution Guide

Tasks that can be worked concurrently (no shared dependencies):
- 1, 8 (different files / different phases)
- 7 (P5, independent of P4 wording)

Tasks that must be sequential (shared file regions / dependencies):
- 2 → 3 → 4 → 5 → 6 (all edit data.md Phase 4; sequential to avoid overlap; 6 references 2-5 wording)
- 8 → 9 (routing references the new module file)
- 1-10 → 11 (consistency pass is the final done-gate)

## Completed

| # | Task | Completed | Commit |
|---|------|-----------|--------|
| 1 | P1 Canonical Entity Resolution + disambiguation glossary | 2026-06-10 | (this commit) |
| 2 | P4 Semantic-layer-first contract | 2026-06-10 | (this commit) |
| 3 | P4 Metadata-as-product contract | 2026-06-10 | (this commit) |
| 4 | P4 Provenance footer contract | 2026-06-10 | (this commit) |
| 5 | P4 Delivery contract + 4-channel menu | 2026-06-10 | (this commit) |
| 6 | P4 doc-model colocation rule + Rules update | 2026-06-10 | (this commit) |
| 7 | P5 Evals for non-deterministic outputs | 2026-06-10 | (this commit) |
| 8 | NEW analytics_references.md | 2026-06-10 | (this commit) |
| 9 | SKILL.md routing split | 2026-06-10 | (this commit) |
| 10 | SKILL.md module-loaded checklist row | 2026-06-10 | (this commit) |
| 11 | Self-consistency pass (fixed "Phases 1 and 4" → "1,4,5"; TypedDict comment) | 2026-06-10 | (this commit) |
