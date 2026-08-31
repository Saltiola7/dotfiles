# Fedora Workstation Personal Profile

The `fedora-workstation` machine type is a full personal Fedora ARM64 desktop,
not the terminal-only `lmsh` profile. It owns personal Bash/common startup,
Kitty, Starship, Atuin, Yazi, desktop/developer package declarations, 1Password,
Tailscale, native cache paths, and manual system updates. It never owns OpenCode,
Codex CLI, Herdr, DBSCTR, or their managed configuration.

## Behavior

- Given Fedora ARM64 and `machine_type=fedora-workstation`, chezmoi applies a
  deny-by-default workstation target set and no macOS application, LaunchAgent,
  Keychain, Homebrew, private key, or host-service target.
- Given the data-disk sentinel is healthy, documented native path controls place
  Downloads, DNF/npm/pre-commit/Playwright/uv caches, rootless Podman storage,
  Flatpak applications/runtimes, and JetBrains install/system state below the
  data mount.
- Given the data disk is unavailable or unsafe, stateful AI commands fail closed;
  ordinary shell startup remains usable and does not create matching internal
  fallback directories.
- Given Atuin is installed, its client uses the existing sync endpoint, account,
  and encryption key after explicit login while retaining a distinct local
  database and host identity.
- Given Tailscale is installed, tailnet and SSH enrollment require one explicit
  interactive action; no key, tag, peer name, or policy enters the source.
- Given 1Password ARM64 desktop and CLI are installed, the user signs in inside
  Fedora and enables SSH integration locally. Rendering and shell startup never
  authenticate automatically.
- Given `fedora-update`, one full DNF upgrade runs, no reboot occurs, and the
  result reports reboot and Parallels integration follow-up.
- Given `fedora-reset-cache GROUP`, only the exact rebuildable group is removed.
  Auth, sessions, history, downloads, container volumes, IDE local history, and
  unrelated state remain.
- Given both chezmoi sources are initialized, personal applies first and the
  managed-target intersection with the AI workstation profile is empty.

## Package Set

The first profile installs Kitty, Zen through its supported ARM64 Flatpak,
JetBrains Toolbox ARM64, 1Password ARM64 desktop plus CLI integration, Tailscale,
Git, GitHub CLI, chezmoi, uv, ripgrep, jq, rootless Podman, build tools, Atuin,
Starship, and the existing portable terminal tool set. Toolbox owns interactive
PyCharm selection and updates. GNOME ricing remains outside this feature.

## Storage

`/mnt/data` is the guest ext4 data mount. Native controls are preferred over
symlinks. OpenCode and Codex private state are configured by the AI source, not
this feature. The accepted plain-storage risk and retention behavior are owned by
the Parallels Fedora workstation context.

## Validation

Render exact Fedora and existing macOS/`lmsh` target inventories, prove no AI
target ownership, parse shell/TOML, test healthy and missing data roots, verify
rootless Podman SELinux labels, and perform live Atuin, 1Password, Tailscale SSH,
desktop application, update, and reboot integration smokes.
