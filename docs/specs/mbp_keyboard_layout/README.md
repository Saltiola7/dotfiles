# MBP Built-in Keyboard Layout

**Status:** Draft
**Created:** 2026-11-18
**Last updated:** 2026-11-18

## Engineering Profile

Stable defaults live in [PROFILE.md](PROFILE.md). Current-cycle overrides:
risk `routine`, delivery intent `local` (chezmoi apply on mbp-omarchy), affected
scope limited to the mbp built-in keyboards and Touch Bar policy.

## Overview

One software keyboard stack for the mbp-omarchy built-in keyboard: Colemak-DH
via XKB with Finnish ä/ö typed directly, displaced punctuation relocated to an
AltGr cluster, tap/hold layers (HYPER, MEH, arrows, backslash) via keyd, and a
Touch Bar default of media controls with F1–F12 on fn. Everything ships through
this chezmoi repository; no firmware or other machine changes.

Problem being solved:

- ä/ö today require holding Right-Alt to flip into a second Finnish XKB group
  (`grp:ralt_switch`), which also burns Right-Alt as a group switch.
- The `colemak_dh_ortho` variant maps both LSGT (`<>` key) and the z key to `z`
  on this ISO keyboard — a literal duplicate z.
- The AltGr level of the Finnish group carries never-used symbols
  (`¡ºª¢€ħðþ…`) while `[ ] { } '` need new homes after ä/ö take their keys.
- Hyper/Meh chords in `bindings.lua` exist but have no comfortable physical
  source; the Touch Bar shows the opposite of the wanted default layer.

## File Map

| Path | Purpose |
|------|---------|
| `private_dot_config/hypr/input.lua.tmpl` | mbp branch: built-in devices move from `us,fi` group switching to the custom keymap (`kb_file` or `~/.config/xkb` overlay, see OD-2) |
| `private_dot_config/xkb/tis.xkb` | Compiled custom keymap loaded by Hyprland (committed; regenerated from source) |
| `private_dot_config/xkb/src/tis.keymap` | Keymap source (`xkb_keymap` directives over `us(colemak_dh_ortho)`) |
| `run_always_mbp-keyboard-layers.sh.tmpl` | Installs keyd, writes `/etc/keyd/mbp.conf`, persists Touch Bar fn policy; gated like `run_always_mbp-asahi-hardware.sh.tmpl` |
| `tests/test_mbp_keyboard_layout.py` | Render and content contract tests (pytest, same authority as `test_omarchy_try_profile.py`) |

## Architecture

### Visual Evidence

| Concern | Decision |
|---|---|
| Boundary | `required: Context/container flowchart` — ownership of the three remapping layers decides every mapping |
| Interaction | `not_applicable: prose Given/When/Then scenarios below` |
| State | `not_applicable: stateless remapping; tap/hold resolution is a single timeout decision` |
| Data/trust | `not_applicable: no data crosses an ownership boundary; all artifacts are local config` |
| Schema | `not_applicable: no persistent entities` |
| Dependency/deployment | `not_applicable: delivery is one chezmoi apply; the boundary chart covers the only topology` |
| Quantitative | `not_applicable: no decision depends on measured data` |

```mermaid
flowchart LR
    accTitle: mbp-omarchy built-in keyboard remapping pipeline
    accDescr: Physical built-in keyboard events pass through keyd tap/hold
    layers, then Hyprland applies the custom XKB keymap before applications
    receive symbols. External keyboards skip keyd and keep the Finnish base
    layout because the ZSA firmware owns their Colemak-DH.
    HW[Built-in keyboard<br/>apple-spi-keyboard] --> KEYD
    KEYD[keyd tap/hold layers<br/>caps=HYPER · space=MEH ·<br/>right-Cmd=arrows · hold-/=\\] --> HYP[Hyprland input]
    HYP --> XKB[custom keymap tis<br/>colemak_dh_ortho + ä/ö + AltGr cluster]
    XKB --> APPS[applications]
    HYP --> BINDS[window chords<br/>MEH/HYPER + number reuse]
    EXT[External keyboards<br/>ZSA firmware Colemak-DH] --> FI[global kb_layout fi]
    FI --> HYP
```

**Text Equivalent:** Built-in keyboard events (device `apple-spi-keyboard`)
flow through keyd, which owns tap/hold resolution and modifier layers, then
into Hyprland, which applies the custom single-group XKB keymap (base
`us(colemak_dh_ortho)`, Finnish keys and AltGr cluster added, LSGT duplicate
fixed) before delivering symbols to applications. Hyprland keybinds consume
MEH/HYPER chords produced by keyd unchanged. External keyboards bypass keyd
(device-scoped) and keep the untouched global Finnish layout, since the ZSA
firmware already owns their Colemak-DH.

## Domain

### Bounded Context

