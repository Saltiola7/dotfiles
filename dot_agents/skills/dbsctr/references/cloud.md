# Cloud / Platform / IaC References

Non-normative examples. They do not select a provider, tool, threshold, or gate.

## IaC and topology

- Terraform or Pulumi can render a reviewable plan and manage state; Kubernetes manifests or Kamal configuration can describe runtime delivery.
- A Pulumi component may return a typed dataclass such as `ClusterOutput`; this is an implementation option, not a module requirement.
- GCP, Hetzner, and Kubernetes are provider/platform examples. An environment may use Pulumi stacks, Terraform workspaces, variables, or another project-selected configuration mechanism.

## Stateful-data protection

- A project can combine a provider deletion-protection flag, IaC retain-on-delete behavior, and a non-empty-resource destroy guard. This three-layer pattern is an example, not a universal exact pattern.
- A database volume, bucket, or managed database can use provider backups, retention rules, and a tested restore runbook. The required retention and recovery objectives come from policy.

## Identity, networking, and secrets

- Kubernetes Workload Identity, GCP Workload Identity Federation, or short-lived cloud roles can replace service-account key files.
- Kubernetes NetworkPolicy, a cloud firewall allow-list, private endpoints, a Tailnet, and a bastion are possible boundary controls.
- Pulumi encrypted configuration, a cloud secret manager, 1Password injection, and Kubernetes Secrets are example secret authorities; project policy determines suitability.

## Cost and resilience

- Hetzner instance sizes such as `cpx11`, `cpx21`, and `cpx41` are sizing examples, not ceilings.
- KEDA cron or HTTP scaling can scale workloads to zero; autoscaling minima, maxima, schedules, budgets, and alerts are project policy.
- Spot/preemptible capacity can suit retryable batch work; it needs failure handling and recovery evidence.

## Delivery and provenance

- Kubernetes rolling updates, blue-green delivery, and `kamal rollback` are rollout and rollback examples.
- Kubernetes liveness, readiness, and startup probes are health-signal examples.
- GCP Artifact Registry or another registry can store images; a Git SHA tag is one immutable-identification convention, while `latest` avoidance may be project policy.

## Worked example

```text
Production service: private application runtime → managed database → object storage.
IaC: Terraform plan reviewed before authorized apply; state access limited to platform operators.
Identity: workload role grants database and storage actions needed by this service only.
Network: public ingress terminates at the gateway; database accepts application-network traffic only.
Data: backups retained per policy; restore runbook has named owner and last-test evidence.
Delivery: immutable image digest, staged rollout, health check, documented rollback.
Operations: logs, metrics, alert route, incident owner, and decommission retention decision.
```
