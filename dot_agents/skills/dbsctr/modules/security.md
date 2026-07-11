# DBSCTR Module: Security

## Applicability

- **REQUIRED:** Core lifecycle work considers trust boundaries, secrets, dependencies, and unsafe input.
- **CONDITIONAL:** Load this module when the Engineering Profile or new evidence identifies elevated or critical security or data impact.
- **CONDITIONAL:** Load for authentication, authorization, sensitive data, public interfaces, external integrations, production access, supply-chain changes, or incident remediation when risk is elevated or critical.
- **PROJECT POLICY:** Risk classification, regulatory obligations, data classes, and control authorities come from the Engineering Profile and project artifacts.
- **EXAMPLE:** A routine local refactor with no boundary or data impact may retain core security considerations without loading this module.

## Engineering Profile Extensions

- **REQUIRED:** Record assets, data classification, trust boundaries, entry points, identities, privileged operations, dependencies, and accountable security/operational owner where applicable.
- **REQUIRED:** Record material threats, impact, risk level, selected controls, and evidence authorities.
- **CONDITIONAL:** For elevated or critical work, record abuse cases, assumptions, failure modes, recovery needs, and residual risk.
- **PROJECT POLICY:** Threat-model format, review roles, retention rules, regulatory controls, and approved secret/key systems are project-defined.
- **EXAMPLE:** A boundary map can show user input, service calls, storage, administrators, and third-party integrations.

## Required Outcomes

- **REQUIRED:** Define and validate trust boundaries; validate untrusted input before use and fail safely on invalid or unauthorized requests.
- **REQUIRED:** Keep secrets out of source, logs, artifacts, and error output; use approved secret handling and limit access to need.
- **REQUIRED:** Identify direct and transitive dependencies, assess known relevant risk, and preserve provenance appropriate to the deliverable.
- **REQUIRED:** Apply least privilege to identities, permissions, and data access; authenticate and authorize separately where both apply.
- **REQUIRED:** Minimize collection, access, retention, and disclosure of personal or sensitive data; protect it in transit and at rest when applicable.
- **REQUIRED:** Produce actionable security failures without exposing sensitive detail, and preserve audit evidence where policy requires it.
- **CONDITIONAL:** For elevated or critical changes, document threat-driven mitigations and test controls at each affected boundary.
- **CONDITIONAL:** For critical work, require independent review where a qualified reviewer is available and explicit rollback/recovery evidence.
- **PROJECT POLICY:** Cryptographic choices, log retention, access review, vulnerability handling, and compliance evidence follow project policy.
- **EXAMPLE:** Input validation may be proven by contract tests, integration tests, review evidence, or another configured authority.

## Conditional Controls

- **CONDITIONAL:** When handling credentials, tokens, keys, or sessions, define issuance, storage, rotation, revocation, expiry, and exposure response.
- **CONDITIONAL:** When auth or authorization changes, test denied as well as allowed access and prevent privilege escalation or cross-tenant access.
- **CONDITIONAL:** When accepting files, structured payloads, URLs, commands, templates, or serialized data, constrain parsing, execution, outbound access, size, and resource use to the threat model.
- **CONDITIONAL:** When a dependency, build, or release path changes, verify source integrity, review scope, artifact provenance, and update handling according to risk.
- **CONDITIONAL:** When sensitive data is stored, transferred, exported, or deleted, define access, retention, deletion, recovery, and disclosure controls.
- **CONDITIONAL:** When an incident or vulnerability is active, preserve relevant evidence, contain safely, communicate through approved paths, and track remediation to closure.
- **PROJECT POLICY:** Required approvals, segregation of duties, disclosure process, and incident ownership are project-defined.
- **EXAMPLE:** A signed artifact, reviewable build record, or controlled registry may provide supply-chain evidence; no mechanism is universal.

## Validation Capabilities

- **REQUIRED:** Map each applicable security outcome to a project-selected authority or evidence; missing capability is a gap, not a pass.
- **REQUIRED:** Validate trust boundaries, secret exposure prevention, dependency/supply-chain posture, and unsafe-input controls for affected scope.
- **CONDITIONAL:** For elevated or critical risk, validate threat scenarios, authorization decisions, data handling, logging/redaction, recovery, and incident readiness as applicable.
- **PROJECT POLICY:** The project selects scanners, tests, reviews, monitoring, and external assessments; do not install or mandate a universal scanner.
- **EXAMPLE:** Evidence may combine focused tests, code review, configuration inspection, dependency inventory, and monitored exercises.

## Lifecycle Obligations

- **REQUIRED:** Record applicable security gates, authorities, results, owners, and follow-up in the Gate Ledger.
- **REQUIRED:** A failed or unavailable required control blocks completion unless it is deferred or accepted as risk under the lifecycle contract.
- **REQUIRED:** Accepted security risk includes rationale, accountable owner, and expiry or review condition.
- **CONDITIONAL:** For elevated or critical work, carry threat, mitigation, residual-risk, release/deployment, and operational evidence through completion.
- **CONDITIONAL:** For supported or long-lived systems, evaluate vulnerability intake, dependency/runtime maintenance, incident readiness, deprecation, and secure retirement.
- **PROJECT POLICY:** Security review cadence, maintenance commitments, and retirement evidence are defined by project policy.
- **EXAMPLE:** A local change may rule out deployment evidence while retaining a documented maintenance obligation.
