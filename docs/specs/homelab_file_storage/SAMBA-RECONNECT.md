# Central Samba policy and macOS reconnect

Status: Implemented; selectively deployed and verified on the personal Mac.
Owner: personal dotfiles operator. Bounded context:
`homelab_file_storage`; topology, backups and AI configuration remain adjacent.

## Outcome and scope

Maintain one source of shared Samba security/settings for Pi and Omarchy. Keep
existing installed configuration paths as thin renders of that source so current
provisioning commands stay compatible. A central public-safe logical catalog
includes Pi and HP Omarchy, plus the Omarchy ARM guest as a declared/manual
entry with deployment unverified. Catalog inclusion does not provision a new VM
share or claim availability. Pi and HP Omarchy both reconnect by default on
the administration Mac. The Omarchy ARM guest remains manual with deployment
unverified. Reuse existing Pi and HP mounts; do not create duplicate mounts.
macOS native file-sharing exports are outside this Samba ownership migration.

No share root moves, existing-file deletion, disk formatting, credential changes,
public exposure, Tailscale toggle, router changes or workload migration occurs.
Pi remains loopback Samba through private Tailscale Serve TCP 445. Omarchy keeps
its current authenticated private-LAN plus Tailscale access. Both expose only
owner Shared folders, with SMB2+, no guest access, NetBIOS or printing, and
0600/0700 file/directory masks.

## Domain and interfaces

A Share Declaration identifies a logical target, share name, server policy and
client reconnect default. Server Policy owns common Samba settings and explicit
transport differences. Connection Binding supplies an endpoint and username
privately; it contains no password. Mounted Share is identified by actual
server/share metadata, never by an ambiguous Shared or Shared-1 directory name.
Reconnect Attempt is a bounded, serialized per-user operation.

Source design: one `.chezmoidata/` declaration and `.chezmoitemplates/` Samba
renderer; existing Pi and Omarchy source files become thin wrappers. A macOS
catalog under `~/.config/samba/`, a maintained `~/.local/bin/smb-shares` helper
and an Aqua user LaunchAgent implement client access. Private connection
bindings under `~/.config/samba/` are unmanaged, owner-only files; they are never
committed. Existing homelab access bindings may seed Pi's endpoint locally but
are not expanded into public source. The helper offers read-only plan/status,
explicit private binding enrollment, one reconnect pass and explicit launchd
activation/removal. The concrete commands are defined below.

The launchd job uses RunAtLoad and a 60-second StartInterval. It has no KeepAlive
network-state dependency, privileged helper or password in ProgramArguments.
The helper checks Tailscale is Running and the intended tailnet peer/SMB endpoint
is reachable before mounting. It does not change Tailscale configuration.
Native NetFS uses NoUI and system-managed credentials; passwords never cross
Python, command arguments, environment, configuration or logs. A separate
bounded worker limits native mount calls for each target independently. Missing
credentials result in a safe status and later retry, never an automatic password
dialog.

Use default NetFS /Volumes placement. Detect already mounted shares through
native mount metadata and reuse exact identities, preserving current HP and Pi
mounts. No forced unmount, destructive mountpoint replacement, local fallback
folder or password-bearing URL is permitted. A still-mounted session is left
for macOS recovery; this job is not authorized to force recovery of busy or stale
open handles. Missing or ambiguous identity fails closed rather than mounting a
duplicate or returning another host's Shared folder. Foreign-owned SMB mounts
are inspected only through cached kernel identity, never through their paths or
NetFS. A matching foreign mount is an `identity-conflict`; it is not usable as
the current user's mount and is never replaced by this helper.

## Concrete CLI and configuration contract

`~/.local/bin/smb-shares plan`, `status` and `reconnect` respectively preview
logical targets, report safe result classes, and perform one bounded pass.
`bind TARGET --host HOST --user USER [--alias-host HOST]` explicitly writes
owner-only private metadata, never a password. `enable` and `disable` affect
only `dev.dotfiles.smb-reconnect` in the current GUI user domain. Internal
native workers run in subprocesses and are not public provisioning interfaces.

