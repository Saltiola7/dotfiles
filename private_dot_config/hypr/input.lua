-- Hardware-mapped ZSA and remote keyboards must not be remapped twice.
-- Apply software Colemak DH only to the laptop's built-in keyboard.
-- Use the unshifted bottom row (Z X C D V), matching the ZSA arrangement.
-- Match shortcuts by the symbol produced by each keyboard's own layout.
hl.config({ input = { resolve_binds_by_sym = true } })
hl.device({
  name = "at-translated-set-2-keyboard",
  kb_layout = "us",
  kb_variant = "colemak_dh_ortho",
})
