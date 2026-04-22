"""Shared fixtures for kitty workspace tests."""

import json
import os
import pytest
import tempfile


# ---------------------------------------------------------------------------
# Realistic kitty @ ls state fixtures
# ---------------------------------------------------------------------------

def _make_window(win_id, cwd, fg_cmd=None, user_vars=None, cmdline=None):
    """Helper to build a realistic kitty window dict."""
    fg_procs = []
    if fg_cmd:
        fg_procs.append({"cmdline": fg_cmd, "pid": 10000 + win_id})
    else:
        # Default: just a shell
        fg_procs.append({"cmdline": ["/bin/bash"], "pid": 10000 + win_id})

    return {
        "id": win_id,
        "pid": 20000 + win_id,
        "title": os.path.basename(cwd),
        "cwd": cwd,
        "cmdline": cmdline or ["/bin/bash", "-l"],
        "foreground_processes": fg_procs,
        "is_focused": False,
        "user_vars": user_vars or {},
        "env": {"SHELL": "/bin/bash"},
    }


def _make_tab(tab_id, title, windows, layout="splits", is_active=False,
              enabled_layouts=None):
    """Helper to build a realistic kitty tab dict."""
    if enabled_layouts is None:
        enabled_layouts = ["splits", "fat", "grid", "horizontal", "stack",
                           "tall", "vertical"]
    return {
        "id": tab_id,
        "title": title,
        "layout": layout,
        "enabled_layouts": enabled_layouts,
        "is_active": is_active,
        "is_focused": is_active,
        "windows": windows,
    }


def _make_oswin(oswin_id, tabs, is_focused=False):
    """Helper to build a realistic kitty OS window dict."""
    return {
        "id": oswin_id,
        "is_focused": is_focused,
        "platform_window_id": 100 + oswin_id,
        "tabs": tabs,
    }


@pytest.fixture
def single_workspace_state():
    """Single OS window with workspace 'myproject', 2 tabs (shell + opencode)."""
    shell_win = _make_window(
        win_id=1,
        cwd="/Users/tis/repos/myproject",
        user_vars={"workspace": "myproject"},
    )
    opencode_win = _make_window(
        win_id=2,
        cwd="/Users/tis/repos/myproject",
        fg_cmd=["opencode"],
        user_vars={"workspace": "myproject"},
    )
    tab_shell = _make_tab(10, "shell", [shell_win], is_active=True)
    tab_oc = _make_tab(11, "opencode", [opencode_win])
    oswin = _make_oswin(1, [tab_shell, tab_oc], is_focused=True)
    return [oswin]


@pytest.fixture
def multi_workspace_state():
    """Two OS windows: 'myproject' (focused) and 'dotfiles' (not focused)."""
    # OS window 1: myproject (focused)
    shell_win1 = _make_window(
        win_id=1,
        cwd="/Users/tis/repos/myproject",
        user_vars={"workspace": "myproject"},
    )
    oc_win1 = _make_window(
        win_id=2,
        cwd="/Users/tis/repos/myproject",
        fg_cmd=["opencode"],
        user_vars={"workspace": "myproject"},
    )
    tab1_shell = _make_tab(10, "shell", [shell_win1], is_active=True)
    tab1_oc = _make_tab(11, "opencode", [oc_win1])
    oswin1 = _make_oswin(1, [tab1_shell, tab1_oc], is_focused=True)

    # OS window 2: dotfiles (not focused)
    shell_win2 = _make_window(
        win_id=3,
        cwd="/Users/tis/.local/share/chezmoi",
        user_vars={"workspace": "dotfiles"},
    )
    tab2_shell = _make_tab(20, "shell", [shell_win2], is_active=True)
    oswin2 = _make_oswin(2, [tab2_shell], is_focused=False)

    return [oswin1, oswin2]


