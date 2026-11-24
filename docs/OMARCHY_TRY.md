# Try Omarchy workstation profile

This profile adds personal configuration to the released Try Omarchy application.
It does not build or fork the VM runtime. The app owns firmware, bootloader,
kernel integration, graphics, display scaling, clipboard, gestures, host audio,
and shared-folder transport. Keep the existing Parallels VM and HP installation
unchanged while evaluating it.

## Source and installation layout

Use an isolated source checkout based on current committed personal dotfiles;
the existing working Mac checkout contains unrelated uncommitted changes. The
`omarchy-try` role is distinct from the HP `omarchy` role. Do not substitute the
HP role or the old Parallels branch's boot, kernel, device or package-hold files.

The VM directory belongs on `/Volumes/ext`, selected in Try Omarchy's launcher.
Clone/copy personal and AI source into the guest's own disk, for example
`~/Projects/dotfiles` and `~/Projects/dotfiles-ai`. Keep active databases, container
storage, Python environments and indexing workloads on the guest disk; use a
separate disposable shared folder for interoperability tests. Do not share host
SSH keys, provider state, VM bundles or the whole Mac home.

## Personal configuration

Copy `config.omarchy-try.example.toml` to
`~/.config/chezmoi/omarchy-try.toml`, replace `/home/you` and the public Git identity,
and set its permissions to `0600`. Review the target list before applying:

```sh
chezmoi --config ~/.config/chezmoi/omarchy-try.toml managed --include files,scripts,symlinks
chezmoi --config ~/.config/chezmoi/omarchy-try.toml diff
chezmoi --config ~/.config/chezmoi/omarchy-try.toml apply --exclude scripts
```

The initial files-only apply makes the essentials installer available without
starting privileged installation from a noninteractive remote session. Inspect
its plan, then install from the guest terminal after taking a recovery snapshot:

```sh
~/.local/bin/omarchy-apps --plan
~/.local/bin/omarchy-apps --install
~/.local/bin/omarchy-apps --check
chezmoi --config ~/.config/chezmoi/omarchy-try.toml apply
```

The apply hook runs the same missing-only installer when its source changes.
Signed repository packages are installed with `pacman -S --needed` from the guest's
existing sync databases: no refresh and no system upgrade, so no partial upgrade
either. Omarchy reserves upgrades for `omarchy update`, and its pacman guard rejects
a direct `-Syu`. Review the ordinary package-manager prompt. Factory Try Omarchy has
its own kernel/update policy; this installer imposes no historical Parallels holds.

The personal role owns only:

- `.bashrc`, preserving Omarchy's shell initialization and selecting AI-owned
  commands from `~/.local/bin` when installed;
- personal Kitty appearance, navigation and workspace helpers;
- `hypr/input.lua`, setting a Finnish base without software Colemak or device
  overrides, and `hypr/bindings.lua`, adding AeroSpace-style workspace navigation;
- Catppuccin theme selection and the native persistent stay-awake marker;
- the reviewed essentials installer, its two application recipes, and public
  RustDesk server routing.

It does not own `hyprland.lua`, monitor configuration, the Try integration package,
HP Waynergy/Synergy, laptop hardware, host credentials, server/backup jobs, or AI
commands. Every keyboard uses Finnish; the ZSA firmware supplies Colemak-DH.
`Cmd+Ctrl+Shift+Alt+1..7` sends a window without following it;
`Ctrl+Shift+Alt+1..7` switches workspaces. The same chords with `8` provide a normal
workspace for hidden apps. `Cmd+Space` opens the application launcher when the
host forwards the shortcut. The HP-only Option+2 text-injection workaround is not
loaded in this guest.

## Essentials and owners

Repository essentials are Python, curl, Git and Podman. Existing native providers
are retained. The reviewed application catalog is deliberately limited to:

- PyCharm 2026.2.3, using JetBrains' architecture-matched archive and retained
  SHA-256 pins from the previous qualified setup;
- RustDesk 1.5.3, using the retained reviewed community PKGBUILD and upstream
  artifact hashes. `makepkg` runs unprivileged; only dependency/package installation
  uses sudo. Its package hook does not automatically enable remote access.
- Espanso 2.4.1, only after `espanso_enabled = true` is added to the guest's
  chezmoi data: a reviewed copy of the AUR `espanso-wayland` recipe builds natively
  for ARM64 from a checksum-pinned source archive with unprivileged `makepkg`. Its
  hook grants `cap_dac_override+p` to the binary so the daemon reads input devices
  without root. Chezmoi then manages the Finnish `config/`, the graphical service
  and startup. Personal matches come from an enrolled private Git checkout; see
  Espanso configuration in the README.

No Zed, Docker, office/media suite, hardware packages or broad HP app catalog are
installed. These are reproducible retained versions, not a claim that each is
upstream's newest release. Update recipes only after reviewing the new native
artifact and checksum. The presence-based installer does not downgrade or replace
an existing executable.

Codex, OpenCode, Herdr, Herdr Desktop/Core, Worktrunk and uv belong to the separate
`dotfiles-ai` source. Use its native Linux workstation configuration, private guest
state root and ARM-capable installers. Do not copy credentials or session state
from the Mac or Parallels VM. Authenticate providers interactively in the guest.
The full AI apply must be checked for disjoint ownership before activation.

