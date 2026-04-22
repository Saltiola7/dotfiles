"""Comprehensive tests for kitty-query.py — unit tests + CLI integration tests.

Tests cover:
    - Pure functions (JSON traversal, map file parsing, session queries, etc.)
    - Typer CLI subcommands via CliRunner
"""

import importlib.util
import json
import os
import sqlite3
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# ── Import the module under test ──────────────────────────────────────────

_MODULE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "private_dot_config"
    / "kitty"
    / "executable_kitty-query.py"
)

spec = importlib.util.spec_from_file_location("kitty_query", str(_MODULE_PATH))
assert spec and spec.loader
kitty_query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kitty_query)

# Expose the typer app and all functions
app = kitty_query.app
find_oswin_by_workspace = kitty_query.find_oswin_by_workspace
find_win_by_workspace = kitty_query.find_win_by_workspace
detect_workspace_by_win = kitty_query.detect_workspace_by_win
list_all_win_ids = kitty_query.list_all_win_ids
parse_extra_tabs = kitty_query.parse_extra_tabs
find_socket = kitty_query.find_socket
parse_map_file = kitty_query.parse_map_file
compute_stale_bindings = kitty_query.compute_stale_bindings
write_map_file = kitty_query.write_map_file
get_bound_session_ids = kitty_query.get_bound_session_ids
query_sessions = kitty_query.query_sessions
session_exists = kitty_query.session_exists
consume_seed = kitty_query.consume_seed
debug_log = kitty_query.debug_log
detect_active_opencode_pids = kitty_query.detect_active_opencode_pids
find_active_session_id = kitty_query.find_active_session_id
find_unbound_session_id = kitty_query.find_unbound_session_id

runner = CliRunner()


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def single_workspace():
    """Single OS window with workspace 'myproject', 2 tabs."""
    return [
        {
            "id": 1,
            "tabs": [
                {
                    "id": 10,
                    "title": "shell",
                    "windows": [
                        {
                            "id": 100,
                            "user_vars": {"workspace": "myproject"},
                            "cwd": "/home/user/myproject",
                        }
                    ],
                },
                {
                    "id": 11,
                    "title": "opencode",
                    "windows": [
                        {
                            "id": 101,
                            "user_vars": {"workspace": "myproject"},
                            "cwd": "/home/user/myproject",
                        }
                    ],
                },
            ],
        }
    ]


@pytest.fixture
def multi_workspace():
    """Two OS windows: 'myproject' and 'dotfiles'."""
    return [
        {
            "id": 1,
            "tabs": [
                {
                    "id": 10,
                    "title": "shell",
                    "windows": [
                        {
                            "id": 100,
                            "user_vars": {"workspace": "myproject"},
                            "cwd": "/home/user/myproject",
                        }
                    ],
                },
            ],
        },
        {
            "id": 2,
            "tabs": [
                {
                    "id": 20,
                    "title": "shell",
                    "windows": [
                        {
                            "id": 200,
                            "user_vars": {"workspace": "dotfiles"},
                            "cwd": "/home/user/dotfiles",
                        },
                        {
                            "id": 201,
                            "user_vars": {},
                            "cwd": "/home/user/dotfiles",
                        },
                    ],
                },
            ],
        },
    ]


@pytest.fixture
def no_workspace():
    """OS window with no workspace user var."""
    return [
        {
            "id": 1,
            "tabs": [
                {
                    "id": 10,
                    "title": "tab",
                    "windows": [
                        {"id": 100, "user_vars": {}, "cwd": "/tmp"}
                    ],
                }
            ],
        }
    ]


@pytest.fixture
def empty_state():
    """Empty kitty state."""
    return []


