---
name: dbsctr
description: >
  DBSCTR development methodology — Domain, Behavior, Spec, Contract, Test, Refactor.
  A six-phase pipeline that enforces design-before-implementation discipline.
  Each phase produces artifacts consumed by the next. No phase may be skipped.
  All artifacts are incremental — update existing ones before creating new ones.
trigger: /dbsctr
---

# DBSCTR Development Methodology

All implementation work MUST follow the DBSCTR pipeline. Never write implementation code without
completing the prior phases. Each phase produces an artifact that the next phase consumes.

**Critical: This methodology is incremental.** Before creating any new artifact, check if relevant
artifacts already exist in `docs/specs/`, the codebase, and test files. Update and extend existing
artifacts rather than creating duplicates.

**Critical: Read the project's AGENTS.md** for project-specific adaptations before starting any phase.
The project AGENTS.md defines which patterns to use for error handling, contracts, domain types, and testing.

---

## Phase 1: Domain

**Goal:** Establish the bounded context, entities, value objects, and domain events before any logic is written.

**Process:**
1. Check `docs/specs/` for existing specs that cover this area — read them first
2. Identify the bounded context this work belongs to
3. List all entities (things with identity) and value objects (things defined by attributes)
4. List domain events (past-tense verbs: `OrderPlaced`, `CrawlCompleted`, `ReportGenerated`)
5. Define the ubiquitous language — exact terms that will appear in code, tests, docs, and conversation
6. Write domain types using the project's conventions:
   - Check project AGENTS.md for domain type patterns (Django models, Pydantic, dataclasses, etc.)
   - Structure only — no logic yet
7. Identify external data sources and sinks as named domain concepts:
   - Each source the system reads from (files, APIs, webhooks, queues) gets a name in the ubiquitous language
   - Each sink the system writes to (output files, downstream APIs, caches) gets a name
   - For multi-hop pipelines, sketch the full chain using arrow notation:
     ```
     source: raw_events (Kafka topic)
       → transform: deduplicate + validate schema
       → intermediate: validated_events (staging table)
       → transform: enrich with user profile join
       → serve: enriched_events (production table)
       freshness: source updates continuously; serve ≤ 5min behind source
     ```
   - Document expected schema shape informally here — formal contracts come in Phase 4

**Artifact:** If a spec exists in `docs/specs/`, update its domain sections. If no spec exists,
create one using the project's `docs/specs/_template_spec.md`.

**TodoWrite items:**
- Identify bounded context and adjacent contexts
- Check existing specs in docs/specs/
- Define entities, value objects, domain events
- Write/update domain types (no logic)
- Document ubiquitous language in glossary

**Rules:**
- Domain terms from this phase MUST appear verbatim in all subsequent phases
- If you cannot name the bounded context, STOP and ask the user
- Do NOT add methods to domain types yet — that comes in Spec phase
- If an existing spec covers this domain, UPDATE it — do not create a parallel doc

---

## Phase 2: Behavior

**Goal:** Define what the system should do from the user/stakeholder perspective using structured scenarios.

**Process:**
1. Check the spec (from Phase 1) for existing behavior descriptions — many specs already describe
   user interactions, process flows, and edge cases
2. Write Given/When/Then scenarios for each user-facing behavior
3. Each scenario must use the ubiquitous language from Phase 1
4. Scenarios describe WHAT, never HOW — no implementation details
5. Group scenarios by feature or aggregate

**Artifact:** Add a "Behavior Scenarios" section to the spec in `docs/specs/`. Format:

```
## Behavior Scenarios

### Feature: [Name using ubiquitous language]

**Scenario: [Happy path description]**
- Given [precondition using domain terms]
- And [additional precondition]
- When [action using domain terms]
- Then [expected outcome]
- And [additional outcome]

**Scenario: [Error/edge case description]**
- Given [precondition]
- When [action that triggers the edge case]
- Then [expected error handling behavior]
```

**TodoWrite items:**
- Write Given/When/Then scenarios for happy paths
- Write scenarios for error/edge cases
- Verify all scenarios use ubiquitous language from Phase 1
- Review scenarios with user if ambiguity exists

**Rules:**
- Every scenario MUST reference domain terms from Phase 1
- Do NOT describe internal implementation in scenarios
- If a behavior is ambiguous, ask the user — do not assume
- Scenarios become the basis for acceptance tests in Phase 5

---

## Phase 3: Spec

**Goal:** Bridge behaviors to concrete code interfaces — function signatures, type annotations,
and example input/output pairs.

