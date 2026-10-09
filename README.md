# dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

macOS-focused configuration for development workstations. Secrets are managed via 1Password CLI and age encryption — nothing sensitive is stored in plain text in this repo.

## Not for direct use

This repository is not meant to be cloned or applied directly. It's published as a reference for how I structure my environment. Machine-specific differences are handled via chezmoi templates.

## What's in here

- Shell configuration (bash/zsh)
- Terminal emulator (kitty)
- Editors (neovim/AstroNvim, Zed)
- Window manager (AeroSpace)
- Keyboard remapping (Karabiner)
- Tmux, starship prompt, atuin, direnv, git, ssh
- Homebrew dependencies (Brewfile)

## Zed

Zed stable is installed by the Brewfile (`brew install --cask zed`). Chezmoi
manages `~/.config/zed/settings.json` from `private_dot_config/zed/settings.json`.
Automatic update checks are disabled so Homebrew owns application updates;
run `brew upgrade --cask zed` to update it. Launch it with `zed .`.

To deploy only Zed settings after installing the cask:

```bash
chezmoi apply --exclude=scripts ~/.config/zed
```

The Brewfile also includes `age`, required to decrypt existing managed SSH files.

### Notes and appearance

Zed automatically installs Catppuccin, Catppuccin Icons, and Markdown Oxide.
Both the editor and icons use Catppuccin Mocha. Markdown uses the
Obsidian-inspired [Markdown Oxide](https://zed.dev/extensions/markdown-oxide)
language server, wraps at 100 columns, and does not reformat notes on save.
Open your notes folder as a project so the server can resolve links across files.

- `Cmd+Shift+B`: toggle the built-in outline panel.
- `Cmd+Shift+O`: navigate headings/symbols in the current file.
- Command palette: `markdown: open preview to the side`.
- Use Markdown links or `[[wiki links]]` for connected notes.

This provides a Markdown editing companion for a notes vault, not Logseq's
block database or the full Neorg environment. No Neorg/Norg extension was
listed in the Zed extension registry when checked on 2026-10-01.

### AI authentication

AI credentials are not stored in these dotfiles. Authentication remains a
per-machine setup:

- For Zed's native agent and inline assistant, run `agent: open settings`,
  then configure the desired LLM provider. API keys entered there are stored
  in the system keychain. Provider environment variables are also supported
  and take precedence over saved keys.
- For Codex, Claude, or OpenCode as an external agent, run `zed: acp registry`,
  install the agent, and start its thread. The agent owns its authentication
  and billing; follow its login prompt if needed. Native Zed provider keys
  do not automatically authenticate these external agents.
- Existing CLI credentials may be reused when the agent supports them and
  runs with the same configuration/home directory. Login reuse has not been
  verified on this machine. A shell's lazy `secret` command does not by itself
  inject credentials into an already-running Zed process.

References: [API access](https://zed.dev/docs/ai/use-api-access),
[external agents](https://zed.dev/docs/ai/external-agents).

## Omarchy desk profile

Set `[data].machine_type = "omarchy"` in the local chezmoi configuration.
This profile manages desktop input and shortcuts, Waynergy startup, Samba,
private RustDesk, Catppuccin Mocha, and Zen. It does not apply the
macOS shell, installers, encrypted SSH files, or AI configuration.

```bash
chezmoi apply --dry-run --verbose
chezmoi apply
hyprctl reload
hyprctl configerrors
omarchy-desk-setup smb
```

The SMB command installs Samba, validates the configuration, backs up any changed
system configuration, creates `~/Shared`, asks for an SMB password if needed, and
enables the service. Connect from Finder using `smb://<laptop-IP>/Shared` and your
Linux username. When UFW is installed, setup permits TCP port 445 on the
current private LAN interface/subnet and on Tailscale. Rerun setup if the LAN changes.

The built-in keyboard uses `us(colemak_dh_ortho)` for an unshifted Z X C D V
bottom row. A ZSA already mapping keys in hardware
must not receive another Colemak remapping. Finnish symbols and remote input
mapping need separate verification with the actual Mac input-sharing application.

Synergy licenses, activation state, Samba passwords, and runtime credentials stay
outside Git. `dotfiles-ai` remains an independent source and must not own the same
live files. Use its opt-in `linux_workstation` profile and `config.omarchy.example.toml`;
leave sandbox and guest VMs disabled.
The Omarchy `.bashrc` preserves the packaged shell integrations and routes
Codex, OpenCode, Herdr and Worktrunk to their user-local managed commands,
including after Mise updates PATH. Open a new terminal after applying it.

### Input-sharing experiment

Run `omarchy-desk-setup input` in a terminal to install `synergy3-bin` and
`waynergy` through Omarchy's AUR package workflow, plus `wl-clipboard` from the
Arch repositories. Test the clients separately; never run both simultaneously.
Synergy activation and generated runtime state remain outside Git. Hyprland
support and interoperability with the Mac's Synergy version remain experimental.
The setup helper enables `omarchy-waynergy.service` for future desktop logins.
Set `[data].waynergy_server` in chezmoi to override the default Mac LAN address,
and `waynergy_client_name` to match the Mac screen name.
Verify screen-edge switching, Finnish symbols and modifiers on both keyboards.
Waynergy supports text clipboard; image clipboard is not available through this
client. Images and files can use SMB/LocalSend.
The Mac's `@` symbol is routed to a dedicated virtual key whose XKB type consumes
its symbol-producing Option/Shift modifiers. This prevents an Option+2 firmware
chord from activating a browser shortcut while keeping Option+letter navigation.

## Tests

Unit tests for kitty workspace scripts (session serialization/deserialization):

```bash
python3 -m venv /tmp/dotfiles-test-venv
source /tmp/dotfiles-test-venv/bin/activate
pip install pytest
pytest tests/ -v
```

CI runs on push/PR via GitHub Actions.

### Private RustDesk server

`omarchy-desk-setup tailscale` installs the Arch package and enables `tailscaled`
at boot; enroll interactively in your existing tailnet. Then run
`omarchy-rustdesk-setup` to install the managed Podman Quadlet definitions and system
services. It runs before desktop login and publishes only native-client ports
21115–21117 on the Tailscale IPv4 address. Every client must join the tailnet
and use the printed ID server, relay address, and public server key.
Podman runs without a permanent daemon. A prior Docker deployment is stopped
only after migration preparation; server data is reused and Docker is disabled
only when no other workloads are running. The official OSS image is pinned to the 1.1.16 registry digest. Private keys and
database remain in `/var/lib/rustdesk-server`; never commit that directory.
The laptop must be awake for registration and relaying. No guest VMs are used.
The setup also runs `omarchy-rustdesk-firewall`, which adds persistent UFW
forwarding rules limited to Tailscale ingress, the discovered Podman bridge
and IPv4 subnet, and RustDesk TCP 21115–21117 / UDP 21116. This is required
when Omarchy’s existing Docker guard rejects traffic to container subnets
before Tailscale’s forwarding rule. To repair an already installed server,
run `omarchy-rustdesk-firewall` in a terminal. A local port check does not
exercise this forwarded path: verify connectivity from another tailnet peer.

### Mac-primary keyboard navigation

Waynergy maps Mac native wire keycodes to Linux evdev positions using a Finnish
Mac symbols map; the ZSA's firmware supplies Colemak DH. This avoids letter keys
colliding with Omarchy's physical number/media bindings. The built-in keyboard
continues using its separate Colemak-DH Ortholinear configuration. Shortcut
matching uses each keyboard’s actual symbols (`resolve_binds_by_sym`).
The managed Hyprland bindings mirror core AeroSpace actions: Option+N/E/I/O
focuses left/down/up/right, Shift adds window movement, Ctrl+Shift+Option+1–7
selects workspaces, and Cmd adds silent window transfer. Option+Tab returns to
the previous workspace. Cmd+Space opens apps; Cmd+W or Cmd+Q closes a window.
Omarchy's app-aware Cmd+C/V clipboard shortcuts remain active; preinstalled
app/web shortcuts are disabled. Hyprland directional movement swaps tiles;
AeroSpace's tree joining and accordion/service modes are not identical and
are not emulated by this core navigation profile.

### Mocha and Zen

The managed theme script selects Omarchy’s stock `catppuccin` (Mocha). The bar
uses `transparent=false`. Run `omarchy-zen-setup` in a terminal to install the
AUR browser, deploy the existing Mocha CSS to registered profiles, and install
Dark Reader through a browser policy. A pacman hook preserves that policy
after Zen upgrades while retaining packaged and unrelated policies. Restart
Zen after configuration changes.

Dark Reader does not consume managed theme settings. Its supported import
file lives at `~/.config/zen-managed/darkreader-mocha.json`: in the extension,
open Settings → Advanced → Import settings and select that file. It uses
Mocha background `#1e1e2e`, text `#cdd6f4`, and mauve selection `#cba6f7`.
Import again after changing the source file; browser sync is disabled so it
does not overwrite this machine’s managed preset.

### Rebuilding an Omarchy machine

1. Install chezmoi from Arch and authenticate GitHub to clone both repositories.
2. Initialize this source with `machine_type=omarchy`, then review the diff and
   apply. Use the Omarchy branch containing these changes until merged.
3. Run `omarchy-desk-setup input`, pair Synergy on the Mac, and stop its native
   Linux client before starting `systemctl --user start omarchy-waynergy`.
4. Run `omarchy-desk-setup tailscale`, enroll in the tailnet, then
   `omarchy-rustdesk-setup`. Configure clients with its printed public key.
5. Run `omarchy-desk-setup terminal`, `omarchy-desk-setup smb`, and
   `omarchy-zen-setup`. Import Dark Reader’s
   managed preset once.
   For an always-on desk host, run `omarchy-desk-setup always-on` as well.
6. Copy the AI repository’s Omarchy example config, substitute home and username
   paths, apply it, then run `dotfiles-ai-omarchy-setup`. Authenticate each AI
   provider separately.
7. Run `omarchy-espanso-setup`, restore the private Espanso source from the
   encrypted backup, and apply it using its separate chezmoi config. Test on
   both built-in and remote keyboards. See `~/.config/omarchy-host/next-steps.md`
   for the interactive sign-ins, transfer, theme import, and access checks.

Configuration and installation are reproducible; authentication is interactive.
To preserve the RustDesk server’s identity across a wipe, securely back up
`/var/lib/rustdesk-server` outside the laptop before wiping and restore it
before starting its services. Otherwise it generates a new key and clients
need updating. Likewise, back up Synergy’s paired private certificate and
Waynergy trust hashes securely, or pair again. Never place these secrets,
Tailscale enrollment state, provider credentials or Samba passwords in Git.

### Kitty terminal

Run `omarchy-desk-setup terminal` to install Arch’s Kitty package and
`ttf-monofur-nerd`, then select Kitty through Omarchy’s default-terminal command.
Chezmoi owns `~/.config/xdg-terminals.list`, the shared Kitty configuration,
Mocha palette, and portable snapshot scripts. macOS titlebar configuration
is rendered only on macOS; the Linux profile adds Cmd/Super+T for a new tab
and Cmd/Super+N for a new OS window.

Open Kitty with Cmd+Enter from the Mac or Super+Enter on the built-in keyboard,
or choose Kitty from the Cmd+Space app launcher. Cmd+C/V use Omarchy’s
terminal-aware copy/paste dispatch and Kitty’s explicit Insert mappings.
Ctrl+Shift+C/V remain available as direct terminal shortcuts. Drag to select
text before copying. Ctrl+Cmd+T now toggles floating/tiling; Cmd+T passes
through to the application instead.

Fonts use the Mac configuration’s Monofur Nerd Font at 14pt. The existing
macOS workspace session files contain project-specific paths and are not
deployed to this new laptop. The optional xonsh shortcut still requires
xonsh to be installed separately.

### Controlling this Omarchy desktop with RustDesk

Run `omarchy-rustdesk-client-setup` in a terminal. It installs `rustdesk-bin`
through Omarchy’s AUR workflow, enables the packaged `rustdesk.service` at boot,
and applies the managed private-server settings through RustDesk’s CLI.
It reads the local server’s current public key and Tailscale address when
available, so rebuilding that server does not leave this client pointed at
a stale key. The fallback routing preset is in
`~/.config/rustdesk-client/server.json`.

The client’s device identity and access credentials are runtime state and
stay outside Git. Open RustDesk from the app launcher, enter its displayed ID
on the Mac/iPhone, approve the incoming connection, and select the screen
when the Wayland portal asks. Set a permanent access password through
RustDesk’s Security settings if needed; never commit it.

The server’s boot readiness and the desktop client’s availability differ:
the standard RustDesk client has experimental Wayland support, and this
Hyprland profile does not provide remote login-screen access. Screen capture
and remote input must be verified in an active, logged-in desktop session.
The packaged root service handles input injection; do not make `/dev/uinput`
world-writable as a workaround.

### Encrypted recovery archive

Run `omarchy-recovery-backup` in Kitty after setup and copy the resulting
`~/Shared/Recovery/*.tar.gz.age` off this laptop. The helper briefly stops
active RustDesk and Samba services to copy their databases consistently,
encrypts directly with your configured chezmoi age recipient, and restarts
the services. It includes RustDesk identities, Samba password hashes,
Synergy certificates, Waynergy trust, local chezmoi configuration and available
Codex/OpenCode authentication. It never writes a plaintext archive.

Keep the matching age private identity safely on another device. Verify the
archive there before wiping, for example with
`chezmoi decrypt omarchy-YYYYMMDD-HHMMSS.tar.gz.age | tar -tzf -`.
To restore on a rebuilt machine with the same username, decrypt and extract
the archive into `/` while RustDesk and Samba are stopped, then rerun the
managed setup commands. Local configurations contain the original home and
state paths; update them if the username changes. Enroll Tailscale again.
The archive contains credentials: keep it encrypted and outside Git.

Zen's user desktop entry opens `~/.zen/omarchy` explicitly, so launching it
from the app menu or a link uses the managed profile instead of a profile picker.

### Always-on access

Run `omarchy-desk-setup always-on` in Kitty to install the managed logind
drop-in and enable Tailscale SSH. On external power, closing the lid does not
suspend the laptop; battery lid behavior remains unchanged. Automatic idle
suspension is disabled. Explicit sleep/shutdown and power loss still stop
network access. The existing five-minute desktop lock is retained and does
not stop the system services. RustDesk registration/relay, Samba and Tailscale
run at boot independently of the desktop session.

From another authenticated tailnet device, use `ssh tis@100.86.125.94` (substitute
the rebuilt host's username/IP). Tailscale supplies SSH authentication and
authorization, so no separate SSH daemon or public SSH port is required.
The tailnet policy must permit both network and SSH access; its default rule
allows access to your own devices and may require browser reauthentication.

RustDesk's current Wayland client does not guarantee access to the login screen
after logout. Screen capture and unlocking an idle-locked Hyprland session must
be tested from the actual remote client. Omarchy's existing desktop autologin
starts the session after boot, but the encrypted root disk must first unlock;
neither RustDesk nor ordinary SSH is available at that early disk prompt.
No disk-unlock or desktop-login security settings are changed by this helper.

For long-lived server availability, review this device's key expiry in the
Tailscale admin console and disable expiry there if that matches your policy.
Enrollment and expiry are tailnet state, not settings chezmoi can recreate.

### Private Espanso configuration

`omarchy-espanso-setup` installs the prebuilt Wayland release through AUR and
enables its managed desktop service. It skips the first-run wxWidgets wizard,
which crashes with the prebuilt Debian executable on this Arch installation.
Search/forms still use that GUI library and need separate verification. The
service limits repeated restarts and core dumps. The helper initializes the
built-in keyboard as `us(colemak_dh_ortho)` and disables the double-Alt toggle.
Personal Espanso files must remain in a separate
private chezmoi source; this public source does not manage `~/.config/espanso`
and ignores accidental Espanso source directories in Git. Never add snippet
contents or a configuration archive to this public repository.

Transfer the Mac configuration through the private Samba share for initial
import. The recovery helper includes live Espanso configuration and the local
private source in its encrypted archive. Recreate and verify the off-machine
backup after changing those files. Wayland Espanso reads kernel input devices;
expansions from Waynergy's compositor-level virtual keyboard require separate
verification and are not guaranteed by installing Espanso.

The local private source is `~/.local/share/chezmoi-private/espanso`, configured
by `~/.config/chezmoi-private/espanso.toml`; it has no public Git remote. Manage it
with `chezmoi --config ~/.config/chezmoi-private/espanso.toml ...`. After editing
the live configuration, use that command with `add ~/.config/espanso` to save it,
then refresh the encrypted recovery backup. A private Git remote can be added
later; never push this source to the public dotfiles repository.
