# Host maintenance changelog

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
