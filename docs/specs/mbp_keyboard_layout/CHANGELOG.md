# Changelog: MBP Keyboard Layout

All notable changes to this bounded context.

## Unreleased — MKL-002: keep the pointer still while typing on the MBP

The existing keyboard installer marks `keyd virtual keyboard` internal for
libinput. It adopts the manual fix or appends its one section, preserving
other rules on every apply. A conflicting section is reported and left intact.
The [feature contract](README.md#trackpad-protection-while-typing) covers
fresh installs, verification and rollback. All 29 MBP keyboard/daily-driver
tests passed. The installer also adopted a copy of the live file without a
write. Two guest tests (Espanso package rehearsal and the HP keymap fixture)
failed identically on the pre-change tree, `b686869`. Intended delivery:
draft PR into `main`, then terminal apply and a fresh-session typing check.
Deployment is pending; no gate exception.

## 2026-11-19 — MKL-001: tis keymap + keyd layers + fn policy

Outcome: mbp built-in keyboard moved from `us,fi` group switching to a
single-group custom keymap (Colemak-DH ortho, direct ä/ö, AltGr bracket
cluster, duplicate-z fix) loaded via `kb_file`; keyd tap/hold layers
(HYPER/MEH/arrows/hold-/) scoped to the SPI keyboard; Touch Bar flipped
to media-default (`hid_apple fnmode`).

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
