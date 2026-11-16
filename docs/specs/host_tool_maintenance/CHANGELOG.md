# Host maintenance changelog

## 2026-11-16 — mbp-omarchy synergy client and input-method hygiene

- Waynergy managed package now builds on aarch64 (the M1 host joins the
  mini's Synergy desktop as screen mbp-omarchy; server-side screen list
  stays app-owned in Synergy 3).
- fcitx5 fully retired on mbp-omarchy: uwsm env clears every IM_MODULE
  for future sessions, and a run_always script re-disables
  omarchy-fcitx5.service on each apply in case a preset update re-enables
  it (its Finnish QWERTY virtual keyboard rewrote local Colemak and
  remote-session typing).

## 2026-11-16 — mbp-omarchy daily-driver enablement

- Backup declared: `mbp-omarchy-borg-backup` script + systemd user
  timer moved into the repo, hostname-gated, prune scoped to the
  omarchy archives.
- M1 hardware declared: TTY-gated `run_onchange_after_mbp-asahi-hardware`
  applies the brightness udev grants, keeps the keyboard backlight off,
  and installs/enables tiny-dfr for the Touch Bar.
- Input finalized on main (fi base, DH Matrix internal, natural scroll)
  and deployed live to mbp-omarchy.

## 2026-11-16 — macbook native menu bar

- SketchyBar removed from the macbook thin client after repeated
  native-menu-bar conflicts: AeroSpace's after-startup-command no longer
  launches it, its formulas left the macbook Brewfile branch, the
  sketchybar config tree is ignore-gated off the host, and the stack hook
  restores Apple menu-bar defaults (bar always visible) while stopping any
  brew-services resurrect agent. mac-mini hosts keep the SketchyBar stack
  unchanged. AeroSpace outer.gaps.top is 5 on macbook (native bar visible)
  and 30 elsewhere.

## 2026-11-15 — macOS thin-client transition

- Retired roughly 45 GB of applications for the thin-client role with an
  explicit keep list (Slack, Telegram, WhatsApp, Zen, RustDesk, Mullvad
  VPN, all wallet apps, ChatGPT as fallback, Citrix, 1Password, kitty,
  Obsidian, Trader Workstation, utilities layer). Capture One archived to
  ext-2 for restore-on-demand; Steam saves and the Zotero library copied
  to ext-2 app-data; retired brew casks commented in the Brewfile with a
  dated marker instead of deleted declarations.
- Carbon Copy Cloner retired: `mbp-borg-backup` (LaunchAgent, daily 03:00,
  ts-mbp-gated) now owns the recurring macOS-side backup into the ext-2
  repository seeded by the pre-install baseline. Keepalive-hardened SSH
  settings prevent the silent hang observed in earlier runs.
- microSD card cleared for reuse: verified off-card copy (701/701 exact
  plus FFDB) recorded in the fuji-sd-500gb registry entry.
- Logged MBP-ARCHIVE-RECONCILE-001 and MBP-IBKR-LINUX-001 follow-ups in
  the backlog.

## 2026-11-15 — Omarchy MacBook Pro install prep and card validation

- Chose the official Omarchy for Apple Silicon installer for the 13" M1
  MacBook Pro over the legacy Asahi Alarm script route, and installed
  installer 2.3.16 on the host via `brew install omacom/mac/omarchy`.
  Recorded the phased runbook, the post-install Apple Silicon quirk
  checklist, and the open backup-shape decision in
  `features/omarchy-mbp-install.md`. Pre-flight observed: macOS 27.2.1,
  FileVault on, 176 GiB free.
- Validated the owner's 471 GB exFAT microSD (retired Fujifilm camera
  card) against the 8 TB backup disk before any reuse: only 73 of 701
  files matched by name and size; 551 files including every MOV are
  absent by original filename. Registered the card as `fuji-sd-500gb` in
  the homelab registry with a do-not-empty guard note, and recorded the
  8 TB's observed 136 GiB free near-full state on `mac-backup-disk`.
- Amended the runbook pre-flight after the owner retired Carbon Copy
  Cloner: the pre-install safety net is a one-time borg baseline of the
  macOS home to a homelab disk, consistent with the repo's borg/borgmatic
  backup engine decision.
