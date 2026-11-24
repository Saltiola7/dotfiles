# Host maintenance backlog

- ESPANSO-HOST-001: deployed on the guest (package, config, service) ahead of
  delivery. Remaining: the operator's typed guest-only expansion, then adopt the Mac
  matches in private Git, enroll the guest and verify the shared match and offline
  behavior. Final Push tracked in Cycle Record.

- OMARCHY-SHELL-001: deployed and qualified on HP; guard the null-focus crash,
  select sparse capture and safely retain dead logs. Final Push tracked in Cycle Record.

- RUSTDESK-SYNERGY-001: deployed and live-qualified on Mac mini, including helper
  SIGKILL/restart during an incoming desktop; Final Push tracked in Cycle Record.

- SSD-HOST-SDK-SHELL: implemented and host-qualified; Final Push tracked in Cycle Record.
- SSD-HOST-SDK-BOOTSTRAP: implemented and host-qualified; Homebrew duplicate
  ownership retired without zap, installation backups retained.
- SSD-HOST-UV-SHELL: installed mise uv/uvx selected consistently and host-qualified.
- SSD-HOST-RETIRED-SOURCES: retired startup and package declarations reconciled;
  configured source inventory no longer includes Colima startup targets.
- Remaining Initiative lanes: classified upgrades and runtime migration.

- MBP-ARCHIVE-RECONCILE-001: reconcile MBP MGM and github archives landed at
  /Volumes/ext/git/Work/MGM/mbp-archive-2026-11-15 and
  /Volumes/ext/git/Personal/mbp-archive-2026-11-15; MGM/git/seo-data-science
  carries 32 unpushed commits (bundle preserved alongside) and several github
  repos hold uncommitted changes. Decide per-tree: merge, remote-push, or keep
  as cold archive.

- MBP-IBKR-LINUX-001: programmatic IBKR access from Omarchy. TWS/IB Gateway
  official Linux builds are x86_64-only; interim path is ib_async from Linux
  against Trader Workstation kept on the macOS thin client (allowlist Omarchy
  IP in TWS); alternative is IB Gateway in an x86_64 container under qemu.

- DOTFILES-AI-AARCH64-001: dotfiles-ai's herdr data declares linux x86_64 only
  (`linux_amd64_asset_url`) but upstream v0.9.5 ships `herdr-linux-aarch64`;
  the install script selects by fixed URL, so the omarchy profile would install
  a broken binary on ARM hosts. Add `linux_aarch64_asset_url` and make the
  installer arch-aware, then run `dotfiles-ai-omarchy-setup` on mbp-omarchy
  (state root /var/lib/dotfiles-ai/tis; provider logins interactive). mbp-omarchy
  runs herdr 0.9.5 aarch64 via a manual install + /usr/local/bin shim until then.

- SYNERGY-MBP-TRY-001: add mbp-omarchy (and/or the Try Omarchy VM) to the
  mini's Synergy 3 server. The GUI rejects every add path and regenerates
  its server config from an opaque database; client side (waynergy aarch64,
  TLS trust, service) is complete and waiting. Full state and avenues in
  features/synergy-mbp-handoff.md.
