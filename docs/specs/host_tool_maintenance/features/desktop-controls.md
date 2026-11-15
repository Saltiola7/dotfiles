# Desktop volume and menu-bar controls

## Intent and profile

An internal personal macOS desktop configuration, owned by the dotfiles maintainer.
Engineering Profile: ../PROFILE.md. The original slice was elevated risk because it
was deployed together with scoped local credential retirement. Modules: Security for
retirement; Bash/templates and existing Python/pytest fixture validation. No new
runtime dependencies, audio device drivers, product service or package release.

Completion route: the operator selected a lighter local workflow after live
validation disproved retiring the hover helper. The original DBSCTR cycle remains
incomplete, with its failed evidence preserved; this document does not certify it
as passed. No push or draft pull request is part of the lighter completion.

## Domain and behavior

SketchyBar owns the speaker item and popup; macOS owns current output, volume,
mute state and the native menu bar. AeroSpace reserves the bar's desktop space.
The existing `sketchybar-toggle` helper changes SketchyBar visibility on top-edge
hover. SketchyBar starts it only when missing; the window manager and coding
session do not independently own its startup.

- Given the bar is loaded, show the speaker icon without an always-visible
  percentage or slider. Clicking it opens/closes a popup with a draggable slider,
  percentage and explicit mute/unmute action. Leaving bar/popup closes it.
- Given a supported current audio output, slider release sets system output
  volume in 0–100. Mute remains an explicit independent action. Other volume
  changes refresh icon, slider and percentage. Scrolling preserves bounded volume
  adjustment; right-click retains access to native Sound settings.
- Given malformed slider/scroll input, do not pass it to AppleScript. Given an
  audio read/write failure or unchanged read-back after a requested change, show
  unavailable/device-controlled status rather than false success. A later refresh
  recovers normal display. No additional audio software is installed.
- Given auto-hide is enabled, the native bar can appear above SketchyBar on hover
  and receive clicks; SketchyBar hides at the top edge and returns when the
  pointer leaves the menu region. Keep desktop and fullscreen auto-hide enabled. Verify each
  attached display and fullscreen manually; do not claim that intermittent OS
  failures are solved solely because preference values are correct.

## Interfaces and affected scope

- `private_dot_config/sketchybar/items/executable_volume.sh`: native SketchyBar
  popup, slider and mute item; existing colors/icons/font.
- `private_dot_config/sketchybar/plugins/executable_volume.sh`: dispatch
  `mouse.clicked`, `mouse.scrolled`, `mouse.exited.global`, volume/wake refresh.
  Read back actual macOS state using existing `osascript`; validate numeric event
  input before constructing commands. UI status uses text as well as icon/color.
- `private_dot_config/sketchybar/executable_sketchybarrc`: native bar layering
  (`topmost=off`) so Apple owns hover overlay. The auth retirement slice also
  removes the AWS item include. Start the installed hover helper if it is missing,
  without duplicating a running helper; this shared file has one serial owner.
- `dot_aerospace.toml.tmpl` and
  `run_onchange_after_start-sketchybar-stack.sh.tmpl`: remove helper autostart
  interference by leaving helper startup to SketchyBar, preserving AeroSpace,
  SketchyBar and borders startup.
- A bounded macOS settings hook may persist
  `com.apple.controlcenter AutoHideMenuBarOption=2` and
  `AppleMenuBarVisibleInFullscreen=false`, and clears the stale legacy
  `_HIHideMenuBar` key it previously wrote. Do not continuously reset
  preferences, install a watchdog or automatically kill system UI processes.
- `tests/test_sketchybar_volume.py`: isolated command-stub behavior checks.
- Context README/BACKLOG/CHANGELOG and affected AWS documentation: completion
  evidence and links; material normative changes return to Discovery.

## Findings and limits

Active volume files match the managed source. Existing volume clicks mute rather
than open a slider. Live preference values already request native auto-hide.
The installed helper's published state machine restores SketchyBar on a click
below its trigger zone, including within the native menu region. Above-native
layering makes this a plausible local interference mechanism, not proof of every
reported random failure. Removing the helper failed live acceptance because the
bars no longer swapped. Restoring it with below-native layering restored swapping.
Initial native hiding still differed by application despite equal effective
preferences. The operator approved SystemUIServer and Dock restarts; SystemUIServer
alone did not fix it. A MenuBarAgent restart was denied by SIP and was not bypassed.
After the intervening session/server recovery, the operator confirmed expected
native auto-hide and volume behavior. The exact cause of the native recovery was
not isolated; do not present any one restart as a proven cure.
On 2026-11-15 the native bar was held hidden with no hover-reveal on macOS
27.0.1: this hook's legacy `_HIHideMenuBar=true` coexisted with
`AutoHideMenuBarOption=0`, and a stuck Control Center panel (window level
above the menu bar) additionally blocked right-side menu clicks. Clearing the
panel and persisting `AutoHideMenuBarOption=2` restored reveal and clicking.
The hover helper's `topmost=window` prerequisite warning remains intentionally
unmet: the bar must stay below the native menu bar (`topmost=off`).

## Validation, deployment and recovery

Use existing pytest with stubbed SketchyBar/osascript for popup toggle, mute,
slider, malformed inputs, bounds, read/write failure and recovery. Run Bash syntax
checks and chezmoi rendering/diff for touched targets; no repository-wide audit.
Deploy only reviewed targets from the task checkout, preserve the hover helper,
reload SketchyBar/AeroSpace as needed, and query live item/slider state. Preserve
actual audio level/mute across automated smoke tests. Human verification covers
popup traversal, current headphones, native hover/click, both displays and
fullscreen. Failure leaves the gate open rather than inventing visual success.

Rollback restores the prior nonsecret configs and helper launch behavior, then
reloads the affected user applications. No automatic reboot or system daemon
restart; one-off diagnostic restarts require separate operator approval.

## Gate Ledger

The original cycle required Domain, Behavior, Spec, Contract, Test-driven
implementation, Refactor, Review/Integrate, Deploy, Operate and Maintain/Retire.
Its Spec was reopened and failed deployment evidence remains recorded. Release
was not_applicable (unversioned host configuration). No Gate Exception was granted.
The operator explicitly selected lighter local completion rather than claiming
those original gates passed. Local tests, deployment and operator observations
are reported separately in CHANGELOG.md.

## Visual Evidence

State: required, transition table below. Boundary, interaction, data/trust,
schema, dependency/deployment and quantitative: not_applicable; the short ownership,
interface and deployment contracts above answer those questions without a diagram.

| State/event | Result |
| --- | --- |
| Closed / left-click speaker | Popup open, current system state displayed |
| Open / left-click speaker or pointer leaves bar and popup | Popup closed |
| Open / valid slider release or mute action | Write current output, read back, refresh |
| Any / read failure or rejected write | Explicit unavailable/device-controlled state |
| Error / successful subsequent refresh | Current system state restored |

Text Equivalent: clicking the speaker toggles the popup; leaving closes it.
Valid input writes and reads the current output; errors are visible and a later
successful refresh restores normal state. Source: this contract; owner: dotfiles
maintainer; update trigger: any event, state or failure-semantics change.
