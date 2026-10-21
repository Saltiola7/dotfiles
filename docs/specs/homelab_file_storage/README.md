# Private homelab file storage

Status: Existing Pi Samba is deployed and delivered. Authenticated file
roundtrip, denied access, SELinux enforcement, fresh startup and macOS Finder
access have been verified. Shared server policy and the logical share catalog
are centralized in dotfiles. The personal Mac reconnects Pi and HP Omarchy
through a per-user LaunchAgent; see SAMBA-RECONNECT.md for enrollment and recovery.

## Intent and ownership

The Pi is the always-on primary file server. Store ordinary folders accessible
directly by local tools and expose them through authenticated SMB over Tailscale.
Connected-only access is sufficient. No web drive, offline synchronization,
public sharing, data migration or disk formatting are included. Shared policy
centralization and macOS client reconnection are governed by SAMBA-RECONNECT.md;
existing HP exposure and existing files must be preserved. Personal dotfiles
owns declarations; secrets are private runtime state. Backup and topology retain independent ownership.

## Engineering Profile

The committed PROFILE.md owns runtime, module, risk and validation defaults.
The Samba reconnect extension adds macOS client automation and centralizes
existing server policy without changing current network exposure.

## Existing Pi behaviors and contracts

- Given an authenticated owner on the tailnet, when creating or editing a file,
  the same ordinary file is accessible directly on the Pi.
- Given anonymous or non-tailnet access, when opening SMB, access is denied.
- Given an existing configuration or data directory, setup preserves it and
  refuses incompatible ownership instead of replacing data.
- Given a failed validation, setup does not activate the candidate configuration.
- Given a reboot, the share and access policy persist without interactive login.

Candidate share: owner-only `Shared`, rooted under the owner's home. Reuse the HP
share convention without copying its service identities. Disable guest access,
SMB1, printers and NetBIOS. Bind SMB to loopback and expose it through Tailscale
Serve TCP 445; preserve unrelated Serve routes and retain SSH administration.
Samba skips the non-broadcast Tailscale interface, so direct interface binding
was tested and failed; loopback forwarding preserves private-only exposure.
SELinux labeling must be
specific to the share. Ask the owner privately for sudo and SMB password when
required. Never use the sudo password as provisioning input or log passwords.

## Visual Evidence

Boundary, data/trust and deployment are required and represented below.
Interaction and state are represented by the validation/activation contract:
preview, validate, activate, verify; failure preserves the previous state.
Schema is not applicable: no application data schema is introduced.
Quantitative is not applicable: throughput has not been benchmarked.

```mermaid
flowchart LR
  accTitle: Private Pi file service
  accDescr: Owner clients access Samba over Tailscale. Samba exposes ordinary Pi folders. Independent backup consumes those folders.
  Clients[Owner Mac and phone] -->|Tailscale and authenticated SMB| Samba[Pi Samba]
  Samba -->|ordinary file access| Files[Pi Shared folder]
  Files -->|backup source| Backup[Independent backup context]
```

**Text Equivalent:** Owner clients access Pi Samba over Tailscale with SMB
authentication. Samba exposes ordinary files in the Pi's Shared folder. Backup
reads this source independently. Canonical source is this contract; the operator
owns it and updates the visual when access or hosting changes.

## Delivery and recovery

Preview managed files and privileged operations before setup. Test configuration,
authentication, ordinary-file parity, unauthorized access and fresh startup.
Rollback restores backed-up configuration and disables only the new service;
never delete user files. Observe disk free space, service health and backup age.
Retirement requires independent recovery verification and explicit data disposal.

## Existing Pi interfaces and observations

Managed source consists of `~/.config/homelab-file-storage/smb.conf`, the
`tailscale.conf` systemd drop-in, `~/.local/bin/pi-samba-setup` and
`~/.local/bin/pi-samba-check`. These targets belong only to the Fedora server
profile. Configuration templates contain owner/home placeholders; setup renders
them from the actual owner and refuses unexpected or symlink share paths.

`pi-samba-setup --plan` is read-only. `--configure` requires Fedora ARM64,
SELinux enforcing, installed Fedora Samba and policy tools, the intended owner,
an existing Tailscale interface and an unused or matching Serve TCP 445 route.
It validates candidate configuration, backs up existing configuration privately,
creates only an absent owner folder, labels that subtree, installs configuration,
enrolls an SMB identity through a private terminal prompt if needed and starts
Samba. It waits before checking active state to detect immediate startup failure.
It never installs packages, disables SELinux, opens physical LAN interfaces,
resets Serve configuration or writes credentials into source.

`pi-samba-check` privately prompts for SMB authentication and uses a uniquely
named temporary file to test upload, download, content equality and deletion.
It never touches existing data. Authentication remains separate from the sudo
password and SSH identity.

Runtime observations: Samba 4.24.7 serves loopback; Tailscale forwards TCP 445.
Authenticated browsing and file roundtrip passed; anonymous share access was
denied, physical LAN access was refused and SELinux remained enforcing.
Fresh system startup validation passed. No throughput claim is made from the
small functional roundtrip. Finder connected as the owner, and distinct SMB
upload/download files matched on macOS and Pi; test files were removed. Phone
UI behavior remains unverified.

## Update and recovery procedure

Review the source revision before applying these four targets selectively with
chezmoi and scripts excluded; configure `machine_type = "fedora-server"` first.
Do not apply unrelated desktop, work or AI targets. During this deployment the
four files were installed from verified staging while the independent server
profile deployment remains pending. Run the read-only plan before invoking
`pi-samba-setup --configure` in a private terminal. Follow with listener checks,
denied access and `pi-samba-check`. Package updates use Fedora's signed package
repositories. Take a verified data backup before major Samba or OS upgrades.

Configuration backups are under the root-owned
`/var/lib/homelab-file-storage/backups/` directory; record the selected backup
privately. To roll back, stop Samba, disable only the created Serve TCP 445
forwarder and restore the saved Samba/drop-in configuration. Preserve all Shared
files. Restore prior service enablement according to recorded predeployment
state; do not reset unrelated Serve routes. A running share is not data recovery:
the independent Borg context supplies versioned restore.
