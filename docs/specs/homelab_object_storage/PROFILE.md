# Homelab Object Storage Engineering Profile

Operator-owned private development infrastructure in personal dotfiles. Fedora
ARM64 Raspberry Pi 400; native RustFS binary and systemd user service. Cloud and
Security modules apply; elevated risk. This is a bounded single-node development
service, not a high-availability or production-capacity commitment.

Interfaces: S3 path-style requests, private Tailscale TCP forwarding, separate
object data and owner-only credential files. Public source owns version, digest,
resource limits and setup/update procedures. Private endpoints, passwords, node
identities and credential files are excluded from source.

Authorities: scoped pytest, shell/Python syntax, immutable release checksum,
systemd configuration, denied requests, S3/DVC roundtrip in an isolated test
bucket, limits/pressure inspection and fresh startup checks. Every kernel,
review, deployment, operations and maintenance gate applies. Release does not:
no public package or hosted artifact is published.

Preserve Samba, Tailscale SSH, existing data and backup jobs. No disk formatting,
workload migration or existing DVC remote change. Important object data requires
a separately verified consistent backup; a running service is not redundancy.
