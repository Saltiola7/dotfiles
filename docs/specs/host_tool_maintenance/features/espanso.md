# Espanso machine configuration

Extension to the [host maintenance profile](../PROFILE.md): explicitly include the ARM64 Wayland guest, macOS Mac mini, ARM64 MBP Omarchy and x86-64 HP Omarchy. The [initiative](../../../initiatives/espanso-distribution/README.md) owns ordering and gates.

Public chezmoi owns reviewed `config/` settings beneath the platform Espanso config root, install declarations and login startup. Private Git owns only `match/`. Public Git and chezmoi ignore rules must protect match trees on both platforms while allowing only intended machine settings. Never feed generated guest defaults back into private Git. Replace the legacy helper's combined `add` behavior before enrolling an existing installation.

Use a checksum-pinned native Wayland source package for the ARM64 guest; the HP helper's AMD64 Debian payload cannot serve it. Build unprivileged and verify packaged input permissions rather than running the daemon as root. Use one graphical user service on Linux. Preserve the guest's Finnish layout, the MBP's custom keymap and the HP's working settings; preserve the Mac app and startup during adoption.

## Apply contract and acceptance

| Given | When | Expected |
|---|---|---|
| No explicit local enrollment | Public apply | Public configuration works without contacting private Git. |
| Enrolled host with clean tracked checkout | Normal full apply | Validate the configured origin and disjoint leaf ownership, fast-forward only, validate incoming match scope, then apply matches once. No auto-push. |
| Targeted apply, diff or dry run | Preview or single-file operation | No private network or synchronization side effects. Integration must not recurse or double-run the Mac's existing apply workflow. |
| Offline, unknown origin, conflicting edits, divergent history, overlapping ownership or invalid YAML | Sync requested | Report incomplete sync without values; preserve local work and last working matches. No force, reset or automatic merge. |
| Fresh VM with both host and guest expanders available | Type a guest-only test trigger directly in the VM window | One guest expansion. Also verify one shared match, login startup, unchanged repeat apply and offline behavior. Remote-control keyboard paths are outside this acceptance gate. |

Use synthetic fixtures for profile rendering, ignored/private paths and sync failure tests; extend `tests/test_omarchy_try_profile.py` and run the configured pytest suite. Compare rendered leaf owners before and after update. Preview on each host and retain restricted preimages. Roll back only owned changes after checking for newer edits; disabling enrollment stops sync without deleting matches.

## Visual Evidence

The behavior table is the interaction/state authority. **Text Equivalent:** only an enrolled full apply crosses into the private sync step; unsafe inputs stop replacement. Ownership and deployment are mapped in the initiative. No new data schema or quantitative decision. Owner: host maintainer; update when enrollment, failure or acceptance behavior changes.
