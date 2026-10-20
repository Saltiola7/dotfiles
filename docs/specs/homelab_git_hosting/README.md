# Private Pi Git hosting

Status: Installed; private Git and encrypted isolated Forgejo restore passed. Operator approved separate Git-hosting
context in personal dotfiles. Probe shows four ARM64 CPU cores, 3.2 GiB available
memory, zero swap use and 446 GiB SSD free, with low current load. These are
observations, not a sustained concurrency guarantee.

## Intent and ownership

Provide private personal Git repositories on Pi, keeping HP fallback unnecessary
for initial small usage. `homelab_git_hosting` owns Forgejo and its data, topology
owns hosting declarations, backup owns encrypted archive/recovery interfaces.
Existing Samba, RustFS, HP services, repositories and disks are preserved.
No build runners or existing repository migration are included.

## Behavior, interfaces and contracts

Pin official Forgejo 15.0.10 LTS ARM64 binary and verify GPG signature against
published release-signing fingerprint plus SHA-256 before execution. Fedora's
available Forgejo 14 is discontinued upstream and is not selected. Support for
15 LTS runs through 15 July 2027. Native deployment avoids a new container runtime
on Pi; the requested Fedora/Podman HP fallback is not needed with current capacity.

Run owner service with separate private data/configuration; bind web to loopback
3000 and embedded Git SSH to loopback 2222. Existing administrative SSH stays
unchanged and Forgejo never writes the owner's administration authorized_keys.
Private Tailscale HTTPS serves web; Git SSH forwarding is tailnet-only. Preserve
existing TCP routes and refuse conflicting routes rather than resetting them.
SQLite avoids an additional database service. Resource limits: one CPU equivalent,
MemoryHigh 384 MiB, MemoryMax 768 MiB, zero service swap. Initial small Git traffic
is tested; heavy indexing/build/registry traffic requires a new capacity decision.
Disable open registration, require sign-in to browse, lock initial installer,
create one owner administrator with private generated temporary password, and
store enrollment tokens/credentials only in owner-private files. First login
requires changing the temporary password. Never print it in tool output or pass
secrets in CLI arguments. Existing generic Git identities/remotes are unchanged.

Given verified sources, explicit setup refuses unknown existing binary, unit,
data or private configuration rather than overwriting them. Given invalid
credentials, private repository access is denied. Given owner Git SSH identity,
create only an isolated probe repository and verify clone/push/fresh clone bytes.
Given reboot/logout, service and routes recover without an interactive login.
Given upgrade, freeze consistent data/configuration and compatible binary first;
SQLite migrations can require full-state restore rather than binary downgrade.

## Recovery and maintenance

Declare complete stopped Forgejo data, SQLite database/journals, repositories,
private configuration/secrets, embedded SSH host keys, binary and version manifest
in a frozen capture in the existing Borg repository. Resume previously active
service before upload; fail safely and recover original state after interruption.
Do not archive live SQLite by blindly adding its directory to ordinary sources.
Before retention eligibility, restore the complete generation privately, start
isolated loopback instance and verify repository/metadata and signed Git access.
Never overwrite live data as part of a drill. Cloud recovery remains independent.

Observe memory, restarts, free space and backup age. Use health and authentication
checks and a small Git smoke test after upgrades. Review upstream LTS security
updates. Retirement disables only this service/routes, revokes app credentials and
retains data until explicit operator disposal. No automatic data deletion.

## Visual Evidence

Boundary/data-trust/deployment: required, represented by ownership table below.
Interaction/state: required, represented by rollout table. Schema and quantitative:
not applicable; no application schema or capacity benchmark introduced.

| Component | Owner and boundary |
| --- | --- |
| Client | Private Tailscale access; separate Git app authentication |
| Forgejo | Loopback-only web/embedded SSH; exclusive SQLite/repository files |
| Frozen generation | Private complete stopped capture; no live mutation |
| Borg | Existing encrypted Mac-disk destination and restricted SSH identity |

| Transition | Guard |
| --- | --- |
| Verified to configured | Official signature/checksum; no conflicting state |
| Configured to private service | Locked installer, sign-in, limits, safe routes |
| Service to validated | Signed Git roundtrip and denied anonymous access |
| Data to recovery verified | Clean stop/copy/resume and isolated Borg/Git restore |

