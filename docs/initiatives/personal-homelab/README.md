# Personal homelab initiative

Status: Discovery specifications complete for first delivery. Context map approved;
implementation launch still requires exact preflight approval.
Method: DBSCTR V3 revision 3.29. Coordinator and both context homes: dotfiles.

The owner needs a trustworthy map of personal machines, guests, containers and
storage, and an explicit development target for each relevant environment. The
first dependent provisioning slice brings up a Raspberry Pi 400 over Ethernet
without monitor or keyboard. Workloads are declared, not moved.

## Approved boundaries and order

1. `homelab_topology`: identities, hosting relationships, purposes, desired versus
   observed state, development targets and a diagram/table output.
2. `raspberry_pi_bootstrap`: independently reproducible macOS-launched preparation,
   explicit SSD flashing, headless first access, enrollment and recovery. Depends
   on a declared target identity from topology.
3. Existing chezmoi and AI distribution contexts retain user/application ownership.
   Their implementation is not duplicated here.

The manifest gives stable requirement coverage and independent delivery slices.
Owner-approved scope is personal infrastructure only. External dependencies may
be named logically but are not deployment targets. No workload migration,
existing VM replacement, cloud purchase or public service exposure is included.

## Settled scope and validation limits

- Scope settled: infrastructure only; phones and tablets are omitted.
- Privacy settled: public-safe committed topology plus private local connection
  inventory. No connection overlay is committed.
- MacBook Pro remote identity is owner-confirmed and remains private. Pi USB
  boot from this drive has not been attempted; HP root-level Podman RustDesk inventory is observed; virtualization remains unknown.
- Personal Lima backend is selected; tools, architecture and free space verified.
  Interactive sudo and image provenance are implementation checks; VM and services
  remain running.
- Password-required sudo with key-only SSH is owner-approved.

## Validation and launch

Configured repository authorities are pytest on Python 3.12–3.14, chezmoi
rendering/isolation and affected shell checks. No dedicated topology publication
or privacy authority was identified during bounded repository inspection. Existing scoped QA/diff review and future public/private output tests are the
selected publication evidence; no additional scanner or denylist is invented.
Current candidate documents contain logical names and no connection endpoints,
serials or credentials. They remain local until scoped review and delivery gates pass.

Run initiative-check after manifest changes. Before implementation, run the
slice receipt and real DBSCTR begin preflight in a clean isolated checkout, then
present the exact launch digest for approval. No disk-write approval is implied
by context-map approval.
