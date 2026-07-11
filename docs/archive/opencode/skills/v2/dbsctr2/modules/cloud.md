# DBSCTR2 Domain Module: Cloud / Platform / IaC

**Applies when:** Task involves infrastructure-as-code (Pulumi, Terraform), cloud resources (GCP, AWS,
Hetzner), deployment (Kamal, k8s), scaling (KEDA), networking (firewalls, Tailnet), or platform services
(managed databases, object storage, registries).

This module extends Phases 1 and 4 of core DBSCTR2 with cloud/platform-specific patterns.

---

## Phase 1 Extensions (Domain)

### Infra-as-Domain-Types

Cloud resources ARE domain concepts. Every IaC component returns a typed, documented output:

```python
@dataclass
class GkeOutput:
    """Output of create_gke_cluster().

    Provides the GKE cluster resource and Fleet metadata needed by
    downstream components (K8s provider, Helm releases, KEDA).
    """
    cluster: container.Cluster
    endpoint: pulumi.Output[str]
    ca_cert: pulumi.Output[str | None]
    membership_id: pulumi.Output[str]
```

**Rules for component outputs:**
- Replace ad-hoc tuples, dicts, and raw resource references with typed dataclasses
- Each field has a docstring explaining what downstream consumers need it for
- TYPE_CHECKING imports for Pulumi resource types (avoid import-time SDK loading)
- Group outputs by bounded context (GKE, Storage, Networking, Identity, Orchestration)

### Resource Topology

Sketch the dependency graph of infrastructure components:

```
IaC Component Graph:
  create_iam() → WorkloadIdentityOutput
    ↓ (SA bindings)
  create_gke_cluster() → GkeOutput
    ↓ (k8s provider)
  create_shared_infra(gke) → SharedInfraOutput (postgres, redis, keda)
    ↓ (connection strings)
  create_seo_orchestration(shared, identity) → OrchestrationOutput
    ↓ (Prefect + workers)
  create_tailnet_access(gke) → AccessOutput (ingress)
```

Document dependency flow — which component output feeds which downstream component's input.
This IS the infra lineage.

### Environment Model

Declare environments upfront:

| Environment | Purpose | Differences from prod |
|-------------|---------|----------------------|
| **prod** | Live workloads | Full resources, real data, alerts enabled |
| **dev** | Local development | Docker Compose, minimal resources, mocked externals |
| **staging** (if exists) | Pre-prod validation | Reduced scale, prod-like topology |

**Rule:** Pipeline logic and IaC component logic MUST be environment-agnostic. Differences handled
ONLY by: Pulumi stack config, env vars, and resource sizing parameters.

### ADR Practice

When an infrastructure decision has meaningful tradeoffs, record it:

```
docs/adr/ADR-NNN-<slug>.md

Format:
- Title
- Status (proposed / accepted / superseded by ADR-NNN)
- Context (what problem, what constraints)
- Decision (what we chose)
- Consequences (tradeoffs accepted)
```

