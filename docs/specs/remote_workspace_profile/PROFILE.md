# Remote Workspace Profile Engineering Profile

| Concern | Default |
|---|---|
| Deliverable and owner | Owner-only personal chezmoi overlay; operator owned |
| Languages and modules | Go templates, TOML, Bash, and Python contract tests; Security module |
| Runtime and platform | CentOS Stream 10 x86_64 remote workspace; Yazi and portable CLI dependencies |
| Interfaces | Chezmoi `machine_type=remote-workspace` and deny-by-default Yazi target allowlist |
| Compatibility | Existing macOS and `lmsh` rendering remains unchanged; the shared `dotfiles-ai` source retains agent and runtime ownership |
| Trust/data | Public Yazi configuration; history, account identity, credentials, and private endpoints remain outside this source |
| Delivery | Explicit owner initialization and apply only after the shared foundation is ready |
| Operations | Render, target-overlap, executable version, idempotency, and rollback checks |
| Maintenance | Pin portable releases, preserve disabled defaults, and remove the overlay without deleting user history or credentials |
| Authorities | Full `pytest`, isolated chezmoi rendering, rendered and installed target comparison, checksums, and live owner smoke |

RWUE-003 is elevated risk because it installs executable code into a user home on
a shared remote host. Release is not applicable. Deploy, Operate,
Maintain/Retire, and Review/Integrate are required.