Personal Linux input remapping for one laptop. Adjacent: `omarchy_try`
input template branch in the same file (must stay byte-identical), the macOS
AeroSpace keymap reference ([`docs/keymap.md`](../../keymap.md)), and the ZSA
Oryx firmware layout (external authority, see OD-1).

### Ubiquitous Language

| Term | Definition |
|------|-----------|
| built-in keyboards | The `apple-spi-keyboard` device (and `at-translated-set-2-keyboard` fallback) named in `input.lua.tmpl` |
| HYPER | Ctrl+Alt+Shift+Super chord; physical source: Caps Lock held |
| MEH | Ctrl+Alt+Shift chord; physical source: space held |
| arrows layer | keyd layer active while right Cmd is held |
| AltGr cluster | Level-3 bindings of the custom keymap, home for displaced punctuation |
| LSGT | ISO `<>` key left of left Shift |
| ZSA parity | Final pass aligning symbol placement with the Moonlander Oryx layout |

## Behavior Scenarios

### Feature: Finnish letters typed directly

**Scenario: ä and ö without group switching**
- Given the mbp built-in keyboard is active with the custom keymap
- When `[` is tapped, then `ä` is produced; with Shift, `Ä`
- When `'` is tapped, then `ö` is produced; with Shift, `Ö`
- When Right-Alt is held, it selects AltGr symbols, not a Finnish group

**Scenario: Swedish å is out of scope**
- Given any input
- Then no key or layer produces `å`; the operator never uses it

### Feature: Displaced punctuation on AltGr

**Scenario: cluster lookup**
- Given AltGr is held
- When `7 8 9 0` are tapped, then `{ [ ] }` are produced
- When `[` is tapped, then `[`; when `'` is tapped, then `'`
- And the AltGr number row never yields the legacy `¡ºª¢€ħðþ…` set

### Feature: Quote and pipe relocation

**Scenario: double quote moves to backslash key**
- Given the custom keymap is active
- When `\` is tapped, then `\`; with Shift, `"`
- When `` ` `` is tapped, then `` ` ``; with Shift, `~`

**Scenario: pipe from tap/hold slash**
- Given keyd layers are active
- When `/` is tapped, then `/`
- When `/` is held, then `\` is produced
- When Shift+`/` is held, then `|` is produced (see OD-3)
- When AltGr+`` ` `` is tapped, then `|` (ZSA-style fallback always present)

### Feature: Modifier layers

**Scenario: Caps Lock is HYPER**
- Given Caps Lock is held
- Then all keys emit Ctrl+Alt+Shift+Super chords, driving the existing
  `SUPER+CTRL+SHIFT+ALT+<n>` move-window binds with zero bind edits

**Scenario: space hold is MEH**
- Given space is tapped and released quickly, then a space is emitted
- When space is held ≥ 200 ms, then keys emit Ctrl+Alt+Shift chords, driving
  the existing `CTRL+SHIFT+ALT+<n>` workspace-switch binds

**Scenario: right Cmd is the arrow layer**
- Given right Cmd is held
- When the keys at Colemak `n e i o` positions (raw keycodes `j k l ;`) are
  tapped, then ← ↓ ↑ → are produced in any focused application
- And left Cmd and Caps Lock remain the window Super keys

### Feature: Duplicate z removed

**Scenario: LSGT no longer z**
- Given the custom keymap is active
- When LSGT is tapped, then `<`; with Shift, `>`
- And exactly one physical key produces `z`

### Feature: Touch Bar default layer

**Scenario: media by default, F-keys on fn**
- Given the Touch Bar policy is applied
- Then the bar shows device/media controls by default
- When fn is held, the bar shows F1–F12

## Contracts & Invariants

### Custom keymap `tis` (XKB)

| Key (XKB code) | Level 1 | Level 2 (Shift) | Level 3 (AltGr) |
|---|---|---|---|
| `[` (AD11) | ä | Ä | `[` |
| `'` (AC11) | ö | Ö | `'` |
| `\` (BKSL) | `\` | `"` | `\|` |
| `` ` `` (TLDE) | `` ` `` | `~` | `\|` |
| LSGT | `<` | `>` | reserved (OD-1) |
| `7`/`8`/`9`/`0` | unchanged | unchanged | `{` `[` `]` `}` |
| all other keys | inherit `us(colemak_dh_ortho)` | | |

- **Invariant:** letter map equals `colemak_dh_ortho` everywhere except LSGT;
  ZXCV positions are preserved.
- **Invariant:** no keycode produces `z` other than the z key.

### keyd `/etc/keyd/mbp.conf`

| Binding | Action |
|---|---|
| `capslock` | `layer(hyper)`; `[hyper:C-M-A-S]` |
| `space` | `overloadt(meh, space, 200)`; `[meh:C-A-S]` |
| `rightmeta` | `layer(arrows)`; arrows layer maps `j k l ;` → left/down/up/right |
| `slash` | tap `/`; hold → backslash (see OD-3 for Shift variant) |
| `[ids]` | built-in keyboards only; external keyboards never match |

