# Reproduce the Pi headless server

This runbook composes existing bounded contexts; it does not replace their safety
contracts. The owner controls the physical Pi, both source revisions, private
service enrollment and backup custody. Public Git declares software intent;
credentials, storage identities and connection bindings remain local.

## Ownership and inputs

- Image, key-only SSH and password-required sudo: Raspberry Pi bootstrap context.
- `machine_type=fedora-server`: shared Bash and terminal/developer packages.
- Additional `homelab_target=pi400`: public Samba, Borg, RustFS and Forgejo
  setup/check helpers, unit inputs and release manifests. It changes no hardware.
- Separate dotfiles-ai `headless_server.enabled=true`: native Linux Codex
  bootstrap and selection guard, with its own source/config/state database.
- Upstream Codex owns its executable and `~/.codex`. Authentication, sessions,
  Samba password, Borg key/passphrase, RustFS keys and Forgejo admin/SSH keys are
  private enrollment or encrypted recovery state, never template data.

The generic Fedora profile does not enable Pi services. Neither role changes SSH,
network, sudo, boot settings or desktop applications during chezmoi apply.
Existing homelab setup helpers perform enrollment only when explicitly invoked.
A password prompt is not automation drift; passwords must not be committed.

## Initial source and package setup

After the verified headless image boots, use the trusted SSH alias from private
inventory. Install Git from Fedora if absent, clone the public personal dotfiles
repository into `~/.local/share/chezmoi`, then run the declared installer:

```sh
bash ~/.local/share/chezmoi/dot_local/bin/executable_fedora-server-setup \
  --manifest ~/.local/share/chezmoi/private_dot_config/fedora-server/dnf-packages.txt \
  --role-manifest ~/.local/share/chezmoi/private_dot_config/fedora-server/pi-packages.txt --plan
bash ~/.local/share/chezmoi/dot_local/bin/executable_fedora-server-setup \
  --manifest ~/.local/share/chezmoi/private_dot_config/fedora-server/dnf-packages.txt \
  --role-manifest ~/.local/share/chezmoi/private_dot_config/fedora-server/pi-packages.txt
```

The second command asks for the owner's sudo password. It installs signed Fedora
packages plus checksum-pinned user-local Starship; no tmux or desktop packages.
Review and pin both Git revisions for a recovery exercise. Keep checkouts clean;
do not force-reset local changes when updating.

Create a private `~/.config/chezmoi/chezmoi.toml` with absolute owner paths:

```toml
sourceDir = "/home/you/.local/share/chezmoi"
persistentState = "/home/you/.local/state/chezmoi/chezmoi.boltdb"
[data]
machine_type = "fedora-server"
homelab_target = "pi400"
name = "Your name"
email = ""
atuin_sync_address = "https://api.atuin.sh"
```

Replace `/home/you` with the real home directory. Use mode 0600 for local configs,
0700 for private directories. Atuin automatic synchronization stays disabled until
explicit owner enrollment. Preview `chezmoi managed` and `chezmoi diff`; back up
existing managed targets privately, then apply. A second apply must be clean.
No image or system disk rewrite is needed for ordinary profile updates.

Clone dotfiles-ai separately into `~/.local/share/chezmoi-dotfiles-ai`. Copy its
`config.headless-server.example.toml` into `~/.config/dotfiles-ai/chezmoi.toml`,
substitute actual absolute paths and keep it private. Preview and apply using
`chezmoi --config ~/.config/dotfiles-ai/chezmoi.toml`. Do not enable workstation,
remote-user or centralized-state roles alongside this headless role. Verify both
sources have disjoint managed leaf targets before applying them.

## Service enrollment and recovery

The explicit Pi package manifest covers Samba/SELinux, Borg and Git LFS prerequisites.
Keep Tailscale enrollment from image bootstrap. Enable owner user-service persistence
explicitly with `sudo loginctl enable-linger "$USER"`; ordinary apply does not change it.
Follow the existing file-storage, backup, object-storage and Git-hosting specs in
that order. Public inputs are source-owned; enrollment is explicit and must not
reset credentials on each apply. Preserve private client configuration and keys
from the approved encrypted backup. Re-enroll secrets privately if unavailable.
Restore data into an isolated location and prove the service-level roundtrip
before replacing live data. Borg must refuse an unavailable or wrong 8TB volume.
Never place the only Borg decryption key inside the encrypted repository.

Validate authenticated SMB write/read/delete, RustFS signed S3/DVC access, private
Forgejo Git push/clone, encrypted Borg backup and isolated restores. Check user
services and timer after a controlled reboot. Tailnet-only forwarding and closed
anonymous access remain required. Owner first Forgejo login/password change and
adding client public keys remain private steps.

## Updates and incident handling

Fetch each repository, inspect the diff and fast-forward only the intended clean
checkout. Review package plans separately; chezmoi apply does not run DNF. Run
`codex update` explicitly for the native CLI; reapply must preserve its healthy
selected release and existing login. Authenticate with device login on the Pi;
never copy Mac tokens. Review pinned service security/support notices before
updates. Take and verify a consistent Borg archive before service/data migrations,
and retain the previous binary/configuration until isolated restore passes.

For renewed I/O errors or a read-only root, stop workloads and preserve logs before
repair. Do not repeatedly power cycle, reflash or remount writable. With Pi off,
identify the exact system SSD again, keep it unmounted/read-only for diagnosis,
and retain a private sparse recovery copy before owner-approved offline repair.
On macOS the buffered `/dev/diskNsP` device was required for successful ext4 repair;
the raw `/dev/rdiskNsP` path produced an alignment-related metadata write failure.
Disk numbers are examples, never reusable identities. Optional extent-tree
optimization messages alone were not filesystem corruption. The October incident
showed USB failures involving old RAID members, but retained logs did not prove
the exact cause of the root read-only transition. Those suspect drives remain
retired; current short stability checks are not a long-term hardware guarantee.

Backblaze selection of the Mac backup drive does not prove cloud upload or restore.
Track that verification separately from local encrypted Borg restore.
