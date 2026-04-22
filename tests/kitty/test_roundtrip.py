"""Round-trip tests: generate_session_file -> parse_session_file -> verify equivalence.

These tests verify that the serializer and deserializer are compatible:
what generate_session_file produces can be correctly consumed by parse_session_file,
and the result structurally matches the original input.
"""

import importlib.util
import os
import tempfile

import pytest

# Import both modules
_save_path = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    "private_dot_config", "kitty", "executable_save-workspace.py",
)
_save_spec = importlib.util.spec_from_file_location("save_workspace", _save_path)
save_workspace = importlib.util.module_from_spec(_save_spec)
_save_spec.loader.exec_module(save_workspace)

_load_path = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    "private_dot_config", "kitty", "executable_load-snapshot.py",
)
_load_spec = importlib.util.spec_from_file_location("load_snapshot", _load_path)
load_snapshot = importlib.util.module_from_spec(_load_spec)
_load_spec.loader.exec_module(load_snapshot)

generate_session_file = save_workspace.generate_session_file
parse_session_file = load_snapshot.parse_session_file


def _roundtrip(oswin, tmp_path):
    """Generate a session file from oswin, parse it back, return (tabs, focus_idx)."""
    content = generate_session_file(oswin)
    path = tmp_path / "roundtrip.conf"
    path.write_text(content)
    return parse_session_file(str(path)), content


class TestRoundTrip:
    """Verify generate -> parse round-trip preserves structure."""

    def test_tab_count_preserved(self, single_workspace_state, tmp_path):
        """Number of tabs survives round-trip."""
        oswin = single_workspace_state[0]
        (tabs, _), _ = _roundtrip(oswin, tmp_path)
        assert len(tabs) == len(oswin["tabs"])

    def test_tab_titles_preserved(self, single_workspace_state, tmp_path):
        """Tab titles survive round-trip."""
        oswin = single_workspace_state[0]
        (tabs, _), _ = _roundtrip(oswin, tmp_path)
        original_titles = [t["title"] for t in oswin["tabs"]]
        parsed_titles = [t["title"] for t in tabs]
        assert parsed_titles == original_titles

    def test_tab_layouts_preserved(self, complex_oswin, tmp_path):
        """Tab layouts survive round-trip."""
        (tabs, _), _ = _roundtrip(complex_oswin, tmp_path)
        original_layouts = [t["layout"] for t in complex_oswin["tabs"]]
        parsed_layouts = [t["layout"] for t in tabs]
        assert parsed_layouts == original_layouts

    def test_focus_tab_preserved(self, complex_oswin, tmp_path):
        """Active tab index survives round-trip."""
        (tabs, focus_idx), _ = _roundtrip(complex_oswin, tmp_path)
        # complex_oswin has tab at index 1 as active
        assert focus_idx == 1

    def test_pane_count_per_tab_preserved(self, complex_oswin, tmp_path):
        """Number of panes per tab survives round-trip."""
        (tabs, _), _ = _roundtrip(complex_oswin, tmp_path)
        original_pane_counts = [len(t["windows"]) for t in complex_oswin["tabs"]]
        parsed_pane_counts = [len(t["panes"]) for t in tabs]
        assert parsed_pane_counts == original_pane_counts

    def test_cwd_preserved(self, complex_oswin, tmp_path):
        """Working directories survive round-trip."""
        (tabs, _), _ = _roundtrip(complex_oswin, tmp_path)
        for orig_tab, parsed_tab in zip(complex_oswin["tabs"], tabs):
            for orig_win, parsed_pane in zip(orig_tab["windows"], parsed_tab["panes"]):
                assert parsed_pane["cwd"] == orig_win["cwd"]

    def test_fg_process_commands_preserved(self, complex_oswin, tmp_path):
        """Non-shell foreground processes survive round-trip as commands."""
        (tabs, _), _ = _roundtrip(complex_oswin, tmp_path)

        # Tab 0 (dev): pane 0 is shell (no cmd), pane 1 is python runserver
        assert tabs[0]["panes"][0]["cmd"] == []
        assert tabs[0]["panes"][1]["cmd"] == ["python3", "manage.py", "runserver"]

        # Tab 1 (opencode): pane 0 is opencode
        assert tabs[1]["panes"][0]["cmd"] == ["opencode"]

        # Tab 2 (logs): pane 0 is shell (no cmd)
        assert tabs[2]["panes"][0]["cmd"] == []

    def test_workspace_var_preserved(self, complex_oswin, tmp_path):
        """Workspace user var survives round-trip as --var= arg."""
        (tabs, _), _ = _roundtrip(complex_oswin, tmp_path)
        for tab in tabs:
            for pane in tab["panes"]:
                assert "--var=workspace=myproject" in pane["var_args"]

    def test_simple_workspace_roundtrip(self, single_workspace_state, tmp_path):
        """Full round-trip for a simple 2-tab workspace."""
        oswin = single_workspace_state[0]
        (tabs, focus_idx), content = _roundtrip(oswin, tmp_path)

        assert len(tabs) == 2
        assert tabs[0]["title"] == "shell"
        assert tabs[1]["title"] == "opencode"
        assert focus_idx == 0

        # Shell tab: one pane, no command
        assert len(tabs[0]["panes"]) == 1
        assert tabs[0]["panes"][0]["cmd"] == []

        # Opencode tab: one pane, opencode command
        assert len(tabs[1]["panes"]) == 1
        assert tabs[1]["panes"][0]["cmd"] == ["opencode"]

    def test_empty_oswin_roundtrip(self, tmp_path):
        """Empty OS window (no tabs) round-trips cleanly."""
        oswin = {"id": 1, "tabs": []}
        (tabs, focus_idx), _ = _roundtrip(oswin, tmp_path)
        assert tabs == []
        assert focus_idx == 0

    def test_multiple_user_vars_roundtrip(self, tmp_path):
        """Multiple user vars survive round-trip."""
        from tests.kitty.conftest import _make_window, _make_tab, _make_oswin

        win = _make_window(
            win_id=1, cwd="/tmp",
            user_vars={"workspace": "proj", "role": "dev"},
        )
        tab = _make_tab(10, "mytab", [win], is_active=True)
        oswin = _make_oswin(1, [tab], is_focused=True)

        (tabs, _), _ = _roundtrip(oswin, tmp_path)
        var_args = tabs[0]["panes"][0]["var_args"]
        assert "--var=workspace=proj" in var_args
        assert "--var=role=dev" in var_args

    def test_generated_content_is_valid_session_format(self, complex_oswin, tmp_path):
        """The generated content follows kitty session file format conventions."""
        content = generate_session_file(complex_oswin)
        lines = [l for l in content.split("\n") if l.strip()]

        # Must start with new_tab
        assert lines[0].startswith("new_tab")
        # Must end with focus_tab
        assert lines[-1].startswith("focus_tab")

        # Every tab block must have: new_tab, layout, enabled_layouts, cd, launch
        in_tab = False
        for line in lines:
            if line.startswith("new_tab"):
                in_tab = True
            elif line.startswith("focus_tab"):
                in_tab = False
