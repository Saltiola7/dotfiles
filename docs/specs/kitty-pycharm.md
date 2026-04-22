# Kitty-PyCharm Workspace Integration Specification

**Status:** Experimental (v1, initial implementation)
**Created:** 2026-04-20

## Overview

A system that integrates Kitty terminal workspaces with PyCharm via a single hotkey. Each project gets a dedicated Kitty OS window with tabs for servers, tools, and an opencode AI assistant. The hotkey either focuses an existing workspace or creates one from scratch, with opencode session resumption so conversations persist across workspace restarts.

The core design principle: Kitty is the terminal platform (rendering, window management, remote control), not a multiplexer. There is no detach/reattach -- Kitty stays open. Persistence comes from periodic snapshots that capture evolved layout state plus opencode session bindings.

## File Map

### Kitty Configuration

| Path | Purpose | Status |
|------|---------|--------|
| `~/.config/kitty/kitty.conf` | Main config: remote control, session keybindings, tab bar filter (30 lines) | Stable |
| `~/.config/kitty/kitty.conf.bak` | Backup of original config | Reference |
| `~/.config/kitty/mocha.conf` | Catppuccin Mocha color scheme (included from kitty.conf) | Stable |

### Session Files

| Path | Purpose | Status |
|------|---------|--------|
| `~/.config/kitty/sessions/seo-data-science.conf` | SEO workspace base session definition | Stable |
| `~/.config/kitty/sessions/tsc.conf` | TSC workspace base session definition | Stable |
| `~/.config/kitty/sessions/dotfiles.conf` | Dotfiles workspace base session definition | Stable |
| `~/.config/kitty/sessions/{workspace}.snapshot.conf` | Auto-generated snapshot of evolved workspace state | Runtime |

### Scripts

| Path | Purpose | Status |
|------|---------|--------|
| `~/.local/bin/kitty-workspace` | Workspace launcher with `--validate` and debug logging | Experimental |
| `~/.local/bin/opencode-kitty` | OpenCode session binding with stale-purge, `--validate`, and debug logging | Experimental |
| `~/.config/kitty/save-workspace.py` | F16 handler: snapshot workspace state per project | Experimental |
| `~/.config/kitty/load-snapshot.py` | Snapshot parser for extra-tab restoration | Experimental |

### Chezmoi Infrastructure

| Path (chezmoi source) | Purpose |
|----------------------|---------|
| `run_once_create-kitty-socket-dir.sh` | Creates `~/.local/share/kitty/` on first `chezmoi apply` (required for socket) |

### Storage (created at runtime)

| Path | Purpose | Format |
|------|---------|--------|
| `~/.local/share/opencode-kitty/{workspace}.map` | Live window-to-session bindings | `kitty_window_id=opencode_session_id` (one per line) |
| `~/.local/share/opencode-kitty/{workspace}.seed` | Session IDs to restore from snapshot | One session ID per line (consumed on use) |
| `~/.local/share/opencode-kitty/{workspace}.map.snapshot` | Backup of map at snapshot time | Same as .map |
| `~/.local/share/kitty/workspace.log` | Debug log (when `KITTY_WORKSPACE_DEBUG=1`) | Timestamped log lines |

### External Dependencies

| Dependency | Used by | Purpose |
|-----------|---------|---------|
| Kitty 0.43+ | All | Sessions, `save_as_session`, `tab_bar_filter`, remote control. Discovered via `command -v kitty` (bash) or `shutil.which("kitty")` (Python). |
| `sqlite3` | opencode-kitty | Queries opencode's session database |
| `python3` | save-workspace.py, load-snapshot.py, kitty-workspace | JSON parsing, session file generation |
| `opencode` | opencode-kitty | `opencode db path`, `opencode --session` |
| OpenCode SQLite DB | opencode-kitty | Session lookup (`~/.local/share/opencode/opencode.db`) |

## Architecture

### Kitty Remote Control Setup