**Process:**
1. For each behavior scenario, define the function/method signatures that will implement it
2. Add type annotations (check project AGENTS.md for type hint requirements)
3. Write concrete example input/output pairs as docstring examples
4. Define error types using the project's error handling convention:
   - Check project AGENTS.md for error handling patterns
   - Some projects use exceptions (Django), others may use Result types (data pipelines)

**Artifact:** Function stubs WITH complete type signatures, docstrings, and examples — written
directly in the source code files where they will live. Each function's docstring must reference
which behavior scenario(s) it implements.

```python
def process_article(
    article_id: str,
    layers: list[str],
) -> AnnotatedArticle:
    """Process an article with the specified annotation layers.

    Args:
        article_id: The unique document identifier.
        layers: List of annotation layer names to apply.

    Returns:
        AnnotatedArticle with highlight offsets and metadata.

    Raises:
        ArticleNotFoundError: If article_id does not exist in the data lake.
        ProcessingError: If annotation fails for any layer.

    Examples:
        >>> process_article("doc_123", ["ner_person", "discrepancy_stale"])
        AnnotatedArticle(id="doc_123", highlights=[...], layer_count=2)

    Behaviors:
        - "Process article with selected annotation layers"
        - "Reject processing for non-existent article"
    """
    ...
```

**TodoWrite items:**
- Define function signatures with type annotations
- Write docstrings with example inputs/outputs
- Map each function to its behavior scenarios
- Define error types per project convention

**Rules:**
- Every function MUST reference which behavior scenario(s) it implements
- Example inputs/outputs must be concrete values, not placeholders
- Error handling follows the project's convention (read project AGENTS.md)

---

## Phase 4: Contract

**Goal:** Define runtime invariants — preconditions, postconditions, and class invariants that
enforce correctness beyond what tests cover.

**Process:**
1. For each function from Phase 3, define preconditions (what must be true before calling)
2. Define postconditions (what must be true after the function returns)
3. Define class/module invariants (what must ALWAYS be true)
4. For each external data boundary (identified in Phase 1), define **data contracts**:
   - **Source schema**: Declare expected fields/columns, types, and nullability as code
   - **Table-level invariants**: Uniqueness constraints, referential integrity, value ranges
   - **Freshness bounds**: Maximum acceptable age for time-partitioned or cached data
   - **Volume bounds**: Expected row counts or payload sizes with tolerance bands (e.g., ±50% of 7-day avg)
   - **Materialization strategy**: How outputs are written (see vocabulary below)
   - **Lineage**: Source → transform → output mapping using column-level notation
5. Implement contracts using the project's validation tools:
   - Check project AGENTS.md for contract implementation patterns
   - Django projects: model `clean()`, `constraints`, validators, serializer validation
   - Data pipelines: assertions, Pydantic validation
   - Service layer: assertions in function bodies
   - External data boundaries (files, APIs, webhooks, queues):
     * Declare source schema as a dataclass, TypedDict, or Pydantic model in `_domain.py`
     * Add load-time assertions that run BEFORE transform logic (row counts, nulls, types)
     * For tabular data: validate uniqueness keys, referential links between sources
     * For time-partitioned data: assert freshness (max age since last partition/update)
     * For API responses: validate shape against schema before deserializing into domain types
   - Lineage notation (use in spec docs and code comments):
     * Arrow syntax: `source.column → transform_fn() → output.column`
     * Fan-in: `[source_a.col, source_b.col] → join_on(key) → output.col`
     * Derived: `source.col → DERIVED(formula) → output.col`
   - Materialization vocabulary (choose one per output):
     * **Full-refresh**: DROP + recreate. Use when table is small or logic changes often.
     * **Incremental append**: INSERT new rows only. Use for immutable event streams.
     * **Incremental merge**: UPSERT by key. Use when source rows can be updated.
     * **Partition-replace**: Replace one partition (e.g., day). Use for gap-fill/backfill patterns.
     * **Materialized view**: DB engine handles incremental. Use when transform is simple SQL.
     * **Snapshot (SCD)**: Track historical changes. Use for slowly-changing dimensions.
   - For each output, document alongside its materialization strategy:
     * **Idempotency**: Can you re-run safely? What guarantees does the strategy provide?
     * **Backfill**: How to reprocess historical data? (date range param, full replay, etc.)
     * **Failure recovery**: If write fails mid-way, what state is the output in? How to resume?

**Artifact:** Two outputs:
1. Contracts section added to the spec in `docs/specs/` (documentation)
2. Validation logic added to the code (implementation)

