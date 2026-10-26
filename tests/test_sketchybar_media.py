"""Exercise media polling through its shell and CLI boundaries."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
BAR = ROOT / "private_dot_config/sketchybar"
SCRIPT = BAR / "plugins/executable_media.sh"


@pytest.fixture
def media(tmp_path):
    tools = tmp_path / "bin"
    tools.mkdir()
    shutil.copyfile(BAR / "executable_icons.sh", tmp_path / "icons.sh")
    calls_path = tmp_path / "calls.jsonl"
    started = tmp_path / "started"
    stub = tools / "stub"
    stub.write_text(f'''#!{sys.executable}
import json, os, sys, time
from pathlib import Path
name = Path(sys.argv[0]).name
with open(os.environ["CALLS"], "a") as stream:
    stream.write(json.dumps([name, *sys.argv[1:]]) + "\\n")
if name != "nowplaying-cli":
    sys.exit(0)
if sys.argv[1] != "get":
    sys.exit(0)
Path(os.environ["STARTED"]).touch()
time.sleep(float(os.environ.get("QUERY_DELAY", "0")))
if os.environ.get("QUERY_FAIL"):
    sys.exit(1)
payload = os.environ["METADATA"]
if "--json" in sys.argv:
    print(payload)
else:
    try:
        value = json.loads(payload).get(sys.argv[2])
    except (ValueError, AttributeError):
        value = payload
    print("null" if value is None else value)
''')
    stub.chmod(0o755)
    for name in ("nowplaying-cli", "sketchybar"):
        (tools / name).symlink_to(stub)
    jq = shutil.which("jq")
    assert jq, "jq is required by the managed SketchyBar configuration"
    (tools / "jq").symlink_to(jq)
    lockf = shutil.which("lockf")
    if lockf:
        (tools / "lockf").symlink_to(lockf)
    else:
        # CI runs Linux; keep native inherited-descriptor locking semantics.
        portable_lockf = tools / "lockf"
        portable_lockf.write_text(f'''#!{sys.executable}
import fcntl, sys
try:
    fcntl.flock(int(sys.argv[-1]), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(75)
''')
        portable_lockf.chmod(0o755)

    base_env = os.environ | {
        "PATH": str(tools),
        "CONFIG_DIR": str(tmp_path),
        "TMPDIR": str(tmp_path),
        "NAME": "media",
        "SENDER": "routine",
        "BUTTON": "left",
        "CALLS": str(calls_path),
        "STARTED": str(started),
        "METADATA": json.dumps({"title": "Song", "artist": "Artist", "playbackRate": 1}),
    }

    def calls():
        if not calls_path.exists():
            return []
        return [json.loads(line) for line in calls_path.read_text().splitlines()]

    def run(payload=None, **extra):
        env = base_env | extra
        if payload is not None:
            env["METADATA"] = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(["/bin/bash", str(SCRIPT)], env=env,
                              capture_output=True, text=True, timeout=5)

    return SimpleNamespace(run=run, calls=calls, env=base_env, tools=tools,
                           started=started, directory=tmp_path)


def metadata_calls(media):
    return [call for call in media.calls() if call[:2] == ["nowplaying-cli", "get"]]


def bar_calls(media):
    return [call for call in media.calls() if call[0] == "sketchybar"]


def test_one_query_preserves_playing_label(media):
    result = media.run()
    assert result.returncode == 0, result.stderr
    assert metadata_calls(media) == [["nowplaying-cli", "get", "--json", "title", "artist", "playbackRate"]]
    call, = bar_calls(media)
    assert "label=Song - Artist" in call
    assert "drawing=on" in call
    assert "icon=󰐊" in call


@pytest.mark.parametrize("artist", [None, "", "null", "(null)"])
def test_absent_artist_shows_title_only(media, artist):
    assert media.run({"title": "Song", "artist": artist, "playbackRate": 0}).returncode == 0
    assert "label=Song" in bar_calls(media)[-1]
    assert "icon=󰏤" in bar_calls(media)[-1]


@pytest.mark.parametrize("payload", [
    {"title": None}, {"title": "null"}, {"title": "(null)"},
    {"title": {"unexpected": "object"}}, "broken json", "null", "[]",
])
def test_unavailable_metadata_hides_and_recovers(media, payload):
    assert media.run(payload).returncode == 0
    assert "drawing=off" in bar_calls(media)[-1]
    assert media.run().returncode == 0
    assert "label=Song - Artist" in bar_calls(media)[-1]


def test_command_failure_hides_and_recovers(media):
    assert media.run(QUERY_FAIL="1").returncode == 0
    assert "drawing=off" in bar_calls(media)[-1]
    assert media.run().returncode == 0
    assert "drawing=on" in bar_calls(media)[-1]


def test_metadata_stays_inert_label_text(media):
    sentinel = media.directory / "must-not-exist"
    title = f'$(touch "{sentinel}") `false` "quoted"'
    artist = "A\\B; name"
    assert media.run({"title": title, "artist": artist, "playbackRate": "1.0"}).returncode == 0
    assert f"label={title} - {artist}" in bar_calls(media)[-1]
    assert "icon=󰐊" in bar_calls(media)[-1]
    assert not sentinel.exists()


@pytest.mark.parametrize("dependency", ["nowplaying-cli", "jq", "lockf"])
def test_missing_dependency_hides_without_query(media, dependency):
    (media.tools / dependency).unlink()
    assert media.run().returncode == 0
    assert "drawing=off" in bar_calls(media)[-1]
    assert metadata_calls(media) == []


def test_overlapping_refresh_skips_without_queue(media):
    first = subprocess.Popen(["/bin/bash", str(SCRIPT)],
                             env=media.env | {"QUERY_DELAY": "1"},
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 3
        while not media.started.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert media.started.exists(), "first refresh did not reach metadata query"
        second = media.run()
        assert second.returncode == 0, second.stderr
        assert first.poll() is None, "second refresh waited for the active refresh"
        assert len(metadata_calls(media)) == 1
        assert first.wait(timeout=4) == 0
    finally:
        if first.poll() is None:
            first.terminate()
        first.communicate(timeout=4)
    assert media.run().returncode == 0
    assert len(metadata_calls(media)) == 2


def test_lockfile_survives_without_stale_ownership(media):
    assert media.run().returncode == 0
    lock = media.directory / f"sketchybar-media-{os.getuid()}.lock"
    assert lock.exists()
    assert lock.stat().st_mode & 0o777 == 0o600
    lock.write_text("retained inode")
    assert media.run().returncode == 0
    assert len(metadata_calls(media)) == 2
    assert lock.read_text() == "retained inode"


@pytest.mark.parametrize("sender,button,expected", [
    ("mouse.exited.global", "left", ["sketchybar", "--set", "media", "popup.drawing=off"]),
    ("mouse.clicked", "right", ["nowplaying-cli", "togglePlayPause"]),
])
def test_controls_work_during_active_refresh(media, sender, button, expected):
    first = subprocess.Popen(["/bin/bash", str(SCRIPT)],
                             env=media.env | {"QUERY_DELAY": "1"},
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 3
        while not media.started.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert media.started.exists()
        assert media.run(SENDER=sender, BUTTON=button).returncode == 0
        assert expected in media.calls()
        assert len(metadata_calls(media)) == 1
    finally:
        if first.poll() is None:
            first.terminate()
        first.communicate(timeout=4)
