# Keymap Reference

**Updated:** 2026-05-01

Navigation uses Colemak NEIO (left/down/up/right) on macbook, QWERTY on mac-mini.

---

## Kitty Terminal

| Shortcut | Action |
|---|---|
| `Ctrl+Space` | Toggle quick-access dropdown terminal |
| `kitty_mod+Enter` | New window (same cwd) |
| `kitty_mod+T` | New tab (same cwd) |
| `kitty_mod+X` | New tab running xonsh |
| `F16` | Save workspace |

---

## AeroSpace - Main Mode

| Shortcut | Action | Machine |
|---|---|---|
| `alt+N/E/I/O` | Focus left/down/up/right | both |
| `alt+shift+N/E/I/O` | Move window left/down/up/right | macbook |
| `ctrl+shift+alt+N/E/I/O` | Join with left/down/up/right | both |
| `ctrl+shift+alt+[0-9]` | Switch to workspace 0-9 | mac-mini |
| `shift+ctrl+alt+[1-5]` | Switch to workspace 1-5 | macbook |
| `shift+ctrl+alt+cmd+[0-9]` | Move window to workspace 0-9 | mac-mini |
| `shift+ctrl+alt+cmd+[1-5]` | Move window to workspace 1-5 | macbook |
| `alt+Tab` | Workspace back-and-forth | both |
| `alt+shift+Tab` | Move workspace to next monitor | both |
| `ctrl+shift+alt+.` | Toggle tiles h/v | mac-mini |
| `ctrl+shift+alt+,` | Toggle accordion h/v | both |
| `shift+ctrl+alt+/` | Toggle tiles h/v | macbook |
| `alt+-` | Resize smart -50 | macbook |
| `alt+=` | Resize smart +50 | macbook |
| `alt+shift+R` | Flatten workspace tree (reset) | both |
| `alt+shift+;` | Enter service mode | both |

## AeroSpace - Service Mode

| Shortcut | Action |
|---|---|
| `Esc` | Reload config + return to main |
| `R` | Flatten workspace tree + return |
| `F` | Toggle floating/tiling + return |
| `Backspace` | Close all windows but current + return |
| `Up` / `Down` | Volume up / down |
| `shift+Down` | Mute + return to main |
| `alt+shift+N/E/I/O` | Join with direction + return (macbook) |

---

## SketchyBar Click Actions

| Element | Left Click | Right Click | Scroll |
|---|---|---|---|
| Apple logo | Popup: About, Settings, Force Quit, Lock, Sleep, Restart | - | - |
| Workspace [0-10] | Switch to workspace | - | - |
| Front app | Activate app | - | - |
| Media (Brain.fm) | Popup: Play/Pause, Next Track, Open Brain.fm | Quick play/pause | - |
| Clock | Popup: Full date, Open Calendar | - | - |
| Brew updates | Open kitty dropdown: `brew update && brew upgrade` | - | - |
| Docker | Popup: List running containers | - | - |
| Volume | Toggle mute | Open Sound Settings | Adjust volume |
| WiFi/Network | Open Network Settings | - | - |
| Disk | Open Disk Utility | - | - |
| CPU | Open Activity Monitor | - | - |
| Memory | Open Activity Monitor | - | - |
