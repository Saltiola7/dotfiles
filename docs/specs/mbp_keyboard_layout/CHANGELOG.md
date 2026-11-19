# Changelog: MBP Keyboard Layout

All notable changes to this bounded context.

## 2026-11-19 — MKL-001: tis keymap + keyd layers + fn policy

Outcome: mbp built-in keyboard moved from `us,fi` group switching to a
single-group custom keymap (Colemak-DH ortho, direct ä/ö, AltGr bracket
cluster, duplicate-z fix) loaded via `kb_file`; keyd tap/hold layers
(HYPER/MEH/arrows/hold-/) scoped to the SPI keyboard; Touch Bar flipped
to media-default (`hid_apple fnmode`).

Round 2 (operator matrix revisions, same day): `fnmode=1` proved to be
F-keys-first (the inverse of the goal), so the policy flips to
`fnmode=3` (media default, F1-F12 on fn). Hold-/ moved to `?` (tap `/`);
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
`main` (Saltiola7/dotfiles).