**Spec documentation format:**

```
## Contracts & Invariants

### Function: process_article
- **Pre:** article_id exists in data lake
- **Pre:** layers is non-empty and contains only valid layer names
- **Post:** returned AnnotatedArticle has highlights for each requested layer
- **Post:** highlight offsets are within article body bounds

### Model: CrawlState
- **Invariant:** page_count >= 0
- **Invariant:** status is COMPLETE only if page_count > 0
- **Invariant:** started_at <= completed_at when both are set

### Data Contract: event_feed (API source)
- **Schema:** event_type (str, required), payload (dict, required), timestamp (ISO8601 str, required)
- **Uniqueness:** event_id is unique across all received events
- **Invariant:** event_type ∈ ALLOWED_EVENT_TYPES
- **Invariant:** timestamp parses to datetime within ±24h of server time
- **Freshness:** Last event received ≤ 5 minutes ago (health check)
- **Materialization:** Append-only to event log table
- **Idempotency:** Safe to re-deliver (deduplicate on event_id)
- **Failure recovery:** Append is atomic per batch; partial failure leaves prior batches intact

### Data Contract: analytics_cache (tabular source)
- **Schema:** doc_id (str, not null), metric_name (str, not null), value (float, nullable),
  partition_date (date, not null)
- **Uniqueness:** (doc_id, metric_name) is unique per partition_date
- **Referential:** Every row's doc_id exists in documents source
- **Freshness:** Latest partition_date ≤ 7 days from today
- **Volume:** 500K–2M rows/day; tolerance ±50% of 7-day rolling avg; action: warn, don't halt
- **Materialization:** Partition-replace per pipeline run (keyed on date)
- **Idempotency:** Safe to re-run — replaces entire partition
- **Backfill:** Pass date_range param to reprocess historical partitions
- **Failure recovery:** Incomplete partition is invisible until swap; old partition remains on failure

### Lineage: metric_summary output
- `analytics_cache.value → avg_by_doc() → metric_summary.mean_value`
- `[analytics_cache.doc_id, documents.title] → join_on(doc_id) → metric_summary.doc_title`
- `analytics_cache.partition_date → MAX() → metric_summary.last_seen`
```

**TodoWrite items:**
- Define preconditions for each function
- Define postconditions for each function
- Define class/module invariants
- Define source schemas for external data inputs (as typed code artifacts)
- Add table-level invariants (uniqueness, referential integrity, value ranges)
- Define freshness bounds for time-sensitive sources
- Document materialization strategy for each output (full-refresh / append / merge-on-key)
- Document lineage using arrow notation (source.col → transform → output.col)
- Implement contracts using project's validation tools
- Document contracts in spec

**Rules:**
- Contracts are NOT a substitute for tests — they catch invariant violations at runtime
- Preconditions validate inputs; postconditions validate outputs
- Contracts should be cheap to evaluate — no heavy computation
- Use the project's idiomatic validation tools, not raw assertions everywhere
- Data contracts apply at ALL external data boundaries — files, APIs, webhooks, queues, caches
- Source schemas MUST be declared as code (dataclass, TypedDict, or Pydantic model), not just prose
- Table-level assertions run at load time, BEFORE any transform logic executes
- Freshness contracts prevent silently stale data from propagating through pipelines
- Lineage documentation uses arrow notation and lives in the spec alongside function contracts
- Materialization strategy is explicit per output — never implicit "whatever the framework does"
- Volume contracts catch silent data loss — a pipeline that returns 0 rows is worse than one that errors
- Pipeline logic MUST be environment-agnostic. Environment differences (dev/staging/prod) handled
  ONLY by: connection config (env vars), table name suffixes/prefixes, and skip/include flags for
  expensive operations. Never branch on environment inside transform logic.

---

## Phase 5: Test

**Goal:** Write failing tests first (red), then implement to make them pass (green).

**Process:**
1. Write tests BEFORE implementation code
2. Tests must map directly to behavior scenarios from Phase 2
3. Use pytest with clear test names that read as sentences
4. Check project AGENTS.md for testing conventions (fixtures, factories, etc.)
5. Include both unit tests and integration tests where appropriate
6. Consider property-based testing (Hypothesis) for pure functions — recommended, not mandatory

**Artifact:** Test files following project conventions. Each test class/function should reference
which behavior scenario it covers.

