# Private Pi Git hosting

Status: Installed; trusted private HTTPS, private Git and encrypted isolated Forgejo restore passed. Operator approved separate Git-hosting
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
preserving existing routes. It requires owner-entered sudo and returns success
only after the HTTPS readiness check passes. An issuance failure leaves the
configured routes in place for Tailscale recovery; it does not undo other services.
Ordinary chezmoi apply never enrolls credentials, activates network or restores data.

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

## HTTPS readiness and certificate recovery

`pi-forgejo-setup https-check` is a read-only, non-root readiness command. It
resolves this node's private DNS name from local Tailscale status, validates the
hostname shape, and requests the fixed HTTPS health endpoint with normal system
CA and hostname verification. It requires HTTP 200 and JSON `status: pass`, a
reachable login page, and denied anonymous `/api/v1/user` access (401 or 403).
Reject redirects, unexpected status/body, oversized responses, invalid TLS,
timeouts and malformed names. Do not read service secrets or print response
bodies, private URLs, tokens or provider errors. No proxy environment, forced
issuance, retry loop, network reset, certificate deletion or privileged action
is part of this command. Each request has a ten-second timeout; bound response
bodies to 64 KiB. A bounded request failure returns a nonzero result with safe
recovery guidance. A fresh installation may need a later check while Tailscale
finishes initial issuance; a successful Serve configuration write is not readiness.

Given only configured forwarding, `network` must not report usable HTTPS before
trusted TLS, health and anonymous-denial checks pass. Given a provider outage,
it fails safely while preserving all routes, secure cookies, registration policy
and private state. Given provider recovery, one explicit `https-check` succeeds
without reenrollment or a service restart. Given valid HTTPS, owner first browser
login/password change remains a separate private enrollment step.

| Observed state | Meaning and next action |
| --- | --- |
| Loopback health fails | Investigate the Forgejo user service and its private logs first. |
| Loopback passes; TLS/order fails | Preserve routes; inspect Tailscale certificate logs and provider DNS status. |
| `SetDNS` returns HTTP 500 | Tailscale's control-plane DNS record operation failed; this is outside Forgejo. |
| Trusted health/login pass; anonymous user API denied | HTTPS transport is ready; owner can enroll privately. |

**Text Equivalent:** Check Forgejo locally before investigating certificate
provisioning. Tailscale owns its managed public DNS challenge and certificate
issuance; Forgejo owns application readiness and authorization. Keep these
failure domains separate. An unsuccessful certificate order is never permission
to publish HTTP, enable Funnel or bypass TLS verification. Canonical source: the
HTTPS readiness contract above; owner: homelab operator; update this table when
provisioning or readiness behavior changes. This table extends the existing
boundary, interaction, state and trust evidence; no new schema or quantitative
visual is applicable.

During the 2026-10-19 incident, local application health and private Git worked.
Private daemon logs showed rejected ACME orders and Tailscale `SetDNS` HTTP 500
responses (`failed to create DNS record`). Later the existing daemon obtained a
certificate without a local configuration change. Trusted HTTPS health, login
page and anonymous API denial were verified from the Pi and Mac. This supports a
transient certificate-provisioning failure; the precise cause of earlier CA
rejections is not known. Multiple DNS-01 TXT values alone do not prove corruption.
The certificate-issuance deferral is resolved; owner first login is still pending.

On recurrence:

1. Run `pi-forgejo-setup https-check` once. If it fails, compare local readiness
   with `curl --fail http://127.0.0.1:3000/api/healthz` on the Pi.
2. Inspect `tailscale serve status` and, where permitted, private
   `journalctl -u tailscaled --since "30 minutes ago" --no-pager`. Ask the owner
   for sudo only if the logs are inaccessible. Retain sanitized UTC timestamps,
   daemon version and decisive errors locally; keep tailnet identities and
   challenge values out of public Git.
3. Check clock synchronization and Tailscale service status. Distinguish DNS
   record-write errors, certificate validation failures and rate limiting. The
   older `WaitOrder invalid` message does not expose the CA challenge reason;
   upstream has added better diagnostics. Do not assume upgrading fixes issuance.
4. Leave the current routes and certificate cache intact. Let Tailscale manage
   issuance/renewal. Avoid repeated probes during an active outage; honor any
   provider `Retry-After`, then make one later readiness check. Escalate persistent
   DNS API failures to Tailscale with sanitized evidence. Do not reset Serve,
   rotate node identity, or restart remote networking without owner approval.
5. Recheck from a separate tailnet client using ordinary HTTPS verification.
   Retain private Git, Samba, RustFS and administrative SSH health. No production
   data restore or credential change is a certificate-recovery operation.

Sources: [Tailscale Serve and certificate management](https://tailscale.com/docs/features/tailscale-serve),
[Tailscale DNS record control-plane operation](https://github.com/tailscale/tailscale/blob/main/control/controlclient/direct.go),
[upstream ACME error diagnostics](https://github.com/tailscale/tailscale/pull/21790),
[DNS-01 challenge behavior](https://letsencrypt.org/docs/challenge-types/),
[certificate rate limits](https://letsencrypt.org/docs/rate-limits/).
