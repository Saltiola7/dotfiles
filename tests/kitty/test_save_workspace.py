"""Tests for save-workspace.py: find_active_workspace and generate_session_file."""

import importlib.util
import os
import sys

import pytest

# Import from the chezmoi source file (non-standard filename)
_script_path = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    "private_dot_config", "kitty", "executable_save-workspace.py",
)
_spec = importlib.util.spec_from_file_location("save_workspace", _script_path)
save_workspace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(save_workspace)

find_active_workspace = save_workspace.find_active_workspace
generate_session_file = save_workspace.generate_session_file


# ===================================================================
# Tests for find_active_workspace
# ===================================================================

class TestFindActiveWorkspace:
    """Tests for find_active_workspace(state)."""

    def test_single_focused_workspace(self, single_workspace_state):
        """Returns workspace name and oswin when focused window has workspace var."""
        name, oswin = find_active_workspace(single_workspace_state)
        assert name == "myproject"
        assert oswin is not None
        assert oswin["id"] == 1

    def test_multi_workspace_returns_focused(self, multi_workspace_state):
        """With multiple OS windows, returns the focused one's workspace."""
        name, oswin = find_active_workspace(multi_workspace_state)
        assert name == "myproject"
        assert oswin["id"] == 1

    def test_no_workspace_var(self, no_workspace_state):
        """Returns (None, None) when no window has a workspace user var."""
        name, oswin = find_active_workspace(no_workspace_state)
        assert name is None
        assert oswin is None

    def test_no_focused_window(self, no_focus_state):
        """Returns (None, None) when no OS window is focused."""
        name, oswin = find_active_workspace(no_focus_state)
        assert name is None
        assert oswin is None

    def test_empty_state(self):
        """Returns (None, None) for empty state list."""
        name, oswin = find_active_workspace([])
        assert name is None
        assert oswin is None

    def test_focused_but_workspace_on_unfocused_tab(self):
        """Workspace var is only on a window in a non-active tab — should still find it."""
        from tests.kitty.conftest import _make_window, _make_tab, _make_oswin

        # Tab 1: no workspace var (active)
        plain_win = _make_window(win_id=1, cwd="/tmp")
        tab1 = _make_tab(10, "plain", [plain_win], is_active=True)

        # Tab 2: has workspace var (not active)
        ws_win = _make_window(
            win_id=2, cwd="/Users/tis/repos/proj",
            user_vars={"workspace": "proj"},
        )
        tab2 = _make_tab(11, "proj", [ws_win], is_active=False)

        oswin = _make_oswin(1, [tab1, tab2], is_focused=True)
        name, result_oswin = find_active_workspace([oswin])
        assert name == "proj"
        assert result_oswin["id"] == 1


# ===================================================================
# Tests for generate_session_file
# ===================================================================

