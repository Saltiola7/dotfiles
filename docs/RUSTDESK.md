# RustDesk and Tailscale startup

Chezmoi manages desktop startup for the Mac mini, MacBook, and Omarchy. Existing
RustDesk credentials, access permissions, and server routing remain machine-local.

## macOS

The Brewfile installs RustDesk. The managed LaunchAgent
`~/Library/LaunchAgents/dev.dotfiles.rustdesk-login.plist` opens the installed app
in the background at graphical login. It uses Launch Services, so it does not
create a second `--server` process alongside RustDesk's own service.

Apply and activate it without applying unrelated dotfiles:

```bash
chezmoi apply --exclude=scripts ~/Library/LaunchAgents/dev.dotfiles.rustdesk-login.plist
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/dev.dotfiles.rustdesk-login.plist
```

If the agent is already loaded, use `launchctl kickstart
"gui/$(id -u)/dev.dotfiles.rustdesk-login"` instead of bootstrapping it again.

Access before graphical login requires RustDesk's native system service. Install
it from RustDesk's service controls once, granting the requested administrator
authorization. Verify both jobs:

```bash
launchctl print system/com.carriez.RustDesk_service
launchctl print "gui/$(id -u)/com.carriez.RustDesk_server"
```

Screen Recording and Accessibility permissions must also be granted in macOS
System Settings for remote viewing and control. Chezmoi does not grant them.

## Omarchy

The existing `omarchy-rustdesk-client-setup` installs the native client and enables
`rustdesk.service` for boot. Chezmoi additionally manages the desktop tray's user
unit and its `graphical-session.target.wants` symlink. The graphical session starts
the tray automatically; terminal-only sessions do not launch it.

```bash
chezmoi apply --exclude=scripts \
  ~/.config/systemd/user/dev.dotfiles.rustdesk-tray.service \
  ~/.config/systemd/user/graphical-session.target.wants/dev.dotfiles.rustdesk-tray.service
systemctl --user daemon-reload
systemctl --user start dev.dotfiles.rustdesk-tray.service
sudo systemctl enable --now rustdesk.service
systemctl is-enabled rustdesk.service
systemctl is-active rustdesk.service
systemctl --user is-enabled dev.dotfiles.rustdesk-tray.service
systemctl --user is-active dev.dotfiles.rustdesk-tray.service
```

These tray targets are restricted to the `omarchy` machine profile. macOS startup
is excluded on non-macOS hosts; terminal-only and Fedora allowlists remain unchanged.

References: [RustDesk macOS setup](https://rustdesk.com/docs/en/client/mac/),
[native macOS service installation](https://github.com/rustdesk/rustdesk/blob/master/src/platform/privileges_scripts/install.scpt),
[native Linux service](https://github.com/rustdesk/rustdesk/blob/master/res/rustdesk.service).

## Tailscale

On macOS, the managed `dev.dotfiles.tailscale-connect` LaunchAgent invokes the
installed application's CLI with `up` at graphical login. `TAILSCALE_BE_CLI=1`
ensures launchd starts the CLI rather than the GUI. Existing tailnet identity,
exit-node, DNS, and route preferences are preserved. A failed invocation retries
with a 60-second throttle; a successful connection exits normally without polling
or overriding a later deliberate disconnect. Initial enrollment still requires
the user's authentication. This provides login startup, not access before login.

```bash
chezmoi apply --exclude=scripts ~/Library/LaunchAgents/dev.dotfiles.tailscale-connect.plist
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/dev.dotfiles.tailscale-connect.plist
/Applications/Tailscale.app/Contents/MacOS/Tailscale status
```

On Omarchy, the existing managed `omarchy-desk-setup tailscale` setup enables
`tailscaled.service` at boot and connects the device. For an already installed and
enrolled client, verify and restore the native daemon directly:

```bash
sudo systemctl enable --now tailscaled.service
sudo tailscale up
systemctl is-enabled tailscaled.service
systemctl is-active tailscaled.service
tailscale status
```

An online peer proves current connectivity, but remote access is still required
to verify its local daemon's boot enablement. An offline MacBook cannot be checked
or configured until it becomes reachable.

References: [Tailscale CLI](https://tailscale.com/docs/reference/tailscale-cli),
[unattended operation](https://tailscale.com/docs/how-to/run-unattended).
