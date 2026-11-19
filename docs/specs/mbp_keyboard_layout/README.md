# MBP Built-in Keyboard Layout

**Status:** Implemented (pending live deploy)
**Created:** 2026-11-18
**Last updated:** 2026-11-19

## Engineering Profile

Stable defaults live in [PROFILE.md](PROFILE.md). Current-cycle overrides: risk
`routine`, delivery intent `draft_pr` (feature branch + draft PR into `main`;
durable delivery is `chezmoi apply` on mbp-omarchy after merge), affected
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
| `private_dot_config/hypr/input.lua.tmpl` | mbp branch: built-in devices and keyd's virtual keyboard load the custom keymap via `kb_file` |
| `private_dot_config/xkb/keymap/tis.xkb` | Self-contained keymap source (`xkb_keymap` directives with `include` over system `us(colemak_dh_ortho)`); loaded directly by Hyprland, no compiled artifact or regen script |
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

**Scenario: the backslash key becomes the quote key**
- Given keyd layers are active
- When the backslash key is tapped, then `"`; held past 200 ms, `'`
- And `|` stays at AltGr on the same key

**Scenario: grave key — pipe on tap, tilde on hold**
- Given keyd layers are active
- When the grave key is tapped, then `|`
- When the grave key is held past 200 ms, then `~`
- And `|` also stays on AltGr+`\` in the keymap

### Feature: Markdown key on the ISO `<>` key

**Scenario: backtick tap, code fence hold, backslash on shift**
- Given keyd layers are active
- When the `<>` key (LSGT) is tapped, then `` ` ``
- When it is held past 200 ms, then ``` ``` ``` is typed for a code fence
- When Shift+`<>` is tapped, then `\` (a plain shift level — AltGr+grave
  woke Atuin in terminals via its escape sequence, so backslash avoids
  AltGr entirely)
- And the letter `z` is untouched (one physical z key only)

### Feature: Displaced angle brackets on comma and dot

**Scenario: comma and dot hold**
- Given keyd layers are active
- When `,` is tapped, then `,`; held, `<`
- When `.` is tapped, then `.`; held, `>`

**Scenario: question mark from holding slash**
- When `/` is tapped, then `/`
- When `/` is held past 200 ms, then `?` (Shift+`/` tap also gives `?`)

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
| `\` (BKSL) | `"` | `'` | `\|` |
| `` ` `` (TLDE) | `\|` | `~` | reserved |
| LSGT (`<>` key) | `` ` `` | `\` | reserved (hold: ``` ``` ``` via keyd) |
| `7`/`8`/`9`/`0` | unchanged | unchanged | `{` `[` `]` `}` |
| all other keys | inherit `us(colemak_dh_ortho)` | | |

- **Invariant:** letter map equals `colemak_dh_ortho` everywhere except LSGT;
  ZXCV positions are preserved.
- **Invariant:** no keycode produces `z` other than the z key.

### keyd `/etc/keyd/mbp.conf`

| Binding | Action |
|---|---|
| `[ids]` | `05ac:0341:89b7fedc` — the built-in SPI keyboard node only (keyd ids are prefix matches with no glob syntax; the uid suffix excludes the same-id SPI trackpad) |
| `capslock` | `layer(hyper)`; `[hyper:C-M-A-S]` |
| `space` | `overloadt(meh, space, 200)`; `[meh:C-A-S]` |
| `rightmeta` | `layer(arrows)`; arrows layer maps `j k l ;` → left/down/up/right |
| `slash` | `timeout(slash, 200, S-slash)`: tap `/`, hold `?` |
| `grave` | `timeout(grave, 200, S-grave)`: tap `\|`, hold `~` |
| `backslash` | `timeout(backslash, 200, S-backslash)`: tap `"`, hold `'` |
| `fn` | `fn = fn`: explicit KEY_FN passthrough so tiny-dfr keeps receiving it through the virtual keyboard |
| `102nd` (LSGT) | `timeout(102nd, 200, macro(102nd 102nd 102nd))`: tap `` ` ``, hold types ``` ``` ``` |
| `comma` / `dot` | `timeout(..., 200, S-...)`: tap `,`/`.`, hold `<`/`>` |

