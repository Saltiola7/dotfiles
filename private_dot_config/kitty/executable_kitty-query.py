#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer", "plumbum"]
# ///
"""
kitty-query — Shared Python module for kitty workspace management.

Consolidates inline Python snippets and complex bash logic from
kitty-workspace and opencode-kitty into testable, typed functions
with a typer CLI entry point.

Subcommands:
    find-oswin          Find OS window ID by workspace name
    find-win            Find window ID by workspace name
    detect-workspace    Detect workspace name from a window ID
    list-win-ids        List all window IDs from kitty state
    parse-extra-tabs    Parse snapshot for non-base tabs
    find-socket         Find the kitty remote control socket
    find-active-session Detect opencode sessions held by running processes
    find-unbound-session Find an available session for binding
    purge-stale         Remove stale window->session bindings
"""

from __future__ import annotations

import glob as globmod
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from plumbum import local

# ── Constants ──────────────────────────────────────────────────────────────

LOG_FILE = Path.home() / ".local" / "share" / "kitty" / "workspace.log"
OC_STORAGE = Path.home() / ".local" / "share" / "opencode-kitty"
SOCKET_GLOB = str(Path.home() / ".local" / "share" / "kitty" / "control-socket-*")

# ── Pure functions (no side effects, fully testable) ───────────────────────


def find_oswin_by_workspace(kitty_state: list[dict], workspace: str) -> int | None:
    """Find the OS window ID containing a window with the given workspace user var.

    Traverses the kitty @ ls JSON structure and returns the oswin ID of the
    first OS window that has any window with user_vars.workspace == workspace.

    Returns None if no matching workspace is found.
    """
    for oswin in kitty_state:
        for tab in oswin.get("tabs", []):
            for win in tab.get("windows", []):
                if win.get("user_vars", {}).get("workspace") == workspace:
                    return oswin["id"]
    return None


def find_win_by_workspace(kitty_state: list[dict], workspace: str) -> int | None:
    """Find the first window ID carrying the given workspace user var.

    Returns the window ID (not OS window ID) of the first window whose
    user_vars.workspace matches.

    Returns None if no matching workspace is found.
    """
    for oswin in kitty_state:
        for tab in oswin.get("tabs", []):
            for win in tab.get("windows", []):
                if win.get("user_vars", {}).get("workspace") == workspace:
                    return win["id"]
    return None


def detect_workspace_by_win(kitty_state: list[dict], win_id: int) -> str | None:
    """Detect the workspace name from a window ID.

    Finds which OS window contains win_id, then scans all windows in that
    OS window for a workspace user var.

    Returns the workspace name or None.
    """
    for oswin in kitty_state:
        # Check if win_id is anywhere in this OS window
        found_in_oswin = False
        for tab in oswin.get("tabs", []):
            for win in tab.get("windows", []):
                if win["id"] == win_id:
                    found_in_oswin = True
                    break
            if found_in_oswin:
                break

        if found_in_oswin:
            # Scan all windows in this OS window for workspace var
            for tab in oswin.get("tabs", []):
                for win in tab.get("windows", []):
                    ws = win.get("user_vars", {}).get("workspace")
                    if ws:
                        return ws
    return None


def list_all_win_ids(kitty_state: list[dict]) -> list[int]:
    """Extract all window IDs from kitty state.

    Returns a flat list of every window ID across all OS windows and tabs.
    """
    ids: list[int] = []
    for oswin in kitty_state:
        for tab in oswin.get("tabs", []):
            for win in tab.get("windows", []):
                ids.append(win["id"])
    return ids