The public catalog is `~/.config/samba/shares.json` with `schema_version: 1`
and `shares`: each row has `id`, `share`, `policy`, `reconnect` and `deployment`.
IDs are `pi400`, `hp-envy`, `omarchy-arm`; `Shared` remains the share name.
`reconnect` is true for Pi and HP, false for the unverified ARM guest. Policy
is `tailscale-only` for Pi and `private-lan-and-tailscale` for Omarchy. Native
mount access still uses only each bound host's Tailscale endpoint.

`~/.config/samba/private-connections.json` has `schema_version: 1` and a
`bindings` object keyed by catalog ID. Each value contains `host`, `user` and
`aliases` (validated host strings only). Aliases recognize an existing approved
LAN mount but are never used as an automatic fallback destination. Only known
Tailscale peer addresses/names authorize new mount attempts. Unknown IDs,
fields, duplicate keys, embedded URL credentials, malformed names and unsafe
private-file permissions are rejected before any mount request.

Public source remains `.chezmoidata/samba.json`, one Samba configuration
renderer in `.chezmoitemplates/`, thin wrappers at existing server source paths,
and a thin rendered client catalog. No endpoint or per-user password belongs in
those sources. Existing server wrappers must render the same effective policy.
The helper's native adapter is under `~/.local/lib/smb_shares/`; it calls
NetFSMountURLSync with default placement, NoUI and no password argument, and
NetFSCopyURLForRemountingVolume for mounted identity. A per-user lock serializes
passes. Tailscale queries, peer port probes and native subprocesses have explicit
timeouts; each target is independently attempted. Fixed safe state is atomically
replaced under `~/.local/state/smb-shares/` with owner-only permissions.

## Behavior

- Given a healthy existing Pi or HP Omarchy mount, repeated reconnect passes
  reuse it and do not create duplicate mounts.
- Given either enabled share is absent, usable saved SMB credentials and a
  reachable Tailscale peer, the next scheduled pass mounts that share without a
  password dialog. A failure or offline peer for one target does not suppress
  the other target's independent bounded attempt.
- Given Tailscale is stopped, peer is offline, TCP 445 is unavailable or saved
  credentials are missing, the pass records a safe logical status and retries
  later without changing networking, credential state or existing mounts.
- Given a macOS login or wake, launchd runs the same bounded idempotent pass;
  a missed timer while asleep may run after wake according to launchd behavior.
- Given malformed/private-file permissions, unsupported catalog values,
  endpoint mismatch, concurrent invocation or unknown mount identity, no unsafe
  mount, credential disclosure or unrelated state change occurs.
- Given another user or privileged backup application owns the target mount,
  the pass reports `identity-conflict`, preserves that mount and retries later.
- Given Pi and Omarchy are rendered from the central server policy, their
  existing access boundaries and installed provisioning paths remain compatible.
- Given an operator removes the reconnect job, future retries stop while
  mounted shares, server configuration, files and saved credentials remain.

## Contracts and validation

Python runtime is 3.12+ with no additional dependency. Private files are bounded
regular owner files, reject symlinks and unsafe permissions, validate exact
fields and do not permit password-bearing URLs or arbitrary executable paths.
Network probes, subprocesses and native mounting are bounded. One process owns
a per-user lock; no parallel duplicate retries. Logs/status expose only logical
IDs and fixed result classes, with private permissions and bounded retention.

Regression tests precede implementation for profile isolation, central rendering
and preserved policy, malformed bindings, offline/missing-credential behavior,
mount identity/collisions, bounded retries and idempotence. Configured pytest,
chezmoi, shell/plist syntax and focused diff/privacy review are authorities.
No dedicated publication scanner is configured; reuse scoped public/private
source tests and diff review rather than inventing a second denylist.

