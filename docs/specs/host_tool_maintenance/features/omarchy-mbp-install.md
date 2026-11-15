# Omarchy bare-metal install on the MacBook Pro

## Domain and scope

Owner: dotfiles maintainer. Target: `macbook-pro` (MacBookPro17,1, 13" M1,
16 GB, 512 GB SSD, macOS 27.2.1, FileVault on). Risk: elevated — the install
repartitions the internal disk and changes boot policy while macOS stays
bootable beside Omarchy. Delivery: registry and runbook first (this slice);
the bare-metal install itself is executed at the host in one guided session.

Route chosen: the official Omarchy for Apple Silicon installer
(`brew install omacom/mac/omarchy`, installer 2.3.16 installed 2026-11-15)
over the legacy Asahi Alarm script route. Reasons: least physical console
time, official release channel, USB-C multi-monitor and Touch ID login are
installer features, and M1 is the best-qualified silicon for it. macOS stays
installed by design; firmware updates continue to come through macOS.

The legacy Intel-Mac USB/Secure Boot flow from the Omarchy manual does not
apply. No USB drive is required; the installer shrinks the APFS container
after the operator attests to a current backup (Carbon Copy Cloner is the
owner's backup tool; Time Machine is not used on this host).

## Install runbook

| Phase | Actor | Required outcome |
|---|---|---|
| 0. Pre-flight | session | Free space confirmed (176 GiB observed), macOS 27.2.1 confirmed, FileVault state recorded, installer installed via Homebrew. |
| 1. Backup | owner | Fresh Carbon Copy Cloner clone of the macOS side. The installer's backup checkbox is an attestation, not a check. |
| 2. Installer GUI | owner at host | Review disk plan, set Omarchy size (100–120 GB), tick backup attestation, authorize with the macOS admin password; stay on power. |
| 3. Recovery finish | owner at host | Shut down, hold power until "Loading startup options", choose Omarchy, sign in with the macOS account, wait for "Installation complete!", restart. |
| 4. First boot | owner at host | Hold power, choose Omarchy, set the disk-encryption password, join Wi-Fi. The passphrase is typed at the machine on every boot; accepted because the host lives on the desk. |
| 5. Remote re-entry | owner then session | Run `omarchy-setup-security-sshd` (re-enables sshd behind the default-deny firewall, can fetch the session key from GitHub keys); session then rejoins over SSH/Tailscale. |
| 6. Qualification | session | Apple Silicon quirk checklist below, then chezmoi omarchy profile deployment and backup enrollment. |

## Known Apple Silicon quirks to check after install

- Wi-Fi dead after install: an Intel-Mac quirk script can write
  `/etc/modprobe.d/brcmfmac.conf` on Apple Silicon Broadcom chips
  (upstream #7439). Fix: remove the file and reload `brcmfmac`.
- Brightness slider no-op: point `OMARCHY_BACKLIGHT_PATH` at the real
  `apple-panel-bl` device (upstream #8125).
- Audio stuck after resume: `systemctl --user restart wireplumber`
  (PipeWire teardown defect, upstream #10858).
- Built-in mic silence on 4.5.0-rc3 on J293 was reported (upstream #17602);
  verify mic and webcam explicitly.
- Installer 2.3.16 had one reported Recovery binary hash-mismatch failure
  (upstream #18016). If hit, fall back to the 2.3.15 dmg.

## Backup shape decision (open)

The new host joins the existing borg/borgmatic stack
(`private_dot_config/omarchy-host/backup`); restic was considered and
rejected in favor of the one tested engine. The repository shape is open
because the preferred network destination `mac-backup-disk` is near full:
a dedicated ext4 disk (HP pattern) versus an SSH forced-command repository
on the mini (homelab pattern) versus both.

## microSD card validation (blocking the storage decision)

The owner attached a 471 GB exFAT microSD (retired Fujifilm camera card,
`fuji-sd-500gb` in the homelab registry) and required its contents be
verified present on `mac-backup-disk` before reuse. Validation on
2026-11-15 compared all 701 card files by filename and size against the
8 TB's `ADATA`, `4TB WD` and `ext-3` trees (Photos library internals and
Capture One catalog backups excluded):

- 73 files matched name and size, all under `ADATA/Transcend/Lumi` and
  `ADATA/Transcend/magialemuria/Capture` (project copies).
- 77 same-name files differ in size; the sampled collisions are an older
  camera counter cycle, including Capture One preview-cache blobs from
  2021.
- 551 files, including every one of the 87 MOV files, are absent by
  original filename.

Conclusion: the card is the only verified copy of roughly 90% of its
content and must not be emptied. The 45 GiB payload fits the 8 TB's
remaining 136 GiB free; a dated dump copy to the 8 TB (or `ext-2`/`ext-3`
overflow) unblocks reuse. Same-folder candidates `ext-3/DCIM/110AF000`
(597 files) and `4TB WD/110AF000` (4 movies) share zero filenames with the
card and are different shoots that reused the folder number.
