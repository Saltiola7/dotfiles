# Remote Workspace Profile Engineering Profile

| Concern | Default |
|---|---|
| Deliverable and owner | Owner-only personal chezmoi overlay; operator owned |
| Languages and modules | Go templates, TOML, Bash, and Python contract tests; Security module |
| Runtime and platform | Intended RHEL 10 x86_64 remote-workspace successor (release qualification pending); Yazi and portable CLI dependencies |
| Interfaces | Chezmoi `machine_type=remote-workspace` and deny-by-default Yazi target allowlist |
| Compatibility | Existing macOS and `lmsh` rendering remains unchanged; the shared `dotfiles-ai` source retains agent and runtime ownership |
| Trust/data | Public Yazi configuration; history, account identity, credentials, and private endpoints remain outside this source |
| Delivery | Explicit owner initialization and apply only after the shared foundation is ready |
| Operations | Render, target-overlap, executable version, idempotency, and rollback checks |
| Maintenance | Pin portable releases, preserve disabled defaults, and remove the overlay without deleting user history or credentials |
| Authorities | Full `pytest`, isolated chezmoi rendering, rendered and installed target comparison, checksums, and live owner smoke |

Historical RWUE-003 is elevated risk because it installs executable code into a
user home on a shared remote host. Release is not applicable. Deploy, Operate,
Maintain/Retire, and Review/Integrate are required.

## RRW-002B Approved Successor Discovery

Initiative `rhel-remote-workspace`, slice `rrw-002b-rhel-owner-overlay`, planned
cycle `RRW-002B` (not registered), keeps the owner-only Yazi overlay explicit and
disjoint after the shared foundation. RHEL replaces the standalone CentOS target as approved
Discovery only, not implementation or deployment evidence; RWUE-003 acceptance
retains its original platform. Risk remains elevated. Existing immutable release,
checksum, and flavor pins and macOS/`lmsh` behavior remain unchanged.

Coordinator authority, gate applicability/results and release qualification
remain pending primary verification. Source preparation is independent; final
paired qualification and live owner apply require the full public merged runtime
SHA. Release has no versioned artifact. UBI10 userland smoke is separate
from eventual actual RHEL owner qualification and private rollout. Only a
regression found during approved Build work permits an in-scope source correction;
this Discovery authorizes none. Normal PR approval applies without admin bypass.
