---
name: discovery
description: Discover and persist a DBSCTR-ready bounded context, Engineering Profile, behaviors, contracts, backlog, risks, and validation strategy at 95% confidence.
trigger: /discovery
---

# Discovery — DBSCTR V3

## Outcome

Reach at least 95% confidence in user intent, then create or update
`docs/specs/{bounded_context}/README.md`, `BACKLOG.md`, and `CHANGELOG.md` so
DBSCTR can proceed without repeating discovery.

Skip the interview when existing artifacts answer all material questions. Do not
use for tiny unrelated changes. If the user accepts lower confidence, label the
result a draft rather than DBSCTR-ready.

## Retrieve

1. Read project instructions and matching specs, ADRs, manifests, lockfiles, CI,
   task runners, configured validation, and relevant source.
2. If `graphify-out/graph.json` exists, check its recorded commit, run one
   targeted query, and verify useful claims against source. Fall back immediately
   when the graph is stale, weak, or irrelevant.
3. Record configured quality commands, authorities, baselines, suppressions,
   unavailable checks, and capability gaps. Do not install or prescribe tools.
4. Update an existing bounded context instead of creating a duplicate.

Search again only for a missing owner, interface, flow, term, artifact,
authority, or downstream contract.

## Engineering Profile

Persist stable defaults in the bounded-context README:

- deliverable kind and accountable owner
- languages, frameworks, and applicable modules
- supported runtimes, platforms, and environments
- public API, CLI, schema, configuration, and data compatibility commitments
- trust boundaries and sensitive-data classification
- release, deployment, operational, maintenance, and retirement obligations
- project-selected quality and security authorities

For the current cycle, record only overrides:

- affected scope and downstreams
- risk: `routine`, `elevated`, or `critical`
- delivery intent: local, merge, release, or deploy
- changed profile values and candidate Gate Statuses

Risk guidance:

- `routine`: localized, reversible, and no material public, production,
  sensitive-data, security-boundary, money, or safety impact
- `elevated`: public compatibility, migration, external integration, production,
  sensitive data, material reliability/performance, or security-boundary impact
- `critical`: irreversible loss, broad outage, regulated exposure,
  authentication/authorization failure, material financial impact, or safety harm

Risk may rise with evidence but never falls silently.

## Interview

For each round:

1. State confidence and the largest uncertainty.
2. Ask 3–5 questions whose answers can change scope, risk, behavior, interfaces,
   delivery, or validation.
3. Prefer concrete options when known; use open questions for motives,
   tradeoffs, and risk tolerance.
4. Update the working summary and challenge consequential vagueness.
5. Stop at 95% when remaining uncertainty cannot change implementation choices.

Cover only what applies: problem and success; stakeholders and downstreams;
goals and non-goals; bounded and adjacent contexts; domain terms and events;
workflows and integrations; compatibility and migration; security/privacy;
failure, recovery, rollback, observability, operations, maintenance, retirement;
validation; delivery intent; and parallel ownership.

## Artifacts

`README.md` contains:

- overview, problem, goals, and non-goals
- Engineering Profile defaults and current-cycle overrides
- ubiquitous language, entities, values, events, sources, and sinks
- implementation-free Given/When/Then behavior
- architecture/data flow and concrete interfaces
- contracts, risks, Gate Ledger, and validation strategy
- facts, assumptions, accepted risks, and unresolved decisions

The Gate Ledger enumerates Development Kernel and completion gates. Each gate is
`required`, `not_applicable` with reason, `deferred` with owner/follow-up, or
`accepted_risk` with rationale, owner, and expiry/review condition.

`BACKLOG.md` contains one table with `id`, `title`, `priority`, `status`,
`depends_on`, `owns`, `reads`, `parallel_safe`, `reason`, `effort`, and
`validation`. Ownership and dependencies prevent concurrent collisions.

`CHANGELOG.md` starts with the current date and records decisions and evidence.
Keep facts, assumptions, non-goals, and open risks distinct.

## OpenCode Execution

Use todos for current interview/artifact state and specs/Git for durable state.
Delegate only independent research. Log agent/model routes and trust sourced
research unless uncertain, contradictory, or controlling a risky decision.

Plan is read-only. When writes are unavailable, return artifact-ready decisions
and a Build Handoff without claiming files changed. Build verifies freshness
before persisting them.

## Handoff

Report bounded context, confidence, Engineering Profile, applicable modules and
gates, remaining risks, next DBSCTR task, and parallel-safe ownership. End a
read-only plan with a Build Handoff containing scope, constraints, affected
artifacts, validation, risks, unresolved decisions, and recommended Build agent.

Stop and ask when the bounded context is unknown, two interpretations change the
solution, destructive/external action lacks approval, or ownership overlaps
cannot be serialized.
