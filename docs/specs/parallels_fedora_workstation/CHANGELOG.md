# Parallels Fedora Workstation Changelog

## 2026-09-05 - Live Sway Session Reconciliation

- The operator configured a working Sway session out of band. Reconciled the
  exact guest bytes into the source: `95-fedora-personal.conf` gained the
  Catppuccin Mocha client colors, pixel borders, `layout toggle all`, and the
  solid `#1e1e2e` background replacing the Fedora wallpaper; new
  `private_dot_config/waybar/config.jsonc` (position top) and `style.css`
  (Mocha, JetBrainsMono Nerd Font) and `private_dot_config/kitty/catppuccin-mocha.conf`
  (upstream Mocha theme) were adopted verbatim. Source SHA-256 values equal the
  live guest files for all four paths.
- `bar-mocha.sh` was removed by the operator and is absent from the source; a
  regression test rejects its reappearance. The retired bar helper is replaced by
  Fedora's waybar integration with the managed theme files.
- The Fedora deny-by-default starter scope now manages the five reconciled
  targets and nothing else. The live guest `~/.config/kitty/kitty.conf` remains
  an intentionally unmanaged stand-in pending the personal-profile template; the
  macOS `kitty.conf` (`include mocha.conf`) is unchanged, and `waybar` plus the
  Catppuccin theme stay excluded on macbook, mac-mini, and `lmsh`.
- `sway --validate --config /etc/sway/config` passed in the real guest headless
  after the drop-in change. No VM restart, session switch, package change, or
  live config write was needed; the guest was already running the reconciled
  state. Scoped suite passed 46 tests each on Python 3.12, 3.13, and 3.14;
  `git diff --check` clean.

## 2026-09-05 - Lighter-Workflow Adoption And Native Starter

- User authorized local implementation/deployment outside DBSCTR completion in
  the existing PFW-001 checkout. PFW-001 remains blocked on its old Initiative
  receipt; this evidence neither rebinds that receipt nor passes its gates.
- Reverified the GUI-installed Fedora Server 44 aarch64 guest with GNOME,
  `parallels` UID/GID 1000, original root/data UUIDs, owner-safe sentinel,
  internal 64 GiB root backing disk and external 160 GiB data backing disk.
  Rechecked APFS identities and 200 GiB quota. Started only the existing VM.
- Replaced legacy ISO download/CLI creation with immediate GUI-guidance refusal.
  Host verification resolves the APFS device dynamically and the VM bundle from
  inventory, verifies existing storage without creating it, and no longer
  requires an installer ISO or attached CD. Guest verification checks actual
  edition/account, filesystems, ownership, native shares and explicit probe output.
- Exclusive-create probes on `/media/psf/ext/git` failed as `parallels` (EACCES)
  and root (EPERM). `/media/psf/git` accepted a `parallels` probe and removed it.
  Host inventory reports global sharing disabled despite mounted custom shares;
  actual guest filesystem results, not that flag or FUSE mount options, establish
  these observed permissions. No guest-only read-only remount was added.
- Installed the official Fedora package subset declared in
  `private_dot_config/fedora-workstation/dnf-packages.txt` using
  `dnf install -y --setopt=install_weak_deps=False` after transaction previews.
  First transaction added 177 packages and updated libgcc/libgomp/libstdc++;
  second added 11 packages for the Sway launcher, portals and session integration.
  No kernel, edition, account, filesystem or default session was replaced.
- Confirmed GNOME and Sway login entries coexist. Deployed the user-owned
  `95-fedora-personal.conf` drop-in without overwriting any existing target;
  it keeps Fedora defaults, selects Kitty and adds Colemak navigation with Super
  substituted for host Alt. Removed conflicting default layout/logout bindings.
  Real guest headless `sway --validate --config /etc/sway/config` returned the
  explicit `SWAY_CONFIG_VALID` marker. No graphical session was switched.
- The Fedora chezmoi starter is deny-by-default and currently manages only the
  Sway drop-in and native package list. This is not a complete personal profile;
  no general chezmoi apply or configuration-repository cloning was performed.
- DNF reported transient systemd scriptlet transport warnings. A subsequent
  `systemctl --failed` listed zero failed units; package presence and post-install
  adoption checks passed. No speculative systemd repair or reboot was attempted.
- Validation: legacy refusal regression first failed as intended; revised
  scoped suite passed 45 tests each on installed Python 3.12, 3.13 and 3.14,
  including starter/profile-isolation and existing terminal/AI ownership checks.
  Shell syntax and `git diff --check` passed. Both deployed starter files matched
  source SHA-256 digests; `systemctl is-system-running` reported `running`.
  Two compound transport checks returned Parallels invalid-argument errors;
  bounded direct `sha256sum` and `systemctl` checks supplied the final evidence.
- Remaining: interactive GNOME/Sway graphics, clipboard, resizing and key
  forwarding; three-workday comparison; full personal shell/state/recovery setup;
  Starship and vendor desktop packages; guest-local enrollment; explicit project
  source/destination selection; separately owned AI distribution/qualification.
  No project content, host credentials, private guest state or valuable data was
  copied, reset or deleted. No commit, push, PR or DBSCTR completion was performed.

## 2026-08-31 - Initiative Discovery

- Defined the Parallels 27, Fedora 44 ARM64 GNOME, internal root, external data,
  host-share, resource-profile, update, recovery, and rebuild contracts.
- Assigned personal desktop/shell ownership to this repository and AI-only
  ownership to the independent `dotfiles-ai` source.
- Recorded guest-local authentication, same-service isolated Atuin state, and the
  operator-accepted unencrypted external-state risk.
- No package, volume, VM, share, guest, credential, or live configuration changed.
