# old-omarchy: remote Intel Mac mini

Host: `old-omarchy`, user `tis`, personal profile `machine_type = "omarchy"`.
Observed Intel Sandy Bridge/i915, 8 GB RAM, encrypted Kingston 120 GB system SSD.
This is not the NVIDIA-equipped 2010 model initially assumed.

## Ownership and convergence

Personal chezmoi owns the hostname-gated:

- `~/.local/bin/old-omarchy-setup` and its package/public-key manifests.
- `~/.config/dotfiles-ai/chezmoi.toml`, pointing at
  `~/Projects/dotfiles-ai` and `/var/lib/dotfiles-ai/tis`.
- Interactive reconciliation through `run_after_configure-old-omarchy`.
  Noninteractive applies deploy files but explicitly report privileged setup
  pending. Run `old-omarchy-setup` from a terminal to finish.

The helper uses existing owners: Omarchy packages (SSH, Tailscale, RustDesk,
gliff, bolt, diagnostics); mise for chezmoi and the Omarchy OpenCode provider;
dotfiles-ai for shared AI configuration and Worktrunk. The Herdr provider stays
pacman-owned at `/usr/bin/herdr`. It never kills an active agent/server to
force an installer past its ownership guard.

The helper preserves existing authorized keys and merges the selected public
keys by type/key material. Private keys, age identities, Tailscale enrollment,
provider credentials and RustDesk permanent passwords are not committed.
Tailscale login remains interactive (`sudo tailscale up --hostname old-omarchy`).

## Headless desktop

Working parameter: `video=HDMI-A-3:1920x1080@60e`.

On this installation `/etc/default/limine` sets `KERNEL_CMDLINE[default]`,
overriding `/etc/kernel/cmdline`. The helper appends only this parameter,
preserves root/LUKS identifiers, backs up the original config once, and runs
`limine-update` only when adding the parameter. It does not reset boot config.
The earlier copy of the parameter in `/etc/kernel/cmdline` is redundant.

Validated: normal Hyprland (not safe mode), parameter in `/proc/cmdline`,
HDMI unplugged, gliff stable. The earlier hot-unplug before the parameter took
effect crashed Hyprland and entered recovery mode.

Reboot still requires LUKS unlock. Gliff/RustDesk/Tailscale cannot handle
pre-boot unlock. An **IP-KVM** with HDMI capture and USB keyboard emulation
can; an ordinary local KVM cannot provide network access.

## Remote access

- HP/MBP: `gliff tis@old-omarchy` over Tailscale.
- Try Omarchy: `gliff tis@192.168.100.146` over LAN (current DHCP address).
  Do not assume the guest has MagicDNS/Tailscale. Reserve this address on the
  router if it must stay stable.
- The reproduced UFW rule allows TCP/22 inbound on `wlp3s0`. This is
  interface-wide LAN access, **not restricted to Try Omarchy's host**.
  SSH authentication remains required. The helper never disables UFW.
- RustDesk is installed, but service/autostart, unattended password and
  Wayland portal capture approval have **not been qualified**. Do not claim
  RustDesk unattended headless readiness based on gliff's successful test.

## Kanex and HDD: unresolved

Only the selected Kanex UUID `0005001a-5404-a700-ffff-ffffffffffff` is enrolled
with automatic policy. Reboot established its ASM1042A USB and ASM1061 SATA
controllers. Both external SATA links report down; no USB-SATA device or
external block device is visible. Authorization alone did not fix the HDD.

Never use `/dev/sda`: it is the internal Kingston system SSD, serial
`50026B7244056BE3`. No format, partitioning or wipe operation is automated.

Next: confirm HDD model/capacity, 2.5 vs 3.5-inch, cabling and power. A
3.5-inch HDD requires a powered adapter supplying 12 V; USB alone is
insufficient. Once enumerated, inspect SMART/signatures read-only. Obtain
explicit erase confirmation for the identified serial before formatting.
For Linux-only data, ext4 is a reasonable default. Declare a future mount by
filesystem UUID with boot-tolerant removable-drive policy, not `/dev/sdX`.
