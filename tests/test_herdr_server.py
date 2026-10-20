"""Exercise Herdr startup using synthetic Unix sockets, never a real session."""

from contextlib import contextmanager
import errno
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "dot_local/bin/executable_omarchy-herdr-server"


@pytest.fixture
def helper(monkeypatch):
    # Short paths avoid AF_UNIX's platform pathname limit on long pytest paths.
    with tempfile.TemporaryDirectory(prefix="herdr-test-") as temporary:
        home = Path(temporary)
        monkeypatch.setenv("HOME", str(home))
        for name in ("XDG_CONFIG_HOME", "HERDR_CONFIG_PATH", "HERDR_SESSION",
                     "HERDR_SOCKET_PATH", "HERDR_CLIENT_SOCKET_PATH", "HERDR_ENV"):
            monkeypatch.delenv(name, raising=False)
        loader = importlib.machinery.SourceFileLoader("herdr_transport_test", str(SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        directory = home / ".config/herdr"
        directory.mkdir(parents=True)
        yield module, home, directory


@contextmanager
def listener(path, drain=False):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path))
        server.listen(512)
        server.settimeout(0.05 if drain else 1)
        stopped = threading.Event()
        requests = []

        def accept_probes():
            while not stopped.is_set():
                try:
                    connection, _ = server.accept()
                except socket.timeout:
                    continue
                with connection:
                    connection.settimeout(1)
                    requests.append(connection.recv(4096))

        thread = threading.Thread(target=accept_probes, daemon=True) if drain else None
        if thread:
            thread.start()
        try:
            yield server
        finally:
            if thread:
                stopped.set()
                thread.join(timeout=2)
                assert not thread.is_alive()
                assert all(request == b"" for request in requests)


def assert_probe_sent_no_request(server):
    connection, _ = server.accept()
    with connection:
        connection.settimeout(1)
        assert connection.recv(4096) == b""


def invoke(module, monkeypatch, option):
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), option])
    return module.main()


def test_missing_socket_allows_start_without_creating_files(helper, monkeypatch):
    module, _, directory = helper
    assert invoke(module, monkeypatch, "--check-not-running") == 0
    assert not list(directory.iterdir())


def test_stale_socket_allows_start_and_is_not_removed(helper, monkeypatch):
    module, _, directory = helper
    path = directory / "herdr.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stale:
        stale.bind(str(path))
    identity = path.stat().st_ino
    assert invoke(module, monkeypatch, "--check-not-running") == 0
    assert path.stat().st_ino == identity


def test_live_socket_skips_start_without_an_api_request(helper, monkeypatch):
    module, _, directory = helper
    with listener(directory / "herdr.sock") as server:
        assert invoke(module, monkeypatch, "--check-not-running") == 1
        assert_probe_sent_no_request(server)


def test_unexpected_socket_error_fails_closed(helper, monkeypatch):
    module, _, _ = helper

    class DeniedConnection:
        def __enter__(self):
            return self

        def __exit__(self, *arguments):
            return None

        def settimeout(self, seconds):
            pass

        def connect(self, path):
            raise PermissionError(errno.EACCES, "permission denied", path)

    # Inject permission denial so this also works under privileged CI users.
    monkeypatch.setattr(module, "socket", SimpleNamespace(
        AF_UNIX=socket.AF_UNIX, SOCK_STREAM=socket.SOCK_STREAM,
        socket=lambda *arguments: DeniedConnection()))
    with pytest.raises(PermissionError) as error:
        invoke(module, monkeypatch, "--check-not-running")
    assert error.value.errno == errno.EACCES


