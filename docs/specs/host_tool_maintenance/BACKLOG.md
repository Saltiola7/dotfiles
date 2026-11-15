# Host maintenance backlog

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
