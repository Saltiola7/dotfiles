# analytics_agent_data

> **Ownership note (2026-07-13):** Deployed DBSCTR target paths remain valid, but
> their source is now `Saltiola7/dotfiles-ai`, not this personal repository.

**Status:** Implemented; module interfaces normalized by DBSCTR V3
**Created:** 2026-06-10
**Last updated:** 2026-06-10

## Overview

Enhancement to the DBSCTR data-engineering domain module
(`~/.agents/skills/dbsctr/modules/data.md`) so it serves the **analytics-agent
consumer**, not just the data-expert consumer.

The existing module covers pipeline-correctness (schemas, freshness, volume,
lineage, materialization). It implicitly assumes the consumer of a dataset is a
data scientist who can validate correctness. That assumption breaks for two real
consumers:

1. **The data/analytics engineer** (AI-heavy authoring loop) — consumes the
   DBSCTR module and reference scaffolding while building governed datasets.
2. **The non-expert agent user** on an agentic analytics platform — consumes the
   *governed deliverables* (canonical dataset definitions, semantic-layer
   metrics, reference docs, provenance) at query time, and cannot validate
   correctness because they do not know the data model.

The driver is the failure analysis in Anthropic's "How Anthropic enables
self-service data analytics with Claude" (2026-06-03). Three failure modes
account for most analytics-agent errors: concept↔entity ambiguity, staleness,
and retrieval failure. This spec adds the patterns that attack each, plus a
**delivery framework** answering: *how does the non-expert agent physically get
the deliverables?*

This is a documentation/skill-authoring change. The artifacts are skill markdown
files, not application code; DBSCTR's implementation gate does not apply, but the
work is recorded as a spec for traceability.

## File Map

| Path | Purpose |
|------|---------|
| `~/.agents/skills/dbsctr/modules/data.md` | Provider-neutral data lifecycle outcomes and controls |
| `~/.agents/skills/dbsctr/modules/analytics.md` | Governed analytics definitions, routing, provenance, review, and correction outcomes |
| `~/.agents/skills/dbsctr/references/analytics.md` | Optional pairwise-skill, reference-doc, and query examples |
| `~/.agents/skills/dbsctr/SKILL.md` | V3 module routing and lifecycle gates |

## Architecture

### Consumers and channels

```
                        ┌─────────────────────────────┐
  data/analytics eng    │  DBSCTR data module +        │
  (AI authoring loop) ──│  analytics module + refs    │
                        └─────────────────────────────┘
                                     │ governs
                                     ▼
              ┌──────────── governed deliverables ────────────┐
              │ canonical dataset def · semantic metric ·      │
              │ reference doc · provenance schema              │
              └───────────────────────────────────────────────┘
                                     │ delivery channel (per-project)
        ┌──────────────┬─────────────┴────────────┬──────────────────┐
        ▼              ▼                            ▼                  ▼
  repo-embedded     MCP resources          hive-partition       git-context split
  skill (baseline)  / tools                sidecar              (context repo ≠ data sink)
        │              │                            │                  │
        └──────────────┴────────────┬───────────────┴──────────────────┘
                                     ▼
                        non-expert agent user (query time)
```

### Delivery principle: colocate + auto-sync

Deliverables travel WITH the thing they describe and stay current automatically.
Data-channel and context-channel may differ per project (example: data written
ClickHouse→ADLS while context ships via git repo, because the orchestrator lacks
ADLS write access for context files). The module provides a 4-channel menu;
Discovery picks the channel(s) per project. Baseline channel is always the
repo-embedded skill; opencode-local is always a destination.

## Domain

### Bounded Context

**analytics_agent_data** — the consumption side of data engineering: governing
datasets for agent consumers and delivering governed context to them. Adjacent:
the existing pipeline-correctness side of `modules/data.md`; the `discovery`
skill (raises delivery per project); the `cloud` module (where context sinks
live).

### Entities

- **Deliverable** — a governed context artifact shipped to a consumer: a
  canonical dataset definition, a semantic-layer metric, a reference doc, or a
  provenance schema.
- **Canonical dataset** — the single source-of-truth table for a concept;
  near-duplicates are deprecated, physical rollups derive mechanically from it.
- **Reference doc** — LLM-targeted markdown describing a domain's tables (grain,
  scope, gotchas, routing triggers).

### Value Objects

- **Delivery channel** — repo-skill | MCP | hive-sidecar | git-context-split.
- **Provenance footer** — source tier (semantic › curated › raw) · freshness ·
  owner.
- **Source tier** — ordinal trust rank of where an answer came from.