@pytest.fixture
def sample_snapshot(tmp_path):
    """Snapshot file with base + extra tabs."""
    content = textwrap.dedent("""\
        new_tab shell
        cd /home/user/myproject
        launch --var=workspace=myproject

        new_tab opencode
        cd /home/user/myproject
        launch --var=workspace=myproject opencode

        new_tab logs
        cd /var/log
        launch --var=workspace=myproject tail -f syslog

        new_tab monitoring
        cd /home/user/monitoring
        launch --var=workspace=myproject htop
    """)
    p = tmp_path / "myproject.snapshot.conf"
    p.write_text(content)
    return str(p)


@pytest.fixture
def snapshot_with_unserialize(tmp_path):
    """Snapshot with kitty-unserialize-data tokens."""
    content = textwrap.dedent("""\
        new_tab extra
        cd /home/user/extra
        launch --var=workspace=myproject 'kitty-unserialize-data=abc' bash
    """)
    p = tmp_path / "unserialize.snapshot.conf"
    p.write_text(content)
    return str(p)


@pytest.fixture
def map_file(tmp_path):
    """Map file with bindings."""
    content = "100=session-aaa\n101=session-bbb\n200=session-ccc\n"
    p = tmp_path / "myproject.map"
    p.write_text(content)
    return str(p)


@pytest.fixture
def map_file_with_comments(tmp_path):
    """Map file with comments and blank lines."""
    content = "# comment\n\n100=session-aaa\n# another comment\n101=session-bbb\n"
    p = tmp_path / "myproject.map"
    p.write_text(content)
    return str(p)


