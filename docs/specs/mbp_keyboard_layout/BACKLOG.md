# Backlog: MBP Keyboard Layout

| # | Task | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Implement cycle: XKB `tis` keymap, keyd conf, template changes, Touch Bar policy, contract tests | high | done | MKL-001 kernel 2026-11-19; contract tests green |
| 2 | Verify Omarchy Lua bridge forwards `kb_file` (OD-2); else wire `~/.config/xkb` overlay fallback | high | done | Resolved: `kb_file` forwarded (device field whitelist); single include-based keymap file |
| 3 | ZSA parity pass from Moonlander Oryx screenshots (OD-1: `~`/`\|` placement, LSGT AltGr) | medium | closed | 2026-11-19: parity dropped as a goal; layout tailored on its own merits (MKL-002) |
| 4 | Live `keyd monitor` walk incl. Shift+hold-/ → `\|` (OD-3); tune 200 ms timeouts | high | pending | Deploy gate; operator runs `chezmoi -S /tmp/mkl-001 apply always_mbp-keyboard-layers.sh` from a terminal for the sudo-gated system layer |