- Recovered stranded local work into main: the volume-popup pytest
  (`tests/test_sketchybar_volume.py`) that belonged to the shipped
  desktop-controls slice, and the DBSCTR gate-plan artifact
  `DESKTOP-CONTROLS.plan.json`.

## 2026-11-15 — Menu-bar auto-hide key migration

- Root-caused a completely unresponsive native menu bar on macOS 27.0.1: the
  stack hook's legacy `NSGlobalDomain _HIHideMenuBar=true` split-brained with
  `com.apple.controlcenter AutoHideMenuBarOption=0`, holding the bar hidden
  with no hover-reveal, while a stuck Control Center panel at a window level
  above the menu bar blocked right-side clicks. SketchyBar itself renders
  below the menu bar (`topmost=off`, layer −20) and was never the blocker.
- The stack hook now persists `AutoHideMenuBarOption=2` (Always) and deletes
  the stale legacy key; `AppleMenuBarVisibleInFullscreen=false` is unchanged.
  Runtime recovery on the host: killed the stuck Control Center panel
  (auto-respawned clean), applied the key and restarted the Dock; ghost
  window gone and reveal restored on operator hover verification.
- Validation: rendered-template Bash syntax check and targeted chezmoi apply
  re-ran the hook; live values confirmed `AutoHideMenuBarOption=2` and the
  legacy key absent. Volume tests unaffected (no volume file touched).
  Spec `features/desktop-controls.md` settings-hook bullet and findings
  updated to match.

## 2026-10-30 — GRAPHIFY-HOST-SOURCE

- Retired the duplicate Graphify Brewfile declaration, old skill installer and
  stale installer comment. Added a non-reintroduction regression and pointers to
  the sole CLI/dependency/skill owner and update procedure in `dotfiles-ai`.
- Validation: failing-first ownership regression followed by passing ownership,
  terminal, uv/SDK selection, remote-profile and Fedora tests. Seven native
  profile inventories preserved all unrelated targets; only the old macOS
  installer disappeared. Ruby/Bash syntax and diff checks passed. Optional
  cross-source coverage not selected by the suite remains outside its claim.
- No live apply, package operation, uninstall, runtime/skill/graph deletion, DKS
  change or credential migration. Dependabot inputs were unavailable because
  alerts are disabled; this slice adds or upgrades no dependency. No exception
  requested or approved.
- Gate Commits `88cdbed` and `9e99b6f` retain contract and implementation history.
  The private Cycle Record owns failed/replacement evidence and final closure.
  Intended Final Push: `discovery/graphify-ownership`, draft PR into
  `Saltiola7/dotfiles:main`; merge and live activation require their own approvals.

## 2026-10-26 — RAINDROP-MCP-SINGLETON

- Added a macOS Raindrop launcher that admits one live connector per existing
  authentication cache. It resolves cached mcp-remote 0.15.2 offline without
  installation, then directly executes Node with the existing endpoint,
  HTTP-only transport and authentication timeout. No persistent npm or shell
  guardian is required; busy contenders exit before resolution.
- Preserved explicit cache selection, caller working directory and MCP stdio.
  The native descriptor lease remains on the Node PID and releases after EOF,
  SIGINT or SIGKILL without removing the lock inode or changing credentials.
- Validation: two intended interface tests failed before the launcher existed;
  all 20 focused tests then passed. Actual Node descriptor/inode/PID checks,
  contention, crash recovery, private resolution failures and stdio passed,
  together with native Bash syntax and diff checks. Gate commits: `ed43d4c`
  (initial contract) and `15b618f` (tests and launcher).
- Deployment: installed only the reviewed launcher and configured the native
  client with the existing authentication cache. Legacy proxy process trees were
  closed gracefully; targeted apply is idempotent. Authenticated MCP discovery
  returned 21 tools. A real contender was rejected in 56 ms; the owning Node
  retained its lease, then exited cleanly and allowed reacquisition.
- The existing application loaded the guarded connector. Competing cached
  contexts were rejected by the lease; no legacy npm parents remain.
  Release is not applicable; no package is published and no gate exception is
  requested. Intended delivery: feature-branch draft PR into main; actual
  deployment and Final Push outcomes belong to the private Cycle Record.

