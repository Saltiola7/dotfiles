# Backlog: analytics_agent_data

**Last updated:** 2026-06-10

## Active

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | data.md P1: Canonical Entity Resolution section + entity-disambiguation glossary rule | high | pending | Attacks concept↔entity ambiguity |
| 2 | data.md P4: Semantic-layer-first contract subsection | high | pending | humans own defs; LLM drafts docs |
| 3 | data.md P4: Metadata-as-product contract (grain/scope/ranges/owner/tier) | high | pending | warehouse legibility |
| 4 | data.md P4: Provenance footer contract | medium | pending | source tier · freshness · owner |
| 5 | data.md P4: Delivery contract + 4-channel menu (repo-skill/MCP/hive-sidecar/git-split) | high | pending | colocate+auto-sync; per-project; data≠context channel allowed |
| 6 | data.md P4: doc-model colocation rule (CI hook) + Rules update | medium | pending | depends on 2-5 wording |
| 7 | data.md P5: Evals for non-deterministic outputs (offline evals, telemetry, ablation, gates, correction harvesting) | high | pending | anchor against drift |
| 8 | NEW modules/analytics_references.md: pairwise skill pattern + reference-doc skeleton + adversarial reviewer | high | pending | from article appendix |
| 9 | SKILL.md: routing split for analytics signal → analytics_references.md | medium | pending | depends on 8 existing |
| 10 | SKILL.md: add "module loaded" row to Phase Verification Checklist | low | pending | also fixes earlier review gap |
| 11 | Self-consistency pass: verify no contradiction with existing data.md content | high | pending | done-gate; after 1-10 |

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
