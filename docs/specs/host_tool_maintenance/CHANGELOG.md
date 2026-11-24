# Host maintenance changelog

## 2026-11-24 — ESPANSO-HOST-001

- Added opt-in Espanso machine configuration. `espanso_enabled` renders the reviewed
  `config/default.yml`, one graphical user service with its enablement, an always-run
  start script and a checksum-pinned native ARM64 source recipe for the Try Omarchy
  guest. Unenabled hosts keep their live state; `omarchy-espanso-setup` now only
  installs and verifies the HP package.
- Added `espanso-match-sync`. An enrolled host, declared by `espanso_private_checkout`
  and `espanso_private_origin`, fast-forwards its private checkout on a full apply and
  deploys top-level match YAML once, after origin, scope, ownership and syntax checks,
  with restricted preimages and rollback. It never pushes; targeted apply, diff, status
  and dry run never run it.
- Validation: 977 passed and 14 skipped under chezmoi 2.74.1 and 2.73.0, including an
  isolated real-apply rehearsal with faked system commands. The archive checksum
  passed `makepkg --verifysource`. An independent review's findings were closed with
  tests. No local lint or Semgrep run was available; Semgrep runs in CI.
- Gate exceptions: Deploy and Operate deferred by operator direction so the change
  merges before the guest install, which needs interactive sudo and a system-upgrade
  review. Maintain/Retire passed on the retirement and recovery tests. Deployment
  evidence is due in the Cycle Record right after the guest install.
- Implementation checkpoints: `0a2d8a5`, `5e634e6`, `f15a027`, `f21e686`, `ac80092`,
  `32d891c`, `a410f40`, `dc6db8d` and this entry.
  Intended Final Push: feature branch and draft PR into main; actual delivery is
  recorded in Cycle Record.

## 2026-11-14 — OMARCHY-SHELL-001

- Added an Omarchy Linux AMD64 user QML guard for the Qt focusless context-menu
  crash. Normal events and guard destruction are qualified against the actual
  Qt extension; packaged Qt and Quickshell remain distribution owned.
- Select native sparse capture for the packaged shell. Archive only exclusively
  locked dead instance logs, verify copies before reclaim, and retain at most
  eight archives, seven days and 64 MiB. Original crash reports and live logs
  remain preserved. Live warning streams have no absolute byte cap.
- Validation: 33 reliability tests passed on macOS and HP Linux; native baseline
  SIGSEGV became guarded survival, with forwarding and lifetime controls passing.
  Independent review verified archive directory replacement, publication failure,
  partial reclaim, FIFO refusal and ZIP64 handling. Broader macOS-compatible run:
  830 passed, one skipped; Linux-only desktop startup tests remain CI-owned.
- HP deployment verified the actual module mapping and activation marker in the
  new shell's own log, sparse argv/import path, healthy timer and clean repeat
  apply. Native serialization added only an empty tray default; all existing
  preferences survived. Reclaimed 6.4 MB of dead runtime logs. Selectively
  reconciled the configured HP source while preserving unrelated dirty files.
- Implementation checkpoints: `4ddc0da` and `307540e`. No gate exceptions;
  independent package release not applicable.
  Intended Final Push: feature branch and draft PR into main; actual delivery is
  recorded in Cycle Record. Worktrunk remains with its separate installer owner.

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