Reference ADRs in code comments and IaC component docstrings (e.g., "ADR-006 triple-layer
deletion protection"). This creates bidirectional traceability.

---

## Phase 4 Extensions (Contract)

### Deletion Protection Contracts

Every stateful resource (databases, buckets, volumes) requires documented protection:

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **Resource-level** | `protect=True` (Pulumi) / `deletion_protection` | Prevent accidental `pulumi destroy` |
| **Retain-on-delete** | `retain_on_delete=True` | If removed from code, orphan don't destroy |
| **Force-destroy guard** | `force_destroy=False` | Prevent deletion of non-empty buckets/DBs |

**Rule:** All three layers required for production stateful resources. Document which ADR mandates this.

### Identity Contracts

| Principle | Implementation |
|-----------|---------------|
| **Workload Identity over key-files** | K8s SA → GCP SA binding; no JSON key files in pods |
| **Least-privilege IAM** | Each SA gets only the roles it needs; document role list |
| **Protected bindings** | IAM bindings set `protect=True` to prevent accidental removal |
| **Multi-org WIF** | Attribute conditions restrict cross-org token exchange |

Example contract:
```
## Identity Contract: seo-worker SA
- Roles: storage.admin (orchestration bucket), bigquery.jobUser, bigquery.dataEditor (pipeline dataset)
- Binding protection: all protect=True
- Access method: Workload Identity (no key files)
- K8s SA: seo-worker in orchestration namespace
- ADR: ADR-014 (WIF multi-org attribute condition)
```

### Blast-Radius Contracts

Limit the damage any single misconfiguration can cause:

| Contract | Implementation |
|----------|---------------|
| **Firewall allow-list** | Only SSH + HTTP(S) + ICMP inbound; all else blocked |
| **Network isolation** | Private cluster endpoint; access via Connect Gateway or Tailnet only |
| **Namespace isolation** | Each workload in its own K8s namespace; no cross-namespace access without explicit NetworkPolicy |
| **Volume locality** | Server location == volume location (invariant; prevent cross-region latency/cost) |

### Locality Invariants

Physical constraints that MUST be enforced:

```python
# Contract: volume must be in same location as server
assert volume.location == server.location, "Volume/server location mismatch"

# Contract: builder architecture must match server type
# cpx11 = x86_64 → Kamal builder.arch: amd64
```

Document these in spec as invariants; enforce via assertions in IaC code or Pulumi policy packs.

### Cost Contracts

Treat cost like volume bounds in data pipelines:

| Contract | Example |
|----------|---------|
| **Instance ceiling** | Server type ≤ cpx21 in dev; ≤ cpx41 in prod |
| **Storage ceiling** | Volume ≤ 50GB (resize-on-demand, never over-provision) |
| **Scale-to-zero** | KEDA cron scaler: 0 replicas outside work window; alert if pods running off-hours |
| **Autoscale bounds** | min=0, max=3 for workers; never unbounded |

### Scale-to-Zero / Cost-Optimization Patterns

| Pattern | When to use | Implementation |
|---------|-------------|----------------|
| **KEDA Cron Scaler** | Batch workloads with known schedule | ScaledObject with cron trigger (e.g., 23:50-01:30 PT) |
| **KEDA HTTP Scaler** | Request-driven apps with idle periods | Scale to 0 when no HTTP traffic |
| **Spot/Preemptible** | Fault-tolerant batch jobs | Node pool with spot VMs + Prefect retries |
| **Volume detach** | Dev environments | Detach volumes when server stopped |

### State Persistence Contracts

| Resource | Contract |
|----------|----------|
| **Block volume** | Survives server destruction; attached via IaC with automount |
| **GCS bucket** | Triple-layer deletion protection; lifecycle rules for archival |
| **Database** | Volume-backed; backup schedule documented; restore procedure tested |
| **Secrets** | Pulumi state or external secret manager; never in code/env files committed to git |

### Deployment Contracts (Kamal / K8s)

| Contract | Rule |
|----------|------|
| **Zero-downtime deploy** | Rolling update or blue-green; health check must pass before traffic shift |
| **Rollback procedure** | Document how to revert (Kamal: `kamal rollback`; k8s: previous ReplicaSet) |
| **Health checks** | Liveness + readiness probes defined; startup probe for slow-init containers |
| **Resource limits** | CPU/memory requests and limits set for all containers; no unbounded pods |
| **Image provenance** | Images from own Artifact Registry; tag = git SHA; no `:latest` in prod |

### Audit & Compliance Contracts

| Contract | Implementation |
|----------|---------------|
| **Data access audit logging** | Enabled on all storage buckets handling user data |
| **IAM audit** | Changes to IAM bindings trigger alert |
| **No hardcoded credentials** | Secrets via env injection (Pulumi config, 1Password, k8s secrets); scan for leaked creds |
| **Encryption at rest** | Default for managed services; explicit for self-managed (volume encryption) |

---

## Rules (Cloud / Platform)

- Every IaC component returns a typed dataclass output — never raw resources or dicts
- All stateful resources have triple-layer deletion protection (or documented exception with ADR)
- Workload Identity over key-files — no SA JSON keys in containers
- All IAM bindings are protected (`protect=True`) and documented per-SA
- Server/volume/resource locality is an enforced invariant, not a suggestion
- Cost bounds are explicit contracts: instance types, autoscale ceilings, scale-to-zero windows
- Single Pulumi project per logical platform; stacks separate environments
- Private-by-default networking; public access requires explicit allow-list + ADR justification
- Secrets never committed to git — use Pulumi config (encrypted), external secret managers, or 1Password injection
- ADRs required for: new cloud provider, access-model changes, cost-significant architecture decisions, deletion-protection exceptions
- Infrastructure changes go through same DBSCTR2 pipeline as application code — Domain types first, then contracts, then implementation

---

## Worked Example: Shared Django Server (Hetzner + Kamal)

```
# Domain (Phase 1)
Component: django_server (Hetzner cpx11, Debian 12, Ashburn VA)
Volumes: tsc-postgres-data (10GB ext4), mlc-postgres-data (10GB ext4)
Network: tsc-firewall (SSH + HTTP/S + ICMP only)
Deployment: Kamal (rolling, amd64 builder)
DNS: Cloudflare (proxied, managed separately in dns.py)
Topology: Single server → 2 Django apps (tsc + mlc) → 2 Postgres volumes

# Contracts (Phase 4)
Locality: server.location == volume.location == "ash" (invariant)
Architecture: server_type cpx11 = x86_64 → Kamal builder.arch: amd64 (invariant)
Firewall: inbound allow SSH(22) + HTTP(80) + HTTPS(443) + ICMP only; all else DROP
Volume persistence: survives server destruction; automount=True
Cost ceiling: cpx11 (2 vCPU, 4GB); upgrade requires explicit decision
State: Postgres data on attached volumes, not ephemeral disk
Deployment: zero-downtime rolling via Kamal; rollback = `kamal rollback`
Secrets: .env via 1Password injection; never in git
```

## Worked Example: GKE Platform (GCP)

```
# Domain (Phase 1)
Components: GKE cluster, GCS buckets (DVC, orchestration, CDN logs),
  Artifact Registry, Workload Identity SAs, KEDA, Tailnet access
Topology: see Resource Topology graph above
Environments: prod (GKE Standard Zonal), dev (Docker Compose local)
ADRs: 004 (Connect Gateway), 005 (single project/stack), 006 (deletion protection),
  007 (KEDA cron), 008 (Tailnet-only), 014 (WIF multi-org), 015 (Standard Zonal)

# Contracts (Phase 4)
Deletion protection: all GCS buckets + volumes have triple-layer (ADR-006)
Identity: Workload Identity for all pod-to-GCP access (ADR-014)
Network: private cluster endpoint; access via Connect Gateway (ADR-004) + Tailnet (ADR-008)
Scale: KEDA cron 23:50-01:30 for nightly batch; scale-to-zero outside window (ADR-007)
Cost: Standard Zonal (not Autopilot — ADR-015); max 3 worker pods
Audit: storage data-access audit logging on all buckets with pipeline data
Registry: us-central1-docker.pkg.dev/project/repo; images tagged with git SHA
Secrets: Pulumi stack config (encrypted); WIF for runtime access
```
