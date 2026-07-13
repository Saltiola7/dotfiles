---
name: discovery
description: Discover and persist a DBSCTR-ready bounded context, Engineering Profile, behaviors, contracts, backlog, risks, and validation strategy.
trigger: /discovery
---

# Discovery — DBSCTR V3

## Outcome

Reach implementation readiness, then create or update
`docs/specs/{bounded_context}/README.md`, `BACKLOG.md`, and `CHANGELOG.md` so
DBSCTR can proceed without repeating discovery.

Readiness means no unresolved question can materially change scope, behavior,
interfaces, safety, delivery, or validation. Skip the interview when existing
artifacts satisfy that test. Do not use for tiny unrelated changes.

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

Before Build starts a new V3.2 cycle, produce an artifact-ready applicability
plan naming the committed bounded-context README and every gate. Kernel gates and
Review/Integrate are required; each `not_applicable` completion gate has a reason
tied to the Engineering Profile. Build persists this JSON outside the repository
and passes it to `dbsctrctl start --plan PATH`; Discovery does not parse Markdown
at runtime or fabricate a profile identity.

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

1. State readiness and the largest material uncertainty.
2. Ask 3–5 questions whose answers can change scope, risk, behavior, interfaces,
   delivery, or validation.
3. Prefer concrete options when known; use open questions for motives,
   tradeoffs, and risk tolerance.
4. Update the working summary and challenge consequential vagueness.
5. Stop when no unresolved question can materially change implementation choices.

Cover only what applies: problem and success; stakeholders and downstreams;
goals and non-goals; bounded and adjacent contexts; domain terms and events;
workflows and integrations; compatibility and migration; security/privacy;
failure, recovery, rollback, observability, operations, maintenance, retirement;
validation; delivery intent; and parallel ownership.

## Artifacts

Every cycle reviews README, BACKLOG, and CHANGELOG. `README.md` contains stable
bounded-context truth and changes only when durable domain, behavior, interface,
contract, profile, or validation truth changes. It contains:

- overview, problem, goals, and non-goals
- Engineering Profile defaults and current-cycle overrides
- ubiquitous language, entities, values, events, sources, and sinks
- implementation-free Given/When/Then behavior
- architecture/data flow and concrete interfaces
- contracts, risks, Gate Ledger, and validation strategy
- facts, assumptions, accepted risks, and unresolved decisions

### Conditional Product Intent

When the Engineering Profile establishes product-facing behavior, first select
and reference the existing authoritative Product Intent artifact. Only create or
update `docs/specs/<context>/PRODUCT.md` when no existing artifact satisfies the
contract. Product Intent contains durable users/stakeholders, problem and desired
outcomes, non-goals, core journeys, success evidence, product constraints,
accessibility expectations, privacy/trust boundaries, compatibility, and
retirement obligations.

Do not create synthetic Product Intent for libraries, infrastructure, or internal
tools unless their profile establishes intentional user journeys. Product Intent
holds durable outcomes, not current cycle status, implementation design, or a
feature wish list. Never duplicate an existing authoritative product artifact.

The Gate Ledger enumerates Development Kernel and completion gates. Each has
separate Gate Applicability (`required` or reasoned `not_applicable`), Gate
Result, and optional user-approved Gate Exception (`deferred` or
`accepted_risk` with rationale, owner, and expiry/review condition).

`BACKLOG.md` contains one active table with `id`, `title`, `priority`, `status`,
`depends_on`, `owns`, `reads`, `parallel_safe`, `reason`, `effort`, and
`validation`. Ownership and dependencies prevent concurrent collisions.

Completed work moves to a concise Completed section with date and commit.

`CHANGELOG.md` records one compact entry per completed cycle with outcome,
evidence, Gate Exceptions, commits, deployment, and intended Final Push target.
The Cycle Record and final response record the actual push result. Keep facts,
assumptions, non-goals, and open risks distinct. Active Cycle Records live under
`.git/dbsctr/`; specifications and Git remain durable authority.

## OpenCode Execution

Use todos for current interview/artifact state and specs/Git for durable state.
Delegate only independent research. Log agent/model routes and trust sourced
research unless uncertain, contradictory, or controlling a risky decision.

Plan is read-only. When writes are unavailable, return artifact-ready decisions
and a Build Handoff without claiming files changed. Build verifies freshness
before persisting them.

## Handoff

Report bounded context, readiness, Engineering Profile, applicable modules and
gates, the V3.2 applicability plan, remaining risks, next DBSCTR task, and
parallel-safe ownership. End a
read-only plan with a Build Handoff containing scope, constraints, affected
artifacts, validation, risks, unresolved decisions, and recommended Build agent.

Stop and ask when the bounded context is unknown, two interpretations change the
solution, destructive/external action lacks approval, or ownership overlaps
cannot be serialized.
