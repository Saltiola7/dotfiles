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

## Visual Evidence

| Concern | Classification |
|---|---|
| Boundary | not_applicable: client and server trust boundaries are unchanged. |
| Interaction | not_applicable: startup performs one environment assignment. |
| State | not_applicable: existing Atuin databases remain authoritative. |
| Data/trust | not_applicable: no client state is copied across machines. |
| Schema | not_applicable: no schema changes. |
| Dependency/deployment | not_applicable: the existing three-client topology is unchanged. |
| Quantitative | not_applicable: no comparative decision uses metrics. |
