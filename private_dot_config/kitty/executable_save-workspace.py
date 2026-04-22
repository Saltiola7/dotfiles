#!/usr/bin/env python3
"""
kitty-save-workspace - Save the current workspace session to its snapshot file.

Reads the kitty state via `kitty @ ls`, finds the focused OS window,
detects its workspace name from the 'workspace' user var, and writes
a kitty session file that can recreate the workspace.

Usage:
    # From command line:
    python3 ~/.config/kitty/save-workspace.py

    # From kitty.conf (mapped to a key):
    map f16 launch --type=background ~/.config/kitty/save-workspace.py

    # The script saves to ~/.config/kitty/sessions/{workspace}.snapshot.conf
"""

import glob
import json
import os
import shutil
import subprocess
import sys

KITTY = shutil.which("kitty")
SESSIONS_DIR = os.path.expanduser("~/.config/kitty/sessions")
OC_STORAGE = os.path.expanduser("~/.local/share/opencode-kitty")
SOCKET_GLOB = os.path.expanduser("~/.local/share/kitty/control-socket-*")


def find_socket():
    sockets = glob.glob(SOCKET_GLOB)
    return sockets[0] if sockets else None


def kitty_ls():
    socket = find_socket()
    if not socket:
        return None
    result = subprocess.run(
        [KITTY, "@", f"--to=unix:{socket}", "ls"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def find_active_workspace(state):
    """Find the workspace name and OS window data for the focused OS window."""
    for oswin in state:
        if not oswin.get("is_focused"):
            continue
        for tab in oswin.get("tabs", []):
            for win in tab.get("windows", []):
                workspace = win.get("user_vars", {}).get("workspace")
                if workspace:
                    return workspace, oswin
    return None, None


def generate_session_file(oswin):
    """Generate a kitty session file from an OS window's state."""
    lines = []
    tabs = oswin.get("tabs", [])
    active_tab_idx = 0

    for i, tab in enumerate(tabs):
        title = tab.get("title", "")
        layout = tab.get("layout", "splits")
        windows = tab.get("windows", [])

        if tab.get("is_active"):
            active_tab_idx = i

        lines.append(f"new_tab {title}")
        lines.append(f"layout {layout}")
        enabled = tab.get("enabled_layouts", "splits,fat,grid,horizontal,stack,tall,vertical")
        if isinstance(enabled, list):
            enabled = ",".join(enabled)
        lines.append(f"enabled_layouts {enabled}")

        for j, win in enumerate(windows):
            cwd = win.get("cwd", os.path.expanduser("~"))
            lines.append(f"cd {cwd}")

            # Build the launch command
            fg_procs = win.get("foreground_processes", [])
            cmdline = win.get("cmdline", [])

            # Determine what command to restart
            # Priority: foreground process (if it's not just a shell), else shell
            restart_cmd = None
            for proc in fg_procs:
                proc_cmd = proc.get("cmdline", [])
                if proc_cmd:
                    name = os.path.basename(proc_cmd[0])
                    # Skip shells -- we just want the shell to start
                    if name in ("bash", "zsh", "fish", "sh", "-bash", "-zsh"):
                        continue
                    restart_cmd = proc_cmd
                    break

            # Preserve user vars
            user_vars = win.get("user_vars", {})
            var_args = ""
            for k, v in user_vars.items():
                var_args += f" --var={k}={v}"

            if restart_cmd:
                cmd_str = " ".join(restart_cmd)
                lines.append(f"launch{var_args} {cmd_str}")
            else:
                lines.append(f"launch{var_args}")

            if j == 0 and len(windows) > 1:
                # After the first window, remaining windows need location hints
                # but session files handle this via the layout state
                pass

        lines.append("")

    lines.append(f"focus_tab {active_tab_idx}")
    return "\n".join(lines)


def main():
    state = kitty_ls()
    if not state:
        print("Could not get kitty state", file=sys.stderr)
        sys.exit(1)

    workspace, oswin = find_active_workspace(state)
    if not workspace:
        print("No workspace found for the focused OS window.", file=sys.stderr)
        sys.exit(1)

    session_content = generate_session_file(oswin)
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    save_path = os.path.join(SESSIONS_DIR, f"{workspace}.snapshot.conf")

    with open(save_path, "w") as f:
        f.write(session_content)

    # Also save the opencode-kitty map file so session bindings survive
    # The map file maps kitty_window_id -> opencode_session_id
    # We copy it as-is; kitty-workspace will seed from it on restore
    map_src = os.path.join(OC_STORAGE, f"{workspace}.map")
    if os.path.isfile(map_src):
        map_dst = os.path.join(OC_STORAGE, f"{workspace}.map.snapshot")
        shutil.copy2(map_src, map_dst)

    print(f"Saved workspace '{workspace}' -> {save_path}")


if __name__ == "__main__":
    main()