Kitty must be configured for socket-based remote control:

```conf
# In kitty.conf
allow_remote_control socket-only
listen_on unix:~/.local/share/kitty/control-socket
```

Kitty appends `-{PID}` to the socket path at startup (e.g., `~/.local/share/kitty/control-socket-36767`). All scripts discover the socket via glob on `~/.local/share/kitty/control-socket-*`.

The socket directory (`~/.local/share/kitty/`) must exist before Kitty starts. This is handled automatically by chezmoi via `run_once_create-kitty-socket-dir.sh`, which runs `mkdir -p ~/.local/share/kitty` on first apply.

`socket-only` restricts remote control to the unix socket -- programs running inside Kitty terminals cannot send remote control commands unless they connect to the socket explicitly. This is more secure than `allow_remote_control yes`.

### Workspace Detection: User Variables

Each workspace's first pane is tagged with a Kitty user variable:

```bash
kitty @ launch --type=os-window --var workspace="seo-data-science" ...
```

This persists in Kitty's state and is queryable via `kitty @ ls`:

```json
{"user_vars": {"workspace": "seo-data-science"}}
```

Detection uses this marker to find existing workspaces and avoid duplicates. It also allows `opencode-kitty` to determine which workspace it belongs to without any environment variable passing.

### PyCharm External Tool Configuration

| Field | Value |
|-------|-------|
| Program | `~/.local/bin/kitty-workspace` (expand `~` to your home directory) |
| Arguments | `$ProjectFileDir$` |
| Working directory | `$ProjectFileDir$` |

Both "Synchronize files after execution" and "Open console for tool output" must be unchecked.

Assign a keyboard shortcut via Settings > Keymap > External Tools > kitty-workspace.

### Data Flow: Workspace Launch

```mermaid
flowchart TD
    A[PyCharm hotkey] --> B[kitty-workspace $ProjectFileDir$]
    B --> S{Kitty running?}
    S -->|Yes| C{Workspace OS window exists?}
    S -->|No| T[open -a kitty, wait for socket]
    T --> C
    C -->|Yes| D[Focus existing OS window]
    C -->|No| E{build_* function defined?}
    E -->|Yes| F[Run build function]
    F --> G[Create OS window with tabs/splits]
    G --> H[Pre-type commands in server panes]
    H --> I[Launch opencode-kitty in opencode tab]
    I --> J{Snapshot exists?}
    J -->|Yes| K[restore_extra_tabs: add non-base tabs from snapshot]
    J -->|No| L[Done]
    K --> L
    E -->|No| M[Fallback: shell tab + opencode tab]
    D --> N[open -a kitty]
    L --> N
    M --> N
```

### Data Flow: Snapshot Save (F16)

```mermaid
flowchart LR
    A[User presses F16] --> B[save-workspace.py]
    B --> C[kitty @ ls: get focused OS window state]
    C --> D{Has workspace user var?}
    D -->|Yes| E[Generate session file from tab/pane state]
    D -->|No| F[Exit: not a workspace]
    E --> G["Write workspace.snapshot.conf"]
    E --> H["Copy workspace.map to .map.snapshot"]
```

### Data Flow: OpenCode Session Resumption

```mermaid
flowchart TD
    A[opencode-kitty starts in pane] --> B[Read KITTY_WINDOW_ID]
    B --> C[kitty @ ls: find workspace name for this window]
    C --> P[Purge stale bindings from .map]
    P --> D{Binding in .map file?}
    D -->|Yes| E{Session still exists in DB?}
    E -->|Yes| F[exec opencode --session ID]
    E -->|No| G[Remove stale binding]
    D -->|No| H{Seed file exists?}
    H -->|Yes| I[Pick first unbound seeded session]
    I --> J[Write binding to .map, remove from seed]
    J --> F
    H -->|No| K[Query DB: most recent unbound session]
    K -->|Found| L[Write binding to .map]
    L --> F
    K -->|None| M[exec opencode, new session]
    G --> H
```