## 2026-10-26 — SKETCHYBAR-MEDIA-POLLING

- Replaced three sequential now-playing queries with one JSON query per refresh.
  A nonblocking native file lock skips overlapping refreshes and automatically
  releases ownership on process exit. Existing labels, icons and popup controls
  remain compatible; installed lockf and jq add no new runtime dependency.
- Validation: focused regression reproduced eight failures before implementation;
  21 media tests and Bash syntax passed. Native descriptor ownership, immediate
  contention failure and retained-file recovery were independently confirmed.
- Deployment: reconciled only the reviewed media plugin into the dirty canonical
  source, preserved source/target preimages and applied that single target through
  chezmoi. Repeat targeted diff is empty; no bar restart was required.
- Live verification: 32.4-second observation, including a ten-second drain of old
  executions, saw five batched queries and at most one concurrent metadata query.
  Independent review found no actionable issue. No gate exception requested.
- Gate commits: `37e5ee6` domain/behavior/contract, `4a6f49a` specification evidence,
  `ca3fe1e` test-driven fix and `ef6ed4c` documentation/refactor. Deployment closure
  commit and actual Final Push result are recorded in the private Cycle Record.
  Intended Final Push: `origin/fix/sketchybar-media-polling`, draft PR into `main`.


## 2026-10-25 — RUSTDESK-SYNERGY-001

- Added Mac-mini-only authenticated incoming RustDesk desktop detection and
  Synergy native Pause/Resume coordination. Durable restoration ownership
  preserves an initial manual pause, overlapping sessions, reconnects and helper
  restart; an unavailable detector does not become a false disconnect.
- Reused installed native app controls and existing Homebrew Python 3.12. Kept
  Synergy login, TLS pairing, HP Waynergy and narrow TLS-deadlock recovery intact.
  Adapter compatibility is explicit: RustDesk 1.5.0 and Synergy 3.8.4.
- Validation: 240 affected tests passed. Native pause/resume idempotency, durable
  recovery after an actual helper SIGKILL, deployed launchd replacement, and
  startup-order regression passed. A real incoming desktop reported count one,
  paused the core and retained its journal through another deployed helper crash.
  Operator confirmed working clicks; real disconnect restored sharing and cleared
  the journal. Targeted repeat apply had no drift; private preimages retained.
- Broader macOS run: 675 passed, one skipped, 12 failures in unchanged Linux
  desktop-startup tests requiring absent `/usr/bin/bash`. Those are outside this
  affected scope; Linux CI retains its full configured suite. No gate exception.
- Implementation commits: `1d7563f`, `5a6aaed`; earlier commits retain the domain,
  behavior, interface and contract transitions. Release not applicable. Intended
  Final Push: feature branch and draft PR into main; actual result is in Cycle Record.

## 2026-10-09 — Desktop controls and local client retirement

- Added an icon-only speaker control with click-open slider, percentage and mute;
  bounded scroll/slider input, system-state read-back and visible audio errors.
- Kept SketchyBar below Apple's menu bar and retained the existing hover helper.
  SketchyBar starts the helper only when missing; AeroSpace no longer starts it
  independently. Live reload retained exactly one helper and the volume popup.
- Initial helper retirement failed host acceptance. Native hiding also differed
  between apps despite equal preferences. Approved SystemUIServer/Dock recovery
  and an intervening session/server recovery preceded operator confirmation that
  volume and native auto-hide behaved as expected. Exact recovery cause remains
  unisolated; exhaustive fullscreen/multi-display coverage was not separately
  recorded. MenuBarAgent restart was SIP-blocked and was not bypassed.
- Retired local client service, SketchyBar integration, shell defaults, profile/session
  and two attributable caches. Preserved Backblaze credentials/profile byte/value
  equality, the shared CLI and one unattributable client-registration cache.
  Generic retired auth source is retained under `docs/_archive/aws-auth/`.
- Validation: 65 focused pytest checks passed, including the startup regression;
  affected Bash/template syntax and AeroSpace TOML passed. Live popup open/close
  and same-volume write/read-back preserved system volume and mute.
- Operator selected lighter local completion after failed deployment evidence.
  Original implementation commit: `d9dc5dc`; original cycle remains incomplete
  with Spec reopened and failed evidence preserved. No Gate Exception, Final Push
  or draft PR is claimed. Local corrections are committed separately.

