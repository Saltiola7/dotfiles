# Remaining interactive steps

Local configuration is deployed. These actions require your Mac, browser login,
private files, or an actual remote-control test.

## Keyboard and Synergy

Fully quit and reopen Synergy on the Mac if Omarchy stops responding. The Linux
Waynergy service reconnects automatically. It has recently connected and then
timed out waiting for traffic; subsequent TLS handshakes were reset by the Mac.
Restarting the Mac application restored access previously. This remains an
unresolved reliability problem, so don't treat the desktop trial as complete.

Test your ZSA's @ key in a ChatGPT message field, a Zen text field, and Kitty.
It should insert @. Test Option+N/E/I/O navigation and Cmd+C/V afterward.
The Option+2 binding inserts the character through wtype after Option releases,
explicitly clearing Alt for the generated event without a fixed delay. The
text-injection keyboard cannot activate desktop shortcuts. Repeated automated
tests produced 40/40 plain @ events; verify your actual ZSA key in those applications.

To open Kitty, use Cmd+Space while controlling Omarchy, type Kitty, and open it.
On the built-in keyboard, the Windows/Super key corresponds to Cmd.

## AI sign-ins

First check `codex login status` and `opencode auth list`. If already signed in,
skip the login steps and test a harmless prompt. Otherwise, in Kitty run:

```sh
codex login --device-auth
```

Leave it running. Open the URL it prints on your Mac, enter the newly displayed
code, and finish signing in. Enable device-code authorization in your ChatGPT
security settings if the login page requires it. Earlier codes have expired.
Check completion with `codex login status`.

Next run `opencode auth login`, select OpenAI, then the ChatGPT/headless login
method. Follow its fresh URL/code and check with `opencode auth list`.
Credentials live in this machine's private AI runtime state, outside Git.
Finally open Codex and OpenCode and send a harmless test prompt in each. Open
Herdr from Kitty to verify a real multiplexer session; sign-in status alone
does not verify a real provider request or a multiplexer session.

Official Codex guidance: https://learn.chatgpt.com/docs/auth

## Private Espanso

Espanso is installed, running, and enabled for desktop startup. Its crashing
first-run wizard is skipped. GUI search/forms still need testing. The bootstrap
configuration uses the built-in Colemak DH layout.

On your Mac, run `espanso path` to locate the configuration directory. In Finder,
connect to `smb://100.86.125.94/Shared` while Tailscale is connected. Copy that
configuration folder there as `espanso-private`. Do not put it in either public
repository or paste your snippets into chat. Tell me when the copy is complete
so I can adapt Mac-specific commands and app filters before activating it.

Before importing, type `:espanso` in an ordinary text field with the built-in
keyboard; the installed default example should expand to `Hi there!`. Repeat
through Synergy. Waynergy injects compositor events, while Espanso reads kernel
input devices, so remote expansion may fail even when built-in expansion works.
If it fails, report which keyboard failed; don't switch Waynergy backends yet.

Private source: `~/.local/share/chezmoi-private/espanso`
Private config: `~/.config/chezmoi-private/espanso.toml`

After intentional edits, save them locally with:

```sh
chezmoi --config ~/.config/chezmoi-private/espanso.toml add ~/.config/espanso/config ~/.config/espanso/match
```

To restore from that source, run `chezmoi --config ~/.config/chezmoi-private/espanso.toml apply`.
This private source has no remote. The encrypted recovery backup includes it.
A private Git repository can be added later if you prefer.

## Dark Reader Mocha

Zen's launcher and its ordinary default both select `~/.zen/omarchy`. If a
different profile appears after restarting, close Zen and run
`omarchy-zen-profile`, then reopen using the app launcher. Alternate profiles
are preserved, with changed registries backed up in `~/.local/state/omarchy-zen`.

In Zen, open Dark Reader's settings, then Advanced → Import settings. Select
`~/.config/zen-managed/darkreader-mocha.json` (Ctrl+L in the file picker accepts
the full path). The extension is installed and its preset is managed, but the
extension's supported import requires this browser action. Confirm a light
website gets the Mocha background.

## Always-on access

With Mac Tailscale connected, run in the Mac terminal:

```sh
ssh tis@100.86.125.94
```

Complete any Tailscale authorization page. Run `hostname` after connecting.
Then lock Omarchy, close its lid while plugged into power, wait a minute, and
try SSH and RustDesk again. Check control, not just connection status.
Services start automatically, and AC lid-close does not suspend. Locked-screen
RustDesk behavior still needs this real test. After a reboot, the encrypted
disk needs physical unlocking before SSH or RustDesk becomes available.

In the Tailscale admin console, consider disabling this machine's device-key
expiry for a long-lived server. Its current expiry is April 6, 2027. Tailnet
enrollment, access rules, and expiry are external state, not chezmoi files.

## External Borg backups