### opencode-kitty Session Resolution Priority

```
0. Purge stale bindings            -> remove .map entries for windows not in kitty @ ls
1. Explicit --session flag         -> pass through to opencode directly
2. Direct binding in .map file     -> verify session exists, resume if valid
3. Seeded session from .seed file  -> pick first unbound seeded session
4. Most recent unbound session     -> query DB, exclude already-bound sessions
5. Fresh session                   -> start opencode with no --session flag
```

All DB queries filter with:
- `p.worktree = $PWD` (match current directory to opencode project)
- `s.time_archived IS NULL` (skip archived sessions)
- `s.parent_id IS NULL` (skip subagent sessions)

### Workspace Build Functions

Projects with custom needs have hardcoded build functions in `kitty-workspace`. These define the base structure:

```bash
build_seo-data-science() {
    # Tab 1: servers (2 vertical split panes)
    #   Left:  pre-typed "mise run local-prefect"
    #   Right: pre-typed "marimo --watch notebooks/"
    # Tab 2: opencode (opencode-kitty with session resumption)
}

build_tsc() {
    # Tab 1: app (pre-typed "make start")
    # Tab 2: flowbite (2 vertical split panes, pre-typed "npm start")
    # Tab 3: opencode (opencode-kitty with session resumption)
}

build_dotfiles() {
    # Tab 1: shell (plain bash)
    # Tab 2: opencode (opencode-kitty with session resumption)
}
```

### Generic Fallback

Projects without a `build_*` function get a generic workspace automatically:

- A new OS window tagged with `workspace=<dirname>`
- Tab 1: shell (project directory)
- Tab 2: opencode (opencode-kitty with session resumption)

This matches the `build_dotfiles` pattern. Any project can be opened from PyCharm without needing a custom build function.

### Auto-Launch

If Kitty is not running when the hotkey is pressed, the script launches it via `open -a kitty` and waits up to 15 seconds for the remote control socket to appear before proceeding.

Commands are pre-typed into panes using `kitty @ send-text` without a trailing newline, so the user can review/edit before pressing Enter.

### Layered Restore Model

When a workspace is opened, the system uses a layered approach:

1. **Base layer (always)**: The `build_*` function creates the defined tabs with their startup commands. This ensures servers always get the right commands pre-typed.

2. **Snapshot layer (if available)**: `restore_extra_tabs` reads the snapshot file and adds any tabs that aren't part of the base definition (e.g., extra opencode tabs the user added manually). Case-insensitive matching prevents duplicates.

3. **Session layer**: `opencode-kitty` handles opencode session resumption independently using its map/seed mechanism.

The build function is always the source of truth for commands, and the snapshot only captures structural additions.

## Kitty Configuration Details

### kitty.conf Additions

```conf
# Remote control for workspace scripts
allow_remote_control socket-only
listen_on unix:~/.local/share/kitty/control-socket

# Sessions
enabled_layouts splits,fat,grid,horizontal,stack,tall,vertical
tab_bar_filter session:~ or session:^$

# Keybindings
map f16 launch --type=background ~/.config/kitty/save-workspace.py
map kitty_mod+enter new_window_with_cwd
map kitty_mod+t new_tab_with_cwd
```

### Key Bindings Summary

| Key | Action | Notes |
|-----|--------|-------|
| F16 | Save workspace snapshot | Silent, auto-detects workspace name. Mapped via Karabiner or similar. |
| Ctrl+Shift+T | New tab in current directory | Uses active pane's cwd |
| Ctrl+Shift+Enter | New split pane in current directory | Uses active pane's cwd |
| PyCharm hotkey (user-defined) | Focus or create workspace | Calls `kitty-workspace $ProjectFileDir$` |

### Tab Bar Filtering

```conf
tab_bar_filter session:~ or session:^$
```

