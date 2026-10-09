-- Mac-primary desk, mirrored from this repository's AeroSpace configuration.
-- Semantic keys support both software and hardware Colemak.
-- Omarchy's app-aware Cmd/Super+C/V clipboard bindings remain enabled.
local function replace(chord, description, action)
  hl.unbind(chord)
  o.bind(chord, description, action)
end
-- Previously window cycling; AeroSpace uses workspace back-and-forth.
replace("ALT + TAB", "AeroSpace: previous workspace", hl.dsp.focus({ workspace = "previous" }))
replace("ALT + SHIFT + TAB", "AeroSpace: move workspace to next monitor", hl.dsp.workspace.move({ monitor = "+1" }))
for key, direction in pairs({ N = "l", E = "d", I = "u", O = "r" }) do
  replace("ALT + " .. key, "AeroSpace: focus " .. direction, hl.dsp.focus({ direction = direction }))
  replace("ALT + SHIFT + " .. key, "AeroSpace: move window " .. direction, hl.dsp.window.swap({ direction = direction }))
end
for workspace = 1, 7 do
  replace("CTRL + SHIFT + ALT + " .. workspace, "AeroSpace: workspace " .. workspace,
    hl.dsp.focus({ workspace = tostring(workspace) }))
  replace("SUPER + CTRL + SHIFT + ALT + " .. workspace, "AeroSpace: move window to workspace " .. workspace,
    hl.dsp.window.move({ workspace = tostring(workspace), follow = false }))
end
replace("ALT + MINUS", "AeroSpace: shrink window", hl.dsp.window.resize({ x = -50, y = 0, relative = true }))
replace("ALT + EQUAL", "AeroSpace: grow window", hl.dsp.window.resize({ x = 50, y = 0, relative = true }))
-- Previously the Omarchy root menu.
replace("SUPER + SPACE", "Application launcher", "omarchy-menu toggle apps")
-- The Finnish Mac/ZSA @ macro sends left Option+2 over Synergy.
-- Insert the character directly instead of forwarding an application shortcut.
replace("ALT + 2", "Insert @ (Finnish Mac keyboard)", "sleep 0.1; wtype -- @")
-- Also cover an already-running Waynergy client with the previous @ ID map.
replace("ALT + at", "Insert @ (Mac symbol event)", "sleep 0.1; wtype -- @")
-- Cmd+W is already close-window; Cmd+Q is an alias.
replace("SUPER + Q", "Close window", hl.dsp.window.close())
-- Cmd+T belongs to Kitty tabs; keep the desktop action on Ctrl+Cmd+T.
hl.unbind("SUPER + T")
replace("SUPER + CTRL + T", "Toggle window floating/tiling", hl.dsp.window.float({ action = "toggle" }))
