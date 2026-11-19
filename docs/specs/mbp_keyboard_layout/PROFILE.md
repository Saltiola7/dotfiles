# MBP Keyboard Layout Engineering Profile

| Concern | Default |
|---|---|
| Deliverable and owner | Owner-only personal input remapping for mbp-omarchy, shipped as chezmoi templates and run scripts; operator owned |
| Languages and modules | XKB keymap directives, Lua (Hyprland `input.lua.tmpl`), INI (keyd), Bash (`run_always` scripts), Python contract tests |
| Runtime and platform | mbp-omarchy only: Arch Linux ARM aarch64, Hyprland (Omarchy Lua bridge), keyd ≥ 2.6, xkeyboard-config, tiny-dfr, `xkbcli` |
| Interfaces | `input.lua.tmpl` machine_type branches; `/etc/keyd/mbp.conf`; keymap `~/.config/xkb/keymap/tis.xkb` loaded via `kb_file` (built-in devices + keyd virtual keyboard); `hid_apple` fnmode + tiny-dfr policy |
| Compatibility | Global Finnish base for external keyboards, the `omarchy-try` template branch, and every existing Hyprland MEH/HYPER chord remain unchanged; ZSA firmware untouched |
| Trust/data | Public configuration only; no credentials, secrets, or private endpoints in this context |
| Delivery | `chezmoi apply` on mbp-omarchy; sudo-gated `run_always` script for system files; no release artifact |
| Operations | keyd and tiny-dfr run as distro-packaged system services; the `keyd-fn-bridge` uinput shim is the one bespoke system service, deployed and enabled by the run script |
| Maintenance | Edit the include-based keymap source directly (no compiled artifact); ZSA-parity pass when Oryx exports arrive; retire by applying the rollback contract |
| Authorities | `pytest tests/`, chezmoi render diff (`omarchy-try` branch byte-identical), `hyprctl configerrors`, `sudo keyd monitor` live walk, Touch Bar visual check |

## Current-cycle overrides

- Affected scope: mbp built-in keyboards and Touch Bar policy only.
- Risk: `routine` — local, reversible configuration; no public, production,
  sensitive-data, security-boundary, money, or safety impact.
- Delivery intent: `draft_pr` (branch → draft PR into `main` → `chezmoi apply`
  on mbp-omarchy after merge).
- Gate overrides: Release/Operate/Retire `not_applicable` with reasons in the
  README Gate Ledger; everything else required.