### Domain Events

- `DeliverableSynced` — a deliverable was pushed to its delivery channel(s).
- `CorrectionHarvested` — a stakeholder correction was captured as an eval / doc fix.
- `EvalDrifted` — offline eval accuracy fell below the per-domain gate threshold.

### Ubiquitous Language

| Term | Definition |
|------|-----------|
| Deliverable | Governed context artifact shipped to a consumer |
| Canonical dataset | Single source-of-truth table per concept |
| Delivery channel | How a deliverable reaches the consumer |
| Colocate + auto-sync | Deliverables live with what they describe; sync on a defined trigger |
| Semantic layer | Compiled metric/dimension definitions; mandatory-first query path |
| Provenance footer | Output trailer: source tier · freshness · owner |
| Reference doc | LLM-targeted domain navigation markdown |
| Offline eval | Question/answer pair anchored to a snapshot, run in CI |
| Ablation | Vary one component, hold eval set fixed, compare pass rates |

## Behavior Scenarios

### Feature: Canonical entity resolution

**Scenario: Concept maps to one governed dataset**
- Given a concept ("revenue for product X") with multiple plausible candidate tables
- When the engineer applies the canonical-dataset rule
- Then one source-of-truth dataset is named, others are marked deprecated, and
  physical rollups are declared to derive mechanically from it

### Feature: Semantic-layer-first contract

**Scenario: Governed metric exists**
- Given a question that maps cleanly to a defined semantic-layer metric
- When the agent answers
- Then it calls the semantic layer first and raw SQL is used only after coverage
  is shown absent

### Feature: Deliverable delivery

**Scenario: Data and context ship on different channels**
- Given data is written ClickHouse→ADLS and the orchestrator cannot write context to ADLS
- When the project picks delivery channels
- Then the data channel is hive-partition and the context channel is git-repo
  split, both declared as delivery contracts, and the repo-embedded skill remains
  the baseline channel

**Scenario: Deliverable drifts from model**
- Given a schema change PR that does not touch the reference doc describing it
- When CI runs
- Then the colocation hook fails the PR until the doc is updated in the same diff

### Feature: Evals for non-deterministic outputs

**Scenario: Eval anchored against drift**
- Given an offline eval for a domain KPI
- When the underlying live number moves
- Then the eval still passes because it is pinned to a snapshot date / stable fact
  table / query-judged grader, not the live number

## Contracts & Invariants

### Deliverable
- **Invariant:** every deliverable declares at least one delivery channel
- **Invariant:** the repo-embedded skill channel is always present (baseline)
- **Invariant:** a deliverable's content stays in sync with what it describes via
  a declared trigger (CI-on-merge | pipeline-run)

### Canonical dataset
- **Invariant:** exactly one canonical dataset per concept; near-dupes carry a
  deprecation marker
- **Invariant:** physical rollups/caches derive mechanically from the canonical
  model, never coexist as alternatives

### Semantic-layer-first
- **Pre:** a governed metric exists for the concept
- **Post:** the answer routes through the semantic layer; raw SQL only on shown
  non-coverage
- **Rule:** humans own metric definitions; LLM drafts documentation only

### Provenance footer
- **Post:** every agent-facing output carries source tier · freshness · owner

### Delivery contract (per output)
- **Invariant:** data-channel and context-channel are declared independently
- **Invariant:** sync trigger is explicit, not implicit framework behavior

## Verification

```bash
# All 6 article concepts present in the module
rg -n "Canonical|Semantic Layer|metadata-as-product|provenance|Delivery|Offline eval|Ablation" \
  ~/.agents/skills/dbsctr/modules/data.md

# Normalized analytics module and optional references exist
test -f ~/.agents/skills/dbsctr/modules/analytics.md && \
test -f ~/.agents/skills/dbsctr/references/analytics.md && echo OK

# SKILL.md routes analytics signals
rg -n "modules/analytics.md" ~/.agents/skills/dbsctr/SKILL.md
```

## Gotchas

- LLM-auto-generated semantic definitions encode the ambiguity they aim to
  remove (Anthropic ablation, net-negative). Generate docs with the model; humans
  own definitions.
- Raw query-corpus grep retrieval moved accuracy <1pt — bottleneck is structure
  (question→entity), not access. Distill corpus into reference docs; do not ship
  raw SQL history as a source of truth.
- Skill docs drift fast: ~95%→65% offline accuracy in one month untreated.
  Colocation + CI coupling is the fix, not periodic cleanup.
- Delivery is per-project and may split data vs context channels. The module must
  not hardcode one channel.