Live validation selectively installs exact reviewed source with unrelated chezmoi
scripts excluded. Verify Pi server configuration parity, SELinux and exposure,
macOS launchd job, repeated no-op pass and isolated SMB upload/download. One
graceful unmount/remount per exact enabled share, sequentially and only when
not busy, may verify noninteractive reconnect; never force it. Preserve all
unrelated mounts and SSH, S3, Git, backup and remote-desktop connectivity. A fresh
macOS login is not claimed unless separately observed. Existing-session success alone does not
prove persistent Keychain enrollment. Credentials saved against an older LAN
address may require one private Finder enrollment for the canonical Tailscale
name; never copy or extract the password to work around that requirement.

## Visual Evidence

Boundary: required, shared policy, servers and client shown below. Data/trust:
required, passwords stay in Samba/Keychain. Dependency/deployment: required,
per-user launchd depends on native NetFS and Tailscale. Interaction/state:
required, transition table below. Schema: not applicable, no application data
schema; small config shapes are specified in prose. Quantitative: not
applicable, no throughput or timing performance claim is made.

```mermaid
flowchart LR
  accTitle: Central Samba policy and private macOS reconnect
  accDescr: Dotfiles renders compatible Pi and Omarchy server inputs. A Mac user agent reads logical share declarations and private bindings, checks Tailscale, and asks native NetFS to mount Pi and HP Omarchy using Keychain-managed authentication. Both existing mounts are reused.
  Source[Dotfiles shared policy] -->|compatible server render| Pi[Pi Samba loopback]
  Source -->|compatible server render| HP[Omarchy Samba]
  Source -->|logical declarations| Agent[Mac user LaunchAgent]
  Bindings[Private connection bindings] -->|endpoint and user only| Agent
  Agent -->|readiness check| Tailnet[Tailscale]
  Agent -->|NoUI mount request| NetFS[macOS NetFS and Keychain]
  NetFS -->|private authenticated SMB| Pi
  NetFS -->|private authenticated SMB and existing mount reuse| HP
```

**Text Equivalent:** Dotfiles is the common server-policy owner and renders
compatible inputs for Pi's private loopback service and Omarchy's existing
service. The Mac user agent combines public logical declarations with private
endpoint/user bindings, checks Tailscale, then requests noninteractive NetFS
mounts using system-managed authentication. Pi and HP Omarchy are default
reconnect targets; both existing mounts are preserved and reused. Passwords
remain in Samba and Keychain.
Canonical source: this contract and the central declarations. Owner: personal
dotfiles operator. Update this visual when ownership, transport or retry flow
changes.

| Current state | Guard/event | Outcome |
| --- | --- | --- |
| Waiting | Invalid binding or no Tailscale | Safe status; no mount; later retry |
| Waiting | Peer/port unavailable | Safe status; existing mounts preserved |
| Waiting | Exact share already mounted | Reuse; no duplicate |
| Waiting | Matching foreign-owned mount | Identity conflict; preserve it; later retry |
| Waiting | Ready and missing mount | One bounded NoUI native request |
| Mounting | Authentication unavailable/error/timeout | Safe status; later retry |
| Mounting | Identity verified | Mounted; next pass reuses it |
| Any | Reconnect disabled | Stop future attempts; preserve mounts and data |

**Text Equivalent:** Every pass first validates bindings and readiness. An exact
existing mount is reused. Only a ready missing share enters one bounded native
mount attempt. Authentication failure, timeout or unavailable peer causes a safe
waiting state; a verified mount becomes reusable. A foreign-owned target stays
untouched until its owner releases it. Disabling the job stops future
attempts without removing data or mounts. Canonical source: behavior and
contracts above; operator owns updates when guards or retry semantics change.

## Deployment, rollback and maintenance

Preview selected files and policy parity before applying. Server candidates
must pass testparm. Byte-equivalent server renders require no service restart.
If a privileged system configuration change proves necessary, ask privately for
sudo and preserve the old configuration before activation. Do not restart or
change a service merely to centralize equivalent source.

