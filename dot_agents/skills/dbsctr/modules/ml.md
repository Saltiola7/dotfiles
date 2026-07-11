# ML / AI Module

## Applicability

- **REQUIRED:** Load this module for model training or serving, predictive or
  generative AI, embeddings, prompts, evaluation pipelines, or automated
  decisions derived from model output.
- **CONDITIONAL:** Load the Security module when ML/AI crosses a sensitive-data,
  security, regulated, financial, or safety boundary.
- **PROJECT POLICY:** Record applicability, risk, delivery intent, data/trust
  classification, operational owner, and downstream impact in the Engineering
  Profile.
- **EXAMPLE:** An embedding-based search feature and an LLM extraction pipeline
  both load this module.

## Engineering Profile Extensions

- **REQUIRED:** Record the system purpose, decision role, inputs, outputs,
  affected users or systems, and accountable owner.
- **REQUIRED:** Record lineage for data, features, model or prompt, evaluation,
  artifacts, and serving or inference path; identify their versions or immutable
  identities where available.
- **REQUIRED:** Record reproducibility inputs appropriate to the system,
  including data and ground-truth versions, code/configuration, dependencies,
  environment, and stochastic controls.
- **CONDITIONAL:** For human-impacting, regulated, safety-relevant, or
  consequential decisions, record affected populations, foreseeable harms,
  oversight role, and escalation authority.
- **PROJECT POLICY:** Define retention, access, provenance, approval, and model
  or prompt versioning rules in the applicable requirements, ADRs, or policies.
- **EXAMPLE:** A prompt template revision is an inference-lineage revision and
  receives a new version identity.
 
## Required Outcomes

- **REQUIRED:** Validate input, feature, and output schemas at their trust
  boundaries; reject, quarantine, or safely handle invalid data explicitly.
- **REQUIRED:** Evaluate changes against versioned, reviewable ground truth or
  other fit-for-purpose evidence that is separated from training or tuning where
  applicable.
- **REQUIRED:** Preserve a baseline and assess regression before accepting a
  model, prompt, data, feature, or serving change.
- **REQUIRED:** Define required quality, cost, latency, reliability, and
  compatibility outcomes for the stated decision role.
- **REQUIRED:** Define monitoring signals and an owner for production or other
  running systems.
- **PROJECT POLICY:** Thresholds, budgets, and acceptance criteria derive from
  requirements, approved baselines, regulation, or ADRs; record their source.
- **EXAMPLE:** Compare a candidate prompt to the approved prompt on a versioned
  review set before use.
 
## Conditional Controls

- **CONDITIONAL:** When input, feature, prediction, or outcome distributions can
  change materially, define drift signals, baselines, response owners, and
  re-evaluation or retraining triggers.
- **CONDITIONAL:** When bias, discrimination, unsafe content, manipulation, or
  material harm is plausible, assess relevant risks and define mitigations,
  escalation, and residual-risk evidence.
- **CONDITIONAL:** When automated output can materially affect people, assets,
  safety, or compliance, provide human oversight, override or appeal where
  appropriate, and a safe abstain/escalation path.
- **CONDITIONAL:** When a dependency, provider, model, or inference path can
  fail, define timeouts, bounded retries where safe, fallback or degraded mode,
  and downstream status propagation.
- **CONDITIONAL:** When retraining, re-embedding, or replacement is supported,
  define approval, validation, rollout, rollback, and compatibility controls.
- **PROJECT POLICY:** Choose providers, models, fallback behavior, and retention
  controls through project requirements or ADRs, not this module.
- **EXAMPLE:** Route malformed structured output to review rather than silently
  accepting it.
 
## Validation Capabilities

- **REQUIRED:** Select an authority or equivalent evidence for schema validation,
  reproducibility, evaluation, baseline/regression comparison, and required
  reliability behavior.
- **CONDITIONAL:** Select an authority or equivalent evidence for drift,
  bias/safety, human-oversight, cost, latency, and monitoring controls when they
  apply.
- **REQUIRED:** Record unavailable required capabilities as gaps, deferred work,
  or accepted risk in the Gate Ledger; do not infer a pass from an unconfigured
  tool.
- **PROJECT POLICY:** Project-selected evaluation harnesses, observability
  systems, and review processes are the authorities for their concerns.
- **EXAMPLE:** A replayable evaluation run can evidence prompt regression if it
  identifies the ground-truth version, prompt version, and baseline.
 
## Lifecycle Obligations

- **REQUIRED:** Carry lineage, evaluation, baseline, and validation evidence
  through applicable development and completion gates.
- **CONDITIONAL:** For running systems, monitor agreed quality, drift, cost,
  latency, failures, and fallback use; investigate material deviations.
- **CONDITIONAL:** For long-lived systems, define reassessment, retraining or
  replacement, deprecation, retention, and retirement triggers and ownership.
- **CONDITIONAL:** For elevated or critical risk, retain review, approval,
  rollback or recovery, and accepted-risk evidence appropriate to the impact.
- **PROJECT POLICY:** Release, deployment, incident, and retirement procedures
  follow the Engineering Profile and project policy.
- **EXAMPLE:** Retire a superseded model only after downstream consumers have
  migrated and required artifacts meet retention policy.
