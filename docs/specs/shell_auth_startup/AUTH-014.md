# AUTH-014 Lima And Atuin Recovery

## Behavior

- Given a parent process with a scoped `XDG_DATA_HOME`, when a host or Lima shell
  starts Atuin, then it uses the existing native client store under
  `~/.local/share/atuin`.
- Given no XDG override, the explicit path remains byte-compatible with Atuin's
  native client location.

## Contract

- `ATUIN_DATA_DIR` is exported as `$HOME/.local/share/atuin` before the macOS and
  Lima profile branches diverge.
- Client databases, host identities, sessions, and encryption keys remain unique
  per machine; only encrypted records synchronize through the server.
- The scoped OpenCode XDG tree never becomes a second Atuin client store.
- The guarded Colima service supplies Homebrew's binary directory explicitly so
  launchd can resolve Colima's `limactl` dependency.
- The service starts only when `/Volumes/ext` is an active APFS mount containing
  the sentinel and every native state home; a stale directory tree fails closed.
- A Mac-mini-only onchange target reloads the LaunchAgent after its managed
  wrapper or plist changes.
- The runtime-state controller atomically manages both `idea.system.path` and
  `idea.log.path`; PyCharm keeps its existing external `system/log` directory
  without compatibility fallback warnings.

## Visual Evidence

| Concern | Classification |
|---|---|
| Boundary | not_applicable: client and server trust boundaries are unchanged. |
| Interaction | not_applicable: startup performs one environment assignment. |
| State | not_applicable: existing Atuin databases remain authoritative. |
| Data/trust | required: accepted risk `AUTH-014-AR1` places VM disks, client keys, and server authentication state on the unencrypted external APFS volume. |
| Schema | not_applicable: no schema changes. |
| Dependency/deployment | required: the guarded LaunchAgent owns restart-at-login for external Colima and Atuin. |
| Quantitative | not_applicable: no comparative decision uses metrics. |

## Accepted Risk

`AUTH-014-AR1`: the operator explicitly approved storing complete Lima and Colima
state on the existing unencrypted, `noowners` external APFS volume. This includes
guest credentials, Atuin keys and sessions, and the server account database.
Review when the volume is replaced, shared with another user, or before
2026-11-09. The operator owns the risk; cold backups and fail-closed mount checks
reduce loss and fallback risk but do not provide encryption at rest.
