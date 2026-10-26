"""Native adapter contracts; all process, socket and HTTP effects are fixtures."""

import copy
import importlib.machinery
import importlib.util
import json
import os
import socket
import stat
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).parents[1]
HELPER = ROOT / "dot_local/bin/executable_synergy-handoff"
LOADER = importlib.machinery.SourceFileLoader("synergy_handoff_surfaces", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
handoff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = handoff
LOADER.exec_module(handoff)

UID = os.getuid()
RUSTDESK_APP = Path("/Applications/RustDesk.app")
RUSTDESK_EXE = str(RUSTDESK_APP / "Contents/MacOS/RustDesk")
SYNERGY_APP = Path("/Applications/Synergy.app")
SYNERGY_SERVICE = str(SYNERGY_APP / "Contents/MacOS/synergy-service")
SYNERGY_GUI = str(SYNERGY_APP / "Contents/MacOS/Synergy")


class RustDeskSocket:
    def __init__(self):
        self.reply = handoff.encode_frame(b'{"t":"VideoConnCount","c":0}')
        self.peer = 100
        self.sent = []
        self.connected = []
        self.timeouts = []
        self.connect_error = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def settimeout(self, timeout):
        self.timeouts.append(timeout)

    def connect(self, address):
        self.connected.append(address)
        if self.connect_error:
            raise self.connect_error

    def getsockopt(self, level, option, length):
        assert (level, option, length) == (0, 2, 4)
        return struct.pack("=i", self.peer)

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        data, self.reply = self.reply[:size], self.reply[size:]
        return data


@pytest.fixture
def rustdesk(monkeypatch):
    adapter = handoff.RustDesk(RUSTDESK_APP)
    peer = handoff.Process(UID, 100, 1, RUSTDESK_EXE)
    entries = [peer]
    metadata = {
        f"/tmp/RustDesk-{UID}": SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=UID),
        f"/tmp/RustDesk-{UID}/ipc": SimpleNamespace(st_mode=stat.S_IFSOCK | 0o600, st_uid=UID),
    }
    real_lstat = Path.lstat

    def lstat(path):
        if str(path) in metadata:
            value = metadata[str(path)]
            if isinstance(value, Exception):
                raise value
            return value
        return real_lstat(path)

    stream = RustDeskSocket()
    opens = []

    def open_socket(family, kind):
        assert (family, kind) == (socket.AF_UNIX, socket.SOCK_STREAM)
        opens.append(True)
        return stream

    monkeypatch.setattr(handoff, "processes", lambda: entries)
    monkeypatch.setattr(handoff, "app_version", lambda app: "1.5.0")
    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(handoff.socket, "socket", open_socket)
    return adapter, stream, entries, metadata, opens


@pytest.mark.parametrize("count", [0, 1, 2, 1024])
def test_rustdesk_uses_authenticated_desktop_count_request_and_validates_peer(rustdesk, count):
    adapter, stream, _, _, _ = rustdesk
    stream.reply = handoff.encode_frame(json.dumps({"t": "VideoConnCount", "c": count}).encode())
    assert adapter.sample() == handoff.SessionSample(count, True)
    assert adapter.error is None
    assert stream.connected == [f"/tmp/RustDesk-{UID}/ipc"]
    assert stream.sent == [handoff.encode_frame(b'{"t":"VideoConnCount","c":null}')]
    assert all(0 < timeout <= 1 for timeout in stream.timeouts)


@pytest.mark.parametrize("response", [
    {}, [], None, 0,
    {"t": "HasNoActiveConns", "c": 0},
    {"t": "VideoConnCount"},
    {"t": "VideoConnCount", "c": None},
    {"t": "VideoConnCount", "c": True},
    {"t": "VideoConnCount", "c": False},
    {"t": "VideoConnCount", "c": "1"},
    {"t": "VideoConnCount", "c": 1.0},
    {"t": "VideoConnCount", "c": -1},
    {"t": "VideoConnCount", "c": 1025},
])
def test_invalid_rustdesk_response_is_unknown_never_zero(rustdesk, response):
    adapter, stream, _, _, _ = rustdesk
    stream.reply = handoff.encode_frame(json.dumps(response).encode())
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error


