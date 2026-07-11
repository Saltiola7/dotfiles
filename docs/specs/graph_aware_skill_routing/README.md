# Graph-Aware Skill Routing

**Status:** Draft
**Created:** 2026-06-18
**Last updated:** 2026-06-18

## Overview

Graph-aware skill routing lets agent skills consult an existing Graphify knowledge graph before broad source search. The graph provides relationship and impact context; source files remain the authority for exact code, configuration, and behavior.

Problem: DBSCTR V3 and Discovery start from manual source search even when `graphify-out/graph.json` exists. That wastes context and can miss dependency relationships that Graphify already extracted.

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

### Feature: Graph Context Gate

**Scenario: Discovery consults existing Graph Snapshot**
- Given a repository has a Graph Snapshot
- When the Discovery skill starts a new requirements interview
- Then the Discovery skill consults graph context for relevant domains and relationships before broad questioning
- And the Discovery skill still asks the required Discovery questions before writing files

**Scenario: DBSCTR consults existing Graph Snapshot**
- Given a repository has a Graph Snapshot
- When the DBSCTR skill starts Phase 1 Domain for an implementation task
- Then the DBSCTR skill consults graph context for bounded context, adjacent contexts, and likely files
- And the DBSCTR skill performs Source Verification before using graph context in artifacts or implementation

**Scenario: Graph context is unavailable**
- Given a repository has no Graph Snapshot
- When Discovery or DBSCTR starts
- Then the skill uses Silent Fallback and continues with Grep, Glob, and Read
- And the skill does not ask the user to build a graph for v1

**Scenario: Graph context is weak or stale**
- Given a Graph Query Result has no useful match or conflicts with Source Truth
- When a skill evaluates the Graph Query Result
- Then the skill treats Source Truth as authoritative
- And the skill continues with Silent Fallback

### Feature: Impact Check

**Scenario: Existing code is about to change**
- Given a task modifies an existing code area, skill workflow, or spec
- When implementation is about to begin
- Then the DBSCTR skill runs an Impact Check when a Graph Snapshot exists
- And the DBSCTR skill verifies affected files with Source Verification before editing

**Scenario: Impact Check cannot run**
- Given Graphify is unavailable or Impact Check fails
- When implementation is about to begin
- Then the DBSCTR skill records no blocker
- And the DBSCTR skill continues with Source Verification using Grep, Glob, and Read

### Feature: Git Hook Refresh

**Scenario: Graphify git hook is installed**
- Given Graphify CLI is available in the repository
- When the approved v1 setup runs
- Then `graphify hook install` installs Graphify-managed git hooks
- And hook failures must not change skill behavior; skills still use Graph Snapshot only when present

**Scenario: Scout remains indirect**
- Given no editable scout prompt or config is discovered
- When graph-aware routing is implemented
- Then scout direct integration remains out of scope
- And DBSCTR and Discovery carry the graph-aware behavior for v1

## Contracts & Invariants

### Module: Discovery Graph Context Gate
- **Pre:** Discovery is required or explicitly requested.
- **Pre:** Graph Snapshot is optional; absence must not block Discovery.
- **Post:** When Graph Snapshot exists, Discovery has attempted graph context before broad source search or artifact writing.
- **Post:** Discovery artifacts only use graph findings after Source Verification.
- **Invariant:** Discovery must still ask required interview questions before writing files.
- **Invariant:** Discovery must use Silent Fallback when graph context is unavailable, weak, stale, or failing.

### Module: DBSCTR Graph Context Gate
- **Pre:** DBSCTR is required or explicitly requested.
- **Pre:** Graph Snapshot is optional; absence must not block any DBSCTR phase.
- **Post:** When Graph Snapshot exists, DBSCTR has attempted graph context before Phase 1 Domain source discovery.
- **Post:** DBSCTR uses graph context to target Source Verification, not to replace it.
- **Invariant:** Source Truth overrides every Graph Query Result.
- **Invariant:** Graphify failures are non-blocking unless the user explicitly asks to debug Graphify itself.

### Module: DBSCTR Impact Check
- **Pre:** Task modifies an existing code area, skill workflow, or spec.
- **Pre:** Impact Check requires an existing Graph Snapshot.
- **Post:** When Graph Snapshot exists, DBSCTR has attempted `graphify affected` for target files, symbols, specs, or domain terms before editing.
- **Post:** DBSCTR reads likely affected files before editing when graph output identifies them.
- **Invariant:** Missing or failing Impact Check falls back to Grep, Glob, and Read.

### Module: Git Hook Setup
- **Pre:** Graphify CLI is available.
- **Pre:** v1 hook setup is approved for the repository.
- **Post:** `graphify hook install` has been attempted.
- **Post:** `graphify hook status` has been checked and reported.
- **Invariant:** Hook setup must not edit Graphify package internals.
- **Invariant:** Hook setup must not introduce OpenCode plugin hooks in v1.
- **Invariant:** Hook-generated `graphify-out/` artifacts are generated state and should not appear as untracked worktree noise.

## Skill Instruction Interfaces

### Discovery Graph Context Gate

```text
Input: user request, repository root
Precondition: Discovery is required or requested
Step 1: If graphify-out/graph.json exists, query graph context for the requested domain, likely bounded contexts, and existing specs.
Step 2: Summarize only useful relationships in working context.
Step 3: Continue required Discovery interview questions.
Fallback: If graph context is unavailable, weak, or stale, continue with Grep/Glob/Read without asking user to build a graph.
Source rule: Verify graph findings with source files before writing Discovery artifacts.
Behaviors: Discovery consults existing Graph Snapshot; Graph context is unavailable; Graph context is weak or stale.
```

### DBSCTR Graph Context Gate

```text
Input: implementation task, repository root
Precondition: DBSCTR is required or requested
Step 1: Before Phase 1 Domain, check for graphify-out/graph.json.
Step 2: If present, query graph context for bounded context, adjacent contexts, existing specs, likely source files, and dependencies.
Step 3: Use graph context to target Grep/Glob/Read, not to replace them.
Fallback: If graph context is unavailable, weak, or stale, continue with standard DBSCTR source discovery.
Source rule: Source Truth overrides Graph Query Result.
Behaviors: DBSCTR consults existing Graph Snapshot; Graph context is unavailable; Graph context is weak or stale.
```

### DBSCTR Impact Check

```text
Input: target files, symbols, specs, or domain terms discovered before editing
Precondition: Task modifies existing code, skill workflow, or spec
Step 1: If graphify-out/graph.json exists, run graph impact query for target files, symbols, specs, or domain terms.
Step 2: Read likely affected files before editing when graph output identifies them.
Step 3: Continue normal implementation when graph impact query fails.
Fallback: Use Grep/Glob/Read for impact discovery.
Source rule: Do not block implementation on Graphify errors.
Behaviors: Existing code is about to change; Impact Check cannot run.
```

### Git Hook Setup

```text
Input: repository root with Graphify CLI available
Precondition: v1 hook setup approved
Step 1: Run graphify hook install.
Step 2: Verify graphify hook status.
Fallback: If hook install fails, leave skill behavior unchanged and report failure.
Source rule: Hook refresh is convenience only; skills still check Graph Snapshot existence.
Behaviors: Graphify git hook is installed.
```

## Verification

```bash
git status --short
graphify hook status
```

## Gotchas

- Graph output is relationship context, not source truth.
- Graphify package internals are out of scope for this bounded context.
- Scout direct integration is deferred unless a configurable scout prompt is discovered.
