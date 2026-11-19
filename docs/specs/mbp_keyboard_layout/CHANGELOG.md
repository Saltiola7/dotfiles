# Changelog: MBP Keyboard Layout

All notable changes to this bounded context.

## 2026-11-19 — MKL-002: quote key, fn passthrough, kitty font, OD-1 closed

Operator tailoring: the backslash key becomes the quote key (tap `"`,
hold `'` via `timeout` + Shift level); the displaced `\` parks at
AltGr+grave. `fn = fn` makes KEY_FN flow explicitly through keyd's
virtual keyboard so tiny-dfr can switch Touch Bar layers (the physical
node is hidden by the grab). ZSA parity is formally dropped — the
layout is tailored on its own merits from here (OD-1 closed). Scope
addition: kitty `font_size` becomes host-aware (9.0 on mbp-omarchy,
14.0 elsewhere) to clear the mbp's only chezmoi drift.

## 2026-11-19 — MKL-001: tis keymap + keyd layers + fn policy

Outcome: mbp built-in keyboard moved from `us,fi` group switching to a
single-group custom keymap (Colemak-DH ortho, direct ä/ö, AltGr bracket
cluster, duplicate-z fix) loaded via `kb_file`; keyd tap/hold layers
(HYPER/MEH/arrows/hold-/) scoped to the SPI keyboard; Touch Bar flipped
to media-default (`hid_apple fnmode`).

Round 3 (fn fix, same day): live capture on keyd's virtual keyboard
proved keyd re-emits `KEY_FN` (464) as its internal keycode 254 —
tiny-dfr matches 464, so Touch Bar layer switching died with the grab.
A udev hwdb remap on the keyd virtual keyboard
(`KEYBOARD_KEY_fe=fn`) restores fn at the libinput layer where
tiny-dfr reads; the script deploys it with `systemd-hwdb update` and
a device trigger. Raw evdev keeps showing 254 by design.

Round 2 (operator matrix revisions, same day): `fnmode=1` proved to be
F-keys-first, but the rendered strip turned out to be tiny-dfr's
`MediaLayerDefault` (packaged default `false` = F-keys, the "stuck"
symptom); the fix is `/etc/tiny-dfr/config.toml` with
`MediaLayerDefault = true` plus `fnmode=3` for the keycode side. Hold-/ moved to `?` (tap `/`);
the grave key became ZSA style (tap `|`, hold `~`); the ISO `<>` key
became the markdown key (tap `` ` ``, hold ``` ``` fence); `,`/`.` holds
produce `<`/`>`. The `[shift]` slash binding was dropped — Shift+`/` tap
already gives `?`. Tap-dance is out of scope: keyd has no double-tap
detection. ä/ö, AltGr brackets, HYPER/MEH chords and arrows passed the
matrix unchanged.

Validation: full pytest suite (891 passed) incl. render contracts for
every machine profile; live mbp preview — keymap loaded on
`apple-spi-keyboard` with empty `hyprctl configerrors`, external
keyboards untouched; `kb_file` forwarding confirmed through `hyprctl
eval`. Operator typing matrix and `keyd monitor` walk per README.

Exceptions: OD-1 (ZSA `~`/`|` parity) open pending Oryx export.

Commits: `1c55820` (kernel gate commit on
`dbsctr/mbp_keyboard_layout/MKL-001`).

Deployment: preview applied via targeted `chezmoi -S <branch-clone>
apply` on mbp-omarchy (user-level targets live); durable delivery =
draft PR into `main`, then terminal `chezmoi apply` on the mbp runs the
sudo-gated keyd/fnmode script. Rollback: `git switch main && chezmoi
apply` restores `us,fi` + `grp:ralt_switch`.

Final Push target: draft PR `dbsctr/mbp_keyboard_layout/MKL-001` →
`main` (Saltiola7/dotfiles), operator-approved to merge when CI is green.
Gate ledger closed at the reconciliation merge with `origin/main`; the
OD-1 ZSA-parity residue (LSGT AltGr slot) stays deferred in the backlog
pending the operator's Oryx export.