@pytest.mark.parametrize("payload", [b"", b"{", b"\xff"])
def test_malformed_rustdesk_json_is_unknown(rustdesk, payload):
    adapter, stream, _, _, _ = rustdesk
    stream.reply = handoff.encode_frame(payload)
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error


def test_detector_clears_previous_error_after_next_verified_response(rustdesk):
    adapter, stream, _, _, _ = rustdesk
    stream.reply = handoff.encode_frame(b"{}")
    assert adapter.sample().count is None
    assert adapter.error
    stream.reply = handoff.encode_frame(b'{"t":"VideoConnCount","c":2}')
    assert adapter.sample() == handoff.SessionSample(2, True)
    assert adapter.error is None


def test_absent_desktop_host_is_distinct_from_idle_or_service_only(rustdesk):
    adapter, _, entries, _, opens = rustdesk
    entries[:] = [handoff.Process(0, 99, 1, str(RUSTDESK_APP / "Contents/MacOS/service"))]
    assert adapter.sample() == handoff.SessionSample(None, False)
    assert opens == []


def test_missing_socket_with_live_host_stays_unknown(rustdesk):
    adapter, _, _, metadata, opens = rustdesk
    metadata[f"/tmp/RustDesk-{UID}/ipc"] = FileNotFoundError("socket missing")
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error
    assert opens == []


def test_connection_failure_with_live_host_stays_unknown(rustdesk):
    adapter, stream, _, _, _ = rustdesk
    stream.connect_error = ConnectionRefusedError("server restarting")
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error
    assert stream.sent == []


def test_incompatible_rustdesk_version_blocks_socket_query(rustdesk, monkeypatch):
    adapter, _, _, _, opens = rustdesk
    monkeypatch.setattr(handoff, "app_version", lambda app: "1.6.0")
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error
    assert opens == []


@pytest.mark.parametrize("peer", [
    handoff.Process(UID + 1, 100, 1, RUSTDESK_EXE),
    handoff.Process(UID, 101, 1, RUSTDESK_EXE),
    handoff.Process(UID, 100, 1, "/tmp/RustDesk"),
])
def test_unexpected_socket_peer_cannot_supply_session_count(rustdesk, peer):
    adapter, stream, entries, _, _ = rustdesk
    # Keep an expected host alive separately so rejection tests peer verification.
    entries[:] = [handoff.Process(UID, 200, 1, RUSTDESK_EXE), peer]
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error
    assert stream.sent == []


@pytest.mark.parametrize("target,mode,owner", [
    ("directory", stat.S_IFDIR | 0o755, UID),
    ("directory", stat.S_IFDIR | 0o700, UID + 1),
    ("directory", stat.S_IFLNK | 0o700, UID),
    ("socket", stat.S_IFSOCK | 0o666, UID),
    ("socket", stat.S_IFSOCK | 0o600, UID + 1),
    ("socket", stat.S_IFREG | 0o600, UID),
    ("socket", stat.S_IFLNK | 0o600, UID),
])
def test_unsafe_rustdesk_socket_metadata_blocks_query(rustdesk, target, mode, owner):
    adapter, _, _, metadata, opens = rustdesk
    path = f"/tmp/RustDesk-{UID}" + ("/ipc" if target == "socket" else "")
    metadata[path] = SimpleNamespace(st_mode=mode, st_uid=owner)
    assert adapter.sample() == handoff.SessionSample(None, True)
    assert adapter.error
    assert opens == []


SETTINGS = {
    "data": {
        "ready": True,
        "serviceInfo": {"serviceVersion": "3.8.4"},
        "local_system": {"core_enabled": True},
        "coreRunning": True,
    }
}


@pytest.fixture
def synergy(monkeypatch):
    adapter = handoff.Synergy(SYNERGY_APP)
    owner = handoff.Process(UID, 300, 1, SYNERGY_SERVICE)
    entries = [owner, handoff.Process(UID, 301, 300, "/private/tmp/synergy-core")]
    settings = copy.deepcopy(SETTINGS)
    monkeypatch.setattr(handoff, "processes", lambda: entries)
    monkeypatch.setattr(adapter, "request", lambda endpoint, method="GET": settings)
    return adapter, entries, settings