After installing RustDesk, explicitly configure its existing private server from
the guest terminal:

```sh
~/.local/bin/omarchy-rustdesk-client-setup
```

This enables the guest service and applies only public routing fields. It does not
set a permanent access password or authorize an incoming screen capture. Approve
Wayland screen sharing and enter any credentials directly in the application.
The routing file may need updating if the existing private server has moved.
Guest access to that tailnet server must be verified independently.

## Qualification and recovery

Record actual versions and verify text and PNG clipboard both ways, repeated file
read/write/hash round trips in a disposable share, RustDesk both as viewer and
controlled endpoint, and real coding sessions with Herdr, Neovim, PyCharm,
notebooks and native ARM Podman containers. Source tests and successful package
installation do not establish runtime usability.

Back up current personal target files and the private chezmoi configuration before
applying. Take a stopped-VM copy or app-supported recovery snapshot before kernel,
compositor or integration upgrades. After the update, test a fresh boot and the
required integrations. Keep the prior recovery point until qualification passes.
A VM snapshot does not roll back writes made to a shared host folder.

To undo personal settings, restore the saved target files and the prior source
revision, then reload the compositor. To restore ordinary idle behavior, remove
the managed stay-awake marker from source before using `omarchy-toggle-idle
allow-idle`; a subsequent apply otherwise restores the marker. Source rollback
alone does not uninstall packages or reverse a full system upgrade: use the guest
recovery snapshot for system rollback, and independent backups for shared files.

## Runtime qualification notes

The Try role also owns `hypr/xdph.conf`, selecting the installed native Hyprland share picker. The factory preview picker crashed during RustDesk screen selection; replacing it allowed the operator to see the remote desktop. Passwords are set only in the guest RustDesk UI and are never managed by chezmoi.

The current guest additionally needs a service-only libxdo compatibility mount to avoid the libxdo 4 null-atom crash. Its private library and root helper are retained in the external VM setup record under `/Volumes/ext/state/try-omarchy`; this compatibility repair is not yet automated by the profile. Installing the package alone must not be described as a fully qualified remote desktop. The ARM64 1.5.3 package was built from the reviewed recipe and its upstream digest verified; the x86 package digest is pinned from the official release but this setup did not test that architecture.

Host behavior is conditional: launching directly on the second monitor and leaving the VM there permits macOS/guest switching per operator. Moving a running fullscreen VM between monitors caused host display/input failure even with full capture disabled. Synergy was paused during these tests. Keep existing Parallels and HP installations preserved while evaluating.

## Guarded guest updates

Keep a verified stopped-VM copy on the Mac before an upgrade. Quit Omarchy cleanly, then run `/Volumes/ext/state/try-omarchy/backup-vm.command` on the Mac. It refuses a running or locked VM, makes an APFS clone of the disk and copies the EFI variables, compares the disk with its source, and records SHA-256 checksums. The clone shares a physical drive with the VM unless copied elsewhere; it is not protection against drive loss. Copy backups to independent storage as well. Start the guest with the reviewed stable launcher.

Run `try-omarchy-update` in a guest terminal rather than starting the update from the menu. It checks the current EFI image and the factory-preservation hook, saves a boot-partition archive and a root Snapper snapshot, and invokes the Omarchy updater with automatic reboot suppressed. The wrapper runs the EFI audit at Omarchy's final boot-verification step and refuses to report success if that check is missing or fails. If any reboot prompt appears, decline it until the wrapper completes. A passing audit checks the configured image checksum and default, embedded kernel against the installed kernel, and initramfs readability; it cannot prove that a future image will boot. Restart after a pass, then verify `uname -r`, desktop, clipboard, RustDesk and other required integrations.

The root-owned `/etc/pacman.d/hooks/00-try-omarchy-preserve-factory.hook` stops any transaction that upgrades `try-omarchy`, because the current upstream cleanup can delete the preserved factory entry and files. A blocked transaction applies no packages. Review the integration release and preservation strategy before disabling the hook or updating it; do not force a partial upgrade. The hook and its isolated package-manager test are in [Try Omarchy maintenance](try-omarchy-maintenance/).

If the update or EFI check fails, leave the guest running and do not reboot. Inspect its output and the saved EFI archive and root snapshot. A root snapshot does not include the FAT EFI partition. For full recovery, cleanly stop the VM, preserve its current disk and EFI variables, verify the chosen baseline's checksums, and restore the disk and matching `efi-vars.fd` together only after confirming the intended recovery point. The older `baseline-20261114-234540` was made before the current checksum repair and therefore contains the previously working direct-kernel default. Do not overwrite newer user data without preserving it first.

Exchange and four explicitly scoped project/worktree folders are shared in the qualified setup. The broader `/Volumes/ext` read/write export remains unqualified: path filters can be bypassed by hard-link aliases, and the installed macFUSE filesystem was unavailable. Do not export the unfiltered volume as a workaround. See [project-share scope and limitations](try-omarchy-maintenance/PROJECT-SHARES.md).