### Template contract

- **Pre:** `input.lua.tmpl` `omarchy-try` branch and the global Finnish base
  are byte-identical before and after this work.
- **Post:** the mbp branch references the custom keymap for exactly the two
  built-in device entries; `run_always` scripts are idempotent and no-op on
  other machines.

### Rollback

Removing the keyd conf, keymap reference, and fn policy restores today's
`us,fi` + `grp:ralt_switch` behavior; no data or firmware is touched.

## Gate Ledger

| Gate | Capability | Applicability | Result | Authority/evidence | Exception | Owner |
|---|---|---|---|---|---|---|
| Development Kernel | required | required | pending | pytest + render diff + live smoke | — | operator |
| Review | required | required | pending | PR review | — | operator |
| Integrate | required | required | pending | merge to `main` | — | operator |
| Release | not_applicable | not_applicable | — | no versioned artifact; chezmoi apply delivers | — | — |
| Deploy | required | required | pending | `chezmoi apply` on mbp-omarchy + live verification | — | operator |
| Operate | not_applicable | not_applicable | — | keyd/tiny-dfr are distro-packaged services | — | — |
| Maintain | required | required | pending | keymap regen script + OD-1 parity pass | — | operator |
| Retire | not_applicable | not_applicable | — | rollback contract above | — | — |

## Artifact Review

- README: created (this document).
- BACKLOG: created; indexed in `docs/BACKLOG.md`.
- CHANGELOG: created; completion entry required at cycle close.

## Verification

```bash
# Static (repo root)
pytest tests/ -k mbp_keyboard_layout
chezmoi apply --dry-run --source . # mbp data renders; omarchy-try diff empty

# Live (mbp-omarchy, after apply)
sudo keyd monitor            # walk every tap/hold mapping incl. Shift+hold-/
hyprctl devices              # built-ins on the custom keymap
hyprctl configerrors         # clean
xkbcli compile-keymap        # regenerates committed tis.xkb byte-identically
cat /sys/module/hid_apple/parameters/fnmode   # 1
```

Manual matrix: ä Ä ö Ö on `[`/`'`; `{ [ ] }` and `'` on AltGr; `\` `" `` ` `` `~`
`|` per the table; tap `/` vs hold `/` vs Shift+hold `/`; Caps+2 and
space-hold+2 move/switch workspace via existing binds; right-Cmd+`neio` arrows
in a terminal and a GUI editor; Touch Bar default vs fn-held layers; ZSA on the
mbp still types its firmware layout.

## Gotchas

- keyd resolves tap/hold below XKB: bind by raw keycode (`j k l ;`), not by
  Colemak glyph; the ZSA (firmware layout) equivalent would be `n e i o`.
- `overloadt` (timeout-resolved) is required for space — plain `overload` fires
  the layer the moment a rolled key press lands while space is down.
- Right Cmd is consumed by the arrows layer and no longer acts as Super;
  left Cmd and Caps Lock remain Super/HYPER sources.
- keyd runs as a system daemon: its conf is deployed via the sudo-gated
  `run_always` script pattern, not plain chezmoi files.

## Facts, Assumptions, Risks, Open Decisions

**Facts (verified 2026-11-18)**

- Current mbp template state: `us,fi` + `colemak_dh_ortho` + `grp:ralt_switch`.
- `colemak_dh` maps LSGT→z and the ortho override re-adds z on the z key
  (upstream comment: LSGT absent on ANSI boards) → duplicate on ISO.
- keyd 2.6.0-5 is in `extra` for aarch64; `xkbcli` present on the mbp.
- Touch Bar runs tiny-dfr 0.3.7 (active, stock config); `hid_apple fnmode=3`.

**Assumptions**

- 200 ms tap/hold default is acceptable (tunable without spec change).
- ZSA Oryx exports (screenshots/share link) will arrive for OD-1; the firmware
  `.bin` in Downloads is compressed and not a readable layout source.

**Risks**

- Typing-roll misfires on space-hold (mitigated by timeout variant; tunable).
- Omarchy's Lua bridge may not forward `kb_file` (OD-2 fallback exists).
- keyd hold-self-emission semantics for hold-/ need live confirmation (OD-3
  fallback exists).

**Open decisions**

- **OD-1** Final `~`/`|` placement and LSGT AltGr slot, from Moonlander Oryx
  screenshots (ZSA parity pass).
- **OD-2** Keymap delivery: `kb_file` via `hl.device` if the Omarchy Lua bridge
  forwards it; else `~/.config/xkb` rules overlay maintained by a run script.
- **OD-3** Shift+hold-/ → `|`: verify keyd `[shift]` modifier-layer routing;
  fallback is Shift+hold-/ → `"` with `|` on AltGr+`` ` `` and AltGr+`\`.
