"""Tests for load-snapshot.py: parse_session_file."""

import importlib.util
import os
import textwrap

import pytest

# Import from the chezmoi source file (non-standard filename)
_script_path = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    "private_dot_config", "kitty", "executable_load-snapshot.py",
)
_spec = importlib.util.spec_from_file_location("load_snapshot", _script_path)
load_snapshot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(load_snapshot)

parse_session_file = load_snapshot.parse_session_file


def _write_session(tmp_path, content):
    """Write session content to a temp file and return its path."""
    p = tmp_path / "test.conf"
    p.write_text(textwrap.dedent(content))
    return str(p)


# ===================================================================
# Tests for parse_session_file
# ===================================================================

class TestParseSessionFile:
    """Tests for parse_session_file(path)."""

    def test_basic_multi_tab(self, sample_session_file):
        """Parses a multi-tab session file into correct structure."""
        tabs, focus_idx = parse_session_file(sample_session_file)
        assert len(tabs) == 3
        assert tabs[0]["title"] == "dev"
        assert tabs[1]["title"] == "opencode"
        assert tabs[2]["title"] == "logs"
        assert focus_idx == 1

    def test_minimal_session(self, minimal_session_file):
        """Parses a minimal single-tab session file."""
        tabs, focus_idx = parse_session_file(minimal_session_file)
        assert len(tabs) == 1
        assert tabs[0]["title"] == "shell"
        assert tabs[0]["layout"] == "splits"
        assert focus_idx == 0

    def test_tab_layout_parsed(self, sample_session_file):
        """Tab layouts are correctly parsed."""
        tabs, _ = parse_session_file(sample_session_file)
        assert tabs[0]["layout"] == "splits"
        assert tabs[1]["layout"] == "stack"
        assert tabs[2]["layout"] == "splits"

    def test_pane_count(self, sample_session_file):
        """Each tab has the correct number of panes."""
        tabs, _ = parse_session_file(sample_session_file)
        assert len(tabs[0]["panes"]) == 2  # dev: shell + runserver
        assert len(tabs[1]["panes"]) == 1  # opencode
        assert len(tabs[2]["panes"]) == 1  # logs: shell

    def test_pane_cwd(self, sample_session_file):
        """Pane working directories are parsed correctly."""
        tabs, _ = parse_session_file(sample_session_file)
        assert tabs[0]["panes"][0]["cwd"] == "/Users/tis/repos/myproject"
        assert tabs[0]["panes"][1]["cwd"] == "/Users/tis/repos/myproject"
        assert tabs[2]["panes"][0]["cwd"] == "/var/log"

    def test_pane_cmd(self, sample_session_file):
        """Pane commands are parsed correctly."""
        tabs, _ = parse_session_file(sample_session_file)
        # First pane in dev tab — just a shell (no cmd after launch)
        assert tabs[0]["panes"][0]["cmd"] == []
        # Second pane in dev tab — runserver
        assert tabs[0]["panes"][1]["cmd"] == ["python3", "manage.py", "runserver"]
        # Opencode tab
        assert tabs[1]["panes"][0]["cmd"] == ["opencode"]
        # Logs tab — shell
        assert tabs[2]["panes"][0]["cmd"] == []

    def test_var_args_preserved(self, sample_session_file):
        """--var= arguments on launch lines are preserved."""
        tabs, _ = parse_session_file(sample_session_file)
        for tab in tabs:
            for pane in tab["panes"]:
                assert "--var=workspace=myproject" in pane["var_args"]

    def test_new_tab_without_title(self, tmp_path):
        """new_tab with no title defaults to 'tab'."""
        path = _write_session(tmp_path, """\
            new_tab
            layout splits
            cd /tmp
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert tabs[0]["title"] == "tab"

    def test_new_tab_with_title(self, tmp_path):
        """new_tab with explicit title uses that title."""
        path = _write_session(tmp_path, """\
            new_tab My Custom Title
            layout splits
            cd /tmp
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert tabs[0]["title"] == "My Custom Title"

    def test_cd_absolute_path(self, tmp_path):
        """cd with absolute path sets cwd directly."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /Users/tis/repos/project
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert tabs[0]["panes"][0]["cwd"] == "/Users/tis/repos/project"

    def test_cd_relative_path(self, tmp_path):
        """cd with relative path resolves against previous cwd."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /Users/tis/repos
            launch
            cd ../other
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert tabs[0]["panes"][0]["cwd"] == "/Users/tis/repos"
        assert tabs[0]["panes"][1]["cwd"] == "/Users/tis/other"

    def test_focus_tab_valid(self, tmp_path):
        """focus_tab with valid integer is parsed correctly."""
        path = _write_session(tmp_path, """\
            new_tab first
            cd /tmp
            launch
            new_tab second
            cd /tmp
            launch
            focus_tab 1
        """)
        _, focus_idx = parse_session_file(path)
        assert focus_idx == 1

    def test_focus_tab_missing_index(self, tmp_path):
        """focus_tab with no index defaults to 0."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /tmp
            launch
            focus_tab
        """)
        _, focus_idx = parse_session_file(path)
        assert focus_idx == 0  # default

    def test_focus_tab_invalid_index(self, tmp_path):
        """focus_tab with non-numeric index defaults to 0."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /tmp
            launch
            focus_tab abc
        """)
        _, focus_idx = parse_session_file(path)
        assert focus_idx == 0  # default

    def test_comments_and_blank_lines_ignored(self, tmp_path):
        """Comments (#) and blank lines are skipped."""
        path = _write_session(tmp_path, """\
            # This is a comment
            new_tab test
            layout splits

            # Another comment
            cd /tmp
            launch

            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert len(tabs) == 1
        assert tabs[0]["title"] == "test"

    def test_enabled_layouts_ignored(self, tmp_path):
        """enabled_layouts directive is skipped (handled separately)."""
        path = _write_session(tmp_path, """\
            new_tab test
            layout splits
            enabled_layouts splits,stack,tall
            cd /tmp
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert len(tabs) == 1
        # enabled_layouts should not affect the parsed tab
        assert tabs[0]["layout"] == "splits"

    def test_set_layout_state_ignored(self, tmp_path):
        """set_layout_state directive is skipped."""
        path = _write_session(tmp_path, """\
            new_tab test
            layout splits
            set_layout_state some_state_data
            cd /tmp
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert len(tabs) == 1

    def test_focus_directive_ignored(self, tmp_path):
        """Bare 'focus' directive is skipped."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /tmp
            launch
            focus
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert len(tabs) == 1

    def test_launch_before_new_tab_skipped(self, tmp_path):
        """launch before any new_tab is ignored."""
        path = _write_session(tmp_path, """\
            launch orphan_command
            new_tab test
            cd /tmp
            launch
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert len(tabs) == 1
        assert len(tabs[0]["panes"]) == 1

    def test_kitty_unserialize_data_skipped(self, tmp_path):
        """'kitty-unserialize-data=' arguments are filtered out."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /tmp
            launch --var=workspace=proj 'kitty-unserialize-data=some_data' mycommand arg1
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        pane = tabs[0]["panes"][0]
        assert pane["cmd"] == ["mycommand", "arg1"]
        assert "--var=workspace=proj" in pane["var_args"]

    def test_launch_with_unknown_flags_skipped(self, tmp_path):
        """Unknown --flags on launch are skipped."""
        path = _write_session(tmp_path, """\
            new_tab test
            cd /tmp
            launch --type=os-window --cwd=/tmp mycommand
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        pane = tabs[0]["panes"][0]
        assert pane["cmd"] == ["mycommand"]

    def test_empty_file(self, tmp_path):
        """Empty file returns empty tabs and focus_tab 0."""
        path = _write_session(tmp_path, "")
        tabs, focus_idx = parse_session_file(path)
        assert tabs == []
        assert focus_idx == 0

    def test_tab_with_no_panes(self, tmp_path):
        """Tab with no launch directives has empty panes list."""
        path = _write_session(tmp_path, """\
            new_tab empty
            layout splits
            cd /tmp
            focus_tab 0
        """)
        tabs, _ = parse_session_file(path)
        assert len(tabs) == 1
        assert tabs[0]["title"] == "empty"
        assert tabs[0]["panes"] == []
