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
