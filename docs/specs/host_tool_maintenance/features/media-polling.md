# SketchyBar media polling

Owner: dotfiles maintainer. Method Revision: 3.29. Context: host tool maintenance.
Risk: routine. Delivery: scoped local chezmoi deployment and feature-branch draft PR.

## Domain and scope

SketchyBar schedules a media refresh every five seconds. The media plugin reads
now-playing metadata from the installed nowplaying-cli and publishes its label,
icon and visibility through the existing SketchyBar item. A refresh owns one
nonblocking, per-user native file lock until its process and inherited children
exit. Popup controls remain independent of refresh ownership.

Only the media plugin, focused regression tests and this context's documentation
change. Existing media item placement, refresh cadence, popup layout, play/pause,
next-track and Brain.fm controls retain their behavior. No new runtime dependency,
OpenCode session operation, package update or unrelated desktop change is included.

## Behavior

| Given | When | Required outcome |
|---|---|---|
| Available metadata | Refresh runs | One metadata query supplies title, artist and playback rate; existing label and play/pause icon appear |
| Missing or null title, failed command, malformed JSON, or missing dependency | Refresh runs | Media item is hidden; a later successful refresh restores it |
| Playing title without artist | Refresh runs | Label contains title only |
| Metadata containing shell syntax, spaces or quotes | Refresh runs | Metadata remains inert label text; nothing is evaluated |
| Refresh still active | Another refresh arrives | New refresh exits immediately without another metadata query or queued work |
| Prior owner has exited and lock file remains | Refresh runs | Native lock can be acquired and polling resumes |
| Refresh active | Pointer exits or right button is clicked | Popup closes or play/pause executes without waiting for polling |

## Interface and contract

The installed CLI supports `nowplaying-cli get --json title artist playbackRate`.
Read its JSON object using installed jq; never evaluate metadata as shell code.
Null or non-string title/artist are empty. Numeric or string playback rate 1
selects the existing playing icon; all other values select paused. A literal
`null` or `(null)` title/artist retains the previous empty-field compatibility.

Use installed macOS `lockf -s -t 0` against inherited descriptor 9. Keep the lock
file in the user's temporary directory, with UID in its name, and do not unlink
it during polling. Kernel ownership releases when all inheriting processes exit,
so an abandoned file never needs PID-based stale-lock removal. Failure to obtain
ownership is a successful skipped refresh, with no UI change or metadata query.

Mouse-exit and right-click handlers execute before dependency checks and lock
acquisition. Preserve the five-second scheduling interval and existing popup item
configuration. Avoid changing process titles, global environment or other scripts.

## Validation and deployment

Run focused pytest cases with isolated temporary state, stubbed metadata and bar
commands, and native locking on macOS. Portable CI fixtures provide equivalent
BSD file-lock semantics where the macOS utility is absent. Reproduce multiple
queries and overlapping refreshes as failing evidence before implementation.
Cover malformed/absent metadata, command failure, untrusted text, command controls,
concurrent refreshes and lock recovery. Run Bash syntax and scoped chezmoi diff.

Before targeted apply, preserve source/target preimages and check the source media
plugin and live target have not changed since inspection. Apply only the reviewed
media plugin; existing scheduled executions naturally consume the next version.
Observe several five-second intervals: at most one metadata process at a time,
one query per refresh, and no growing list of media shell processes. Repeat apply
must have no diff. Rollback restores only matching media preimages after checking
for newer edits; never apply the whole dirty source tree.

## Lifecycle

Domain, Behavior, Spec, Contract, Test-driven implementation, Refactor and
Review/Integrate are required. Deploy, Operate and Maintain/Retire are required
for managed host changes. Release is not applicable: no package is published.
Native macOS owns lockf; Homebrew continues to own nowplaying-cli and jq. A future
CLI schema or private-framework change must rerun focused tests and local smoke
checks. Private cycle evidence owns live gate state and delivery outcomes.

## Visual Evidence

State: required; the behavior table defines refresh ownership and recovery.
Boundary, interaction, data/trust, schema, dependency/deployment and quantitative:
not_applicable; this bounded local plugin preserves existing owners, runtime
connections and cadence, with no persistent metadata or transport changes.

**Text Equivalent:** each scheduled refresh either acquires the existing per-user
kernel lock and issues one metadata query, or immediately skips because a refresh
still owns it. Process exit releases ownership even when the file remains. Popup
controls do not take the polling lock. Owner: dotfiles maintainer. Update this
contract when metadata fields, failure visibility, refresh ownership or controls
change.