class TestGenerateSessionFile:
    """Tests for generate_session_file(oswin)."""

    def test_basic_two_tab_workspace(self, single_workspace_state):
        """Generates valid session file for a simple 2-tab workspace."""
        oswin = single_workspace_state[0]
        content = generate_session_file(oswin)

        lines = content.split("\n")
        # Should have two new_tab directives
        new_tabs = [l for l in lines if l.startswith("new_tab")]
        assert len(new_tabs) == 2
        assert new_tabs[0] == "new_tab shell"
        assert new_tabs[1] == "new_tab opencode"

        # Should have focus_tab pointing to the active tab (index 0)
        assert "focus_tab 0" in lines

    def test_active_tab_tracking(self, complex_oswin):
        """Active tab index is correctly recorded in focus_tab."""
        content = generate_session_file(complex_oswin)
        lines = content.split("\n")
        # Tab at index 1 (opencode) is active
        assert "focus_tab 1" in lines

    def test_shell_process_not_serialized(self, single_workspace_state):
        """Shell-only windows get `launch` with no command (shell starts by default)."""
        oswin = single_workspace_state[0]
        content = generate_session_file(oswin)
        lines = content.split("\n")

        # First tab's shell pane should just have `launch --var=workspace=myproject`
        # (no command after the var args since fg is just bash)
        launch_lines = [l for l in lines if l.startswith("launch")]
        assert any("launch --var=workspace=myproject" == l.strip()
                    for l in launch_lines), \
            f"Expected a plain 'launch --var=workspace=myproject' but got: {launch_lines}"

    def test_fg_process_serialized(self, single_workspace_state):
        """Non-shell foreground processes are serialized in the launch command."""
        oswin = single_workspace_state[0]
        content = generate_session_file(oswin)
        lines = content.split("\n")

        launch_lines = [l for l in lines if l.startswith("launch")]
        assert any("opencode" in l for l in launch_lines), \
            f"Expected 'opencode' in a launch line but got: {launch_lines}"

    def test_complex_multi_tab(self, complex_oswin):
        """Multi-tab workspace with mixed processes generates correct structure."""
        content = generate_session_file(complex_oswin)
        lines = content.split("\n")

        new_tabs = [l for l in lines if l.startswith("new_tab")]
        assert len(new_tabs) == 3
        assert new_tabs[0] == "new_tab dev"
        assert new_tabs[1] == "new_tab opencode"
        assert new_tabs[2] == "new_tab logs"

        # Dev tab has 2 panes: shell (no cmd) and python runserver
        launch_lines = [l for l in lines if l.startswith("launch")]
        assert any("python3 manage.py runserver" in l for l in launch_lines)

    def test_user_vars_preserved(self, single_workspace_state):
        """User vars are included as --var= arguments on launch."""
        oswin = single_workspace_state[0]
        content = generate_session_file(oswin)
        assert "--var=workspace=myproject" in content

    def test_enabled_layouts_as_list(self, complex_oswin):
        """enabled_layouts as a list gets joined into comma-separated string."""
        content = generate_session_file(complex_oswin)
        assert "enabled_layouts splits,stack" in content

    def test_enabled_layouts_as_string(self, complex_oswin):
        """enabled_layouts already as string is passed through directly."""
        content = generate_session_file(complex_oswin)
        # The opencode tab has enabled_layouts="stack"
        lines = content.split("\n")
        # Find the enabled_layouts line after "new_tab opencode"
        found_oc = False
        for line in lines:
            if line == "new_tab opencode":
                found_oc = True
            elif found_oc and line.startswith("enabled_layouts"):
                assert line == "enabled_layouts stack"
                break
        else:
            if found_oc:
                pytest.fail("No enabled_layouts found after 'new_tab opencode'")

    def test_cwd_preserved(self, complex_oswin):
        """Working directories are preserved for each pane."""
        content = generate_session_file(complex_oswin)
        assert "cd /Users/tis/repos/myproject" in content
        assert "cd /var/log" in content

    def test_empty_fg_procs(self, empty_fg_procs_oswin):
        """Window with empty foreground_processes generates launch with no command."""
        content = generate_session_file(empty_fg_procs_oswin)
        lines = content.split("\n")
        launch_lines = [l for l in lines if l.startswith("launch")]
        assert len(launch_lines) == 1
        assert launch_lines[0] == "launch --var=workspace=myproject"

    def test_layout_preserved(self, complex_oswin):
        """Tab layout type is preserved in the session file."""
        content = generate_session_file(complex_oswin)
        lines = content.split("\n")
        layout_lines = [l for l in lines if l.startswith("layout ")]
        assert "layout splits" in layout_lines
        assert "layout stack" in layout_lines

    def test_empty_oswin(self):
        """OS window with no tabs generates just focus_tab 0."""
        oswin = {"id": 1, "tabs": []}
        content = generate_session_file(oswin)
        assert content.strip() == "focus_tab 0"

    def test_multiple_user_vars(self):
        """Multiple user vars are all serialized."""
        from tests.kitty.conftest import _make_window, _make_tab, _make_oswin

        win = _make_window(
            win_id=1, cwd="/tmp",
            user_vars={"workspace": "proj", "role": "dev"},
        )
        tab = _make_tab(10, "mytab", [win], is_active=True)
        oswin = _make_oswin(1, [tab], is_focused=True)

        content = generate_session_file(oswin)
        assert "--var=workspace=proj" in content
        assert "--var=role=dev" in content
