# Homelab versioned backup

Status: Implemented and deployed. Encrypted remote archive, isolated restore,
retention, daily scheduling and fresh startup verified. Source and deployment are maintained in dotfiles.

## Intent and ownership

Protect Pi ordinary files with encrypted, versioned backups, then let the Mac's
existing Backblaze client protect the local repository. Reuse the Borg/borgmatic
family already deployed on HP; preserve the HP repository and timer. This is
recovery rather than synchronization. No formatting, existing data replacement,
Backblaze purchase, database deployment or automatic workload moves are included.

## Engineering Profile

Operator-owned internal infrastructure. Fedora ARM64 backup client; macOS
destination on an existing APFS external disk; Borg 1.x compatibility must be
verified on both ends. Cloud and Security modules apply; elevated risk.
Personal dotfiles owns scripts/configuration, while passwords, encryption keys,
connection bindings and disk UUIDs stay private. Kernel, review, deploy, operate
and maintenance gates are required. Release is not applicable: no
package is published. Authorities: scoped pytest, shell checks, mount identity
validation, Borg repository checks and isolated file restore comparison.

## Behaviors and contracts

- Given the expected destination disk is mounted, a backup creates an encrypted
  archive without modifying the source or unrelated destination folders.
- Given the disk is absent or substituted, backup fails before writing; it must
  not fall back to the Mac's internal filesystem.
- Given an unavailable Mac or tailnet, the job reports failure and retries on a
  later scheduled run; it does not delete prior archives.
- Given an overlapping job, one writer proceeds; duplicate writers fail safely.
- Given backup validation failure, retention pruning does not run.
- Given a selected archive, restore into an isolated directory produces matching
  file contents; restoration never overwrites live data implicitly.

Repository folder: `Homelab-Backups/pi400` under the dedicated external
disk. Public declarations use logical disk identity only. Bind the actual UUID
privately and check it at the destination, including remote writes. Declared
schedule matches HP: daily, with 7 daily, 4 weekly and 6 monthly archives.
The Pi pushes archives over existing Mac SSH using a newly generated dedicated
Pi identity and a restricted forced command on the destination. The forced
command checks the mounted filesystem UUID before starting Borg, then restricts
access to this repository only. Existing Mac SSH identities remain unchanged.
Never reuse or copy the Mac's private administration key onto the Pi.
Repository passwords and exported recovery keys must be kept independently of
the Pi, repository and sole Mac copy. Use a restricted backup identity rather
than unrestricted remote shell credentials. Existing Mac SSH and Borg 1.4.5 are
available. Public host keys are verified from the owned destination before trust
is installed; no private keys are copied.

Backblaze inclusion and a cloud restore must be verified separately. A successful
Borg job is not evidence of cloud protection. Concurrent edits give file-level
copies, not transactional snapshots; databases require separate consistent dumps.
Initial scope is ordinary shared files plus declared configuration inventories.
RustFS object data has independent consistent-backup obligations; this ordinary
file slice must not falsely claim active object/database consistency.

## Visual Evidence

Boundary, data/trust and deployment are required and represented below.
Interaction and state use this transition contract: destination verified,
archive created, archive checked, retention allowed. Failures stop the sequence.
Schema and quantitative are not applicable: no application schema or performance
benchmark is introduced.

```mermaid
flowchart LR
  accTitle: Pi backup and offsite recovery
  accDescr: Pi ordinary files are archived into an encrypted Borg repository on a Mac-connected disk. Existing Backblaze protects that local repository only after inclusion verification. Recovery keys are held separately.
  Pi[Pi ordinary files] -->|Borg archive over private access| Repo[Mac external disk: dedicated repository]
  Repo -->|existing client; inclusion unverified| Cloud[Backblaze external dependency]
  Keys[Independent recovery key custody] -.->|needed for restore| Repo
```

**Text Equivalent:** Pi files are archived to a dedicated encrypted repository on
the Mac-connected disk. Existing Backblaze supplies a separate offsite layer only
after inclusion is verified. Independent key custody is required for restoration.
Canonical source is this contract; operator updates it when recovery paths change.

## Concrete interfaces

The maintained standard-library Python CLI `homelab-backup` supports destination
planning/initialization on macOS and client planning/run/restore checks on Fedora.
Python 3.12+ is supported. Private JSON configuration names exact destination
volume UUID, mount, repository, connection identity and password-file locations.
Public source never embeds that configuration. The destination SSH forced command
is `homelab-borg-serve`; it verifies the mount before executing Borg restricted to
the declared repository. Client execution uses a private dedicated SSH key and
strict host-key checks; the key is generated on Pi and never copied from Mac.

Package prerequisites are explicit: macOS Borg 1.4.x, Fedora borgbackup/borgmatic.
A declared systemd user timer runs daily and catches missed runs. Setup refuses
symlinks, unknown existing repositories and substituted mounts. No service, key
or repository is initialized by an ordinary chezmoi apply. Secret generation and
runtime enrollment are explicit commands, with private files and no secret output.

