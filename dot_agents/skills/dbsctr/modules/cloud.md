# Cloud / Platform / IaC Module

## Applicability

- **REQUIRED:** Load this module when a Lifecycle Cycle creates, changes, or retires cloud, platform, infrastructure-as-code, runtime, network, deployment, or managed-service resources.
- **CONDITIONAL:** Load it for application work when the change alters an operational dependency, deployment path, trust boundary, or production runtime assumption.
- **PROJECT POLICY:** The Engineering Profile identifies supported environments, delivery intent, operational owner, trust/data classification, and applicable platform policies.
- **EXAMPLE:** A documentation-only change with no runtime or infrastructure effect does not load this module.

## Engineering Profile Extensions

- **REQUIRED:** Record topology, resource ownership, environment purpose, stateful data locations, public interfaces, and upstream/downstream dependencies.
- **REQUIRED:** Record the authoritative IaC state, plan/review workflow, drift-detection authority, and operational owner.
- **REQUIRED:** Record identity boundaries, secret classes and authorities, network exposure, resilience target, recovery owner, and delivery/rollback responsibility.
- **CONDITIONAL:** Record regulated-data, residency, retention, availability, recovery, cost, and supply-chain obligations when they apply.
- **PROJECT POLICY:** Project requirements, ADRs, and approved service policies select providers, tools, thresholds, budgets, and implementation patterns.
- **EXAMPLE:** Environments may differ in scale or credentials while preserving the same declared topology and security outcomes.

## Required Outcomes

- **REQUIRED:** Infrastructure topology, ownership, dependencies, and environment differences are documented and traceable to the affected change.
- **REQUIRED:** IaC changes have a reviewable plan; state access is controlled; drift is detected or its absence is recorded as a capability gap or risk.
- **REQUIRED:** Workload and human identity use least privilege, are attributable, and avoid long-lived credentials where a safer supported mechanism exists.
- **REQUIRED:** Secrets are classified, kept out of source and unapproved logs, protected in transit and at rest, and rotated, revoked, or replaced according to policy.
- **REQUIRED:** Networks are private by default; each public path, ingress/egress rule, and trust boundary has an owner and justification.
- **REQUIRED:** Stateful resources have deletion, retention, backup, restore, and recovery obligations appropriate to their data and business impact.
- **REQUIRED:** Cost-affecting resources have explicit bounds, ownership, and a detection or review path for unexpected spend.
- **REQUIRED:** Resilience requirements cover relevant dependency failure, backup integrity, and restore feasibility.
- **REQUIRED:** Build and deployment inputs have traceable provenance; deployed images or artifacts are identifiable and subject to the project supply-chain policy.
- **REQUIRED:** Delivery defines rollout, health evidence, and rollback or recovery before an environment change is authorized.
- **REQUIRED:** Running systems provide appropriate observability, incident ownership, and decommission obligations, including data retention and access removal.

## Conditional Controls

- **CONDITIONAL:** Production, sensitive data, irreversible operations, or critical risk require explicit recovery and rollback evidence; restore capability is exercised when feasible.
- **CONDITIONAL:** Public exposure, cross-boundary connectivity, or privileged access requires threat-appropriate network and identity controls plus audit evidence.
- **CONDITIONAL:** Autoscaling, metered services, or material spend require enforceable or reviewable cost bounds and alerts or reports appropriate to the risk.
- **CONDITIONAL:** Containerized or artifact-based delivery requires provenance, vulnerability handling, and immutable-identification controls appropriate to policy.
- **CONDITIONAL:** Decommissioning requires an approved retention/disposal decision, revocation of access, and removal or transfer of operational ownership.
- **PROJECT POLICY:** Required approvals, segregation of duties, retention periods, recovery objectives, and review frequency come from project policy, regulation, or ADRs.
- **EXAMPLE:** A disposable local development environment can rule out backup and incident-response controls with recorded rationale.

## Validation Capabilities

- **REQUIRED:** Select project authorities or equivalent evidence for IaC syntax and policy validation, plan review, state access, and changed-resource topology.
- **REQUIRED:** Validate applicable identity, secret-handling, network exposure, deletion/data protection, cost bounds, provenance, rollout health, rollback, and observability outcomes.
- **CONDITIONAL:** Test restore, failover, rollback, and incident procedures for elevated or critical changes when a safe authority exists.
- **CONDITIONAL:** Record missing validation capability as a gap, deferral, or accepted risk; never infer a pass from an unavailable preferred tool.
- **PROJECT POLICY:** The Gate Ledger names each authority, evidence location, owner, and expiry/follow-up for non-passing statuses.
- **EXAMPLE:** A reviewed dry-run plan plus a policy report can evidence a local IaC change without applying it.

## Lifecycle Obligations

- **REQUIRED:** During Domain and Contract work, define resource ownership, trust boundaries, state/data lifecycle, failure modes, and delivery/recovery contracts before implementation.
- **REQUIRED:** During Test and Refactor work, preserve or improve the evidence for applicable platform outcomes and validate affected scope.
- **CONDITIONAL:** Release and Deploy gates apply only when producing or changing an environment; prepare plans without external writes until authorized.
- **CONDITIONAL:** Operate, Maintain, and Retire gates apply to running, supported, or long-lived systems and record health, incidents, dependency lifecycle, retention, and decommission decisions.
- **PROJECT POLICY:** The Engineering Profile and Gate Ledger determine applicability and status; commits, applies, publications, and deployments remain repository and user-authorized actions.
- **EXAMPLE:** A planned production migration may validate ordering, health checks, and rollback instructions while stopping before execution.