This restricts the tab bar to showing only tabs from the active Kitty session, plus any tabs not belonging to any session. When multiple workspace OS windows are open, each shows only its own tabs.

Note: This feature works with Kitty's native session system (loaded via `kitty --session`). Workspaces created via `kitty @` remote control are not formal Kitty sessions, so this filter has no effect on them currently. The setting is forward-looking for when the workspace system may adopt native session loading.

## Design Decisions

### Why Programmatic Build Instead of Session Files

Kitty session files (`.conf`) work for static layouts but have limitations when launched via remote control:

1. `kitty --single-instance --session file.conf` is unreliable when called from scripts (silent failures, timing issues)
2. `kitty @ action new_session file.conf` doesn't work via socket-based remote control
3. Commands in session files need login shell wrappers (`bash -l -c "exec ..."`) for PATH resolution

The programmatic approach (`kitty @ launch`) is reliable, composable, and allows `send-text` for pre-typing commands. Session files are kept as documentation and as targets for `save_as_session` snapshots.

### Why `secret &&` Before opencode

Opencode tabs are launched with `bash -l -c "secret && exec opencode-kitty"`. The `secret` function (defined in `.common_profile`) loads API keys from 1Password into environment variables (e.g., `AWS_PROFILE`, `AWS_REGION` for Bedrock). Without it, opencode cannot authenticate with the provider. The login shell (`bash -l`) ensures `.common_profile` is sourced so the `secret` function is available. If `secret` fails (e.g., 1Password not unlocked), the opencode tab will not launch.

### Why Pre-Type Instead of Auto-Execute

Server commands (`mise run local-prefect`, `marimo --watch notebooks/`, `make start`, `npm start`) are pre-typed into panes rather than auto-started because:

1. The user may want to adjust flags or environment before starting
2. Failed processes would close the pane (no `--hold` needed)
3. Allows the user to see all workspace panes before committing to starting services

### Why exec in opencode-kitty

`opencode-kitty` uses `exec opencode --session ID` rather than `opencode --session ID` followed by post-exec cleanup. This is because:

1. When `kitty @ launch` runs a command as a pane's process, the pane closes when the process exits
2. Without `exec`, the bash script would continue after opencode exits, do post-exec work, then exit -- closing the pane
3. With `exec`, opencode replaces the bash process. The pane stays alive as long as opencode runs
4. The tradeoff: post-exec binding for fresh sessions is lost. `opencode-kitty` handles this by falling back to "most recent session" on next launch

### Why User Variables for Workspace Detection

Kitty user variables (`--var workspace=name`) were chosen over alternatives:

| Method | Pros | Cons | Decision |
|--------|------|------|----------|
| Tab title matching | Simple | Titles change dynamically (opencode sets its own) | Rejected |
| OS window title | Stable | Not reliably queryable via `kitty @ ls` | Rejected |
| Process name matching | No setup needed | Fragile, multiple processes with same name | Rejected |
| **User variables** | Persistent, queryable, explicit | Requires Kitty 0.35+ | **Chosen** |

User variables survive tab title changes, process replacements, and are explicitly set by the workspace creator. They're queryable via `kitty @ ls` JSON output.

## Snapshot System

### What Gets Captured

The `save-workspace.py` script (triggered by F16) captures:

- All tabs in the focused workspace OS window
- Tab titles, layout type, enabled layouts
- Per-pane: working directory, foreground process command
- User variables (including the `workspace` tag)
- The opencode-kitty map file (window ID -> session ID bindings)

### What Gets Restored

On workspace open, if a snapshot exists:

1. The base `build_*` function runs first (server tabs with pre-typed commands, opencode tab)
2. `restore_extra_tabs` parses the snapshot for tabs NOT in the base definition
3. Extra tabs are created with their captured commands and working directories
4. The opencode-kitty seed file is populated from the map snapshot for session resumption

### Snapshot Limitations

