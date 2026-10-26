"""Recovery and transport contracts for incoming desktop input ownership."""

import importlib.machinery
import importlib.util
import stat
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
HELPER = ROOT / "dot_local/bin/executable_synergy-handoff"
LOADER = importlib.machinery.SourceFileLoader("synergy_handoff", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
handoff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = handoff
LOADER.exec_module(handoff)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeSynergy:
    def __init__(self, store, enabled=True, running=True):
        self.store = store
        self.state = handoff.SynergyState(enabled=enabled, running=running)
        self.alive = True
        self.actions = []
        self.snapshot_error = None
        self.fail_action = None
        self.fail_after_effect = False
        self.pause_result = handoff.SynergyState(enabled=False, running=False)
        self.resume_result = handoff.SynergyState(enabled=True, running=True)

    def present(self):
        return self.alive

    def snapshot(self):
        if self.snapshot_error:
            raise self.snapshot_error
        return self.state

    def _act(self, action, required_phase, result):
        lease = self.store.read()
        assert lease is not None, "Mutation must have a durable restoration journal"
        assert lease["phase"] == required_phase
        self.actions.append(action)
        if self.fail_action and not self.fail_after_effect:
            raise self.fail_action
        self.state = result
        if self.fail_action:
            raise self.fail_action

    def pause(self):
        self._act("pause", "pause_pending", self.pause_result)

    def resume(self):
        self._act("resume", "resume_pending", self.resume_result)


@pytest.fixture
def rig(tmp_path):
    store = handoff.StateStore(tmp_path / "private-state")
    synergy = FakeSynergy(store)
    clock = Clock()
    return store, synergy, clock


def coordinator(rig, **options):
    store, synergy, clock = rig
    return handoff.Coordinator(store, synergy, clock=clock, grace=5, settle=2, **options)


def sample(count, alive=True):
    return handoff.SessionSample(count=count, host_alive=alive)


def acquire(rig):
    owner = coordinator(rig)
    owner.step(sample(1))
    assert rig[0].read()["phase"] == "paused"
    assert rig[1].state == handoff.SynergyState(enabled=False, running=False)
    return owner


@pytest.mark.parametrize("count", [0, None])
def test_idle_observations_never_toggle_or_acquire(rig, count):
    owner = coordinator(rig)
    owner.step(sample(count))
    owner.step(sample(count))
    assert rig[0].read() is None
    assert rig[1].actions == []


@pytest.mark.parametrize("enabled,running", [(False, False), (False, True), (True, False)])
def test_initial_manual_pause_or_stopped_core_never_creates_restore_ownership(rig, enabled, running):
    store, synergy, _ = rig
    synergy.state = handoff.SynergyState(enabled=enabled, running=running)
    owner = coordinator(rig)
    owner.step(sample(1))
    owner.step(sample(0))
    owner.step(sample(0))
    assert store.read() is None
    assert synergy.actions == []
    assert synergy.state == handoff.SynergyState(enabled=enabled, running=running)


def test_initially_absent_synergy_never_starts_or_acquires(rig):
    rig[1].alive = False
    rig[1].snapshot_error = handoff.SurfaceError("service absent")
    owner = coordinator(rig)
    owner.step(sample(1))
    owner.step(sample(0))
    owner.step(sample(0))
    assert rig[0].read() is None
    assert rig[1].actions == []


def test_acquisition_journals_before_native_pause_and_remains_idempotent(rig):
    owner = acquire(rig)
    for count in [1, 2, 7, 1]:
        owner.step(sample(count))
    assert rig[1].actions == ["pause"]
    assert rig[0].read()["phase"] == "paused"


def test_multiple_sessions_hold_until_two_observations_after_last_disconnect(rig):
    owner = acquire(rig)
    for count in [2, 1, 1, 0]:
        owner.step(sample(count))
    assert rig[1].actions == ["pause"]
    assert rig[0].read() is not None
    owner.step(sample(0))
    assert rig[1].actions == ["pause", "resume"]
    assert rig[0].read() is None
    assert rig[1].state == handoff.SynergyState(enabled=True, running=True)


@pytest.mark.parametrize("interruption", [1, None])
def test_reconnect_or_unknown_resets_consecutive_zero_requirement(rig, interruption):
    owner = acquire(rig)
    for count in [0, interruption, 0]:
        owner.step(sample(count))
    assert rig[1].actions == ["pause"]
    owner.step(sample(0))
    assert rig[1].actions == ["pause", "resume"]


def test_live_host_with_unreadable_ipc_never_becomes_zero(rig):
    owner = acquire(rig)
    for _ in range(6):
        rig[2].advance(60)
        owner.step(sample(None))
    assert rig[0].read() is not None
    assert rig[1].actions == ["pause"]


def test_dead_rustdesk_host_requires_full_grace_then_restores(rig):
    owner = acquire(rig)
    owner.step(sample(None, alive=False))
    rig[2].advance(4.99)
    owner.step(sample(None, alive=False))
    assert rig[1].actions == ["pause"]
    rig[2].advance(0.02)
    owner.step(sample(None, alive=False))
    assert rig[1].actions == ["pause", "resume"]
    assert rig[0].read() is None


def test_host_reappearance_resets_absence_grace(rig):
    owner = acquire(rig)
    owner.step(sample(None, alive=False))
    rig[2].advance(4)
    owner.step(sample(None, alive=True))
    rig[2].advance(2)
    owner.step(sample(None, alive=False))
    rig[2].advance(4)
    owner.step(sample(None, alive=False))
    assert rig[1].actions == ["pause"]
    rig[2].advance(1)
    owner.step(sample(None, alive=False))
    assert rig[1].actions == ["pause", "resume"]


def test_user_quit_relinquishes_without_restarting_synergy(rig):
    owner = acquire(rig)
    rig[1].alive = False
    rig[1].snapshot_error = handoff.SurfaceError("service absent")
    owner.step(sample(1))
    assert rig[0].read() is None
    assert rig[1].actions == ["pause"]
    owner.step(sample(0))
    owner.step(sample(0))
    assert rig[1].actions == ["pause"]


def test_service_only_failure_retains_ownership_for_supervisor_recovery(rig):
    owner = acquire(rig)
    rig[1].snapshot_error = handoff.SurfaceError("service restarting")
    owner.step(sample(1))
    assert rig[0].read() is not None
    rig[1].snapshot_error = None
    owner.step(sample(0))
    owner.step(sample(0))
    assert rig[0].read() is None
    assert rig[1].actions == ["pause", "resume"]


@pytest.mark.parametrize("count", [0, 1])
def test_restart_before_synergy_login_preserves_durable_restoration(rig, count):
    acquire(rig)
    rig[1].alive = False
    rig[1].snapshot_error = handoff.SurfaceError("login service not started")
    restarted = coordinator(rig)
    restarted.step(sample(count))
    restarted.step(sample(count))
    assert rig[0].read() is not None
    assert rig[1].actions == ["pause"]
    rig[1].alive = True
    rig[1].snapshot_error = None
    restarted.step(sample(0))
    restarted.step(sample(0))
    assert rig[0].read() is None
    assert rig[1].actions == ["pause", "resume"]


@pytest.mark.parametrize("after_effect", [False, True])
@pytest.mark.parametrize("exception_type", [RuntimeError, handoff.SurfaceError])
def test_pause_failure_reconciles_journal_and_actual_state_after_restart(rig, after_effect, exception_type):
    owner = coordinator(rig)
    rig[1].fail_action = exception_type("pause interrupted")
    rig[1].fail_after_effect = after_effect
    if exception_type is RuntimeError:
        with pytest.raises(RuntimeError, match="pause interrupted"):
            owner.step(sample(1))
    else:
        owner.step(sample(1))
    assert rig[0].read()["phase"] == "pause_pending"
    rig[1].fail_action = None
    restarted = coordinator(rig)
    restarted.step(sample(1))
    assert rig[0].read()["phase"] == "paused"
    assert rig[1].actions.count("pause") == (1 if after_effect else 2)
    restarted.step(sample(0))
    restarted.step(sample(0))
    assert rig[0].read() is None
    assert rig[1].actions[-1] == "resume"


@pytest.mark.parametrize("after_effect", [False, True])
@pytest.mark.parametrize("exception_type", [RuntimeError, handoff.SurfaceError])
def test_resume_failure_keeps_lease_until_actual_restore_verified(rig, after_effect, exception_type):
    owner = acquire(rig)
    owner.step(sample(0))
    rig[1].fail_action = exception_type("resume interrupted")
    rig[1].fail_after_effect = after_effect
    if exception_type is RuntimeError:
        with pytest.raises(RuntimeError, match="resume interrupted"):
            owner.step(sample(0))
    else:
        owner.step(sample(0))
    assert rig[0].read()["phase"] == "resume_pending"
    rig[1].fail_action = None
    restarted = coordinator(rig)
    restarted.step(sample(0))
    restarted.step(sample(0))
    assert rig[0].read() is None
    assert rig[1].state == handoff.SynergyState(enabled=True, running=True)
    assert rig[1].actions.count("resume") == (1 if after_effect else 2)


def test_pause_http_success_requires_disabled_intent_and_stopped_core(rig):
    rig[1].pause_result = handoff.SynergyState(enabled=False, running=True)
    owner = coordinator(rig)
    owner.step(sample(1))
    assert rig[0].read()["phase"] == "pause_pending"
    rig[1].state = handoff.SynergyState(enabled=False, running=False)
    owner.step(sample(1))
    assert rig[0].read()["phase"] == "paused"


def test_resume_http_success_without_running_core_keeps_pending_lease(rig):
    owner = acquire(rig)
    rig[1].resume_result = handoff.SynergyState(enabled=True, running=False)
    owner.step(sample(0))
    owner.step(sample(0))
    assert rig[0].read()["phase"] == "resume_pending"
    rig[1].state = handoff.SynergyState(enabled=True, running=True)
    owner.step(sample(0))
    assert rig[0].read() is None
    assert rig[1].actions.count("resume") == 1


def test_new_session_during_incomplete_resume_reacquires_pause(rig):
    owner = acquire(rig)
    rig[1].resume_result = handoff.SynergyState(enabled=True, running=False)
    owner.step(sample(0))
    owner.step(sample(0))
    owner.step(sample(1))
    assert rig[0].read()["phase"] == "paused"
    assert rig[1].state == handoff.SynergyState(enabled=False, running=False)
    assert rig[1].actions == ["pause", "resume", "pause"]


class CrashStore:
    """Crash immediately before or after one durable journal operation."""

    def __init__(self, underlying, point):
        self.underlying = underlying
        self.point = point

    def read(self):
        return self.underlying.read()

    def _crash(self, point):
        if self.point == point:
            self.point = None
            raise RuntimeError("journal crash")

    def write(self, lease):
        self._crash("before:" + lease["phase"])
        self.underlying.write(lease)
        self._crash("after:" + lease["phase"])

    def clear(self):
        self._crash("before:clear")
        self.underlying.clear()
        self._crash("after:clear")


@pytest.mark.parametrize("point", ["before:pause_pending", "after:pause_pending", "before:paused", "after:paused"])
def test_pause_journal_crash_boundaries_preserve_restoration(rig, point):
    store, synergy, clock = rig
    faulty = CrashStore(store, point)
    synergy.store = faulty
    owner = handoff.Coordinator(faulty, synergy, clock=clock)
    with pytest.raises(RuntimeError, match="journal crash"):
        owner.step(sample(1))
    synergy.store = store
    restarted = coordinator(rig)
    restarted.step(sample(1))
    assert store.read()["phase"] == "paused"
    restarted.step(sample(0))
    restarted.step(sample(0))
    assert store.read() is None
    assert synergy.state == handoff.SynergyState(enabled=True, running=True)


@pytest.mark.parametrize("point", ["before:resume_pending", "after:resume_pending", "before:clear", "after:clear"])
def test_resume_journal_crash_boundaries_never_duplicate_completed_resume(rig, point):
    acquire(rig)
    store, synergy, clock = rig
    faulty = CrashStore(store, point)
    synergy.store = faulty
    owner = handoff.Coordinator(faulty, synergy, clock=clock)
    owner.step(sample(0))
    with pytest.raises(RuntimeError, match="journal crash"):
        owner.step(sample(0))
    synergy.store = store
    restarted = coordinator(rig)
    restarted.step(sample(0))
    restarted.step(sample(0))
    assert store.read() is None
    assert synergy.actions.count("resume") == 1
    assert synergy.state == handoff.SynergyState(enabled=True, running=True)


def test_state_store_persists_owned_lease_privately_across_instances(rig, tmp_path):
    acquire(rig)
    store, _, _ = rig
    directory = tmp_path / "private-state"
    journal = directory / "lease.json"
    expected = store.read()
    assert expected["schema"] == 1
    assert handoff.StateStore(directory).read() == expected
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(journal.stat().st_mode) == 0o600


@pytest.mark.parametrize("contents", ["{", "[]", '{"schema":2,"phase":"paused"}', '{"schema":1,"phase":"other"}'])
def test_malformed_journal_blocks_mutation(tmp_path, contents):
    directory = tmp_path / "private-state"
    directory.mkdir(mode=0o700)
    journal = directory / "lease.json"
    journal.write_text(contents)
    journal.chmod(0o600)
    store = handoff.StateStore(directory)
    with pytest.raises(handoff.SurfaceError):
        store.read()
    synergy = FakeSynergy(store)
    owner = handoff.Coordinator(store, synergy)
    owner.step(sample(1))
    assert synergy.actions == []
    assert journal.read_text() == contents


class FragmentedSocket:
    def __init__(self, data, fragment=1):
        self.data = data
        self.fragment = fragment
        self.requests = []

    def recv(self, count):
        self.requests.append(count)
        amount = min(count, self.fragment, len(self.data))
        result, self.data = self.data[:amount], self.data[amount:]
        return result


def test_short_bytescodec_request_has_length_header():
    payload = b'{"t":"VideoConnCount","c":null}'
    assert handoff.encode_frame(payload) == bytes([len(payload) << 2]) + payload


@pytest.mark.parametrize("length,header", [(0, b"\x00"), (63, b"\xfc"), (64, b"\x01\x01"), (16383, b"\xfd\xff"), (16384, b"\x02\x00\x01")])
def test_bytescodec_length_boundaries_match_wire_contract(length, header):
    payload = b"x" * length
    assert handoff.encode_frame(payload) == header + payload


@pytest.mark.parametrize("length", [0, 1, 63, 64, 16383, 16384])
@pytest.mark.parametrize("fragment", [1, 7, 32768])
def test_recv_frame_handles_partial_headers_and_payloads(length, fragment):
    payload = b"x" * length
    sock = FragmentedSocket(handoff.encode_frame(payload), fragment=fragment)
    assert handoff.recv_frame(sock) == payload
    assert sock.data == b""


def test_recv_frame_does_not_consume_next_message():
    sock = FragmentedSocket(handoff.encode_frame(b"first") + handoff.encode_frame(b"second"), fragment=32768)
    assert handoff.recv_frame(sock) == b"first"
    assert handoff.recv_frame(sock) == b"second"


@pytest.mark.parametrize("wire", [b"", b"\x01", b"\x02\x00", b"\x03\x00\x00", b"\x04", b"\x0cxy"])
def test_recv_frame_rejects_eof_in_headers_or_payload(wire):
    with pytest.raises(handoff.SurfaceError):
        handoff.recv_frame(FragmentedSocket(wire))


def test_recv_frame_rejects_oversized_header_before_reading_payload():
    length = 16385
    header = ((length << 2) | 2).to_bytes(3, "little")
    sock = FragmentedSocket(header, fragment=32768)
    with pytest.raises(handoff.SurfaceError):
        handoff.recv_frame(sock)
    assert sum(sock.requests) <= 3


def test_recv_frame_preserves_socket_timeout_as_surface_failure():
    class TimedOutSocket:
        def recv(self, count):
            raise TimeoutError("read deadline")

    with pytest.raises(handoff.SurfaceError):
        handoff.recv_frame(TimedOutSocket())
