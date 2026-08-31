# Remote Workspace Profile Engineering Profile

| Concern | Default |
|---|---|
| Deliverable and owner | Owner-only personal chezmoi overlay; operator owned |
| Languages and modules | Go templates, TOML, Bash, and Python contract tests; Security module |
| Runtime and platform | CentOS Stream 10 x86_64 remote workspace; Bash; Atuin client; Starship; Yazi |
| Interfaces | Chezmoi `machine_type=remote-workspace`, machine-local Atuin endpoint, and deny-by-default target allowlist |
| Compatibility | Existing macOS and `lmsh` rendering remains unchanged; the shared `dotfiles-ai` source retains agent and runtime ownership |
| Trust/data | Shell history, account identity, and Atuin keys are sensitive and remain in user-local stores |
| Delivery | Explicit owner initialization and apply only after the shared foundation is ready |
| Operations | Render, target-overlap, shell syntax, Atuin sync, idempotency, and rollback checks |
| Maintenance | Pin portable releases, preserve disabled defaults, and remove the overlay without deleting user history or credentials |
| Authorities | Full `pytest`, isolated chezmoi rendering, managed-target comparison, shell syntax, checksums, and live owner smoke |

RWUE-003 is elevated risk because it changes shell startup and authenticated
history behavior on a remote shared host. Release is not applicable. Deploy,
Operate, Maintain/Retire, and Review/Integrate are required.