@pytest.fixture
def no_workspace_state():
    """Single OS window with no workspace user var set."""
    plain_win = _make_window(win_id=1, cwd="/tmp")
    tab = _make_tab(10, "tab", [plain_win], is_active=True)
    oswin = _make_oswin(1, [tab], is_focused=True)
    return [oswin]


@pytest.fixture
def no_focus_state():
    """OS windows exist but none are focused."""
    shell_win = _make_window(
        win_id=1,
        cwd="/Users/tis/repos/myproject",
        user_vars={"workspace": "myproject"},
    )
    tab = _make_tab(10, "shell", [shell_win], is_active=True)
    oswin = _make_oswin(1, [tab], is_focused=False)
    return [oswin]


@pytest.fixture
def complex_oswin():
    """An OS window with multiple tabs, multiple panes, mixed fg processes."""
    # Tab 1: shell — two panes (shell + running process)
    shell_pane = _make_window(
        win_id=1,
        cwd="/Users/tis/repos/myproject",
        user_vars={"workspace": "myproject"},
    )
    python_pane = _make_window(
        win_id=2,
        cwd="/Users/tis/repos/myproject",
        fg_cmd=["python3", "manage.py", "runserver"],
        user_vars={"workspace": "myproject"},
    )
    tab_shell = _make_tab(
        10, "dev", [shell_pane, python_pane],
        layout="splits", is_active=False,
        enabled_layouts=["splits", "stack"],
    )

    # Tab 2: opencode — single pane
    oc_pane = _make_window(
        win_id=3,
        cwd="/Users/tis/repos/myproject",
        fg_cmd=["opencode"],
        user_vars={"workspace": "myproject"},
    )
    tab_oc = _make_tab(
        11, "opencode", [oc_pane],
        layout="stack", is_active=True,
        enabled_layouts="stack",  # string form (not list)
    )

    # Tab 3: logs — single pane, no fg process (just shell)
    log_pane = _make_window(
        win_id=4,
        cwd="/var/log",
        user_vars={"workspace": "myproject"},
    )
    tab_logs = _make_tab(12, "logs", [log_pane])

    oswin = _make_oswin(1, [tab_shell, tab_oc, tab_logs], is_focused=True)
    return oswin


@pytest.fixture
def empty_fg_procs_oswin():
    """OS window where a window has empty foreground_processes."""
    win = _make_window(
        win_id=1,
        cwd="/Users/tis/repos/myproject",
        user_vars={"workspace": "myproject"},
    )
    win["foreground_processes"] = []
    tab = _make_tab(10, "shell", [win], is_active=True)
    oswin = _make_oswin(1, [tab], is_focused=True)
    return oswin


# ---------------------------------------------------------------------------
# Session file fixtures
# ---------------------------------------------------------------------------

SAMPLE_SESSION_CONTENT = """\
new_tab dev
layout splits
enabled_layouts splits,fat,grid,horizontal,stack,tall,vertical
cd /Users/tis/repos/myproject
launch --var=workspace=myproject
cd /Users/tis/repos/myproject
launch --var=workspace=myproject python3 manage.py runserver

new_tab opencode
layout stack
enabled_layouts stack
cd /Users/tis/repos/myproject
launch --var=workspace=myproject opencode

new_tab logs
layout splits
enabled_layouts splits,fat,grid,horizontal,stack,tall,vertical
cd /var/log
launch --var=workspace=myproject

focus_tab 1
"""

MINIMAL_SESSION_CONTENT = """\
new_tab shell
layout splits
enabled_layouts splits
cd /tmp
launch

focus_tab 0
"""


@pytest.fixture
def sample_session_file(tmp_path):
    """Write a sample session file and return its path."""
    p = tmp_path / "myproject.snapshot.conf"
    p.write_text(SAMPLE_SESSION_CONTENT)
    return str(p)


@pytest.fixture
def minimal_session_file(tmp_path):
    """Write a minimal session file and return its path."""
    p = tmp_path / "minimal.snapshot.conf"
    p.write_text(MINIMAL_SESSION_CONTENT)
    return str(p)
