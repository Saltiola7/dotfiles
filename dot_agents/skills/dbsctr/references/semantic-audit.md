# Semantic Reconciliation Audit Protocol

Use only after `dbsctr_audit` pins one commit and inventories lifecycle artifacts.
This protocol produces a report; it never changes files, lifecycle state, gates,
evidence, branches, worktrees, external systems, or delivery targets.

## Inputs

- Resolved immutable commit ID and deterministic audit inventory.
- Bounded-context README/BACKLOG/CHANGELOG and applicable decisions/contracts at
  that commit.
- V3.8 Evidence Envelope metadata when relevant; never read withheld content.
- Dirty-overlay paths as excluded context only.
- Optional private local references only after explicit user authorization. Pin
  their commit, then run a separate `dbsctrctl inspect` invocation rooted in that
  repository. Use only bounded Git-object actions; never read its filesystem
  overlay. Treat it as comparison material, never project authority or
  publishable source.

## Authority Order

1. Project policy, contracts, decisions, and explicit user intent.
2. Authoritative implementation, tests, schemas, manifests, and configured CI at
   the resolved commit.
3. Valid Evidence Envelope metadata bound to the applicable commit/gate.
4. Current lifecycle artifacts whose claims are being checked.
5. Graph inference and authorized private/local references as routing or
   comparison hints only.

Never choose the convenient source merely to make artifacts agree.

## Claim Trace

For each material lifecycle claim:

1. Assign a stable report-local `claim_id`.
2. Cite the claim artifact and exact committed path/location.
3. Use `dbsctr_inspect` against the already resolved commit for bounded
   `read`, `tree`, `search`, and `object` evidence.
4. Record supporting, contradicting, missing, or unavailable evidence with exact
   committed locations and authority level.
5. State confidence as `high`, `medium`, or `low` and explain uncertainty.
6. Select exactly one classification using this decision order; stop at the
   first matching rule:
   1. `out_of_scope` when the approved audit boundary cannot evaluate the claim.
   2. `missing_artifact` when an applicable contract requires an absent artifact.
   3. `authority_conflict` when the highest applicable authority level contains
      unresolved disagreement.
   4. `historical_unlabelled` when a historically true statement is presented as
      current without a historical label.
   5. `stale_evidence` when the claim's only demonstrated defect is evidence that
      no longer matches identity, scope, binding, or validity.
   6. `confirmed_drift` when the highest applicable authority contradicts the
      current claim and none of the earlier rules applies.
   7. `consistent` when sufficient authoritative evidence supports the claim and
      no applicable contradiction exists.
   8. `unverified_claim` otherwise.

   Definitions:
   - `consistent`: authoritative evidence supports the claim.
   - `confirmed_drift`: authoritative current evidence contradicts the claim.
   - `stale_evidence`: cited evidence no longer matches its identity, scope,
     binding, validity window, or current claim.
   - `missing_artifact`: an applicable contract requires an artifact that is
     absent at the resolved commit.
   - `authority_conflict`: applicable authorities disagree and precedence does
     not resolve the conflict safely.
   - `historical_unlabelled`: historical truth is presented as current without
     an explicit historical label.
   - `unverified_claim`: available evidence neither proves nor contradicts the
     claim.
   - `out_of_scope`: the claim cannot be evaluated within the pinned repository,
     approved references, and audit boundary.

Absence of contradiction is not `consistent`; use `unverified_claim` when proof
is missing. Graph paths never prove a claim.

## Report Shape

Return:

```text
mode: lifecycle_semantic_reconciliation
commit: <full object id>
dirty_overlay_excluded: <paths/count/truncation from deterministic audit>
contexts: <audited bounded contexts>
summary: <counts by classification and severity>
inventory_findings[]: <unchanged deterministic audit findings>
findings[]:
  claim_id, context, classification, severity, confidence
  claim, claim_location
  evidence[]: authority, relation, location, excerpt_or_metadata
  rationale, uncertainty, remediation_cycle
private_references[]: approved, resolved_commit, purpose, public=false,
  authoritative=false
```

Severity is `critical`, `high`, `medium`, `low`, or `informational`; it reflects
impact, not confidence. Omit private machine paths, credentials, environment
values, and withheld evidence content.

## Completion

- Report every material claim checked, including `consistent` and `out_of_scope`.
- Separate deterministic inventory findings from semantic findings.
- Propose collision-safe remediation cycles by bounded context, but do not start
  them without explicit approval.
- Keep `/qa full` separate: QA executes configured quality authorities; this
  audit reconciles lifecycle claims and source evidence.
