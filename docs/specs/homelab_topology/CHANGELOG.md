# Changelog

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
