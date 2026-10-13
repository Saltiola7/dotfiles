# Headless Fedora server profile

## Domain and scope

`machine_type=fedora-server` selects the personal shell/dev subset for a headless
Fedora host, initially Pi400 ARM64. This is server intent, not a Raspberry Pi
hardware selector. Dotfiles owns shared Bash startup, terminal configuration and
an explicit Fedora package installer. Dotfiles-ai retains AI tools, runtime/auth
configuration and independent source ownership. No desktop apps, containers,
workloads, boot settings, SSH policy, sudo policy or network changes are included.
Cycle FEDORA-SERVER-001 uses DBSCTR revision 3.29, Cloud and Security modules,
elevated risk, draft-PR delivery and owner-authorized Pi deployment.

## Behavior

- Given the server profile, a full chezmoi apply installs only the explicit
  terminal/configuration allowlist; desktop, macOS, work credentials, encrypted
  secrets, Omarchy hardware and image preparation targets remain excluded.
- Given SSH command execution, shell startup works without missing-tool errors,
  prompts, authentication, network access or forced interactive initialization.
- Given interactive Bash, existing portable Atuin/zoxide/Starship integrations
  initialize only when available, sharing portable configuration with other hosts.
- Given an explicit package-setup invocation, Fedora packages are installed from
  configured signed repositories using password-required sudo. Apply itself never
  prompts for sudo or installs packages. Repeating setup is safe; no upgrades,
  removal, services, firewall, reboot or shell changes are implied.
- Given an existing shell file or managed target, deployment backs it up privately
  before apply and verifies remote SSH afterward. Failures preserve evidence and
  backups; no private keys, Atuin sessions or secrets are copied into Git.

## Interfaces and contracts

Reuse `.bashrc`, `.bash_profile`, `.common_profile`, Atuin and Starship configuration,
plus the homelab CLI/inventory. Add `.config/fedora-server/dnf-packages.txt` and an
explicit `fedora-server-setup` helper. The helper validates Fedora and root/user
execution mode, reads a constrained package list and delegates only to DNF install.
Baseline tools: chezmoi, Git, Python, uv, Node/npm, Neovim, tmux, ripgrep, fd, fzf,
direnv, Starship, Atuin and zoxide, subject to confirmed repository availability.
No downloaded installer pipes, external repos or unverified binaries are needed.

Reuse the portable `lmsh` shell branch where suitable; platform-specific branches
remain unchanged. Disable unattended Atuin synchronization on the server until
owner sign-in is explicitly performed. History/auth state remains host-local.
Private initialization data uses the owner's existing identity without publishing
it. Fedora release support and architecture are checked on deployment. No workload
or AI runtime is silently assigned by selecting this profile.

## Validation, rollout and recovery

Authorities: isolated chezmoi managed-target/render/apply tests; Bash syntax and
noninteractive smoke tests; explicit installer negative/success/idempotent tests;
existing shell/profile and source-ownership regression tests; trusted Pi SSH probes.
First obtain passing local tests, then review staged files and package plan.
Owner enters Pi sudo password privately for signed package installation. Initialize
chezmoi on Pi without running all source scripts, inspect its plan, back up changed
files and apply only the server allowlist. Verify a new SSH login, installed tools,
clean noninteractive command output, profile identity and absence of desktop targets.
Rollback uses private file backup and a reviewed earlier source revision. Package
rollback is a separately reviewed operation; do not remove dependencies blindly.
No reboot is needed. No private Git credential or private SSH key goes to Pi.

## Visual Evidence

Boundary and data/trust: required, use the public/private boundary diagram and Text
Equivalent in homelab topology README. Personal shell targets and dotfiles-ai retain
separate ownership; private auth remains local. Operator owns these boundaries and
updates their descriptions whenever ownership changes. Interaction: not_applicable
to an additional diagram; ordered rollout above defines sudo and apply handoffs.
State: not_applicable; profile selection is explicit, not a daemon state machine.
Schema: not_applicable; no schema change. Dependency/deployment: required, use the
canonical homelab topology and Pi target. Quantitative: not_applicable; no workload
performance or capacity promise.

## Gate applicability

Domain, Behavior, Spec, Contract, Test-driven implementation, Refactor and
Review/Integrate required. Release not applicable: no packaged artifact.
Deploy, Operate and Maintain/Retire required for the live long-lived server profile.
No gate exception is approved. Current results remain in the private Cycle Record;
completion evidence is appended to the bounded-context changelog.
