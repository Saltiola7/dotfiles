# RustDesk startup

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
