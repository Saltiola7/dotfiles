import ctypes
import ctypes.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]


def test_remote_at_consumes_option_without_changing_letter_shortcuts():
    library = ctypes.util.find_library("xkbcommon")
    if not library:
        pytest.skip("libxkbcommon is unavailable")
    xkb = ctypes.CDLL(library)
    pointer, number = ctypes.c_void_p, ctypes.c_uint
    signatures = {
        "xkb_context_new": ([ctypes.c_int], pointer),
        "xkb_keymap_new_from_string": ([pointer, ctypes.c_char_p, ctypes.c_int, ctypes.c_int], pointer),
        "xkb_state_new": ([pointer], pointer),
        "xkb_keymap_key_by_name": ([pointer, ctypes.c_char_p], number),
        "xkb_keymap_mod_get_index": ([pointer, ctypes.c_char_p], number),
        "xkb_state_update_mask": ([pointer] + [number] * 6, number),
        "xkb_state_key_get_one_sym": ([pointer, number], number),
        "xkb_state_key_get_consumed_mods2": ([pointer, number, ctypes.c_int], number),
        "xkb_state_unref": ([pointer], None),
        "xkb_keymap_unref": ([pointer], None),
        "xkb_context_unref": ([pointer], None),
    }
    for name, (args, result) in signatures.items():
        function = getattr(xkb, name)
        function.argtypes, function.restype = args, result
    context = xkb.xkb_context_new(0)
    keymap = xkb.xkb_keymap_new_from_string(
        context, (ROOT / "private_dot_config/waynergy/xkb_keymap").read_bytes(), 1, 0,
    )
    assert keymap
    state = xkb.xkb_state_new(keymap)
    try:
        key = xkb.xkb_keymap_key_by_name(keymap, b"FK13")
        assert key == 191
        masks = [1 << xkb.xkb_keymap_mod_get_index(keymap, name)
                 for name in (b"Shift", b"Mod1", b"Mod5")]
        for subset in range(8):
            mask = sum(value for i, value in enumerate(masks) if subset & (1 << i))
            xkb.xkb_state_update_mask(state, mask, 0, 0, 0, 0, 0)
            assert xkb.xkb_state_key_get_one_sym(state, key) == ord("@")
            consumed = xkb.xkb_state_key_get_consumed_mods2(state, key, 0)
            assert consumed & mask == mask
        xkb.xkb_state_update_mask(state, masks[1], 0, 0, 0, 0, 0)
        letter = xkb.xkb_keymap_key_by_name(keymap, b"AC01")
        assert xkb.xkb_state_key_get_one_sym(state, letter) == ord("a")
        assert not xkb.xkb_state_key_get_consumed_mods2(state, letter, 0) & masks[1]
    finally:
        xkb.xkb_state_unref(state)
        xkb.xkb_keymap_unref(keymap)
        xkb.xkb_context_unref(context)
