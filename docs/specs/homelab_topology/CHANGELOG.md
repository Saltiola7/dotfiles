# Changelog

## 2026-10-12 — Verified Pi deployment observations

Updated existing Pi and SSD declarations after owner-approved physical deployment.
Trusted SSH, USB root growth, router IPv6, Tailscale and fresh reboot are verified;
attachment and administration edges are observed. Workload assignment remains
unassigned. Private endpoints and SSH identities are local; no other target was
changed. Router IPv4 DHCP and router-peer identity remain separate follow-ups.

## 2026-10-12 — Read-only target inventory

Added versioned public-safe declarations for 17 infrastructure targets and five
dependency edges, a standard-library `homelab` CLI, strict validation, deterministic
Mermaid/text output and explicit private local inspection. Hardware, hosting and
uncertain observations remain distinct; no workloads moved or disks written.

Validation: 23 scoped pytest checks passed, including isolated macOS/Omarchy
chezmoi installs, invalid input, hosting cycles, private omission and stale state.
Installed only CLI/declarations on the Mac and verified `validate`/`inspect pi400`.
No gate exceptions. Kernel commits: fc7d032 and 10f1043; lifecycle closure commit
is recorded in the private Cycle Record. Intended Final Push: feature branch and
draft PR to Saltiola7/dotfiles main. Pi provisioning and physical boot remain pending.
Backup policies, router links and HP virtualization remain explicitly unverified.

## 2026-10-12 — DHCP recovery and planned Flint boundary

Recorded evidence and uncertainty for provider DHCP exhaustion and recovery;
verified Pi IPv4 internet and six-hour lease, plus 242 free addresses in the owner
router table. Updated observed provider gateway/extender and Pi network links.
Declared a future Flint gateway with separate household DHCP/DNS/firewall,
initial double NAT, compatibility checks, cutover approval and rollback. No model,
private addressing, workload move or runtime network change is implied.
