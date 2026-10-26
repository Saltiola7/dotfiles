# Incoming RustDesk and Synergy input ownership

## Domain and scope

Owner: dotfiles maintainer. Target: the current-user macOS Mac mini desktop.
DBSCTR Method Revision: 3.29. Risk: elevated because incorrect ownership can
interrupt desktop input. Delivery: isolated feature branch, draft PR and explicitly
requested targeted Mac deployment. Existing dirty primary files remain untouched.

RustDesk owns authenticated incoming desktop sessions and their connection count.
Synergy owns keyboard/mouse sharing and its persistent enabled/paused setting.
The handoff coordinator owns only a temporary suspension that it records before
requesting it. It must never resume a prior manual pause or launch a previously
closed app. A desktop session includes view-only access because RustDesk's
authenticated desktop count does not expose keyboard permission separately.
File transfer, tunnels, terminal and camera sessions are outside this count.

Adjacent systems are the existing Synergy TLS-deadlock recovery job, Synergy's
native supervisor and current-user launchd. RustDesk transport, authentication,
remote input, TLS pairing, clipboard data and the HP Waynergy client are unchanged.

Cycle override to the Engineering Profile: a small Python 3.12+ standard-library
runtime helper may use the already-installed Homebrew Python, local Unix sockets,
loopback HTTP and private atomic state files. No new dependency or package install.
Existing pytest/chezmoi authorities cover the helper and managed host files.

## Behavior

| Given | When | Required outcome |
|---|---|---|
| Sharing is enabled and running | First authenticated incoming desktop session appears | Journal prior sharing state, request native Pause and verify core stops |
| Sharing is paused, stopped or service absent | A session starts | Preserve that state; do not acquire restoration ownership |
| Two incoming desktop sessions exist | One disconnects | Keep sharing suspended until both end |
| A session reconnects quickly | Zero count is transient | Do not resume between observations; require two consecutive valid zero counts |
| Coordinator owns a suspension | Last session disconnects | Request native Resume and verify enabled state and running core |
| Coordinator crashes before/after Pause or Resume | launchd restarts it | Reconcile durable journal and actual state; no lost restore or duplicate toggles |
| RustDesk crashes | No desktop-host process remains for a grace period | Restore owned suspension without relying on missing disconnect logs |
| IPC is malformed, stale or times out while RustDesk remains alive | Session state cannot be established | Keep owned suspension, report unknown and retry |
| Synergy service crashes while suspended | Its supervisor restarts it | Persistent Pause remains; restore ownership survives |
| User quits Synergy during suspension | GUI and service disappear | Relinquish restore ownership; do not launch Synergy |
| Pause/Resume times out after possibly applying | Next observation arrives | Reconcile observed state; never treat request success alone as completion |
| App version or response schema changes | Adapter cannot verify compatibility | Report incompatibility and do not issue mutations |
| Only outgoing RustDesk or file-transfer activity exists | Detector polls | Incoming desktop count stays zero; preserve sharing |

The table is the canonical state evidence: idle, acquiring, suspended, restoring,
unknown and relinquished are operational states, not independent input owners.

## Interfaces and decisions

`~/.local/bin/synergy-handoff` provides `run`, `once` and `status` commands.
`~/.config/synergy-handoff/config.json` selects enabled state, existing Python/app
paths and a 0.5-second polling interval. A current-user Aqua LaunchAgent runs the
helper with launchd restart supervision. A separate activation helper validates
managed files and loads this job without changing Synergy's own launch jobs.

Private state lives under `~/Library/Application Support/dotfiles/synergy-handoff/`
with mode 0700: an atomic restoration journal, current status, a process lock and
bounded event log. State contains counts and phases, never remote identities,
passwords, clipboard contents or IPC response dumps.

RustDesk 1.5.0: query the current-user `/tmp/RustDesk-UID/ipc` Unix socket with
BytesCodec-framed JSON `{"t":"VideoConnCount","c":null}`. Accept only a bounded
integer response with matching message type. This counts authenticated incoming
desktop sessions, including view-only. Verify socket ownership, permissions and
live peer executable. Never infer session state from logs, socket existence or
`HasNoActiveConns`, which includes other activity.

Synergy 3.8.4: use the same internal loopback service controls as its installed UI:
GET `/v1/settings`, POST `/v1/controls/pauseCore` and POST
`/v1/controls/resumeCore` on port 24803. Require the expected current-user native
service and listener before mutations; validate ready state, version and Boolean
`local_system.core_enabled`/`coreRunning`. This is a version-gated adapter to an
internal interface, not a claimed public API. Native Pause disables supervision
of the core and persists across service restart. Killing core alone is unsuitable.

Runtime interface: `SessionSample(count, host_alive)` feeds a `Coordinator.step`
method. `Synergy.snapshot/pause/resume/present` and atomic `StateStore` are
replaceable test boundaries. A successful HTTP response alone never completes a
transition. Python runtime is the already-installed Homebrew Python 3.12 path,
not the moving unversioned Python. Tests use the repository's Python 3.12+ pytest
authority without a new dependency or lockfile.

Implementation order: detector and adapter fixtures; durable state machine and
crash tests; managed configuration/startup; targeted rendering; native host probes;
authenticated incoming-session acceptance and recovery probes; coherent review.

## Visual Evidence

State: required; the transition table added with the behavior contract is canonical.
Interaction: required; ordered suspension/restoration steps in the contract are canonical.
Boundary and data/trust: not_applicable; owners and local-only boundaries above
fully describe this small coordinator. Schema: not_applicable; private recovery
state is implementation-owned and is not an external data model.
Dependency/deployment: not_applicable; existing app services plus one user job.
Quantitative: not_applicable; no measured comparison or capacity decision.

**Text Equivalent:** RustDesk reports incoming desktop ownership; the coordinator
suspends Synergy only while that ownership exists and restores only state it owns.
Canonical source: this specification. Owner: dotfiles maintainer. Update when
session semantics, state ownership, app interfaces or failure handling changes.
