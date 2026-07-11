# Analytics Module

## Applicability

- **CONDITIONAL:** Load for self-service analytics, natural-language-to-data
  answers, semantic routing, governed metric retrieval, or analytics reference
  documentation. Load `modules/data.md` when the change also creates or changes
  data assets, pipelines, or their contracts.
- **PROJECT POLICY:** The Engineering Profile identifies governed sources,
  owners, data classification, delivery channels, and applicable review gates.

## Engineering Profile Extensions

- **REQUIRED:** Record the canonical metric and entity definitions, governed
  source route, grain, scope/exclusions, owner, freshness expectation, and
  compatibility/deprecation status for each affected answer domain.
- **CONDITIONAL:** For protected data or restricted audiences, record approved
  access paths, privacy constraints, and answer-handling requirements.
- **PROJECT POLICY:** Identify the authority that approves definitions and the
  authority that evaluates answer quality.

## Required Outcomes

- **REQUIRED:** Route each concept to one canonical, governed definition and
  source; resolve ambiguity or ask for clarification before answering.
- **REQUIRED:** Preserve source grain, scope, exclusions, ownership, provenance,
  and freshness in the answer or its accessible metadata.
- **REQUIRED:** Make supported access and privacy constraints effective for data
  and answer delivery.
- **REQUIRED:** Provide a correction path that assigns feedback to the owning
  definition, reference, or evaluation case.
- **REQUIRED:** Declare how analytics definitions and reference material are
  delivered and synchronized with their governed sources.
- **REQUIRED:** Mark superseded definitions and sources as deprecated, name the
  replacement where one exists, and preserve migration compatibility required by
  project policy.

## Conditional Controls

- **CONDITIONAL:** Use a semantic or governed query interface before raw-source
  querying when one covers the request; document demonstrated non-coverage before
  falling back.
- **CONDITIONAL:** For high-impact answers, obtain independent review of the
  interpretation, source selection, and query/result assumptions before delivery.
- **CONDITIONAL:** When no governed source covers the request, label exploratory
  results with their limits and do not present them as canonical.
- **PROJECT POLICY:** Define high-impact, approved reviewers, retention, access,
  privacy, sync triggers, and deprecation windows in the Engineering Profile or
  its referenced policy.

## Validation Capabilities

- **REQUIRED:** Evaluate retrieval and query behavior against representative
  questions, including ambiguous requests, unsupported requests, and known
  corrections.
- **REQUIRED:** Check that outputs identify the selected source, freshness, and
  owner, and that canonical definitions are used consistently.
- **CONDITIONAL:** For high-impact answers, validate independent-review evidence
  and resolution of blocking findings.
- **EXAMPLE:** An evaluation may grade source routing and query shape against a
  fixed snapshot rather than a changing numeric result.

## Lifecycle Obligations

- **REQUIRED:** In Domain and Spec, name concepts, canonical definitions,
  governed routes, ownership, consumers, and delivery/sync boundaries.
- **REQUIRED:** In Contract, define provenance/freshness, grain/scope,
  access/privacy, correction handling, and deprecation behavior.
- **REQUIRED:** In Test and Refactor, retain evaluation evidence, incorporate
  material corrections, remove stale routes, and keep references synchronized
  with the governed model.
- **CONDITIONAL:** At release, maintenance, or retirement, communicate source or
  definition migrations to affected consumers and retain evidence required by
  project policy.
