# [Spec Name]

**Status:** Draft | Experimental | Stable
**Created:** YYYY-MM-DD
**Last updated:** YYYY-MM-DD

## Engineering Profile

### Defaults

| Field | Value |
|---|---|
| Deliverable | |
| Languages/frameworks | |
| Applicable modules | |
| Runtime/platform support | |
| Public compatibility | |
| Trust/data classification | |
| Operational owner | |

## Overview

Brief description of what this bounded context covers.

## File Map

| Path | Purpose |
|------|---------|
| `path/to/file` | Description |

## Architecture

High-level architecture diagram or description.

## Domain

### Bounded Context

Name the bounded context and adjacent contexts.

### Entities

- **EntityName** — description

### Value Objects

- **ValueObjectName** — description

### Domain Events

- `EventNamePastTense` — when/why it fires

### Ubiquitous Language

| Term | Definition |
|------|-----------|
| term | meaning in this context |

## Behavior Scenarios

### Feature: [Feature Name]

**Scenario: [Happy path]**
- Given [precondition using domain terms]
- When [action using domain terms]
- Then [expected outcome]

**Scenario: [Error/edge case]**
- Given [precondition]
- When [action that triggers the edge case]
- Then [expected error handling behavior]

## Contracts & Invariants

### Function: function_name
- **Pre:** precondition
- **Post:** postcondition

### Entity/Module: Name
- **Invariant:** what must always be true

## Gate Ledger

| Gate | Capability | Applicability | Result | Authority/evidence | Exception | Owner |
|---|---|---|---|---|---|---|

Applicability is `required` or `not_applicable`. Result is `pending`, `passed`,
`failed`, `unavailable`, or `not_run`. Exceptions are user-approved `deferred`
or `accepted_risk` records with rationale, owner, and review condition.

For a new V3.2 cycle, export these decisions as JSON for
`dbsctrctl start --plan PATH`. The plan names this committed README and defines
every gate; each `not_applicable` gate includes its reason.

## Artifact Review

- README: reviewed; changed or no-change reason
- BACKLOG: reviewed; active cycle item
- CHANGELOG: reviewed; completion entry required at cycle close

## Verification

```bash
# Commands to verify the system is working
```

## Gotchas

- Known sharp edges and caveats.
