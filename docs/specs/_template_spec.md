# [Spec Name]

**Status:** Draft | Experimental | Stable
**Created:** YYYY-MM-DD
**Last updated:** YYYY-MM-DD

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

## Verification

```bash
# Commands to verify the system is working
```

## Gotchas

- Known sharp edges and caveats.
