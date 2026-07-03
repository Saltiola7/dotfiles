# DBSCTR2 Domain Module: Analytics Reference Scaffolding

**Applies when:** Building a self-service analytics **agent** consumed by
non-experts — semantic-layer routing, warehouse-querying skills, reference docs
that map questions to governed entities. Load alongside `modules/data.md` (which
governs the datasets this scaffolding points at).

This module is procedural: it encodes *how* an analytics agent should navigate
governed data. `modules/data.md` is declarative — it defines the datasets,
contracts, and delivery. Use both together.

The three analytics-agent failure modes and where each is attacked:

| Failure mode | Attacked by |
|--------------|-------------|
| Concept↔entity ambiguity | Canonical datasets + semantic layer (`data.md`) |
| Staleness | Doc-model colocation + correction loop (`data.md` Phase 5) |
| Retrieval failure | The pairwise skill router + reference docs (this module) |

---

## Pairwise Skill Pattern

Split the agent's knowledge into two cooperating skills. This is the answer to
**retrieval failure**: rather than letting the agent search a million-field
warehouse, narrow the space to a few dozen curated files before any query is written.

### Knowledge skill (thin router)

A top-level router that loads domain detail on demand. It says, in effect:
"try the semantic layer first; if no coverage, here are ~30 reference files for
this domain describing relevant tables, columns, joins, and gotchas."

- Routes the agent to the semantic layer first (mandatory).
- Maps each business domain → its reference doc + dashboard catalog.
- Stays small; domain detail loads only when the router points to it.

### Process skill ("unbook")

Encodes the process a senior analyst follows:

1. Clarify the question (time period, segment, the business decision it informs).
2. Find sources via the knowledge skill.
3. Run the query (semantic layer first).
4. Loop the result through adversarial review sub-agents.

Also bundles reusable analysis patterns (retention curves, rate decomposition,
funnel analysis) so common requests aren't reinvented each time.

---

## Reference-Doc Skeleton

Reference docs are written **for retrieval by an LLM**, not for humans. Describe
tables (grain, scope, exclusions), the mechanics of gotchas, and explicit routing
triggers — without prescriptive recipes that go stale.

```markdown
# [Domain] Tables

## Quick Reference
### Business Context — [what this domain means in plain words]
### Entity Grain — [what one row represents]
### Standard Hygiene Filter — [the filter every query in this domain applies]

## Dimensions
- [How key dimensions are encoded, and how the same concept is named
  differently across tables]

## Key Tables
### [table_name]
- **Grain**: [...] · **Scope/exclusions**: [...]
- **Usage**: [when to use it, when NOT to, join keys, required filters]
[... one short section per governed table ...]

## Gotchas
- [The wrong-answer modes a senior analyst would warn you about]

## Best Practices / Common Query Patterns
- [Default choices, standard cuts, worked patterns where the exact query
  form is the hard part]

## Cross-References
- [Neighboring domain docs that own adjacent questions]
```

### Routing triggers

Make routing explicit and negative where it matters:

```
IF the question is about experiment lift → USE references/experiments.md
DO NOT use the experiments tables for raw event counts → USE references/events.md
```

---

## Adversarial Review Sub-Agent

Before the final answer, spawn a sub-agent that aggressively challenges the
underlying assumptions of the query and result.

- **Effect (measured):** +6% accuracy on the eval set, at +32% tokens and +72%
  latency. Worth it for high-stakes answers; a cost/latency tradeoff to declare
  per surface.
- Blocking findings must be fixed and re-reviewed; the answering agent does NOT
  self-certify.
- Swapping the reviewer to a cheaper model lost most of the accuracy gain for no
  real speedup (recorded null result) — keep the reviewer on a capable model.

---

## Rules (Analytics Reference Scaffolding)

- Knowledge skill routes to the semantic layer FIRST; raw SQL only on shown non-coverage
- Reference docs are LLM-targeted: grain/scope/gotchas/routing-triggers, not recipes
- Routing triggers include negative cases ("DO NOT use X for Y")
- Adversarial review is mandatory for high-stakes answers; agent never self-certifies
- These skill files are themselves deliverables — they ship via the `data.md`
  delivery contract (repo-embedded baseline + per-project channels) and obey
  doc-model colocation
- Distill the prior-query corpus into reference docs; never expose raw SQL history
  as a source of truth the agent reads directly (ablation showed <1pt gain)