Normal archive creation runs an integrity check before retention. A failed create
or check stops before pruning. The first test archive is restored into an isolated
directory and compared before unattended scheduling is enabled.

Record last success, archive age, repository identity, disk headroom and errors.
Verify a small file restore before enabling pruning. Establish periodic integrity
checks and restore drills. Keep backup configuration independent of desktop
profiles. Stop scheduling to retire a source; retain archives until explicit
operator-approved expiry. Never delete the only verified recovery copy.

## Verified deployment and limitations

Borg 1.4.5 runs on both ends. A new backup-only key was generated on Pi; the Mac
accepts it only from that tailnet node, with a restricted forced command and no
forwarding or general shell access. Existing identities were preserved. The
destination verified the exact APFS mount identity before repository writes.
Missing/substituted disk and symlink guard tests passed. The volume root required
owner-entered sudo to create only the absent dedicated folder; disk root ownership
and existing contents were not changed.

The first encrypted archive restored a unique test file into a private temporary
directory; bytes matched. Retention remained disabled until that restore passed.
Normal create/check/prune/compact passed. The timer survived a fresh reboot and
ran its catch-up job successfully. CPU is capped at half a core equivalent,
memory at 1 GiB, with low scheduling priority. No sustained throughput or large
archive capacity guarantee is made.

Backblaze metadata confirms the existing external drive is selected. Discovery
of the new repository in its scan and cloud upload/restore are not yet verified;
no offsite recovery guarantee is claimed. This does not weaken the verified local
encrypted archive/restore. The operator must confirm cloud upload and test a
cloud restore before treating that layer as established.

## Maintained setup, update and recovery

Private `destination.json` records mount, UUID, dedicated repository, recovery
file locations, Pi administration binding and Mac tailnet identity. Private
`client.json` records repository, dedicated identity, trust, password-file and
source folders. These bindings and recovery files are excluded from chezmoi and
Git; public `policy.json` records package and retention choices.

Explicit setup order: install declared Borg packages; create only the absent
dedicated owner folder if volume permissions require sudo; run destination plan
and initialize; enroll client identity/trust with `enroll-client`; install client
helper; run client plan and restore-check; then enable the declared timer. These
commands are repeatable except repository initialization, which deliberately
refuses an existing repository. Enrollment preserves matching private files and
refuses conflicting material. Restore a known configuration rather than deleting
partial state blindly.

On Mac, use `homelab-backup destination-plan --config` with the private destination
binding before changes. On Pi, `homelab-backup restore-check --config` exercises
recovery and `run --config` executes a checked archive with retention. Inspect
`systemctl --user list-timers pi-backup.timer`, the oneshot result and private
`last-success.json`. Timer/source updates use selective chezmoi application from
a reviewed revision; do not apply unrelated desktop/work/AI targets.

Private recovery material is under the Mac owner's configuration directory,
outside the backup disk; the passphrase also exists privately on Pi. Save the
exported repokey and passphrase into independent secure custody before relying on
disaster recovery. Neither is displayed by setup. After Pi replacement, rebuild
from declared Fedora bootstrap, restore ordinary files into an isolated location,
enroll a fresh restricted identity and revoke the lost identity explicitly.
After Mac/disk failure, restore the complete repository and independent recovery
material; run integrity and isolated restore checks before resuming retention.
During a disk-full incident, local Mac restoration remains available while the
remote guard refuses new sessions until headroom is recovered.

Initial backups cover Shared and declared Samba configuration, not a full system
image, root-owned SMB identity database, databases or live RustFS objects. Recreate
service identities through explicit private enrollment after a rebuild.


## Consistent RustFS recovery extension

Status: Discovery-ready; implementation and deployment have not started.
`homelab_backup` owns frozen capture, encrypted archives and recovery evidence;
`homelab_object_storage` retains exclusive ownership of live object internals.
The operator requested consistent RustFS backups to the existing dedicated
Mac-connected repository. No new repository, cloud purchase, production-data
replacement, hardware snapshot layer or workload move is required.

### Behavior and concrete interfaces

Extend the maintained backup CLI with explicit `rustfs-plan`, frozen-capture and
isolated restore verification. Integrate capture into the existing daily timer;
retain ordinary Shared sources, the existing repository, encryption, restricted
SSH identity, schedule and 7/4/6 retention. Do not directly archive live object
internals while RustFS runs.

Before stopping S3, validate the private destination and pinned service identity,
acquire the existing exclusive backup lock, record initial service state and
verify local staging headroom for a full independent copy plus the existing
20 GiB reserve. ext4 has no reflink snapshot primitive in this deployment;
ordinary private copying is the selected baseline. Failure before this point
leaves RustFS untouched. Staging is not exposed by Samba or committed to Git.