## 2026-10-07 — SSD-HOST-RETIRED-SOURCES

- Removed obsolete Colima launcher, LaunchAgent, bootstrap hook and ignore entries.
  Retired five Colima/Docker formula declarations and Loop/Shortcat casks, matching
  the preserved primary maintenance intent. No uninstall or data purge performed.
- Replaced obsolete service-start expectations with a non-reintroduction regression.
  Affected terminal, AI ownership, uv and SDK tests passed; Brewfile syntax passed.
- Verified live service and targets remain absent; retained source preimages before
  scoped primary reconciliation. Both source inventories exclude the retired
  targets. Archives, VM state, preferences, rollback variables, optional SSH
  includes and unrelated dirty source changes remain preserved.
- Implementation Gate Commit: `73679e7`. No exceptions; package release not
  applicable. Intended Final Push: feature branch and draft PR into main; actual
  delivery result is retained in the Cycle Record.

## 2026-10-07 — SSD-HOST-UV-SHELL

- Shared mac-mini shell fragment selects already-installed mise uv/uvx in Bash
  and Zsh login modes. No startup install, config rewrite or broad shim activation.
  External mise selection is marker-gated; missing tools/lookups retain selection.
- Promoted the existing external MISE_DATA_DIR setting into tracked configuration;
  exactly matching stale state is unset when the marker is absent. Retained local
  binaries, project pins and unrelated primary changes.
- Validation: failing regression before implementation; 40 scoped tests passed,
  rendered Bash/Zsh syntax passed. All four live login modes select uv 0.12.23
  and uvx from the same installation with a minimal inherited PATH. Python, Node,
  Codex and SDK resolution match each mode's pre-deployment baseline. Repeated
  targeted apply has no drift. Source/target preimages retained privately.
- Implementation Gate Commit: `22fe571`. No exceptions; package release not
  applicable. Intended delivery: feature branch and draft PR into main; actual
  Final Push result is recorded by the Cycle Record.

## 2026-10-07 — SSD-HOST-SDK-BOOTSTRAP

- Added macOS ARM64 standalone SDK bootstrap after Homebrew's before-stage
  prerequisite installation. Verified baseline archive is used only when absent;
  healthy newer installations and extra components remain unchanged.
- Existing unhealthy paths, bad checksums, missing Python, installer failures and
  concurrent destination creation fail without overwriting user state. Installation
  uses isolated HOME/config, disables Python installation and shell-profile edits,
  and retains failed staging evidence. Other platforms remain unchanged.
- Validation: 33 affected pytest cases passed; shell syntax passed; real verified
  archive installation and repeated hook execution passed in an empty home. Live
  targeted chezmoi apply was a healthy-install no-op and repeated cleanly.
- Archived old Homebrew SDK and receipt, verified its six component IDs are covered
  by the standalone installation's nine, then used native non-zap uninstall with
  dependency autoremove disabled. Inactive old SDK directory and external backup
  remain retained. Four Bash/Zsh login modes select standalone gcloud, bq and gsutil.
- Implementation Gate Commit: `2b9e560`. No gate exceptions; package release not
  applicable. Intended Final Push: feature branch and draft PR into main; actual
  delivery result remains in the Cycle Record.

## 2026-10-07 — SSD-HOST-SDK-SHELL

- Restored standalone Google SDK precedence in Bash and Zsh, including
  noninteractive login shells and SDK paths inherited behind Homebrew.
- Guarded PATH updates on an executable SDK; missing/nonexecutable candidates
  preserve selection. Existing completion, AI guards and external-state settings
  remain intact. No SDK, credential or cloud resource was changed.
- Regression evidence: seven failing cases before implementation; affected SDK,
  terminal and AI ownership pytest suites pass afterward. Rendered Bash/Zsh syntax
  passes. Four host login modes select the standalone SDK; repeat targeted apply
  has no drift. Configuration preimages retained privately.
- Implementation Gate Commit: `00a6f0d`. No gate exceptions. Release not applicable.
  Intended Final Push: feature branch and draft PR into main; actual delivery
  result is retained in the Cycle Record.