Rollback boots out only the new per-user reconnect job, restores its backed-up
public helper/config files and restores the prior source revision. Do not
unmount another share, remove credentials, delete user files or reset Serve.
Observe sanitized per-share state, retry age and server/mount health; investigate
repeated authentication failures through private Finder enrollment. Maintain
supported macOS, Python, Samba and Tailscale; review behavior after OS upgrades.
Retirement disables the user job and preserves data/credentials until the owner
explicitly authorizes their independent removal.

## Enrollment and routine use

After reviewing the selected revision, apply only the client files when unrelated
source changes or scripts are pending:

```sh
chezmoi apply --exclude=scripts \
  ~/.local/bin/smb-shares \
  ~/.local/lib/smb_shares/netfs.py \
  ~/.config/samba/shares.json \
  ~/Library/LaunchAgents/dev.dotfiles.smb-reconnect.plist
```

Set each connection binding locally. Replace the example endpoints and username
with verified private values; these are not shell-ready hostnames:

```sh
smb-shares bind pi400 --host PI_TAILSCALE_HOST --user OWNER
smb-shares bind hp-envy --host HP_TAILSCALE_HOST --user OWNER
smb-shares plan
smb-shares reconnect
smb-shares enable
smb-shares status
```

An optional `--alias-host` recognizes an already verified older LAN or Tailscale
mount identity. It never authorizes new connections outside the current peer's
Tailscale addresses. Use Finder's Go → Connect to Server with the canonical
`smb://HOST/Shared` address to enroll missing credentials privately, choosing
the registered user and saving the password when offered. Do not put a password
in the URL or use a command that prints a Keychain password.

Normal chezmoi apply runs the scoped activation hook. The local data setting
`smb_reconnect_enabled = false` renders a disabled job and makes that hook
disable it. `smb-shares disable` also stops future attempts immediately; it
does not disconnect mounted shares. Keep Python 3.12+ and Tailscale available
in the declared LaunchAgent PATH.

`status` reads the last sanitized result; `checked_at` is a Unix timestamp. A
recent `mounted` result verifies identity, not continuous I/O health. Use an
isolated file roundtrip to investigate a suspected stale mount. `needs-login`
requires private Finder enrollment. `timeout`, `unreachable`, `offline` and
`tailscale-unavailable` require connection checks, not credential replacement.
`identity-unavailable` or `identity-conflict` requires mount ownership/identity
inspection before taking any recovery action.

Carbon Copy Cloner can mount a network destination through its privileged
helper. During validation it created a root-owned hidden Pi mount while a user
remount was being tested; the native user mount request returned error 22.
After the owner stopped the backup task and that mount disappeared, a fresh
NoUI Pi mount and file roundtrip passed. The reconnect helper now preserves and
reports a foreign-owned mount instead of competing with it. Let the owning
backup application finish or have the owner stop it; retry after it releases
the mount. Never force unmount or change its task/schedule as automatic recovery.
An independently scheduled backup may recreate the conflict later.

## Verification and deployment limits

The deployed Mac client passed fresh native NoUI mounts for Pi and HP, separate
SMB uploads and downloads compared with server-side bytes, exact-identity reuse
without duplicates, a successful launchd execution and 60-second scheduling.
Only uniquely named test files were created and removed. Pi's writable root,
SELinux enforcing, anonymous share denial and existing Samba, SSH, S3 and Git
service state were checked. HP's Samba configuration remained byte-identical.
The central server renders preserve the old Pi and HP bytes, so no privileged
configuration replacement or server restart was necessary.

The Mac client was installed from a committed, privately staged source archive,
with unrelated chezmoi scripts excluded. Existing dirty Mac and HP source
checkouts were preserved; do not reset or broadly apply them to update this
feature. A clean Pi checkout may fast-forward after delivery. HP can review and
integrate the shared source after its unrelated input work is reconciled; its
running server already matches the central render.

Cold macOS login, wake from sleep and fresh Keychain-unlock persistence were not
observed. NoUI mounts in the active login session can reuse session-managed
authentication and do not prove those cases. Phone UI, the cataloged ARM guest
share and throughput remain unverified. Review these cases after the next
normal login without interrupting an active remote session solely for testing.