```python
class TestProcessArticle:
    """Tests for: Process article with selected annotation layers"""

    def test_processes_article_with_valid_layers(
        self, completed_article: Article
    ) -> None:
        result = process_article(completed_article.id, ["ner_person"])

        assert result.id == completed_article.id
        assert len(result.highlights) > 0

    def test_rejects_nonexistent_article(self) -> None:
        with pytest.raises(ArticleNotFoundError):
            process_article("nonexistent_id", ["ner_person"])
```

**TodoWrite items:**
- Write failing tests for happy path scenarios
- Write failing tests for error/edge cases
- Run tests — confirm they FAIL (red)
- Implement code to make tests pass (green)
- Run tests — confirm they PASS (green)

**Rules:**
- NEVER write implementation before the test exists and fails
- Test names must be readable sentences describing the behavior
- Each test class should reference which behavior scenario it covers
- Use fixtures for test data — no inline object construction
- Run the full test suite after each function is implemented

---

## Phase 6: Refactor

**Goal:** Clean up the implementation while keeping all tests green.

**Process:**
1. Review the implementation for code smells: duplication, long methods, unclear naming
2. Extract functions/classes where responsibilities are mixed
3. Ensure all names match the ubiquitous language from Phase 1
4. Check that contracts are still valid after restructuring
5. Run the full test suite after every refactoring step
6. Check file length limits (project AGENTS.md may specify max lines per file)

**TodoWrite items:**
- Review implementation for code smells
- Extract/simplify where needed
- Verify ubiquitous language consistency
- Run full test suite — confirm still green
- Update docstrings if interfaces changed

**Rules:**
- NEVER refactor without a passing test suite
- Refactoring changes structure, not behavior — tests must not change
- If refactoring reveals a missing test, write the test FIRST, then refactor
- Run tests after EVERY refactoring step, not just at the end

---

## Phase Verification Checklist

Before moving to the next phase, verify:

| From → To | Check |
|-----------|-------|
| Domain → Behavior | All scenarios use domain terms verbatim |
| Behavior → Spec | Every function maps to at least one scenario |
| Spec → Contract | Every function has pre/postconditions; every external data source has a schema contract with lineage |
| Contract → Test | Every test references a behavior scenario |
| Test → Refactor | All tests are green before refactoring begins |
| Refactor → Done | All tests still green, ubiquitous language consistent |

---

## Architecture Decision Records

When you make a significant architectural choice (framework, library, pattern, data model),
create or update an ADR in `docs/adr/`:

```markdown
# ADR-NNN: Title

## Status
Accepted | Superseded by ADR-NNN | Deprecated

## Context
What is the problem or situation that requires a decision?

## Decision
What was decided and why?

## Consequences
What are the tradeoffs? What becomes easier? What becomes harder?
```

**When to write an ADR:**
- Choosing between competing libraries or approaches
- Introducing a new pattern or abstraction
- Changing an existing convention
- Making a tradeoff that future developers need to understand

**Read existing ADRs before starting any task.** If your work contradicts an existing ADR, flag it.

---

## Task Execution Protocol

When given a task that requires DBSCTR:

1. **Read** existing ADRs, relevant specs in `docs/specs/`, and related code
2. **Read** the project's AGENTS.md for project-specific DBSCTR adaptations
3. **Plan** using TodoWrite — create items for each applicable DBSCTR phase
4. **Execute** phases sequentially — do NOT skip ahead
5. **Track** progress — mark todos in-progress and completed as you go
6. **Verify** phase transitions using the checklist above

For tasks involving existing code, start by understanding the current domain model, existing specs,
and conventions before proposing changes.

---

## Incremental Update Protocol

DBSCTR is designed to build incrementally on existing work:

1. **Before creating any artifact**, search for existing ones:
   - `docs/specs/` for domain definitions, behavior descriptions
   - Source code for domain types (models, dataclasses, Pydantic schemas)
   - Test files for existing behavior coverage
   - `docs/adr/` for past architectural decisions

2. **When updating an existing spec:**
   - Add new sections (Behavior Scenarios, Contracts) alongside existing content
   - Do NOT remove existing content unless it's explicitly wrong
   - Update the frontmatter `last_updated` and `version` fields
   - If the spec uses an older template format, add the new sections without restructuring the whole file

3. **When the change is small** (e.g., adding a field to an existing model):
   - Phase 1: Update the data model section in the relevant spec
   - Phase 2: Add/update one behavior scenario if the field affects user-facing behavior
   - Phase 3: Update the function signature that handles this field
   - Phase 4: Add any new invariants (e.g., "field X must be positive")
   - Phase 5: Add test for the new behavior
   - Phase 6: Review the change holistically

   Each phase may take only 1-2 minutes for small changes. The discipline is in the sequence, not the volume.

