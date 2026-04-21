#!/usr/bin/env python3
"""
kitty-load-snapshot - Load a kitty session snapshot into a new OS window.

Parses a kitty session .conf file and recreates the workspace using
kitty @ remote control commands.

Usage:
    kitty-load-snapshot <snapshot.conf> <workspace-name>
"""

import glob
import os
import shlex
import subprocess
import sys

KITTY = "/Applications/kitty.app/Contents/MacOS/kitty"
SOCKET_GLOB = os.path.expanduser("~/.local/share/kitty/control-socket-*")


def find_socket():
    sockets = glob.glob(SOCKET_GLOB)
    return sockets[0] if sockets else None


def kitty_rc(*args):
    socket = find_socket()
    if not socket:
        print("No kitty socket found", file=sys.stderr)
        sys.exit(1)
    cmd = [KITTY, "@", f"--to=unix:{socket}"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def parse_session_file(path):
    """Parse a kitty session file into a list of tabs with their panes."""
    tabs = []
    current_tab = None
    current_cwd = os.path.expanduser("~")
    focus_tab_idx = 0

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("new_tab"):
                title = line[len("new_tab"):].strip() or "tab"
                current_tab = {"title": title, "layout": "splits", "cwd": current_cwd, "panes": []}
                tabs.append(current_tab)

            elif line.startswith("layout "):
                if current_tab:
                    current_tab["layout"] = line.split(None, 1)[1]

            elif line.startswith("cd "):
                path_val = line.split(None, 1)[1]
                # Resolve relative paths
                if path_val.startswith("../") or not path_val.startswith("/"):
                    current_cwd = os.path.normpath(os.path.join(current_cwd, path_val))
                else:
                    current_cwd = path_val
                if current_tab:
                    current_tab["cwd"] = current_cwd

            elif line.startswith("launch"):
                if current_tab is None:
                    continue
                # Parse launch arguments
                parts = shlex.split(line)
                parts = parts[1:]  # remove 'launch'

                cmd = []
                var_args = []
                skip_next = False
                for i, part in enumerate(parts):
                    if skip_next:
                        skip_next = False
                        continue
                    if part.startswith("'kitty-unserialize-data="):
                        # Skip the unserialize metadata
                        continue
                    if part.startswith("--var="):
                        var_args.append(part)
                    elif part.startswith("--"):
                        # Skip other launch options
                        continue
                    else:
                        cmd.append(part)

                pane = {
                    "cwd": current_tab["cwd"],
                    "cmd": cmd,
                    "var_args": var_args,
                }
                current_tab["panes"].append(pane)

            elif line.startswith("focus_tab"):
                try:
                    focus_tab_idx = int(line.split()[1])
                except (IndexError, ValueError):
                    pass

            elif line.startswith("enabled_layouts") or line.startswith("set_layout_state"):
                pass  # skip, we handle layout separately

            elif line == "focus":
                pass  # skip

    return tabs, focus_tab_idx


def build_workspace(tabs, focus_tab_idx, workspace_name):
    """Create the workspace using kitty @ remote control."""
    if not tabs:
        return

    first_win_id = None

    for tab_idx, tab in enumerate(tabs):
        panes = tab["panes"]
        if not panes:
            panes = [{"cwd": tab["cwd"], "cmd": [], "var_args": []}]

        first_pane = panes[0]

        if tab_idx == 0:
            # Create OS window with first tab
            launch_args = [
                "launch", "--type=os-window",
                f"--tab-title={tab['title']}",
                f"--cwd={first_pane['cwd']}",
                f"--var=workspace={workspace_name}",
            ]
            # Add any preserved var args
            for va in first_pane.get("var_args", []):
                if "workspace=" not in va:
                    launch_args.append(va)

            if first_pane["cmd"]:
                launch_args.extend(first_pane["cmd"])

            stdout, _, rc = kitty_rc(*launch_args)
            if rc != 0:
                print(f"Failed to create OS window", file=sys.stderr)
                return
            first_win_id = stdout
        else:
            # Create new tab
            launch_args = [
                "launch", "--type=tab",
                f"--match=window_id:{first_win_id}",
                f"--tab-title={tab['title']}",
                f"--cwd={first_pane['cwd']}",
            ]
            for va in first_pane.get("var_args", []):
                launch_args.append(va)

            if first_pane["cmd"]:
                launch_args.extend(first_pane["cmd"])

            kitty_rc(*launch_args)

        # Add remaining panes as vsplits
        if tab_idx == 0:
            match_win = first_win_id
        else:
            # Get the latest window id
            stdout, _, _ = kitty_rc("ls")
            import json
            state = json.loads(stdout)
            match_win = None
            for oswin in state:
                for t in oswin.get("tabs", []):
                    if t.get("title") == tab["title"]:
                        wins = t.get("windows", [])
                        if wins:
                            match_win = str(wins[-1]["id"])
            if not match_win:
                continue

        for pane in panes[1:]:
            split_args = [
                "launch",
                f"--match=window_id:{match_win}",
                "--location=vsplit",
                f"--cwd={pane['cwd']}",
            ]
            for va in pane.get("var_args", []):
                split_args.append(va)
            if pane["cmd"]:
                split_args.extend(pane["cmd"])
            kitty_rc(*split_args)

    # Focus the right tab
    if tabs and 0 <= focus_tab_idx < len(tabs):
        target_title = tabs[focus_tab_idx]["title"]
        kitty_rc("focus-tab", "--match", f"title:^{target_title}$")


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <snapshot.conf> <workspace-name>", file=sys.stderr)
        sys.exit(1)

    snapshot_path = sys.argv[1]
    workspace_name = sys.argv[2]

    if not os.path.isfile(snapshot_path):
        print(f"Snapshot not found: {snapshot_path}", file=sys.stderr)
        sys.exit(1)

    tabs, focus_tab_idx = parse_session_file(snapshot_path)
    build_workspace(tabs, focus_tab_idx, workspace_name)


if __name__ == "__main__":
    main()