@pytest.mark.parametrize("enabled,running", [(True, True), (False, False), (True, False)])
def test_synergy_snapshot_matches_verified_settings_and_owned_core(synergy, enabled, running):
    adapter, entries, settings = synergy
    settings["data"]["local_system"]["core_enabled"] = enabled
    settings["data"]["coreRunning"] = running
    if not running:
        entries.pop()
    assert adapter.snapshot() == handoff.SynergyState(enabled, running)


@pytest.mark.parametrize("path,value", [
    (("data",), None),
    (("data", "ready"), False),
    (("data", "ready"), 1),
    (("data", "serviceInfo"), []),
    (("data", "serviceInfo", "serviceVersion"), "3.9.0"),
    (("data", "local_system"), []),
    (("data", "local_system", "core_enabled"), 1),
    (("data", "local_system", "core_enabled"), "true"),
    (("data", "coreRunning"), 1),
    (("data", "coreRunning"), None),
])
def test_synergy_snapshot_rejects_unready_version_or_schema_drift(synergy, path, value):
    adapter, _, settings = synergy
    target = settings
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(handoff.SurfaceError):
        adapter.snapshot()


@pytest.mark.parametrize("core", [
    handoff.Process(UID, 301, 999, "/private/tmp/synergy-core"),
    handoff.Process(UID + 1, 301, 300, "/private/tmp/synergy-core"),
    handoff.Process(UID, 301, 300, "/private/tmp/synergy-core-other"),
])
def test_synergy_core_requires_same_user_expected_parent_and_executable(synergy, core):
    adapter, entries, _ = synergy
    entries[-1] = core
    with pytest.raises(handoff.SurfaceError):
        adapter.snapshot()


def test_synergy_reported_stopped_core_must_really_be_stopped(synergy):
    adapter, _, settings = synergy
    settings["data"]["coreRunning"] = False
    with pytest.raises(handoff.SurfaceError):
        adapter.snapshot()


def test_synergy_service_replacement_during_snapshot_rejects_observation(synergy, monkeypatch):
    adapter, entries, _ = synergy
    replacement = [handoff.Process(UID, 400, 1, SYNERGY_SERVICE)]
    observations = iter([entries, entries, replacement])
    monkeypatch.setattr(handoff, "processes", lambda: next(observations))
    with pytest.raises(handoff.SurfaceError):
        adapter.snapshot()


@pytest.mark.parametrize("entries", [
    [],
    [handoff.Process(UID + 1, 300, 1, SYNERGY_SERVICE)],
    [handoff.Process(UID, 300, 1, SYNERGY_SERVICE), handoff.Process(UID, 400, 1, SYNERGY_SERVICE)],
])
def test_synergy_owner_must_be_unique_and_current_user(synergy, monkeypatch, entries):
    adapter, _, _ = synergy
    monkeypatch.setattr(handoff, "processes", lambda: entries)
    with pytest.raises(handoff.SurfaceError):
        adapter.owner()


@pytest.mark.parametrize("executable,uid,present", [
    (SYNERGY_SERVICE, UID, True),
    (SYNERGY_GUI, UID, True),
    (SYNERGY_SERVICE, UID + 1, False),
    ("/tmp/synergy-service", UID, False),
])
def test_presence_preserves_service_only_restart_and_gui_only_state(monkeypatch, executable, uid, present):
    monkeypatch.setattr(handoff, "processes", lambda: [handoff.Process(uid, 300, 1, executable)])
    assert handoff.Synergy(SYNERGY_APP).present() is present


class HttpResponse:
    def __init__(self, body):
        self.body = body
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self, size):
        self.read_sizes.append(size)
        return self.body[:size]


