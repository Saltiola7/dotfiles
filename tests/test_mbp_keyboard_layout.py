"""MKL-001: mbp built-in keyboard — custom XKB keymap, keyd layers, fn policy.

Contract tests against docs/specs/mbp_keyboard_layout/README.md: direct ä/ö,
AltGr punctuation cluster, duplicate-z fix, keyd tap/hold layers scoped to the
built-in keyboard, Touch Bar fn policy, and zero drift on other machines.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
KEYMAP_REL = "private_dot_config/xkb/keymap/tis.xkb"
SCRIPT_REL = "run_always_mbp-keyboard-layers.sh.tmpl"
INPUT_REL = "private_dot_config/hypr/input.lua.tmpl"

CHEZMOI = {"os": "linux", "arch": "arm64", "homeDir": "/home/test"}
MBP = {"machine_type": "omarchy", "chezmoi": {**CHEZMOI, "hostname": "mbp-omarchy-tis"}}
DESK = {"machine_type": "omarchy", "chezmoi": {**CHEZMOI, "hostname": "desk-tis"}}
TRY = {"machine_type": "omarchy-try", "chezmoi": {**CHEZMOI, "hostname": "try-tis"}}


def chezmoi(*args, data=None, text=None):
    import json
    return subprocess.run(
        ["chezmoi", "-S", str(ROOT), "--config", "/dev/null", "--config-format", "toml",
         "--override-data", json.dumps(data or MBP), *args], input=text,
        capture_output=True, text=True, check=True,
    ).stdout


def render(path, data=None):
    return chezmoi("execute-template", data=data, text=(ROOT / path).read_text())


def keyd_conf():
    script = render(SCRIPT_REL)
    block = re.search(r"<< 'KEYD'\n(.*?)\nKEYD\n", script, re.S)
    assert block, "keyd heredoc missing from run script"
    return block.group(1)


# --- Template contract ------------------------------------------------------


def test_mbp_devices_load_custom_keymap_and_drop_group_switching():
    lua = render(INPUT_REL, MBP)
    assert lua.count('kb_file = "/home/test/.config/xkb/keymap/tis.xkb"') == 3
    for name in ("at-translated-set-2-keyboard", "apple-spi-keyboard",
                 "keyd virtual keyboard"):
        assert f'name = "{name}"' in lua
    # Single-group layout: no Finnish group switch, no shared us,fi pair.
    for gone in ("grp:ralt_switch", "us,fi", "colemak_dh_ortho"):
        assert gone not in lua, gone
    # Chord binds must still resolve through the global config.
    assert "resolve_binds_by_sym = true" in lua


def test_other_machines_keep_today_s_layout():
    desk = render(INPUT_REL, DESK)
    assert "kb_file" not in desk
    assert 'kb_layout = "us,fi"' in desk
    assert 'kb_options = "grp:ralt_switch"' in desk
    assert 'kb_variant = "colemak_dh_ortho,' in desk
    # Non-mbp machines keep today's template untouched (both legacy entries).
    guest = render(INPUT_REL, TRY)
    assert "kb_file" not in guest
    assert 'kb_layout = "fi"' in guest


# --- Keymap contract --------------------------------------------------------


def test_keymap_inherits_colemak_dh_ortho_and_binds_altgr():
    keymap = (ROOT / KEYMAP_REL).read_text()
    assert 'include "pc+us(colemak_dh_ortho)+inet(evdev)+level3(ralt_switch)"' in keymap
    overrides = {
        "AD11": ["adiaeresis", "Adiaeresis", "bracketleft"],
        "AC11": ["odiaeresis", "Odiaeresis", "apostrophe"],
        "BKSL": ["backslash", "quotedbl", "bar"],
        "TLDE": ["bar", "asciitilde", "grave"],
        "LSGT": ["grave", "less"],
        "AE07": ["7", "ampersand", "braceleft"],
        "AE08": ["8", "asterisk", "bracketleft"],
        "AE09": ["9", "parenleft", "bracketright"],
        "AE10": ["0", "parenright", "braceright"],
    }
    for code, symbols in overrides.items():
        block = re.search(rf"key <{code}> \{{([^}}]*)\}}", keymap)
        assert block, f"<{code}> override missing"
        for symbol in symbols:
            assert re.search(rf"\b{symbol}\b", block.group(1)), (code, symbol)
    # Invariants: one z source only (LSGT must not repeat it), no å anywhere.
    lsgt = re.search(r"key <LSGT> \{([^}]*)\}", keymap).group(1)
    assert not re.search(r"\bz\b", lsgt)
    assert "aring" not in keymap


# --- keyd contract ----------------------------------------------------------


def test_keyd_layers_match_spec_table():
    conf = keyd_conf()
    assert re.search(r"\[ids\]\n05ac:0341:89b7fedc\n", conf)  # keyboard node uid only
    assert "capslock = layer(hyper)" in conf
    assert "space = overloadt(meh, space, 200)" in conf
    assert "rightmeta = layer(arrows)" in conf
    # Tap/hold symbol keys: hold emits shift+key resolved through the keymap.
    assert "slash = timeout(slash, 200, S-slash)" in conf        # / tap, ? hold
    assert "grave = timeout(grave, 200, S-grave)" in conf        # | tap, ~ hold
    assert "102nd = timeout(102nd, 200, macro(102nd 102nd 102nd))" in conf  # ` tap, ``` hold
    assert "comma = timeout(comma, 200, S-comma)" in conf        # , tap, < hold
    assert "dot = timeout(dot, 200, S-dot)" in conf              # . tap, > hold
    assert "[shift]" not in conf  # Shift+/ tap already gives ? via the keymap
    assert "[hyper:C-M-A-S]" in conf  # Ctrl+Super+Alt+Shift
    assert "[meh:C-A-S]" in conf      # Ctrl+Alt+Shift
    arrows = re.search(r"\[arrows\]\n((?:[^\[]\n?)*)(?:\n|$)", conf).group(1)
    for binding in ("j = left", "k = down", "l = up", "; = right"):
        assert binding in arrows
    # External keyboards (ZSA over USB) never match these ids.
    assert len(re.findall(r"^[0-9a-f]{4}:", conf, re.M)) == 1


def test_run_script_installs_keyd_and_persists_fn_policy():
    script = render(SCRIPT_REL)
    assert script.startswith("#!/bin/bash\n")
    subprocess.run(["bash", "-n"], input=script, text=True, check=True)
    assert "pacman -S --needed --noconfirm keyd" in script
    assert "/etc/keyd/mbp.conf" in script
    assert "systemctl enable --now keyd" in script
    assert "options hid_apple fnmode=3" in script
    # tiny-dfr owns the rendered strip; MediaLayerDefault=true = media keys
    # by default, F1-F12 while fn is held (fnmode only picks keycodes).
    assert 'MediaLayerDefault = true' in script
    assert 'systemctl restart tiny-dfr' in script
    assert "/sys/module/hid_apple/parameters/fnmode" in script


def test_run_script_noops_off_mbp():
    for data in (DESK, TRY):
        script = render(SCRIPT_REL, data)
        assert script.strip().splitlines()[-1] == "exit 0"
        assert "pacman" not in script
        assert "/etc/keyd" not in script
        assert "fnmode" not in script


# --- chezmoi managed-set contract -------------------------------------------


def test_artifacts_scoped_to_mbp_in_managed_set():
    mbp = set(chezmoi("managed", "--include", "files,scripts,symlinks").splitlines())
    assert ".config/xkb/keymap/tis.xkb" in mbp
    assert "always_mbp-keyboard-layers.sh" in mbp
    for data in (DESK, TRY):
        other = set(chezmoi("managed", "--include", "files,scripts,symlinks", data=data).splitlines())
        assert ".config/xkb/keymap/tis.xkb" not in other
        assert "always_mbp-keyboard-layers.sh" not in other
        assert ".config/hypr/input.lua" in other
