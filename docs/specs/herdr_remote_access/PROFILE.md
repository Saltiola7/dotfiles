# Herdr remote access Engineering Profile

Owner: dotfiles maintainer. Deliverable: chezmoi-managed SSH alias
configuration enabling `herdr --remote` attach from controller hosts to
Herdr servers on personal tailnet targets. No new product UI or public
service.

Languages: SSH client configuration, chezmoi source naming and permissions,
Markdown specifications. Supported scope: existing personal hosts on the
private tailnet — three controllers (two Omarchy Linux, one macOS) and the
Linux targets they attach to. No third-party or employer hosts.

Compatibility: source already owned a mac-mini-only managed config; this
cycle makes that ownership uniform across controllers instead of introducing
a second file. Adoption must not silently discard pre-existing local content
on unverified hosts; alias stanzas are additive and render no wildcard
`Host *` stanza on Linux controllers, so unrelated connection defaults stay
untouched there — mac-mini's legacy globals render only behind a darwin
condition. Rendered file mode 600, directory 700. The public repository must
never contain credentials, key material, tailnet addresses, or the tailnet
DNS domain; aliases and bare MagicDNS host names only. The pre-existing
darwin-scoped encrypted key file is retained unchanged and never renders on
Linux controllers.

Trust boundaries: public source repository versus private tailnet. Source
ships connection names only. Authentication stays outside the repository:
Linux targets authenticate through Tailscale SSH; the macOS target uses
plain sshd with operator-authorized public keys. Enabling Tailscale SSH on
each host and starting each target's Herdr server are operator runbook
actions, not repository state.

Authorities: `ssh -G` alias-resolution probes, chezmoi rendering/diff and
targeted apply, file-mode checks, live `herdr --remote` attach smoke per
target, repository pytest suite and semgrep CI for published content.

Lifecycle: Development Kernel and Review/Integrate required. Deploy required
— managed config applied across controllers plus prerequisite runbook
enablement. Operate required — live attach verification. Maintain/Retire
required — host retirement and alias drift. Release not applicable: no
package or versioned artifact is published.

## Visual Evidence

Boundary, interaction, state, data/trust, schema, dependency/deployment and
quantitative: not_applicable; this profile declares defaults, while the
feature contract in README.md owns topology and trust evidence.
