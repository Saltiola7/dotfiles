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
The Option+2 binding inserts the character through wtype. An automated chord
test produces a plain @ event; verify your actual ZSA key in those applications.

To open Kitty, use Cmd+Space while controlling Omarchy, type Kitty, and open it.
On the built-in keyboard, the Windows/Super key corresponds to Cmd.

## AI sign-ins

In Kitty on Omarchy, run:

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
Herdr from Kitty to verify a real multiplexer session; provider behavior has
not yet been tested because both tools are unauthenticated.

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

## Recovery before wiping

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