- Scroll history is not captured (Kitty doesn't expose this via `kitty @ ls`)
- Pane geometry beyond layout type (exact split ratios) is not restored
- Running process state is lost -- only the command name is captured
- The snapshot captures ALL OS windows' state but only saves the focused workspace's data

## Testing Checklist

### Manual Tests

1. **First hotkey press**: Creates workspace with correct tabs, splits, and pre-typed commands
2. **Second hotkey press**: Focuses existing workspace without duplicating
3. **F16 in workspace**: Creates `{workspace}.snapshot.conf` silently
4. **Close + reopen workspace**: Loads base structure + extra tabs from snapshot
5. **Opencode session**: Resumes the correct session (check with `opencode session list`)
6. **Ctrl+Shift+T in workspace**: New tab opens in project directory, not root
7. **Multiple workspaces**: Each OS window is independent, no cross-contamination
8. **Kitty not running**: Hotkey launches kitty, waits for socket, then creates workspace
9. **Stale bindings**: Close kitty, reopen, verify old window->session bindings are purged
10. **Secret authentication**: Opencode tab loads API keys via 1Password before starting

### Validation

Run `--validate` on both scripts to check prerequisites without side effects:

```bash
kitty-workspace --validate
opencode-kitty --validate
```

## Debugging

### Debug Logging

Both scripts support debug logging controlled by `KITTY_WORKSPACE_DEBUG=1`:

```bash
# Ad-hoc debugging from terminal
KITTY_WORKSPACE_DEBUG=1 kitty-workspace /path/to/project

# Watch logs in real-time
tail -f ~/.local/share/kitty/workspace.log
```

To enable permanently in PyCharm, add `KITTY_WORKSPACE_DEBUG=1` as an environment variable in the External Tool configuration.

Log file: `~/.local/share/kitty/workspace.log`

Both scripts log key decision points: socket discovery, workspace detection, session binding, stale purge actions, and build function dispatch.

### Error Handling

Scripts use `set -uo pipefail` (strict unset-variable checking + pipe failure propagation) with an ERR trap that prints the failing line number:

```
opencode-kitty: error on line 142
```

The `-e` (exit-on-error) flag is intentionally **not** used. Previous iterations showed that `set -e` caused silent script deaths on benign failures (e.g., `ls` glob returning no matches, `grep` finding no results). Instead, critical operations check return values explicitly, and non-critical operations use `|| true` to degrade gracefully.

## Portability

All kitty-related scripts avoid hardcoded user or machine-specific paths:

| Concern | Approach |
|---------|----------|
| Kitty binary location | Discovered at runtime via `command -v kitty` (bash) or `shutil.which("kitty")` (Python) |
| Home directory | `$HOME` in bash scripts; `os.path.expanduser("~")` in Python |
| Project paths in `build_*` functions | Use `$HOME/...` rather than `/Users/tis/...` |
| Socket directory creation | Automated by chezmoi `run_once_create-kitty-socket-dir.sh` |
| PyCharm External Tool | User expands `~/.local/bin/kitty-workspace` to their home directory |

**Note:** `open -a kitty` (used to bring Kitty to foreground) is macOS-specific. A Linux equivalent would use `wmctrl` or similar.

## Known Issues and Future Work

### Known Issues

- `tab_bar_filter session:~` has no effect on workspaces created via remote control (they're not formal Kitty sessions)
- F16 requires Karabiner-Elements or similar to map a physical key to F16
- `save-workspace.py` runs as `--type=background` which means it has no association with the focused window at the exact moment of invocation; it queries `kitty @ ls` for `is_focused`/`is_active` to find the right workspace

### Future Work

- **Periodic auto-snapshot**: launchd plist that calls `save-workspace.py` every N minutes
- **Session switcher keybinding**: Map a key to quickly switch between workspaces (e.g., `kitty @ action goto_session`)
- **Aerospace integration**: Auto-route workspace OS windows to specific Aerospace workspaces via `on-window-detected` rules
