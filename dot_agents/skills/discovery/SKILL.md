---
name: discovery
description: >
  Deep requirements interview for new features and initiatives. Produces a spec (README.md)
  and backlog (BACKLOG.md) through structured questioning until 95% confidence is reached.
  Use when starting a new project, feature, or initiative. Auto-suggested when DBSCTR is
  required but no spec exists for the bounded context.
trigger: /discovery
---

# Discovery — Requirements Interview

Discovery is Phase 0 of the development pipeline. It produces the inputs that DBSCTR consumes.
Never skip Discovery for new features or initiatives. For bug fixes and small changes to
existing features, Discovery is optional — the existing spec provides sufficient context.

## Graph Context Gate

Before broad source search or writing Discovery artifacts, check whether `graphify-out/graph.json`
exists in the repository. If it exists:

- Run `graphify query "<feature, domain, or user request>" --budget 2000` to identify likely bounded
  contexts, adjacent domains, existing specs, source files, and relationships.
- Use graph context to target Grep, Glob, and Read. Do not treat graph output as source truth.
- Verify useful graph findings with source files before including them in the interview summary,
  README.md, BACKLOG.md, or CHANGELOG.md.
- If graph output is empty, weak, stale, conflicting, or Graphify fails, silently fall back to Grep,
  Glob, and Read.
- Do not ask the user to build a graph for v1 unless the task is specifically about Graphify.
- Do not modify Graphify package internals or add OpenCode plugin hooks for v1.

## When to Run Discovery

**Required:**
- New project or initiative
- New feature that doesn't have an existing spec in docs/specs/
- Major rework of an existing feature (scope change, not bug fix)

**Optional (but recommended):**
- Feature that has a spec but the spec is outdated or incomplete
- Cross-system changes affecting multiple specs

**Not needed:**
- Bug fixes where the spec already describes the expected behavior
- Small additions to existing features (a new field, a UI tweak)
- Refactoring that doesn't change behavior

## Interview Process

### Phase A: Problem Space (understand WHAT and WHY)

Ask these questions. Do not proceed until each is answered:

1. **Problem statement**: What problem are we solving? What's broken or missing?
2. **Stakeholders**: Who benefits from this? Who uses it? Who maintains it?
3. **Success criteria**: How do we know when this is done? What does "working" look like?
4. **Scope boundaries**: What are we explicitly NOT doing? What's out of scope?
5. **Constraints**: What technical, time, or resource constraints exist?

### Phase B: Solution Space (understand HOW at the architectural level)

6. **Bounded context**: What domain does this belong to? Adjacent domains?
7. **Entities and relationships**: What are the key things being modeled?
8. **User workflows**: Walk me through the user's experience step by step
9. **Data flow**: Where does data come from? Where does it go? What transformations?
10. **Integration points**: What existing systems does this touch?

### Phase C: Validation (challenge assumptions)

11. **Edge cases**: What happens when things go wrong? Empty data? Concurrent users?
12. **Ambiguity check**: Re-state the requirements back to the user. Ask: "Is this what you mean?"
13. **Priority**: If we can only ship half of this, which half matters most?
14. **Dependencies**: What must exist before this can work? What's blocked?

### Phase D: Confidence Check

After each round of questions, assess confidence:
- **< 70%**: Keep interviewing. There are gaps.
- **70-90%**: Summarize understanding, ask targeted clarifying questions.
- **> 90%**: Present the spec draft for review before writing files.

## Interview Rules

- Ask questions in batches of 3-5 (not all at once, not one at a time)
- Use the Question tool for structured choices when the answer is categorical
- Push back on vague answers: "What specifically do you mean by X?"
- Challenge scope creep: "Is this needed for v1, or can it wait?"
- If the user says "just do what makes sense" — identify the specific ambiguity and ask again
- Never assume requirements — if unsure, ask
- Interview until you have 95% confidence about what the user actually wants,
  not what they think they should want

## Output Artifacts

When confidence reaches 95%, produce these files:

### 1. README.md (Spec)

Create `docs/specs/{spec_name}/README.md` using the project's spec template (`_template_spec.md`).
Must include at minimum:
- Overview with problem statement and ubiquitous language glossary
- Architecture section with at least a component diagram and data flow diagram
- Behavior scenarios (Given/When/Then) for the core happy paths
- Contracts & invariants for the key domain rules

### 2. BACKLOG.md

Create `docs/specs/{spec_name}/BACKLOG.md` using `_template_backlog.md` with:
- Prioritized task table (all tasks visible in one table)
- Dependency chain documented
- Parallel execution guide (which tasks can be worked concurrently by sub-agents)
- Effort estimates (S/M/L)

### 3. CHANGELOG.md

Create `docs/specs/{spec_name}/CHANGELOG.md` with just the header:

```markdown
# Changelog — {Spec Name}
```

### Naming Convention

Spec directory names use snake_case matching the bounded context:
- `article_explorer` (not `article-explorer`)
- `content_audit_workflow` (not `content-audit-workflow`)
- `kw_metrics_pipeline` (not `keyword-metrics-pipeline`)

## Handoff to DBSCTR

After Discovery produces the spec and backlog:
1. The DBSCTR pipeline is invoked for each task in the backlog
2. Phase 1 (Domain) may be partially complete — Discovery already defined entities and glossary
3. Phase 2 (Behavior) may be partially complete — Discovery already wrote core scenarios
4. The DBSCTR pipeline fills in any gaps and proceeds through Spec → Contract → Test → Refactor
5. After each task completes, update BACKLOG.md (mark done) and CHANGELOG.md (add entry)

## Post-Session Backlog Update

At the end of each session (or when the user indicates work is done for now):
1. Update BACKLOG.md task statuses
2. Add completed work to CHANGELOG.md with date, description, test counts, and ADR references
3. Update README.md if the spec needs revision based on what was learned during implementation
