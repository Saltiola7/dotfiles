---
name: discovery2
description: Use when starting or scoping a feature, initiative, or bounded context, or when DBSCTR2 lacks an adequate matching spec; interviews to 95% confidence and writes DBSCTR2-ready artifacts.
trigger: /discovery2
---

# Discovery2

## Outcome

Reach at least 95% confidence in user intent, then create or update the matching
`docs/specs/{bounded_context}/README.md`, `BACKLOG.md`, and `CHANGELOG.md` so
DBSCTR2 can proceed without repeating discovery.

Skip the interview when an existing spec answers the material questions. Do not
use for tiny unrelated changes. If the user explicitly accepts lower confidence,
stop without presenting final artifacts as 95%-ready unless they request a draft.

## Retrieve

Read matching specs, applicable project instructions, manifests, CI, task
runners, and configured validation. Record project-selected quality commands,
authorities, baselines, unavailable checks, and gaps; do not install or prescribe
tools during Discovery2.

If `graphify-out/graph.json` exists, run one targeted query and verify useful
results against source. Search again only for a missing owner, interface, flow,
domain term, artifact, or validation command.

## Interview

For each round:

1. State confidence and the largest uncertainty.
2. Ask 3-5 questions whose answers can change scope or implementation.
3. Prefer concrete choices when the answer space is known; use open questions
   for motives, tradeoffs, and risk tolerance.
4. Update the working summary and challenge consequential vagueness.
5. Stop when confidence reaches 95% and remaining gaps do not affect choices.

Cover only what applies: problem and timing; stakeholders and downstreams;
success and failure; goals and non-goals; technical, security, compatibility,
data, UX, time, and operational constraints; bounded and adjacent contexts;
Domain terms, entities, values, and events; workflows and integrations; data
sources, sinks, transformations, freshness, volume, and lineage; edge cases,
failure modes, rollback, observability, validation, and parallel ownership.

## Artifacts

`README.md` contains the overview, problem, goals, non-goals, ubiquitous
language, Given/When/Then behavior, relevant architecture or data flow,
contracts, risks, and validation strategy.

The validation strategy records each configured command's authority, scope,
baseline, and availability.

`BACKLOG.md` contains one table with `id`, `title`, `priority`, `status`,
`depends_on`, `owns`, `reads`, `parallel_safe`, `reason`, `effort`, and
`validation`. Ownership and dependencies must prevent concurrent collisions.

`CHANGELOG.md` starts with the current date and records discovery decisions.
Update an existing matching context rather than duplicating it. Distinguish
facts, assumptions, non-goals, and open risks; never narrow scope silently.

## Handoff

Report the bounded context, confidence, remaining risks, next DBSCTR2 task, and
parallel-safe tasks. Stop and ask when the bounded context is unknown or two
plausible interpretations would produce different specs.
