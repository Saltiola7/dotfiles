# Raspberry Pi Bootstrap Engineering Profile

Owner: personal dotfiles maintainer/operator. Internal infrastructure deliverable;
no synthetic Product Intent artifact is required. Home repository: dotfiles.
Applicable modules: Cloud/Platform/IaC and Security; Python module when Python
implementation is selected. Existing personal and AI target ownership must remain
separate. Public documentation must not contain credentials or private connection
inventory. History and node credentials are never provisioning source.

Authorities: configured pytest (Python 3.12–3.14), focused schema/behavior tests,
chezmoi target/rendering checks for managed files, source review and live read-only
observations. A missing required capability stays unavailable, not passed.

Runtime: macOS launches a existing personal Lima ARM64 Fedora preparation backend; Raspberry
Pi 400 runs Fedora Minimal aarch64 from its external USB SSD. Existing Parallels guests cannot prepare images. Existing personal Lima
services must remain unchanged. Fedora target input must be pinned and publisher-authenticated before
preparation. Existing Lima backend identity/capabilities are verified before use. The operator owns physical power/cabling and Tailscale enrollment.

Interfaces: explicit plan/prepare/flash/verify operations; target IDs come from
homelab_topology. Private key material stays on the administrator device. SSH host
identity is generated per target and verified through trusted prepared-image
provenance or a separate trusted channel, never blindly accepted on the LAN.

Risk: critical for the flash slice because selecting a wrong device causes
irreversible data loss. Fresh physical-device identity, immutable prepared-image
identity, explicit target-bound consent and recovery evidence precede writes.
No recurring apply hook invokes flashing. Existing flashed state may be replaced
only after the precise disk-write operation is approved.

Kernel, Review/Integrate, Release (prepared image identity), Deploy (disk write and
first boot), Operate (SSH/network health) and Maintain/Retire (Fedora EOL, reimage,
credential revocation and disposal) are required. Prepared images and owned staging
storage have a bounded local retention/cleanup policy; no image is committed to
Git. USB firmware support remains unverified; absent microSD limits recovery.

Cycle scope may deliver preparation separately from flash/boot. Preparation is
elevated risk (privileged image modification and authentication artifacts);
flash/boot is critical (physical disk erasure). Each slice retains required
provenance, artifact release, backend deployment/health and maintenance evidence;
image preparation never claims physical Pi boot evidence.