def test_synergy_http_opener_explicitly_disables_environment_proxies(monkeypatch):
    seen = []
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("http_proxy", "http://proxy.invalid:3128")
    monkeypatch.setattr(handoff.urllib.request, "build_opener", lambda *handlers: seen.extend(handlers))
    handoff.Synergy(SYNERGY_APP)
    proxy = next(handler for handler in seen if isinstance(handler, handoff.urllib.request.ProxyHandler))
    assert proxy.proxies == {}
    assert any(isinstance(handler, handoff.NoRedirect) for handler in seen)


def test_synergy_http_redirect_never_follows_to_another_endpoint():
    request = handoff.urllib.request.Request("http://127.0.0.1:24803/v1/settings")
    with pytest.raises(handoff.SurfaceError):
        handoff.NoRedirect().redirect_request(request, None, 302, "redirect", {}, "http://elsewhere.invalid/")


@pytest.mark.parametrize("method,endpoint", [("GET", "settings"), ("POST", "controls/pauseCore")])
def test_synergy_request_uses_fixed_loopback_with_deadline_and_bounded_read(method, endpoint):
    adapter = handoff.Synergy(SYNERGY_APP)
    response = HttpResponse(b'{"data":{}}')
    calls = []

    def open_request(request, timeout):
        calls.append((request.full_url, request.get_method(), timeout))
        return response

    adapter.http = SimpleNamespace(open=open_request)
    assert adapter.request(endpoint, method) == {"data": {}}
    assert calls == [("http://127.0.0.1:24803/v1/" + endpoint, method, 2)]
    assert response.read_sizes == [262145]


@pytest.mark.parametrize("body", [b"{", b"\xff", b"[]", b"null", b"x" * 262145])
def test_synergy_request_rejects_invalid_or_oversized_response(body):
    adapter = handoff.Synergy(SYNERGY_APP)
    adapter.http = SimpleNamespace(open=lambda request, timeout: HttpResponse(body))
    with pytest.raises(handoff.SurfaceError):
        adapter.request("settings")


@pytest.mark.parametrize("output", [
    "p300\nn127.0.0.1:24803\n",
    "p300\nf12\nn127.0.0.1:24803\n",
])
def test_listener_parser_accepts_only_expected_owned_loopback_listener(output):
    assert handoff.parse_listener(output, 300) is True


@pytest.mark.parametrize("output", [
    "", "p300\n", "n127.0.0.1:24803\n", "f12\nn127.0.0.1:24803\n",
    "p301\nf12\nn127.0.0.1:24803\n",
    "p300\nf12\nn*:24803\n",
    "p300\nf12\nn0.0.0.0:24803\n",
    "p300\nf12\nn[::1]:24803\n",
    "p300\nf12\nn127.0.0.1:24804\n",
    "p300\nf12\nn127.0.0.1:24803\nf13\nn127.0.0.1:24804\n",
    "p300\nf12\nn127.0.0.1:24803\np301\nf13\nn127.0.0.1:24803\n",
])
def test_listener_parser_rejects_ambiguous_foreign_or_nonloopback_listener(output):
    assert handoff.parse_listener(output, 300) is False


@pytest.mark.parametrize("action,method", [("pauseCore", "pause"), ("resumeCore", "resume")])
def test_native_control_verifies_listener_then_sends_exact_post(synergy, monkeypatch, action, method):
    adapter, _, _ = synergy
    posts = []
    monkeypatch.setattr(handoff.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="p300\nf12\nn127.0.0.1:24803\n"))
    monkeypatch.setattr(adapter, "snapshot", lambda: handoff.SynergyState(True, True))
    monkeypatch.setattr(adapter, "request", lambda endpoint, method="GET": posts.append((endpoint, method)))
    getattr(adapter, method)()
    assert posts == [("controls/" + action, "POST")]


def test_native_control_never_posts_to_foreign_listener(synergy, monkeypatch):
    adapter, _, _ = synergy
    posts = []
    monkeypatch.setattr(handoff.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="p999\nf12\nn127.0.0.1:24803\n"))
    monkeypatch.setattr(adapter, "snapshot", lambda: handoff.SynergyState(True, True))
    monkeypatch.setattr(adapter, "request", lambda *args: posts.append(args))
    with pytest.raises(handoff.SurfaceError):
        adapter.pause()
    assert posts == []