@pytest.fixture
def opencode_db(tmp_path):
    """Create a test opencode database with sessions."""
    db_path = tmp_path / "opencode.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT NOT NULL
        );
        CREATE TABLE session (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            time_updated TEXT NOT NULL,
            time_archived TEXT,
            parent_id TEXT,
            FOREIGN KEY (project_id) REFERENCES project(id)
        );

        INSERT INTO project (id, worktree) VALUES ('proj1', '/home/user/myproject');
        INSERT INTO project (id, worktree) VALUES ('proj2', '/home/user/other');

        INSERT INTO session (id, project_id, time_updated, time_archived, parent_id)
        VALUES ('sess-1', 'proj1', '2026-01-01 10:00:00', NULL, NULL);
        INSERT INTO session (id, project_id, time_updated, time_archived, parent_id)
        VALUES ('sess-2', 'proj1', '2026-01-01 11:00:00', NULL, NULL);
        INSERT INTO session (id, project_id, time_updated, time_archived, parent_id)
        VALUES ('sess-3', 'proj1', '2026-01-01 12:00:00', NULL, NULL);
        INSERT INTO session (id, project_id, time_updated, time_archived, parent_id)
        VALUES ('sess-archived', 'proj1', '2026-01-01 09:00:00', '2026-01-02 00:00:00', NULL);
        INSERT INTO session (id, project_id, time_updated, time_archived, parent_id)
        VALUES ('sess-child', 'proj1', '2026-01-01 13:00:00', NULL, 'sess-1');
        INSERT INTO session (id, project_id, time_updated, time_archived, parent_id)
        VALUES ('sess-other', 'proj2', '2026-01-01 14:00:00', NULL, NULL);
    """
    )
    conn.close()
    return str(db_path)


@pytest.fixture
def seed_file(tmp_path):
    """Seed file with session IDs."""
    content = "sess-1\nsess-2\nsess-3\n"
    p = tmp_path / "myproject.seed"
    p.write_text(content)
    return str(p)


# ═══════════════════════════════════════════════════════════════════════════
# Unit tests: pure functions
# ═══════════════════════════════════════════════════════════════════════════


class TestFindOswinByWorkspace:
    def test_finds_matching_workspace(self, single_workspace):
        assert find_oswin_by_workspace(single_workspace, "myproject") == 1

    def test_returns_none_for_missing(self, single_workspace):
        assert find_oswin_by_workspace(single_workspace, "nonexistent") is None

    def test_finds_correct_oswin_multi(self, multi_workspace):
        assert find_oswin_by_workspace(multi_workspace, "dotfiles") == 2

    def test_returns_first_match(self, multi_workspace):
        assert find_oswin_by_workspace(multi_workspace, "myproject") == 1

    def test_empty_state(self, empty_state):
        assert find_oswin_by_workspace(empty_state, "any") is None

    def test_no_workspace_var(self, no_workspace):
        assert find_oswin_by_workspace(no_workspace, "myproject") is None

    def test_empty_user_vars(self):
        state = [{"id": 1, "tabs": [{"windows": [{"id": 1, "user_vars": {}}]}]}]
        assert find_oswin_by_workspace(state, "x") is None

    def test_missing_user_vars_key(self):
        state = [{"id": 1, "tabs": [{"windows": [{"id": 1}]}]}]
        assert find_oswin_by_workspace(state, "x") is None


class TestFindWinByWorkspace:
    def test_finds_first_window(self, single_workspace):
        assert find_win_by_workspace(single_workspace, "myproject") == 100

    def test_returns_none_for_missing(self, single_workspace):
        assert find_win_by_workspace(single_workspace, "nonexistent") is None

    def test_finds_in_correct_oswin(self, multi_workspace):
        assert find_win_by_workspace(multi_workspace, "dotfiles") == 200

    def test_empty_state(self, empty_state):
        assert find_win_by_workspace(empty_state, "any") is None

    def test_no_workspace_var(self, no_workspace):
        assert find_win_by_workspace(no_workspace, "myproject") is None


class TestDetectWorkspaceByWin:
    def test_finds_workspace_by_window_id(self, single_workspace):
        assert detect_workspace_by_win(single_workspace, 100) == "myproject"

    def test_finds_workspace_from_sibling(self, single_workspace):
        # Window 101 is in the same OS window, should find workspace from win 100
        assert detect_workspace_by_win(single_workspace, 101) == "myproject"

    def test_finds_in_multi_workspace(self, multi_workspace):
        # Window 200 is in dotfiles OS window
        assert detect_workspace_by_win(multi_workspace, 200) == "dotfiles"

    def test_window_without_workspace_in_workspace_oswin(self, multi_workspace):
        # Window 201 has no workspace var but is in dotfiles OS window
        assert detect_workspace_by_win(multi_workspace, 201) == "dotfiles"

    def test_unknown_window_id(self, single_workspace):
        assert detect_workspace_by_win(single_workspace, 999) is None

    def test_empty_state(self, empty_state):
        assert detect_workspace_by_win(empty_state, 1) is None

    def test_no_workspace_var_anywhere(self, no_workspace):
        assert detect_workspace_by_win(no_workspace, 100) is None

    def test_does_not_cross_oswin_boundary(self, multi_workspace):
        # Window 100 is in oswin 1 (myproject), shouldn't find dotfiles
        assert detect_workspace_by_win(multi_workspace, 100) == "myproject"


class TestListAllWinIds:
    def test_single_workspace(self, single_workspace):
        assert sorted(list_all_win_ids(single_workspace)) == [100, 101]

    def test_multi_workspace(self, multi_workspace):
        assert sorted(list_all_win_ids(multi_workspace)) == [100, 200, 201]

    def test_empty_state(self, empty_state):
        assert list_all_win_ids(empty_state) == []

    def test_no_windows(self):
        state = [{"id": 1, "tabs": [{"windows": []}]}]
        assert list_all_win_ids(state) == []


class TestParseExtraTabs:
    def test_filters_base_tabs(self, sample_snapshot):
        tabs = parse_extra_tabs(sample_snapshot, ["shell", "opencode"])
        titles = [t["title"] for t in tabs]
        assert "shell" not in titles
        assert "opencode" not in titles
        assert "logs" in titles
        assert "monitoring" in titles

    def test_extra_tab_cwd(self, sample_snapshot):
        tabs = parse_extra_tabs(sample_snapshot, ["shell", "opencode"])
        logs_tab = next(t for t in tabs if t["title"] == "logs")
        assert logs_tab["cwd"] == "/var/log"

    def test_extra_tab_cmd(self, sample_snapshot):
        tabs = parse_extra_tabs(sample_snapshot, ["shell", "opencode"])
        logs_tab = next(t for t in tabs if t["title"] == "logs")
        assert "tail" in logs_tab["cmd"]
        assert "-f" in logs_tab["cmd"]

    def test_case_insensitive_base_match(self, sample_snapshot):
        tabs = parse_extra_tabs(sample_snapshot, ["Shell", "OpenCode"])
        titles = [t["title"] for t in tabs]
        assert "shell" not in titles
        assert "opencode" not in titles

    def test_no_base_tabs_returns_all(self, sample_snapshot):
        tabs = parse_extra_tabs(sample_snapshot, [])
        assert len(tabs) == 4

    def test_all_base_tabs_returns_empty(self, sample_snapshot):
        tabs = parse_extra_tabs(
            sample_snapshot, ["shell", "opencode", "logs", "monitoring"]
        )
        assert tabs == []

    def test_strips_flags_from_launch(self, sample_snapshot):
        tabs = parse_extra_tabs(sample_snapshot, ["shell", "opencode"])
        for tab in tabs:
            assert "--var" not in tab["cmd"]

    def test_strips_unserialize_data(self, snapshot_with_unserialize):
        tabs = parse_extra_tabs(snapshot_with_unserialize, [])
        assert len(tabs) == 1
        assert "kitty-unserialize-data" not in tabs[0]["cmd"]
        assert "bash" in tabs[0]["cmd"]

    def test_missing_cwd_defaults_home(self, tmp_path):
        content = "new_tab extra\nlaunch bash\n"
        p = tmp_path / "nocwd.conf"
        p.write_text(content)
        tabs = parse_extra_tabs(str(p), [])
        assert tabs[0]["cwd"] == os.path.expanduser("~")

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_extra_tabs(str(tmp_path / "nonexistent.conf"), [])

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.conf"
        p.write_text("")
        assert parse_extra_tabs(str(p), []) == []


class TestFindSocket:
    def test_finds_existing_socket(self, tmp_path):
        socket_dir = tmp_path / ".local" / "share" / "kitty"
        socket_dir.mkdir(parents=True)
        sock = socket_dir / "control-socket-12345"
        sock.touch()
        glob_pattern = str(socket_dir / "control-socket-*")
        with patch.object(kitty_query, "SOCKET_GLOB", glob_pattern):
            result = find_socket()
            assert result == str(sock)

    def test_returns_none_when_no_socket(self, tmp_path):
        glob_pattern = str(tmp_path / "nonexistent-*")
        with patch.object(kitty_query, "SOCKET_GLOB", glob_pattern):
            result = find_socket()
            assert result is None

    def test_returns_first_sorted(self, tmp_path):
        socket_dir = tmp_path / ".local" / "share" / "kitty"
        socket_dir.mkdir(parents=True)
        (socket_dir / "control-socket-999").touch()
        (socket_dir / "control-socket-100").touch()
        glob_pattern = str(socket_dir / "control-socket-*")
        with patch.object(kitty_query, "SOCKET_GLOB", glob_pattern):
            result = find_socket()
            assert result == str(socket_dir / "control-socket-100")


class TestParseMapFile:
    def test_parses_bindings(self, map_file):
        bindings = parse_map_file(map_file)
        assert bindings == {
            "100": "session-aaa",
            "101": "session-bbb",
            "200": "session-ccc",
        }

    def test_skips_comments(self, map_file_with_comments):
        bindings = parse_map_file(map_file_with_comments)
        assert bindings == {"100": "session-aaa", "101": "session-bbb"}

    def test_nonexistent_file(self, tmp_path):
        bindings = parse_map_file(tmp_path / "nonexistent.map")
        assert bindings == {}

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.map"
        p.write_text("")
        assert parse_map_file(p) == {}

    def test_preserves_session_id_with_special_chars(self, tmp_path):
        p = tmp_path / "test.map"
        p.write_text("42=01JHG9ABC-DEF_xyz\n")
        bindings = parse_map_file(p)
        assert bindings["42"] == "01JHG9ABC-DEF_xyz"


class TestComputeStaleBindings:
    def test_all_live(self):
        bindings = {"100": "sess-a", "200": "sess-b"}
        live, stale = compute_stale_bindings(bindings, [100, 200])
        assert live == bindings
        assert stale == {}

    def test_all_stale(self):
        bindings = {"100": "sess-a", "200": "sess-b"}
        live, stale = compute_stale_bindings(bindings, [300])
        assert live == {}
        assert stale == bindings

    def test_mixed(self):
        bindings = {"100": "sess-a", "200": "sess-b", "300": "sess-c"}
        live, stale = compute_stale_bindings(bindings, [100, 300])
        assert live == {"100": "sess-a", "300": "sess-c"}
        assert stale == {"200": "sess-b"}

    def test_empty_bindings(self):
        live, stale = compute_stale_bindings({}, [100])
        assert live == {}
        assert stale == {}

    def test_empty_live_ids(self):
        bindings = {"100": "sess-a"}
        live, stale = compute_stale_bindings(bindings, [])
        assert live == {}
        assert stale == bindings


class TestWriteMapFile:
    def test_writes_bindings(self, tmp_path):
        p = tmp_path / "test.map"
        write_map_file(p, {"100": "sess-a", "200": "sess-b"})
        content = p.read_text()
        assert "100=sess-a" in content
        assert "200=sess-b" in content

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "deep" / "nested" / "test.map"
        write_map_file(p, {"1": "a"})
        assert p.exists()

    def test_empty_bindings_writes_empty(self, tmp_path):
        p = tmp_path / "test.map"
        write_map_file(p, {})
        assert p.read_text() == ""

    def test_roundtrip(self, tmp_path):
        p = tmp_path / "test.map"
        original = {"100": "sess-a", "200": "sess-b"}
        write_map_file(p, original)
        parsed = parse_map_file(p)
        assert parsed == original


class TestGetBoundSessionIds:
    def test_returns_values(self, map_file):
        ids = get_bound_session_ids(map_file)
        assert sorted(ids) == ["session-aaa", "session-bbb", "session-ccc"]

    def test_nonexistent_file(self, tmp_path):
        ids = get_bound_session_ids(tmp_path / "nope.map")
        assert ids == []


class TestQuerySessions:
    def test_returns_most_recent(self, opencode_db):
        results = query_sessions(opencode_db, "/home/user/myproject")
        assert results == ["sess-3"]

    def test_limit(self, opencode_db):
        results = query_sessions(opencode_db, "/home/user/myproject", limit=2)
        assert results == ["sess-3", "sess-2"]

    def test_excludes_archived(self, opencode_db):
        results = query_sessions(opencode_db, "/home/user/myproject", limit=10)
        assert "sess-archived" not in results

    def test_excludes_child_sessions(self, opencode_db):
        results = query_sessions(opencode_db, "/home/user/myproject", limit=10)
        assert "sess-child" not in results

    def test_exclude_ids(self, opencode_db):
        results = query_sessions(
            opencode_db,
            "/home/user/myproject",
            exclude_ids=["sess-3"],
            limit=1,
        )
        assert results == ["sess-2"]

    def test_only_ids(self, opencode_db):
        results = query_sessions(
            opencode_db,
            "/home/user/myproject",
            only_ids=["sess-1"],
            limit=1,
        )
        assert results == ["sess-1"]

    def test_only_ids_empty_list(self, opencode_db):
        results = query_sessions(
            opencode_db,
            "/home/user/myproject",
            only_ids=[],
        )
        assert results == []

    def test_wrong_project(self, opencode_db):
        results = query_sessions(opencode_db, "/home/user/nonexistent")
        assert results == []

    def test_other_project(self, opencode_db):
        results = query_sessions(opencode_db, "/home/user/other")
        assert results == ["sess-other"]

    def test_nonexistent_db(self, tmp_path):
        results = query_sessions(str(tmp_path / "nope.db"), "/any")
        assert results == []

    def test_exclude_and_only_combined(self, opencode_db):
        results = query_sessions(
            opencode_db,
            "/home/user/myproject",
            exclude_ids=["sess-2"],
            only_ids=["sess-1", "sess-2", "sess-3"],
            limit=10,
        )
        assert "sess-2" not in results
        assert "sess-3" in results


class TestSessionExists:
    def test_active_session(self, opencode_db):
        assert session_exists(opencode_db, "sess-1") is True

    def test_archived_session(self, opencode_db):
        assert session_exists(opencode_db, "sess-archived") is False

    def test_nonexistent_session(self, opencode_db):
        assert session_exists(opencode_db, "nonexistent") is False

    def test_nonexistent_db(self, tmp_path):
        assert session_exists(str(tmp_path / "nope.db"), "sess-1") is False


class TestConsumeSeed:
    def test_removes_session(self, seed_file):
        consume_seed(seed_file, "sess-2")
        remaining = Path(seed_file).read_text().strip().splitlines()
        assert "sess-2" not in remaining
        assert "sess-1" in remaining
        assert "sess-3" in remaining

    def test_removes_only_exact_match(self, tmp_path):
        p = tmp_path / "test.seed"
        p.write_text("sess-1\nsess-10\nsess-100\n")
        consume_seed(str(p), "sess-1")
        remaining = p.read_text().strip().splitlines()
        assert "sess-1" not in remaining
        assert "sess-10" in remaining
        assert "sess-100" in remaining

    def test_nonexistent_file(self, tmp_path):
        # Should not raise
        consume_seed(str(tmp_path / "nonexistent.seed"), "sess-1")

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.seed"
        p.write_text("")
        consume_seed(str(p), "sess-1")
        assert p.read_text() == ""


class TestDetectActiveOpencodePids:
    def test_no_opencode_processes(self):
        with patch.object(kitty_query, "local") as mock_local:
            mock_ps = mock_local.__getitem__.return_value
            mock_ps.return_value = "  PID COMMAND\n  123 bash\n"
            result = detect_active_opencode_pids("/home/user/project")
            assert result == []

    def test_handles_ps_failure(self):
        with patch.object(kitty_query, "local") as mock_local:
            mock_local.__getitem__.side_effect = Exception("ps not found")
            result = detect_active_opencode_pids("/home/user/project")
            assert result == []


class TestFindActiveSessionId:
    def test_no_active_processes(self, opencode_db):
        with patch.object(
            kitty_query, "detect_active_opencode_pids", return_value=[]
        ):
            result = find_active_session_id(opencode_db, "/home/user/myproject")
            assert result is None

    def test_active_process_returns_latest(self, opencode_db):
        with patch.object(
            kitty_query, "detect_active_opencode_pids", return_value=[12345]
        ):
            result = find_active_session_id(opencode_db, "/home/user/myproject")
            assert result == "sess-3"


class TestFindUnboundSessionId:
    def test_finds_unbound_session(self, opencode_db, tmp_path):
        map_path = tmp_path / "test.map"
        map_path.write_text("100=sess-3\n")
        with patch.object(
            kitty_query, "detect_active_opencode_pids", return_value=[]
        ):
            result = find_unbound_session_id(
                opencode_db, "/home/user/myproject", str(map_path), "myproject"
            )
            # sess-3 is bound, so should return sess-2
            assert result == "sess-2"

    def test_no_sessions_available(self, opencode_db, tmp_path):
        map_path = tmp_path / "test.map"
        map_path.write_text("100=sess-1\n200=sess-2\n300=sess-3\n")
        with patch.object(
            kitty_query, "detect_active_opencode_pids", return_value=[]
        ):
            result = find_unbound_session_id(
                opencode_db, "/home/user/myproject", str(map_path), "myproject"
            )
            assert result is None

    def test_uses_seed_file(self, opencode_db, tmp_path):
        map_path = tmp_path / "test.map"
        map_path.write_text("")
        seed_path = tmp_path / "myproject.seed"
        seed_path.write_text("sess-1\n")
        with (
            patch.object(
                kitty_query, "detect_active_opencode_pids", return_value=[]
            ),
            patch.object(kitty_query, "OC_STORAGE", tmp_path),
        ):
            result = find_unbound_session_id(
                opencode_db, "/home/user/myproject", str(map_path), "myproject"
            )
            assert result == "sess-1"
            # Seed should be consumed
            remaining = seed_path.read_text().strip()
            assert "sess-1" not in remaining

    def test_excludes_active_session(self, opencode_db, tmp_path):
        map_path = tmp_path / "test.map"
        map_path.write_text("")
        with patch.object(
            kitty_query, "detect_active_opencode_pids", return_value=[12345]
        ):
            result = find_unbound_session_id(
                opencode_db, "/home/user/myproject", str(map_path), "myproject"
            )
            # sess-3 is active (most recent), should be excluded
            # Should return sess-2 instead
            assert result == "sess-2"


class TestDebugLog:
    def test_writes_when_debug_enabled(self, tmp_path):
        log_file = tmp_path / "test.log"
        with (
            patch.dict(os.environ, {"KITTY_WORKSPACE_DEBUG": "1"}),
            patch.object(kitty_query, "LOG_FILE", log_file),
        ):
            debug_log("test message", "test-script")
            content = log_file.read_text()
            assert "test-script: test message" in content

    def test_skips_when_debug_disabled(self, tmp_path):
        log_file = tmp_path / "test.log"
        with (
            patch.dict(os.environ, {"KITTY_WORKSPACE_DEBUG": "0"}, clear=False),
            patch.object(kitty_query, "LOG_FILE", log_file),
        ):
            debug_log("test message")
            assert not log_file.exists()

    def test_skips_when_debug_unset(self, tmp_path):
        log_file = tmp_path / "test.log"
        env = os.environ.copy()
        env.pop("KITTY_WORKSPACE_DEBUG", None)
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(kitty_query, "LOG_FILE", log_file),
        ):
            debug_log("test message")
            assert not log_file.exists()


# ═══════════════════════════════════════════════════════════════════════════
# CLI integration tests (via typer CliRunner)
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIFindOswin:
    def test_finds_workspace(self, single_workspace):
        result = runner.invoke(
            app, ["find-oswin", "myproject"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_missing_workspace_exits_1(self, single_workspace):
        result = runner.invoke(
            app, ["find-oswin", "nonexistent"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 1

    def test_invalid_json_exits_1(self):
        result = runner.invoke(app, ["find-oswin", "x"], input="not json")
        assert result.exit_code == 1


class TestCLIFindWin:
    def test_finds_window(self, single_workspace):
        result = runner.invoke(
            app, ["find-win", "myproject"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 0
        assert result.output.strip() == "100"

    def test_missing_workspace_exits_1(self, single_workspace):
        result = runner.invoke(
            app, ["find-win", "nonexistent"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 1


class TestCLIDetectWorkspace:
    def test_detects_workspace(self, single_workspace):
        result = runner.invoke(
            app, ["detect-workspace", "100"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 0
        assert result.output.strip() == "myproject"

    def test_unknown_window_exits_1(self, single_workspace):
        result = runner.invoke(
            app, ["detect-workspace", "999"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 1


class TestCLIListWinIds:
    def test_lists_all_ids(self, single_workspace):
        result = runner.invoke(
            app, ["list-win-ids"], input=json.dumps(single_workspace)
        )
        assert result.exit_code == 0
        ids = result.output.strip().splitlines()
        assert sorted(ids) == ["100", "101"]

    def test_empty_state(self, empty_state):
        result = runner.invoke(
            app, ["list-win-ids"], input=json.dumps(empty_state)
        )
        assert result.exit_code == 0
        assert result.output.strip() == ""


class TestCLIParseExtraTabs:
    def test_outputs_pipe_delimited(self, sample_snapshot):
        result = runner.invoke(
            app, ["parse-extra-tabs-cmd", sample_snapshot, "shell", "opencode"]
        )
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        assert len(lines) == 2  # logs + monitoring
        assert "|" in lines[0]

    def test_nonexistent_snapshot_exits_1(self, tmp_path):
        result = runner.invoke(
            app,
            ["parse-extra-tabs-cmd", str(tmp_path / "nope.conf"), "shell"],
        )
        assert result.exit_code == 1


class TestCLIFindSocket:
    def test_finds_socket(self, tmp_path):
        socket_dir = tmp_path / "kitty"
        socket_dir.mkdir()
        sock = socket_dir / "control-socket-123"
        sock.touch()
        with patch.object(
            kitty_query, "SOCKET_GLOB", str(socket_dir / "control-socket-*")
        ):
            result = runner.invoke(app, ["find-socket-cmd"])
            assert result.exit_code == 0
            assert "control-socket-123" in result.output

    def test_no_socket_exits_1(self, tmp_path):
        with patch.object(
            kitty_query, "SOCKET_GLOB", str(tmp_path / "nonexistent-*")
        ):
            result = runner.invoke(app, ["find-socket-cmd"])
            assert result.exit_code == 1


class TestCLIPurgeStale:
    def test_purges_stale_bindings(self, tmp_path):
        map_path = tmp_path / "test.map"
        map_path.write_text("100=sess-a\n200=sess-b\n300=sess-c\n")
        result = runner.invoke(
            app, ["purge-stale", str(map_path), "100", "300"]
        )
        assert result.exit_code == 0
        # Check map was rewritten
        bindings = parse_map_file(str(map_path))
        assert "200" not in bindings
        assert bindings == {"100": "sess-a", "300": "sess-c"}

    def test_no_stale_bindings(self, tmp_path):
        map_path = tmp_path / "test.map"
        map_path.write_text("100=sess-a\n")
        result = runner.invoke(
            app, ["purge-stale", str(map_path), "100"]
        )
        assert result.exit_code == 0
        assert "No stale" in result.output

    def test_nonexistent_map(self, tmp_path):
        result = runner.invoke(
            app, ["purge-stale", str(tmp_path / "nope.map"), "100"]
        )
        assert result.exit_code == 0


class TestCLISessionExists:
    def test_existing_session(self, opencode_db):
        result = runner.invoke(
            app, ["session-exists-cmd", opencode_db, "sess-1"]
        )
        assert result.exit_code == 0
        assert "exists" in result.output

    def test_nonexistent_session(self, opencode_db):
        result = runner.invoke(
            app, ["session-exists-cmd", opencode_db, "nonexistent"]
        )
        assert result.exit_code == 1

    def test_archived_session(self, opencode_db):
        result = runner.invoke(
            app, ["session-exists-cmd", opencode_db, "sess-archived"]
        )
        assert result.exit_code == 1


class TestCLIQuerySessions:
    def test_returns_latest(self, opencode_db):
        result = runner.invoke(
            app, ["query-sessions-cmd", opencode_db, "/home/user/myproject"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "sess-3"

    def test_no_sessions_exits_1(self, opencode_db):
        result = runner.invoke(
            app, ["query-sessions-cmd", opencode_db, "/nonexistent"]
        )
        assert result.exit_code == 1