def test_socket_directory_follows_xdg_instead_of_config_file_override(helper, monkeypatch):
    module, home, _ = helper
    config_home = home / "custom-config"
    directory = config_home / "herdr"
    directory.mkdir(parents=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("HERDR_CONFIG_PATH", str(home / "unrelated/config.toml"))
    with listener(directory / "herdr.sock") as server:
        assert invoke(module, monkeypatch, "--check-not-running") == 1
        assert_probe_sent_no_request(server)


def test_server_launch_executes_user_local_binary_with_only_server_argument(helper):
    _, home, _ = helper
    binary = home / ".local/bin/herdr"
    binary.parent.mkdir(parents=True)
    # This executable is a fixture, not Herdr. The subprocess exercises execv
    # rather than replacing it with a mock that merely repeats implementation.
    binary.write_text('#!/bin/sh\nprintf "%s\\n" "$0" "$@" > "$HOME/launch-argv"\n')
    binary.chmod(0o700)
    result = subprocess.run([sys.executable, str(SCRIPT)], env=os.environ.copy(),
                            capture_output=True, text=True, timeout=3)
    assert result.returncode == 0, result.stderr
    assert (home / "launch-argv").read_text().splitlines() == [str(binary), "server"]


class Clock:
    def __init__(self, after_sleep=None):
        self.elapsed = 0
        self.sleeps = []
        self.after_sleep = after_sleep

    def monotonic(self):
        return self.elapsed

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.elapsed += seconds
        if self.after_sleep:
            self.after_sleep(len(self.sleeps))


@pytest.mark.parametrize("error", [TimeoutError(), BlockingIOError(errno.EAGAIN, "busy")])
def test_busy_restoring_server_is_retried_before_readiness(helper, monkeypatch, error):
    module, _, directory = helper
    clock = Clock()
    monkeypatch.setattr(module, "time", clock)
    attempts = []

    def connect(path):
        attempts.append(path)
        if len(attempts) == 1:
            raise error
        return True

    monkeypatch.setattr(module, "listening", connect)
    assert invoke(module, monkeypatch, "--wait-ready") == 0
    assert clock.sleeps == [0.05]
    assert attempts == [directory / "herdr-client.sock", directory / "herdr-client.sock", directory / "herdr.sock"]


def test_readiness_requires_both_real_listeners_and_sends_no_requests(helper, monkeypatch):
    module, _, directory = helper
    with listener(directory / "herdr.sock") as api, listener(directory / "herdr-client.sock") as client:
        clock = Clock()
        monkeypatch.setattr(module, "time", clock)
        assert invoke(module, monkeypatch, "--wait-ready") == 0
        assert clock.elapsed == 0
        assert_probe_sent_no_request(api)
        assert_probe_sent_no_request(client)


@pytest.mark.parametrize("available", ["api", "client", "neither"])
def test_partial_readiness_times_out_instead_of_claiming_startup(helper, monkeypatch, capsys, available):
    module, _, directory = helper
    clock = Clock()
    monkeypatch.setattr(module, "time", clock)

    def verify():
        assert invoke(module, monkeypatch, "--wait-ready") == 1
        assert 60 <= clock.elapsed < 60.1
        assert clock.sleeps
        assert "sixty seconds" in capsys.readouterr().err

    if available == "neither":
        verify()
    else:
        name = "herdr.sock" if available == "api" else "herdr-client.sock"
        with listener(directory / name, drain=True):
            verify()


def test_readiness_retries_until_second_socket_starts_listening(helper, monkeypatch):
    module, _, directory = helper
    client = None

    def start_client_after_three_waits(count):
        nonlocal client
        if count == 3:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.bind(str(directory / "herdr-client.sock"))
            client.listen(1)
            client.settimeout(1)

    clock = Clock(start_client_after_three_waits)
    monkeypatch.setattr(module, "time", clock)
    try:
        with listener(directory / "herdr.sock") as api:
            assert invoke(module, monkeypatch, "--wait-ready") == 0
            assert len(clock.sleeps) == 3
            assert 0 < clock.elapsed < 10
            assert_probe_sent_no_request(api)
            assert_probe_sent_no_request(client)
    finally:
        if client is not None:
            client.close()


def test_invalid_arguments_do_not_start_a_server(helper, monkeypatch, capsys):
    module, home, _ = helper
    assert invoke(module, monkeypatch, "--unknown") == 2
    assert "Usage:" in capsys.readouterr().err
    assert not (home / "launch-argv").exists()
