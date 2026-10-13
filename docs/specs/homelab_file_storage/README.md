# Private homelab file storage

Status: Discovery. The operator approved this context and deployment of Samba on
the Pi. Implementation and deployment evidence are pending.

## Intent and ownership

The Pi is the always-on primary file server. Store ordinary folders accessible
directly by local tools and expose them through authenticated SMB over Tailscale.
Connected-only access is sufficient. No web drive, offline synchronization,
public sharing, data migration, disk formatting or existing HP/Mac share changes
are included. Personal dotfiles owns declarations; secrets are private runtime
state. Backup and topology retain independent ownership.

## Engineering Profile

Internal infrastructure; operator-owned. Fedora ARM64, Samba, systemd and SELinux
enforcing. Cloud and Security modules apply; risk elevated. Configuration is
declared in chezmoi with explicit privileged setup, never implicit apply hooks.
Authority: isolated chezmoi rendering, scoped pytest, Samba testparm, actual
authenticated SMB read/write and denied-access checks. Release is not applicable
because no package is published. All kernel, review, deploy, operate and
maintenance gates are required and pending.

## Behaviors and contracts

- Given an authenticated owner on the tailnet, when creating or editing a file,
  the same ordinary file is accessible directly on the Pi.
- Given anonymous or non-tailnet access, when opening SMB, access is denied.
- Given an existing configuration or data directory, setup preserves it and
  refuses incompatible ownership instead of replacing data.
- Given a failed validation, setup does not activate the candidate configuration.
- Given a reboot, the share and access policy persist without interactive login.

Candidate share: owner-only `Shared`, rooted under the owner's home. Reuse the HP
share convention without copying its service identities. Disable guest access,
SMB1, printers and NetBIOS. Bind SMB explicitly to the Tailscale interface and
validate listener behavior; retain SSH administration. SELinux labeling must be
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