def parse_extra_tabs(
    snapshot_path: str,
    base_tab_names: list[str],
) -> list[dict[str, str]]:
    """Parse a kitty session snapshot for tabs not in the base definition.

    Args:
        snapshot_path: Path to the .snapshot.conf file.
        base_tab_names: List of tab titles that belong to the base workspace
                        definition (case-insensitive match).

    Returns:
        List of dicts with keys: title, cwd, cmd.
        Each represents an "extra" tab that was in the snapshot but not
        part of the base workspace definition.
    """
    known_lower = {t.lower() for t in base_tab_names}
    extra_tabs: list[dict[str, str]] = []
    current_tab: dict[str, str | bool] | None = None

    with open(snapshot_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("new_tab"):
                title = line[len("new_tab") :].strip() or "tab"
                current_tab = {
                    "title": title,
                    "in_base": title.lower() in known_lower,
                }
            elif (
                line.startswith("cd ")
                and current_tab
                and not current_tab["in_base"]
            ):
                current_tab["cwd"] = line.split(None, 1)[1]
            elif (
                line.startswith("launch")
                and current_tab
                and not current_tab["in_base"]
            ):
                # Extract command, skip kitty-unserialize-data and --flags
                parts = line.split()
                cmd: list[str] = []
                for p in parts[1:]:
                    if p.startswith("'kitty-unserialize-data") or p.startswith(
                        "kitty-unserialize-data"
                    ) or p.startswith("--"):
                        continue
                    cmd.append(p)
                current_tab["cmd"] = " ".join(cmd)
                extra_tabs.append(current_tab)  # type: ignore[arg-type]
                current_tab = None

    return [
        {
            "title": str(tab["title"]),
            "cwd": str(tab.get("cwd", os.path.expanduser("~"))),
            "cmd": str(tab.get("cmd", "")),
        }
        for tab in extra_tabs
    ]


def find_socket() -> str | None:
    """Find the first kitty remote control socket.

    Returns the socket path or None if no socket exists.
    """
    sockets = sorted(globmod.glob(SOCKET_GLOB))
    return sockets[0] if sockets else None


def parse_map_file(map_path: str | Path) -> dict[str, str]:
    """Parse a window->session binding map file.

    Format: each line is `window_id=session_id` (or comments starting with #).

    Returns:
        Dict mapping window_id (str) -> session_id (str).
    """
    bindings: dict[str, str] = {}
    path = Path(map_path)
    if not path.exists():
        return bindings

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            wid, sid = line.split("=", 1)
            bindings[wid.strip()] = sid.strip()
    return bindings


def compute_stale_bindings(
    bindings: dict[str, str],
    live_win_ids: list[int],
) -> tuple[dict[str, str], dict[str, str]]:
    """Separate bindings into live and stale based on current kitty window IDs.

    Args:
        bindings: window_id -> session_id map.
        live_win_ids: List of currently live window IDs from kitty.

    Returns:
        Tuple of (live_bindings, stale_bindings).
    """
    live_set = {str(wid) for wid in live_win_ids}
    live: dict[str, str] = {}
    stale: dict[str, str] = {}
    for wid, sid in bindings.items():
        if wid in live_set:
            live[wid] = sid
        else:
            stale[wid] = sid
    return live, stale


def write_map_file(map_path: str | Path, bindings: dict[str, str]) -> None:
    """Write bindings to a map file.

    Args:
        map_path: Path to the map file.
        bindings: window_id -> session_id map to write.
    """
    path = Path(map_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{wid}={sid}" for wid, sid in bindings.items()]
    path.write_text("\n".join(lines) + "\n" if lines else "")


def get_bound_session_ids(map_path: str | Path) -> list[str]:
    """Get all session IDs from a map file.

    Returns list of session IDs (values from the map).
    """
    bindings = parse_map_file(map_path)
    return list(bindings.values())


def query_sessions(
    db_path: str | Path,
    project_dir: str,
    *,
    exclude_ids: list[str] | None = None,
    only_ids: list[str] | None = None,
    limit: int = 1,
) -> list[str]:
    """Query opencode sessions from the database.

    Args:
        db_path: Path to the opencode SQLite database.
        project_dir: Project working directory to filter by.
        exclude_ids: Session IDs to exclude (NOT IN).
        only_ids: Session IDs to include (IN). If empty list, returns [].
        limit: Maximum number of results.

    Returns:
        List of session IDs, ordered by most recently updated.
    """
    path = Path(db_path)
    if not path.exists():
        return []

    conn = sqlite3.connect(str(path))
    try:
        query = """
            SELECT s.id
            FROM session s
            JOIN project p ON s.project_id = p.id
            WHERE p.worktree = ?
              AND s.time_archived IS NULL
              AND s.parent_id IS NULL
        """
        params: list[str] = [project_dir]

        if exclude_ids:
            placeholders = ",".join("?" for _ in exclude_ids)
            query += f" AND s.id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        if only_ids is not None:
            if not only_ids:
                return []
            placeholders = ",".join("?" for _ in only_ids)
            query += f" AND s.id IN ({placeholders})"
            params.extend(only_ids)

        query += " ORDER BY s.time_updated DESC LIMIT ?"
        params.append(str(limit))

        cursor = conn.execute(query, params)
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def session_exists(db_path: str | Path, session_id: str) -> bool:
    """Check if a session exists and is not archived.

    Args:
        db_path: Path to the opencode SQLite database.
        session_id: Session ID to check.

    Returns:
        True if session exists and is active.
    """
    path = Path(db_path)
    if not path.exists():
        return False

    conn = sqlite3.connect(str(path))
    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM session WHERE id = ? AND time_archived IS NULL",
            (session_id,),
        )
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()


def detect_active_opencode_pids(project_dir: str) -> list[int]:
    """Find PIDs of running opencode processes for a given project directory.

    Uses ps to find opencode processes, then lsof to check their working
    directories.

    Returns:
        List of PIDs that are running opencode in the given project_dir.
    """
    try:
        ps = local["ps"]
        lsof = local["lsof"]

        ps_output = ps("-eo", "pid,command")
    except Exception:
        return []

    active_pids: list[int] = []
    for line in ps_output.strip().splitlines():
        line = line.strip()
        if "opencode" not in line or "opencode-kitty" in line:
            continue
        parts = line.split(None, 1)
        if not parts:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue

        # Skip our own process tree
        if pid == os.getpid() or pid == os.getppid():
            continue

        try:
            lsof_output = lsof("-p", str(pid), "-a", "-d", "cwd", "-Fn")
            for lsof_line in lsof_output.strip().splitlines():
                if lsof_line.startswith("n"):
                    cwd = lsof_line[1:]
                    if cwd == project_dir:
                        active_pids.append(pid)
                    break
        except Exception:
            continue

    return active_pids


def find_active_session_id(
    db_path: str | Path,
    project_dir: str,
) -> str | None:
    """Find the session ID being used by a running opencode process.

    If another opencode process is running for the project directory, return
    the most recently updated session ID (which it's likely using).

    Returns:
        Session ID string or None.
    """
    active_pids = detect_active_opencode_pids(project_dir)
    if not active_pids:
        return None

    results = query_sessions(db_path, project_dir, limit=1)
    return results[0] if results else None


def consume_seed(seed_path: str | Path, session_id: str) -> None:
    """Remove a session ID from the seed file.

    Used after a seeded session is picked up by a new pane, so the next
    pane gets the next seeded session.

    Args:
        seed_path: Path to the .seed file.
        session_id: Session ID to remove.
    """
    path = Path(seed_path)
    if not path.exists():
        return

    lines = path.read_text().splitlines()
    escaped = re.escape(session_id)
    remaining = [l for l in lines if not re.match(f"^{escaped}$", l)]
    path.write_text("\n".join(remaining) + "\n" if remaining else "")


def find_unbound_session_id(
    db_path: str | Path,
    project_dir: str,
    map_path: str | Path,
    workspace: str,
) -> str | None:
    """Find an available (unbound) session ID for a workspace.

    Resolution order:
    1. Check for seeded sessions (from snapshot restore)
    2. Fall back to most recent unbound session

    Args:
        db_path: Path to the opencode SQLite database.
        project_dir: Project working directory.
        map_path: Path to the .map file with existing bindings.
        workspace: Workspace name (for seed file lookup).

    Returns:
        Session ID string or None.
    """
    # Collect IDs to exclude
    exclude_ids: list[str] = get_bound_session_ids(map_path)

    # Exclude sessions held by running opencode processes
    active_session = find_active_session_id(db_path, project_dir)
    if active_session and active_session not in exclude_ids:
        exclude_ids.append(active_session)

    # Check seed file first
    seed_path = OC_STORAGE / f"{workspace}.seed"
    if seed_path.exists():
        seed_lines = [
            l.strip() for l in seed_path.read_text().splitlines() if l.strip()
        ]
        if seed_lines:
            results = query_sessions(
                db_path,
                project_dir,
                exclude_ids=exclude_ids,
                only_ids=seed_lines,
                limit=1,
            )
            if results:
                consume_seed(seed_path, results[0])
                return results[0]

    # Fallback: most recent unbound session
    results = query_sessions(
        db_path,
        project_dir,
        exclude_ids=exclude_ids,
        limit=1,
    )
    return results[0] if results else None


def debug_log(message: str, script_name: str = "kitty-query") -> None:
    """Write a debug log entry if KITTY_WORKSPACE_DEBUG=1.

    Args:
        message: Log message.
        script_name: Script name prefix for the log entry.
    """
    if os.environ.get("KITTY_WORKSPACE_DEBUG") != "1":
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {script_name}: {message}\n")


# ── Typer CLI ──────────────────────────────────────────────────────────────

app = typer.Typer(
    name="kitty-query",
    help="Shared tooling for kitty workspace management.",
    no_args_is_help=True,
)


def _read_kitty_state_stdin() -> list[dict]:
    """Read kitty @ ls JSON from stdin."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        typer.echo(f"Error: invalid JSON on stdin: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def find_oswin(
    workspace: Annotated[str, typer.Argument(help="Workspace name to search for")],
) -> None:
    """Find the OS window ID containing a workspace."""
    state = _read_kitty_state_stdin()
    result = find_oswin_by_workspace(state, workspace)
    if result is not None:
        typer.echo(result)
    else:
        raise typer.Exit(code=1)


@app.command()
def find_win(
    workspace: Annotated[str, typer.Argument(help="Workspace name to search for")],
) -> None:
    """Find the first window ID carrying a workspace user var."""
    state = _read_kitty_state_stdin()
    result = find_win_by_workspace(state, workspace)
    if result is not None:
        typer.echo(result)
    else:
        raise typer.Exit(code=1)


@app.command()
def detect_workspace(
    win_id: Annotated[int, typer.Argument(help="Kitty window ID")],
) -> None:
    """Detect the workspace name from a window ID."""
    state = _read_kitty_state_stdin()
    result = detect_workspace_by_win(state, win_id)
    if result:
        typer.echo(result)
    else:
        raise typer.Exit(code=1)


@app.command()
def list_win_ids() -> None:
    """List all window IDs from kitty state (one per line)."""
    state = _read_kitty_state_stdin()
    ids = list_all_win_ids(state)
    for wid in ids:
        typer.echo(wid)


@app.command()
def parse_extra_tabs_cmd(
    snapshot: Annotated[str, typer.Argument(help="Path to snapshot file")],
    base_tabs: Annotated[
        list[str],
        typer.Argument(help="Base tab names (case-insensitive, passed from bash)"),
    ],
) -> None:
    """Parse a snapshot for tabs not in the base definition.

    Output: pipe-delimited lines: title|cwd|cmd
    """
    if not Path(snapshot).exists():
        typer.echo(f"Error: snapshot not found: {snapshot}", err=True)
        raise typer.Exit(code=1)

    tabs = parse_extra_tabs(snapshot, base_tabs)
    for tab in tabs:
        typer.echo(f"{tab['title']}|{tab['cwd']}|{tab['cmd']}")


@app.command()
def find_socket_cmd() -> None:
    """Find the kitty remote control socket path."""
    result = find_socket()
    if result:
        typer.echo(result)
    else:
        raise typer.Exit(code=1)


@app.command()
def find_active_session(
    db_path: Annotated[str, typer.Argument(help="Path to opencode SQLite database")],
    project_dir: Annotated[str, typer.Argument(help="Project working directory")],
) -> None:
    """Detect the session ID held by a running opencode process."""
    result = find_active_session_id(db_path, project_dir)
    if result:
        typer.echo(result)
    else:
        raise typer.Exit(code=1)


@app.command()
def find_unbound_session(
    db_path: Annotated[str, typer.Argument(help="Path to opencode SQLite database")],
    project_dir: Annotated[str, typer.Argument(help="Project working directory")],
    map_file: Annotated[str, typer.Argument(help="Path to .map binding file")],
    workspace: Annotated[str, typer.Argument(help="Workspace name")],
) -> None:
    """Find an available (unbound) session for a workspace."""
    result = find_unbound_session_id(db_path, project_dir, map_file, workspace)
    if result:
        typer.echo(result)
    else:
        raise typer.Exit(code=1)


@app.command()
def purge_stale(
    map_file: Annotated[str, typer.Argument(help="Path to the .map binding file")],
    live_ids: Annotated[
        list[str],
        typer.Argument(help="Live kitty window IDs (space-separated)"),
    ],
) -> None:
    """Remove stale window->session bindings from a map file."""
    if not Path(map_file).exists():
        typer.echo("Map file does not exist, nothing to purge.", err=True)
        raise typer.Exit(code=0)

    bindings = parse_map_file(map_file)
    live_int_ids = [int(x) for x in live_ids if x.strip()]
    live, stale = compute_stale_bindings(bindings, live_int_ids)

    if stale:
        for wid, sid in stale.items():
            debug_log(f"Purging stale binding: window {wid} -> {sid}")
            typer.echo(f"Purged: {wid}={sid}", err=True)
        write_map_file(map_file, live)
        typer.echo(f"Remaining bindings: {len(live)}", err=True)
    else:
        typer.echo("No stale bindings found.", err=True)


@app.command()
def session_exists_cmd(
    db_path: Annotated[str, typer.Argument(help="Path to opencode SQLite database")],
    session_id: Annotated[str, typer.Argument(help="Session ID to check")],
) -> None:
    """Check if a session exists and is active. Exit 0 if yes, 1 if no."""
    if session_exists(db_path, session_id):
        typer.echo("exists")
    else:
        raise typer.Exit(code=1)


@app.command()
def query_sessions_cmd(
    db_path: Annotated[str, typer.Argument(help="Path to opencode SQLite database")],
    project_dir: Annotated[str, typer.Argument(help="Project working directory")],
    limit: Annotated[int, typer.Option(help="Max results")] = 1,
    exclude: Annotated[
        Optional[list[str]],
        typer.Option(help="Session IDs to exclude"),
    ] = None,
) -> None:
    """Query sessions for a project directory."""
    results = query_sessions(
        db_path,
        project_dir,
        exclude_ids=exclude,
        limit=limit,
    )
    for sid in results:
        typer.echo(sid)
    if not results:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
