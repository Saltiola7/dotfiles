# Graph-Aware Skill Routing

**Status:** Draft
**Created:** 2026-06-18
**Last updated:** 2026-06-18

## Overview

Graph-aware skill routing lets agent skills consult an existing Graphify knowledge graph before broad source search. The graph provides relationship and impact context; source files remain the authority for exact code, configuration, and behavior.

Problem: DBSCTR and Discovery start from manual source search even when `graphify-out/graph.json` exists. That wastes context and can miss dependency relationships that Graphify already extracted.

## File Map

| Path | Purpose |
|------|---------|
| `dot_agents/skills/dbsctr/SKILL.md` | DBSCTR workflow instructions that should include graph context and impact gates. |
| `dot_agents/skills/discovery/SKILL.md` | Discovery interview instructions that should include graph context before broad questioning. |
| `docs/specs/graph_aware_skill_routing/README.md` | Living specification for graph-aware skill behavior. |
| `docs/specs/graph_aware_skill_routing/BACKLOG.md` | Task list and dependency chain. |
| `docs/specs/graph_aware_skill_routing/CHANGELOG.md` | Completed work log. |

## Architecture

### Component Diagram

```text
User request
  -> Skill router
    -> Discovery skill
    -> DBSCTR skill
      -> Graph Context Gate
        -> Graphify Graph Snapshot (optional)
      -> Exact Source Search
        -> Grep/Glob/Read
      -> Skill decision or DBSCTR phase output
```

### Data Flow Diagram

```text
repository files
  -> graphify extraction (outside skill flow)
  -> graphify-out/graph.json
  -> graph query / affected output
  -> targeted Grep/Glob/Read
  -> source-backed Discovery or DBSCTR result
```

## Domain

### Bounded Context

The bounded context is `graph_aware_skill_routing`: rules for when DBSCTR and Discovery consult Graphify before or during normal skill execution.

Adjacent contexts:

- `graphify`: knowledge graph extraction and query CLI; treated as external tooling.
- `dbsctr`: design-before-implementation workflow that consumes graph context.
- `discovery`: requirements interview workflow that consumes graph context.
- `opencode_configuration`: agent and skill installation managed by chezmoi.

### Entities

- **Skill Workflow** — named agent workflow such as DBSCTR or Discovery.
- **Graph Snapshot** — existing `graphify-out/graph.json` file for the current repository.
- **Graph Context Gate** — decision point that checks whether a Graph Snapshot exists and whether to query it.
- **Impact Check** — pre-edit relationship query that identifies potentially affected files, symbols, or specs.
- **Source Verification** — exact Grep/Glob/Read pass that confirms graph findings against repository files.
- **Git Hook** — Graphify-managed git hook that refreshes graph data after commit or checkout.

### Value Objects

- **Graph Availability** — whether `graphify-out/graph.json` exists in the repository.
- **Graph Query Result** — relevant nodes, edges, paths, or affected items returned by Graphify.
- **Fallback Decision** — `use_graph_context` or `skip_graph_context` based on availability and usefulness.
- **Source Truth** — verified source file content read after graph context.

### Domain Events

- `GraphContextConsulted` — a skill queried an existing Graph Snapshot.
- `GraphContextSkipped` — no Graph Snapshot existed or the query produced no useful result.
- `ImpactChecked` — a pre-edit graph impact query ran for an existing code area.
- `SourceVerified` — source files were read to confirm graph context.
- `GraphHookInstalled` — Graphify git hook was installed for the repository.

### Ubiquitous Language

| Term | Definition |
|------|------------|
| Graph Snapshot | Existing `graphify-out/graph.json` for the current repository. |
| Graph Context Gate | Skill step that checks for a Graph Snapshot and optionally runs Graphify queries. |
| Impact Check | Relationship query before editing existing code or workflows. |
| Source Verification | Grep/Glob/Read confirmation that source files support the graph finding. |
| Source Truth | Rule that repository files override graph output whenever they differ. |
| Silent Fallback | Continuing with Grep/Glob/Read without user interruption when graph context is unavailable or weak. |
| Git Hook | Graphify-managed post-commit/post-checkout hook that keeps graph data fresh. |

## Behavior Scenarios

TBD in Phase 2.

## Contracts & Invariants

TBD in Phase 4.

## Verification

```bash
git status --short
graphify hook status
```

## Gotchas

- Graph output is relationship context, not source truth.
- Graphify package internals are out of scope for this bounded context.
- Scout direct integration is deferred unless a configurable scout prompt is discovered.
