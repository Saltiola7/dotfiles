# MBP Keyboard Layout Engineering Profile

| Concern | Default |
|---|---|
| Deliverable and owner | Owner-only personal input remapping for mbp-omarchy, shipped as chezmoi templates and run scripts; operator owned |
| Languages and modules | XKB keymap directives, Lua (Hyprland `input.lua.tmpl`), INI (keyd), Bash (`run_always` scripts), Python contract tests |
| Runtime and platform | mbp-omarchy only: Arch Linux ARM aarch64, Hyprland (Omarchy Lua bridge), libinput, keyd ≥ 2.6, xkeyboard-config, tiny-dfr, `xkbcli` |
| Interfaces | `input.lua.tmpl` machine_type branches; `/etc/keyd/mbp.conf`; keymap `~/.config/xkb/keymap/tis.xkb` loaded via `kb_file`; the keyboard's single section in the shared `/etc/libinput/local-overrides.quirks`; `hid_apple` fnmode + tiny-dfr policy |
| Compatibility | Global Finnish base for external keyboards, the `omarchy-try` template branch, and every existing Hyprland MEH/HYPER chord remain unchanged; ZSA firmware untouched |
| Trust/data | Public configuration only; no credentials, secrets, or private endpoints in this context |
| Delivery | `chezmoi apply` on mbp-omarchy; sudo-gated `run_always` script for system files; no release artifact |
| Operations | keyd and tiny-dfr run as distro-packaged system services; no bespoke service ownership |
| Maintenance | Edit the include-based keymap source directly (no compiled artifact); ZSA-parity pass when Oryx exports arrive; retire by applying the rollback contract |
| Authorities | `pytest tests/`, chezmoi render diff (`omarchy-try` branch byte-identical), `hyprctl configerrors`, `sudo keyd monitor` live walk, Touch Bar visual check, fresh-session typing and trackpad check |

## Current-cycle overrides

- MKL-002 scope: classification of the existing keyd virtual keyboard for
  built-in trackpad suppression. Preserve other sections in libinput's local
  overrides file and the existing pointer settings on every host.
- Risk: `routine` — local, reversible configuration; no public, production,
  sensitive-data, security-boundary, money, or safety impact.
- Delivery intent: `draft_pr` (branch → draft PR into `main` → `chezmoi apply`
  on mbp-omarchy after merge).
- Gates: Release and Operate `not_applicable`; kernel, Review/Integrate, Deploy
  and Maintain/Retire required. See the [MKL-002 ledger](README.md#gate-ledger).
