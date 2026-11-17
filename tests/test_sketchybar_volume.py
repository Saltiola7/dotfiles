import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BAR = ROOT / "private_dot_config/sketchybar"


@pytest.fixture
def volume(tmp_path):
    for name in ("icons", "colors"):
        shutil.copyfile(BAR / f"executable_{name}.sh", tmp_path / f"{name}.sh")
    state = tmp_path / "state.json"
    state.write_text('{"volume": 42, "muted": false}')
    log = tmp_path / "calls.jsonl"
    stub = tmp_path / "stub"
    stub.write_text(f'''#!{shutil.which("python3")}
import json, os, re, sys
from pathlib import Path
with open(os.environ["CALLS"], "a") as f:
    f.write(json.dumps([Path(sys.argv[0]).name, *sys.argv[1:]]) + "\\n")
if Path(sys.argv[0]).name != "osascript":
    sys.exit(0)
p = Path(os.environ["STATE"])
s = json.loads(p.read_text())
command = " ".join(sys.argv[1:])
if os.environ.get("READ_FAIL") and "set volume" not in command:
    sys.exit(1)
if "set volume" in command:
    if os.environ.get("WRITE_FAIL"):
        sys.exit(1)
    if not os.environ.get("DEVICE_CONTROLLED"):
        match = re.search(r"output volume (\\d+)", command)
        if match:
            s["volume"] = int(match[1])
        elif "output muted" in command:
            s["muted"] = not s["muted"]
        p.write_text(json.dumps(s))
elif "output volume" in command:
    print(s["volume"])
elif "output muted" in command:
    print(str(s["muted"]).lower())
else:
    sys.exit(2)
''')
    stub.chmod(0o755)
    for name in ("sketchybar", "osascript", "open"):
        (tmp_path / name).symlink_to(stub)

    def run(name="volume", sender="forced", **extra):
        log.write_text("")
        result = subprocess.run(
            ["bash", str(BAR / "plugins/executable_volume.sh")],
            env=os.environ | {"PATH": f"{tmp_path}:{os.environ['PATH']}",
                "CONFIG_DIR": str(tmp_path), "STATE": str(state), "CALLS": str(log),
                "NAME": name, "SENDER": sender, "BUTTON": "left"} | extra,
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(state.read_text()), [json.loads(line) for line in log.read_text().splitlines()]

    return run


def test_popup_and_mute_are_separate(volume):
    state, calls = volume(sender="mouse.clicked")
    assert state == {"volume": 42, "muted": False}
    assert any("popup.drawing=toggle" in call for call in calls)
    state, calls = volume("volume.mute", "mouse.clicked")
    assert state["muted"] is True
    assert any("label=Unmute" in call for call in calls)
    _, calls = volume(sender="mouse.exited.global")
    assert any("popup.drawing=off" in call for call in calls)


def test_slider_scroll_and_external_refresh(volume):
    state, calls = volume("volume.slider", "mouse.clicked", PERCENTAGE="73")
    assert state == {"volume": 73, "muted": False}
    assert any("slider.percentage=73" in call and "label=73%" in call for call in calls)
    state, _ = volume(sender="mouse.scrolled", SCROLL_DELTA="30")
    assert state["volume"] == 100
    state, _ = volume(sender="mouse.scrolled", SCROLL_DELTA="-30")
    assert state["volume"] == 0
    _, calls = volume(sender="volume_change")
    assert any("slider.percentage=0" in call for call in calls)


@pytest.mark.parametrize("value", ["", "-1", "101", "1;do shell script", "999999999999999999999"])
def test_invalid_slider_never_writes_audio(volume, value):
    state, calls = volume("volume.slider", "mouse.clicked", PERCENTAGE=value)
    assert state["volume"] == 42
    assert not any(call[0] == "osascript" and "set volume" in " ".join(call) for call in calls)


@pytest.mark.parametrize("failure", ["READ_FAIL", "WRITE_FAIL", "DEVICE_CONTROLLED"])
def test_audio_failures_visible_and_recoverable(volume, failure):
    state, calls = volume("volume.slider", "mouse.clicked", PERCENTAGE="73", **{failure: "1"})
    assert state["volume"] == 42
    assert any("label=Unavailable" in call or "label=Device-controlled" in call for call in calls)
    _, calls = volume()
    assert any("label=42%" in call for call in calls)


@pytest.mark.parametrize("delta", ["1+1", "--2", "999999999999999999999"])
def test_invalid_scroll_never_writes_audio(volume, delta):
    state, calls = volume(sender="mouse.scrolled", SCROLL_DELTA=delta)
    assert state["volume"] == 42
    assert not any(call[0] == "osascript" and "set volume" in " ".join(call) for call in calls)


def test_native_menu_is_not_covered_by_helper():
    config = (BAR / "executable_sketchybarrc").read_text()
    assert "topmost=window" in config
    assert "exec-and-forget sketchybar-toggle" not in (ROOT / "dot_aerospace.toml.tmpl").read_text()
    assert "nohup sketchybar-toggle" not in (ROOT / "run_onchange_after_start-sketchybar-stack.sh.tmpl").read_text()


@pytest.mark.parametrize("running", [False, True])
def test_bar_starts_hover_helper_only_when_missing(tmp_path, running):
    (tmp_path / "items").mkdir()
    for name in ("colors", "icons"):
        shutil.copyfile(BAR / f"executable_{name}.sh", tmp_path / f"{name}.sh")
    for name in ("apple", "spaces", "front_app", "media", "clockify", "clock", "battery",
                 "brew", "docker", "volume", "wifi", "disk", "cpu", "memory"):
        (tmp_path / "items" / f"{name}.sh").write_text("")
    for name, body in {
        "sketchybar": "exit 0",
        "pgrep": f"exit {0 if running else 1}",
        "sketchybar-toggle": 'echo started >> "$CONFIG_DIR/helper.log"',
    }.items():
        path = tmp_path / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o755)
    subprocess.run(["bash", "-c", 'source "$1"; wait', "bash", str(BAR / "executable_sketchybarrc")],
        env=os.environ | {"PATH": f"{tmp_path}:{os.environ['PATH']}", "CONFIG_DIR": str(tmp_path)},
        capture_output=True, text=True, check=True)
    assert (tmp_path / "helper.log").exists() is not running
