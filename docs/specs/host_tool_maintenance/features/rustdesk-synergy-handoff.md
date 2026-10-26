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

## Contract and ordered recovery

1. Serialize helper instances with an OS lock. Read bounded, private configuration
   and journal files; malformed state blocks mutation and is reported.
2. Query authoritative session state with bounded exact reads and a deadline.
   Positive count acquires input immediately. Two consecutive valid zeros release
   it. An absent socket is unknown while a desktop-host process remains alive.
   If no RustDesk desktop-host process exists for five seconds, its sessions are
   necessarily gone; release without depending on a disconnect log.
3. Before the first Pause, atomically persist a journal only if sharing was enabled
   and its core running. A crash before mutation is recoverable because actual
   settings are reconciled on restart. Pause is idempotent; verify both disabled
   intent and stopped core before reporting suspension complete.
4. During positive/unknown ownership keep the journal. On last disconnect write
   `resume_pending` before Resume. Verify enabled intent and running core before
   deleting the journal. A crash at either side of a request preserves recovery.
   Failed verification keeps a visible pending state and retries with bounded I/O.
5. If both Synergy GUI and service disappear after being observed in this helper
   run, relinquish the journal and do not launch either app. Initial absence after
   restart/login keeps the journal until independent startup completes; it does
   not prove a user quit. A service-only crash with GUI present retains it. Initial
   manual pause/absence never creates a journal. An additional Pause click while
   already automatically paused has no distinct observable intent; operators must
   disable the coordinator after session completion to retain a new manual pause.

Compatibility failure never becomes a valid zero count or successful control.
HTTP uses direct loopback without environment proxies or redirects. Local peers,
paths and listener identity are checked; network endpoints are not configurable.
No credentials or RustDesk permission changes are required. Idle polling never
starts or pauses Synergy. Acquisition is bounded polling, not a synchronous hook
before RustDesk's first input; live acceptance must assess that short handoff delay.

Validation: meaningful pytest state/transport fixtures cover positive/zero/unknown
counts, overlapping sessions, reconnects, malformed frames, ownership, version
drift, request timeouts and crash boundaries. Render all changed templates for
Mac mini and exclusion profiles; validate shell/plist syntax. Native probes verify
real read-state, native Pause stops core, native Resume starts it, idempotency and
coordinator restart. Authenticated incoming session and remote-viewer crash require
actual separate-client evidence; fixtures alone cannot claim those passed.

Deployment: retain preimages, apply only new handoff targets from this checkout,
verify launchd health/status and an empty repeat diff. Existing Synergy login and
TLS-recovery configuration remain independent. Rollback waits until sessions end
and owned restoration completes, unloads the handoff job and restores only its
preimages. Never delete a restoration journal to force apparent completion.

Maintenance: requalify both adapters after RustDesk/Synergy upgrades. Expose
incompatibility in status and log. Owner: dotfiles maintainer. No package release
or automatic upstream app upgrade. Feature retirement uses the rollback sequence.

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