---

## Commit Convention

Commit messages reference the DBSCTR phase:

- `[domain] Add CrawlState entity and domain events`
- `[behavior] Define keyword report generation scenarios`
- `[spec] Add generate_keyword_report function signature`
- `[contract] Add preconditions for crawl state transitions`
- `[test] Add tests for keyword report generation`
- `[refactor] Extract report formatting into dedicated module`

Multi-phase commits (when phases are small): `[spec][contract] Add report API with validation`

---

## Git Protocol — Phase Commits

Auto-commit at each DBSCTR phase transition. Use the `caveman-commit` skill for message format.

**Process at each phase boundary:**
1. Stage all files changed during the phase (`git add`)
2. Generate commit message with phase prefix: `[domain]`, `[behavior]`, `[spec]`, `[contract]`, `[test]`, `[refactor]`
3. Commit automatically without asking the user
4. If no files changed since the last commit, skip

**Commit message format:**
- Subject: `[phase] <imperative description>` (max 50 chars)
- Body: Only when the "why" isn't obvious from the subject
- Multi-phase commits allowed when phases are trivially small: `[spec][contract] Add report API with validation`

**Rules:**
- Do NOT batch multiple phases into one commit unless they produced changes to the same files
  and the phase work was trivially small (< 5 minutes of work)
- Do NOT commit files that contain secrets (.env, credentials)
- Do NOT push to remote unless the user explicitly asks
- If a commit fails due to pre-commit hooks, fix the issue and create a NEW commit
- Run `git status` after each commit to verify success

---

## Spec Directory Protocol

Specs live in `docs/specs/`. Two formats:

**Flat file** — for simple, standalone specs:
```
docs/specs/kw_metrics_pipeline.md
```

**Directory** — for specs with active development:
```
docs/specs/{spec_name}/
├── README.md        # The living specification (Domain, Behavior, Architecture, Contracts)
├── BACKLOG.md       # Prioritized task table with parallel execution guide
└── CHANGELOG.md     # Completed work log (date-sectioned, detailed)
```

**Rules:**
- A flat spec graduates to a directory when active development begins (create the dir,
  move the flat file to README.md, add BACKLOG.md and CHANGELOG.md)
- After all work is complete, BACKLOG.md can be deleted (README.md + CHANGELOG.md remain)
- Spec directory names use snake_case matching the bounded context
- Use project templates: `_template_spec.md`, `_template_backlog.md`, `_template_changelog.md`

### BACKLOG.md Updates

After completing each DBSCTR cycle (one task):
1. Mark the task as `done` in BACKLOG.md
2. Add an entry to CHANGELOG.md with: date, description, test counts, ADR references if any
3. Move completed tasks from the Active table to the Completed section
4. Update README.md only if the implementation revealed spec changes

### Parallel Execution

When the backlog has independent tasks (no shared dependencies), note this in the
"Parallel Execution Guide" section. Structure tasks so sub-agents can work concurrently:
- Independent tasks touch different files/modules
- Sequential tasks share models, migrations, or API contracts
- Note which tasks are safe to parallelize and which must be sequential

---

## XP Practices

This methodology integrates Extreme Programming practices:

- **Planning Game**: Discovery interview produces the backlog. Each session is a micro-sprint.
- **TDD**: Phase 5 enforces red-green-refactor. Tests must exist and fail before implementation.
- **Continuous Integration**: Every phase commit must leave tests green. No broken commits on main.
- **Small Releases**: Each phase commit is a deployable increment.
- **Simple Design**: Phase 6 (Refactor) enforces simplicity. No speculative abstractions.
- **Collective Code Ownership**: All specs and code are shared context. Any agent can work on any task.

When committing at a phase transition:
1. Run the project's test suite first
2. If tests fail, fix before committing (this is a Phase 5 issue, not Phase 6)
3. Only commit when tests are green

---

## What NOT To Do

- Do NOT jump straight to implementation code
- Do NOT write tests after the code works
- Do NOT skip the refactor step after tests pass
- Do NOT use vague names that don't match the domain language
- Do NOT silently override an existing ADR
- Do NOT create a new spec when one already exists for this domain area
- Do NOT write a test that tests implementation details rather than behavior
- Do NOT batch multiple todo completions — mark each done as you finish it
- Do NOT add mock data to production functions — mocks belong in tests only