**Text Equivalent:** Private clients authenticate to capped Forgejo, which owns
its database and repositories. A stopped private copy is encrypted in existing
Borg storage and tested in isolation. Signature/configuration and denied/allowed
Git tests gate rollout. Canonical source: this contract; owner: operator; change
trigger: hosting, data, credentials, deployment, backup or upgrade changes.

Sources: [supported releases](https://forgejo.org/releases/),
[binary installation and SQLite](https://forgejo.org/docs/v15.0/admin/installation/binary/),
[release signatures](https://forgejo.org/download/).


## Maintained interfaces and enrollment

`pi-forgejo-setup fetch` downloads the fixed signed-release identity and verifies
both compressed and decompressed SHA-256 values recorded in source. The release
signature was separately verified in isolated GPG staging against the official
published fingerprint before pinning those values. `plan` checks the binary;
`install` requires Git/Git LFS and installs only matching/absent owner state.
`network` explicitly requests private Tailscale HTTPS and embedded Git forwarding,
preserving existing routes. It requires owner-entered sudo; ordinary chezmoi
apply never enrolls credentials, activates network or restores data.

Initial administrator output is stored privately in the service data tree;
first login requires password change. `pi-forgejo-check` creates only a uniquely
named temporary verification account/repository and identity, verifies signed
Git push/clone, freezes the complete Forgejo generation to existing Borg, restores
it into an isolated loopback service, compares repository bytes and privacy, then
removes only those probe resources. Credentials and tokens remain in captured
process memory or private files and never command arguments/output.

Backup CLI provides `forgejo-plan`, `forgejo-enable`, `forgejo-recover` and
`archive-check`. Explicit private `include_forgejo` enrollment triggers complete
stopped capture. SQLite quick_check, clean exit, staging headroom and pinned
binary identity gate promotion. The daily service's additional stop-post hook
recovers only a recorded previously active Forgejo process. Retention additionally
requires compatible `forgejo-restore-verified` evidence. Existing RustFS and Shared
coverage stays intact. Earlier archives without a Forgejo source locator do not
contain this recovery generation.

After version upgrades, preserve the compatible binary and full data/configuration
and repeat isolated restore proof before resuming retention. A binary downgrade
cannot reverse SQLite migrations. Source data replacement always needs a separate
operator-approved production recovery procedure.


## Verified rollout and limits

Official ARM64 LTS signature and both release checksums were verified before
execution. Git/Git LFS were installed by the owner using password-required sudo.
Forgejo 15.0.10 runs as an enabled owner service with SQLite, one-CPU/768 MiB
limits, no swap and loopback web/embedded Git SSH. Initial observed idle service
memory was approximately 100 MiB; this is not a capacity benchmark.

The generated probe account/repository pushed a committed payload over signed
SSH with strict host-key trust bound to owned Forgejo keys. The complete stopped
SQLite/data/configuration/binary generation was encrypted in existing Borg.
Recovered bytes and manifest matched; an isolated loopback instance returned the
private repository metadata, denied anonymous access and produced matching bytes
in a fresh Git clone. Probe repository/account were removed; no owner repositories
were moved or deleted. Original Forgejo readiness recovered; RustFS and Samba
remained healthy. Daily retention now requires compatible Forgejo restore proof.

Web access is private Tailscale HTTPS; Git uses embedded SSH on its private port.
Enrollment is an explicit owner-sudo step and does not reset other Serve routes.
The operator retrieves initial administrator enrollment from its owner-private
file and changes the password during first login; credentials are never posted
in chat. Add client public SSH keys through Forgejo; keep private keys on clients.

## Current HTTPS verification limitation

The post-recovery Git/Borg drill passes, but the tailnet certificate provider
currently returns an invalid ACME order. HTTPS forwarding configuration alone does
not prove usable HTTPS. Preserve TLS verification, secure cookies, closed
registration and existing data while investigating provider/DNS recovery. Do not
expose the loopback HTTP listener publicly, enable Funnel, disable certificate
checks or change administrator credentials as a workaround. Owner first browser
login remains pending until a valid certificate and authenticated UI check pass.