keyd re-emits all built-in keyboard events through its own `keyd virtual
keyboard` uinput device, so Hyprland's custom keymap must also bind that
device (see the template contract below).

### Template contract

- **Pre:** `input.lua.tmpl` `omarchy-try` branch and the global Finnish base
  are byte-identical before and after this work; non-mbp Omarchy machines keep
  today's `us,fi` device entries.
- **Post:** the mbp branch references the custom keymap via `kb_file` for
  exactly three device entries — `apple-spi-keyboard`,
  `at-translated-set-2-keyboard`, and `keyd virtual keyboard`; `run_always`
  scripts are idempotent and no-op on other machines.

### Rollback

Removing the keyd conf, keymap reference, and fn policy restores today's
`us,fi` + `grp:ralt_switch` behavior; no data or firmware is touched.

## Gate Ledger

| Gate | Capability | Applicability | Result | Authority/evidence | Exception | Owner |
|---|---|---|---|---|---|---|
| Development Kernel | required | required | passed | pytest (890-891 passed across rounds) + render contracts; gate commits `1c55820`, `85e93c8`, `2c5c8ff`, `4413434` | — | operator |
| Review | required | required | passed | diff coherence across rounds + full-suite evidence at final head; operator matrix acceptance | — | operator |
| Integrate | required | required | passed | base reconciliation merge with `origin/main` (clean auto-merge, union validation green); PR 3-way merge into `main` | — | operator |
| Release | not_applicable | not_applicable | — | no versioned artifact; chezmoi apply delivers | — | — |
| Deploy | required | required | passed | live on mbp: keyd matched the SPI keyboard, tis keymap active on keyd virtual keyboard, `configerrors` clean, `fnmode=3`, tiny-dfr `MediaLayerDefault=true`; operator matrix (ä/ö, brackets, HYPER/MEH, arrows, ```` ``` ````, `?`, Touch Bar) | — | operator |
| Operate | not_applicable | not_applicable | — | keyd/tiny-dfr are distro-packaged services | — | — |
| Maintain | required | required | passed | edit keymap source directly (no compiled artifact); OD-1 closed as superseded — layout tailored on its own merits | — | operator |
| Retire | not_applicable | not_applicable | — | rollback contract above | — | — |

## Artifact Review

- README: created (this document).
- BACKLOG: created; indexed in `docs/BACKLOG.md`.
- CHANGELOG: created; completion entry required at cycle close.

## Verification

```bash
# Static (repo root)
uv run --group test pytest tests/            # full suite, incl. other machines
chezmoi apply --dry-run --source .           # mbp data renders; omarchy-try diff empty

# Live (mbp-omarchy, after apply)
sudo keyd monitor                # walk every tap/hold mapping incl. Shift+hold-/
hyprctl devices                 # built-ins + keyd virtual keyboard on the tis map
hyprctl configerrors            # clean
cat /sys/module/hid_apple/parameters/fnmode   # 3 (media first; 1 is F-keys first)
grep MediaLayerDefault /etc/tiny-dfr/config.toml   # true — tiny-dfr owns the strip
systemctl is-active keyd tiny-dfr
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
- keyd `[ids]` are literal prefix matches (`strstr(id, pattern) == id`), not
  globs: `05ac:0341*` matches nothing. Use the full `vendor:product:uid`
  (journal prints it); a bare `vendor:product` would also match the SPI
  trackpad, which keyd grabbing would break.
- keyd actions emit KEYCODES, not glyphs: bind to the key whose XKB level
  carries the wanted symbol (`S-grave` → `~` because TLDE shift is `~`;
  the `grave` keycode no longer types a backtick after the remap — that is
  why LSGT's fence macro fires `102nd` three times).
- keyd has no tap-dance/double-tap detection; hold timeouts and two-key
  chords are the only multi-press primitives.
- keyd's u8 keycode table cannot carry `KEY_FN` (464): the virtual keyboard
  re-emits fn as internal keycode 254 (live-captured), so tiny-dfr — which
  matches `KEY_FN` through libinput — never sees it. No udev-level bridge
  exists: keyd's virtual keyboard has no MSC capability, so libinput never
  applies `KEYBOARD_KEY_*` remaps (and the node carries no MODALIAS for
  hwdb). Fix: the `keyd-fn-bridge` daemon re-emits keycode 254 as real
  `KEY_FN` on a private uinput device; tiny-dfr reads it like any keyboard.
  Raw evdev still shows 254 by design; verification is the bar itself.
- Omarchy's Lua config tree parses at Hyprland start; `hyprctl reload`
  does not re-execute `input.lua`. Live preview without restarting the
  session: `hyprctl eval 'hl.device({...})'`; a fresh session picks the
  file up natively.
- `git hash-object` dereferences symlinks, so `dbsctrctl gate-commit`
  cannot carry symlink paths; base reconciliation therefore rides the
  PR 3-way merge (verified auto-mergeable) instead of a branch merge.

## Facts, Assumptions, Risks, Open Decisions

**Facts (verified 2026-11-18/19)**

- Current mbp template state: `us,fi` + `colemak_dh_ortho` + `grp:ralt_switch`.
- `colemak_dh` maps LSGT→z and the ortho override re-adds z on the z key
  (upstream comment: LSGT absent on ANSI boards) → duplicate on ISO.
- keyd 2.6.0-5 is in `extra` for aarch64; `xkbcli` present on the mbp.
- Touch Bar runs tiny-dfr 0.3.7 (active). Two independent layers, both
  live-verified: tiny-dfr's `MediaLayerDefault` decides the rendered strip
  (packaged default `false` = F-keys shown — the "stuck" symptom); fnmode
  only decides keycodes (`fnmode=1` is F-keys-first, `3` is media-first).
  Policy: `/etc/tiny-dfr/config.toml` with `MediaLayerDefault = true`
  (merged over the packaged template) plus `fnmode=3`, both persisted by
  the run script. tiny-dfr tracks fn through the DFR virtual input device,
  which keyd ignores, so fn-layer switching survives the keyboard grab.
- Built-in keyboard input ids: bus 001c, vendor 05ac, product 0341
  (`Apple SPI Keyboard`); no separate `at-translated` device exists on the mbp.
- Omarchy's Hyprland build forwards `kb_file` in `hl.device` (binary device
  field whitelist, alongside `keybinds`/`share_states` already used here).
- keyd re-emits events through its `keyd virtual keyboard` uinput device;
  `timeout(action1, T, action2)` is the hold-emits-keycode primitive (v2.6.0
  man page), and `[shift]` modifier-layer routing is supported.

**Assumptions**

- 200 ms tap/hold default is acceptable (tunable without spec change).
- ZSA Oryx exports (screenshots/share link) will arrive for OD-1; the firmware
  `.bin` in Downloads is compressed and not a readable layout source.

**Risks**

- Typing-roll misfires on space-hold (mitigated by timeout variant; tunable).
- Hold-to-emit on `/` can misfire on slow deliberate `/` presses (isolated
  hold past 200 ms emits `\`); tunable, and rolls are protected because an
  intervening key resolves the tap.
- keyd char macros assume a US symbol table; all keyd emissions use raw
  keycodes (`backslash`, `S-backslash`) so the custom XKB levels stay authoritative.

**Open decisions**

- **OD-1 (closed 2026-11-19, superseded)** ZSA parity is dropped as a goal;
  the layout is tailored on its own merits. Partial parity already applied
  (grave tap `|` / hold `~`, LSGT `` ` ``/``` fence, `,`/`.` holds for
  `<`/`>`) stays because it tested well; no Oryx export is awaited and the
  LSGT AltGr slot stays free for future tailoring.
- **OD-2 (resolved 2026-11-19)** Keymap delivery: `kb_file` via `hl.device` —
  the Omarchy Hyprland build forwards it (device field whitelist); fallback
  `~/.config/xkb` rules overlay not needed. Verified live at Deploy.
- **OD-3 (resolved 2026-11-19)** Shift+hold-/ emits `"` via
  `[shift] slash = timeout(slash, 200, S-backslash)`; `|` remains on
  AltGr+`` ` `` and AltGr+`\` in the keymap. Live `keyd monitor` walk at Deploy
  confirms timing feel.
