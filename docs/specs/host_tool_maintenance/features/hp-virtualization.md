# HP ENVY 13: KVM virtualization stack

Scope: personal `omarchy` Linux x86_64 HP ENVY 13-ah0xxx (i5-8250U, 8 GB).
Personal chezmoi owns the installer helper, its always-run script and the gate.
The firmware setting, the reboot, the first guest and disk placement stay
operator-owned. old-omarchy needs no declaration: Apple firmware already
exposes VT-x and `/dev/kvm`.

## Behavior and contract

| Given | When | Result |
|---|---|---|
| Machine type, OS, architecture and hostname are not exactly `omarchy` / Linux / amd64 / `omarchy` | Source is applied | Neither the helper nor the script is managed. The Try Omarchy guest shares the hostname and is excluded by its other three values. |
| DMI product is not `HP ENVY Laptop 13-ah0xxx`, or stdin is not a terminal | Helper starts | Refuse with a reason before running anything privileged. |
| Stack packages missing | Helper runs in a terminal | `omarchy pkg add` installs `qemu-desktop`, `libvirt`, `virt-install`, `virt-manager`, `dnsmasq` and `swtpm`. No database refresh, system upgrade or reboot. |
| User missing from the `libvirt` group | Helper runs | Create the group if the package did not, then add the user. Membership applies from the next login. |
| `libvirtd.service` not enabled and active | Helper runs | `systemctl enable --now`. Fail if the read-only socket does not answer within 15 seconds. |
| Default network not persistent | Helper runs | Refuse: the package's definition is missing and is not recreated blindly. |
| Default network not marked autostart or not active | Helper runs | Mark autostart and start it. |
| UFW active without all three `virbr0` rules | Helper runs | `ufw route allow in on virbr0`, `ufw route allow out on virbr0`, `ufw allow in on virbr0`. No default policy and no other rule changes. Inactive UFW is left alone. |
| `vmx` absent from `/proc/cpuinfo` | Helper ends | Report that firmware VT-x is off, with `systemctl reboot --firmware-setup` and the BIOS path. No OS command can enable it. |
| `vmx` present, `/dev/kvm` missing | Helper runs | `modprobe kvm_intel`. Fail if libvirt still does not report the `kvm` domain type. |
| Everything converged | Helper runs | No sudo. Print Ready, or the one-time logout note when the session predates the group change. A noninteractive apply stays silent. |

The gate is four values together because the guest answers to the same hostname.
The helper re-checks the DMI product before acting, so a future Omarchy machine
that keeps the default hostname still refuses the stack.

UFW's default forward policy is DROP, which is why the documented exception is
needed: libvirt's own filter accepts `virbr0`, but UFW's forward chain still
drops the packet. The rules are interface-scoped and appear in
`/etc/ufw/user.rules`; when that file is unreadable the helper simply re-runs
the three idempotent `ufw` commands.

## Rollout and rollback

Run `hp-virtualization-setup` on the HP in a terminal. With VT-x still off it
installs and configures everything, then prints the firmware step. The reboot
that follows is the one login the new group needs:

1. `sudo systemctl reboot --firmware-setup` (the firmware reports this route).
2. Configuration, Virtualization Technology, Enabled, F10 to save.
3. Unlock the disk, log in, run `hp-virtualization-setup` again. Expect
   `[hp-virtualization] Ready:`.

Check before relying on it: `ls -l /dev/kvm` and
`virsh -c qemu:///system capabilities | grep kvm`. The live checks on the HP
that matter beyond the rehearsal are daemon socket mode, the default network
coming up behind UFW, and a first guest reaching the network.

To retire: stop and disable `libvirtd.service`, remove the three `virbr0` rules
(`ufw delete route allow in on virbr0`, likewise out and the input rule), remove
the user from `libvirt`, then remove the two declarations. Nothing else was
changed. Guests in `/var/lib/libvirt/images` are not touched by either path.

## Visual Evidence

State, boundary and interaction: required, the transition table above. **Text
equivalent:** an interactive apply on the HP alone converges the stack; the
firmware switch is the operator's; a converged machine needs no sudo and a
noninteractive apply says nothing. Data/trust: no credentials, keys or guest
images are owned by this source. Schema, deployment diagram and quantitative
chart: not applicable; no image format, extra service or metric is introduced.