Borg/borgmatic configuration is managed under `~/.config/omarchy-host/backup`.
Formatting and privileged installation are explicit steps, never chezmoi apply.
`omarchy-backup-setup` installs the Arch packages and reconfigures an existing
registered drive without formatting. Initial disk preparation needs the explicit
`backup/setup initialize-drive` command with the verified USB by-id path.

The daily timer is scheduled at 03:00 America/Mexico_City with up to 15 minutes
of randomized delay and catches up after downtime. Retention is 7 daily,
4 weekly and 6 monthly archives. An exact filesystem UUID/mount check prevents
writing to the internal disk when the external drive is absent or substituted.
The mount uses `nofail`, so a disconnected drive does not block boot.

The encrypted file backup covers the home directory (including Zen, private
Espanso and unpushed work), `/etc`, `/boot`, `/root`, private service identities,
AI runtime state and package inventories. Caches, virtual environments,
node_modules, old recovery archives and mounted network drives are excluded.
Network-drive data needs its own backup arrangement. Borgmatic uses native
Btrfs snapshots for stable file copies. Every job verifies that existing
critical configuration, Zen and service/AI identity files appear in the archive
before pruning older backups. These snapshots provide crash consistency, not
an application-specific transactional guarantee. `/boot` is copied separately.
This is file recovery after reinstall, not a directly bootable disk clone.

The root-readable password lives at `/etc/omarchy-backup/passphrase`. Setup
creates a private `~/Shared/Backup-Recovery` folder with the password and an
export of the encrypted repository key. Copy that folder to the Mac and save
it in 1Password or another independent secure location. It is excluded from
public Git and the backup archive. Do not store the only recovery password on
the same laptop or the backup thumbdrive.

To inspect or run the configured job:

```sh
systemctl list-timers omarchy-backup.timer
sudo systemctl start omarchy-backup.service
sudo journalctl -u omarchy-backup.service -n 40
sudo borgmatic --config /etc/borgmatic/omarchy.yaml repo-list
```

After losing the machine, install Borg, set `BORG_PASSCOMMAND` to read the
saved password, and access the existing repository. Extract into an isolated
directory first; never overwrite the new system blindly. For example:

```sh
export BORG_PASSCOMMAND='cat /secure/path/passphrase'
borg list /mnt/omarchy-backup/borg
mkdir ~/restore-test
cd ~/restore-test
borg extract /mnt/omarchy-backup/borg::ARCHIVE home/tis/.config/hypr/hyprland.lua
```

For unattended backups on a rebuilt machine, securely restore the password to
`/etc/omarchy-backup/passphrase` (root, mode 0600), restore the managed drive UUID
through chezmoi, then run `omarchy-backup-setup`. Do not initialize the drive.
The setup refuses to invent a password for an existing repository.

## Recovery before wiping

### Current snapshot and backup coverage

Omarchy's Snapper root configuration captures system rollback snapshots before
Omarchy updates and retains five numbered snapshots. Timeline snapshots are
disabled; the cleanup timer is enabled. Root snapshots exclude the separate
`/home`, package-cache and log subvolumes. Limine snapshot integration is
installed. Run `sudo snapper -c root list` to verify actual retained snapshots;
the October 9 audit could read the configuration but could not list snapshots
without a password. Use `omarchy-snapshot create` for a manual system snapshot.

These snapshots remain on the same physical disk. They do not protect against
disk loss or a machine wipe. The existing encrypted recovery archive is also
on this disk; an independent copy and a successful decryption test are pending.
The recovery helper covers service identities, credentials and private Espanso
state, but does not currently include Zen's personal profile, all home files,
or a complete bootable system image.

For the next backup setup, choose an off-machine destination and cover the
personal Zen profile, private configuration and AI state, Shared files, and
service databases/identities. Keep public reproducible configuration in the
two dotfiles repositories. Back up private Git state and any unpushed work as
well. Verify the encryption identity is available independently, perform a
restore test into an isolated directory, and document reinstall and recovery.
Choose whether full disk-image recovery is also needed before implementing
that additional layer. The external Borg setup above adds the daily backup
layer; verify its first archive and recovery credentials before relying on it.

In Omarchy Kitty run `omarchy-recovery-backup` and enter the Linux password.
This briefly stops and restarts RustDesk/Samba to copy their databases safely.
Copy the newest `Shared/Recovery/*.tar.gz.age` archive to your Mac afterward.

On the Mac, decrypt it with the age private identity matching the recipient in
Omarchy's chezmoi config, for example:

```sh
age --decrypt -i /path/to/your/private-age-key /path/to/backup.tar.gz.age | tar -tzf -
```

Do not paste the key or archive listing into chat. Confirm decryption succeeds.
The matching private key is currently absent on Omarchy; having an encrypted
archive alone does not prove you can restore it. Keep the archive and private
identity safely off this laptop before wiping it. Make another backup after
Espanso import and AI sign-in so those private files are included.