For an active service, use RustFS's own orderly SIGTERM shutdown to fence new
S3 admissions and drain accepted requests. Inspection of the exact deployed
commit shows signal handling, S3 shutdown waiting and clean-state persistence; stop timeout, forced termination or unconfirmed process exit
must fail capture rather than assert consistency. Complete capture includes all
object files and hidden internal metadata, owner-private credential files,
installed binary, service definition and release/version manifest. Reject unknown
source identities, symlink ancestors and insufficient space. Do not copy
administration SSH keys or tailnet state.

Copy into a newly owned generation directory, then restart the previously active
service and verify readiness before network transfer. A previously inactive
service stays inactive. Use exception/signal recovery and a systemd stop-post
recovery hook for interrupted scheduled jobs. On host reboot the enabled RustFS
service returns independently. Never promote a partial generation. Remove only
owned staging generations after successful archive/check or explicit recovery;
unknown paths are preserved. Keep one complete capture available if upload fails.

A failed capture, restart, archive check or object restore test prevents pruning.
Snapshot manifest identifies version, capture time and covered components without
credentials. Archive names and source layout remain compatible with prior
ordinary-only archives; those earlier archives do not contain object recovery.
Runtime enrollment is explicit and preserves unrelated private configuration.

### Consistency and restore acceptance

Given an accepted S3 write, when frozen capture succeeds, restored S3 reads return
matching bytes and retained object metadata. Given disk substitution, unavailable
Mac, insufficient staging space or failed shutdown, capture fails safely and no
unverified archive is represented as consistent. Given interrupted copying or
failed uploading, the original service state is recovered and prior Borg archives
remain available. No routine restore writes to the production data directory.

Create only a uniquely generated test bucket/object for the recovery drill.
Recover the selected Borg generation into an isolated owner-private directory,
check its manifest and pinned binary identity, and start a bounded test instance
on unused loopback-only ports using recovered credentials through files. Verify
signed object retrieval and relevant metadata, denied anonymous access, and byte
comparison. Stop the test process and remove only its owned temporary resources.
Production remains untouched except its own generated probe bucket cleanup.
Exercise failure paths with regression tests before deployment.

### Extension visual evidence

Boundary/data-trust/deployment: required, represented by the existing diagram
with this additional contract: live RustFS has exclusive access to live data;
backup captures an independent private generation while that writer is stopped;
only the frozen generation crosses to encrypted Borg on the Mac disk.
Interaction/state: required, expressed by this transition table. Schema and
quantitative: not applicable; no application schema or capacity benchmark.

| State | Guard and next state | Failure behavior |
| --- | --- | --- |
| Planned | Identity, destination, lock and staging headroom verified | No service change |
| Quiesced | New S3 admissions fenced; accepted requests drained; writer stopped cleanly | Recover original service state; no capture claim |
| Captured | Complete private generation and manifest finished | Do not promote partial copy; recover service |
| Resumed | Original active service is ready, or original inactive state preserved | Fail archive rollout; retain capture for diagnosis |
| Archived | Encrypted Borg create and integrity check pass | No pruning; preserve prior archives |
| Restore verified | Isolated RustFS reads match stored object bytes/metadata | No object-retention eligibility |

**Text Equivalent:** Validate everything before downtime; quiesce the writer;
freeze complete data and credentials; recover original service state before
upload; verify encrypted archive and isolated object restoration before retention.
Canonical source is this contract, owned by the operator, updated whenever data
layout, shutdown, version, staging, archive or recovery behavior changes.

### Operations, maintenance and gates

Owner: personal homelab operator. Python, Cloud and Security modules apply;
elevated risk because service availability, private keys and recovery integrity
are affected. Kernel, review/integrate, deploy, operate and maintain/retire gates
are required; release is not applicable because no package is published.
Project authorities remain scoped pytest/Python 3.12–3.14, source/diff and
public/private review, mounted-disk guards, live service-state checks, signed
S3/Borg restore drills and timer verification. No validation exceptions approved.

Record capture age, archive identity, duration, failure and restore status without
secrets. Stage full-copy space and S3 downtime scale with object data; local
measurements cannot guarantee future throughput. Stop scheduling before service
retirement, retain archives until explicitly approved expiry, and restore the
same data format before upgrades. Backblaze upload/cloud restore and independent
Borg-key custody remain separate follow-ups; successful local object recovery
must not imply offsite recovery.


Pinned source inspected: [startup shutdown sequence](https://github.com/rustfs/rustfs/blob/6de965ae3c965a78ff819fbcd7acd4aa44177d92/rustfs/src/startup_shutdown.rs)
and [signal handling](https://github.com/rustfs/rustfs/blob/6de965ae3c965a78ff819fbcd7acd4aa44177d92/rustfs/src/server/service_state.rs).
This supports the selected stop-and-copy design, but does not replace deployed
shutdown/restore validation. No Tailscale route, router or host remote-session
change is needed. If the service starts inactive without demonstrable clean
shutdown state, capture refuses consistency rather than laundering crash state.
