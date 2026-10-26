"""Declarative delivery tests using real rendering and isolated activation tools."""

import json
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
JOB = "private_Library/LaunchAgents/dev.dotfiles.synergy-handoff.plist.tmpl"
CONFIG = "private_dot_config/synergy-handoff/private_config.json.tmpl"
HOOK = "run_onchange_after_load-synergy-handoff.sh.tmpl"
SETUP = ROOT / "dot_local/bin/executable_synergy-handoff-setup"
SOURCES = ["dot_local/bin/executable_synergy-handoff", "dot_local/bin/executable_synergy-handoff-setup", JOB, CONFIG]
LABEL = "dev.dotfiles.synergy-handoff"


def render(path, **data):
    values = {
        "chezmoi": {"os": "darwin", "homeDir": "/Users/Owner's Home & <Tools>"},
        "machine_type": "mac-mini",
        **data,
    }
    result = subprocess.run([
        "chezmoi", "--config", "/dev/null", "--config-format", "toml",
        "--source", str(ROOT), "--override-data", json.dumps(values),
        "execute-template", "--file", str(ROOT / path),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize("enabled", [None, True, False])
def test_config_and_job_share_real_boolean_enable_state(enabled):
    values = {} if enabled is None else {"synergy_handoff_enabled": enabled}
    expected = True if enabled is None else enabled
    config = json.loads(render(CONFIG, **values))
    job = plistlib.loads(render(JOB, **values).encode())
    assert type(config["enabled"]) is bool
    assert config["enabled"] is expected
    assert job["Disabled"] is not expected
    assert config["interval"] == 0.5


def test_rendered_config_and_xml_preserve_quoted_paths_and_spaces():
    home = '/Users/Owner\'s Home & <Tools> "Desk"'
    python = '/opt/Existing Python & "Tools"/python3.12'
    app = '/Applications/Team & "Friends" <Synergy>.app'
    values = {"chezmoi": {"os": "darwin", "homeDir": home},
              "synergy_handoff_python": python, "synergy_app_path": app}
    config = json.loads(render(CONFIG, **values))
    job = plistlib.loads(render(JOB, **values).encode())
    assert config["synergy_app"] == app
    assert config["rustdesk_app"] == "/Applications/RustDesk.app"
    assert job["ProgramArguments"] == [python, home + "/.local/bin/synergy-handoff", "run"]


def test_mac_mini_job_runs_existing_versioned_python_and_restarts_only_on_failure():
    job = plistlib.loads(render(JOB).encode())
    assert job["Label"] == LABEL
    assert job["ProgramArguments"] == [
        "/opt/homebrew/bin/python3.12", "/Users/Owner's Home & <Tools>/.local/bin/synergy-handoff", "run",
    ]
    assert job["LimitLoadToSessionType"] == "Aqua"
    assert job["RunAtLoad"] is True
    assert job["KeepAlive"] == {"SuccessfulExit": False}
    assert job["ThrottleInterval"] >= 1
    assert job["Umask"] == 0o077
    assert job["ProcessType"] == "Background"
    assert "StartInterval" not in job


@pytest.mark.parametrize("platform,machine,expected", [
    ("darwin", "mac-mini", True),
    ("darwin", "macbook", False),
    ("linux", "mac-mini", False),
    ("linux", "omarchy", False),
])
def test_actual_chezmoi_apply_limits_handoff_targets_to_mac_mini(tmp_path, platform, machine, expected):
    source = tmp_path / "isolated source"
    destination = tmp_path / "Fresh Home & Tools"
    source.mkdir()
    destination.mkdir()
    for relative in [*SOURCES, ".chezmoiignore"]:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    values = {"chezmoi": {"os": platform, "homeDir": str(destination)}, "machine_type": machine}
    result = subprocess.run([
        "chezmoi", "--config", "/dev/null", "--config-format", "toml",
        "--source", str(source), "--destination", str(destination),
        "--persistent-state", str(tmp_path / "chezmoi-state.boltdb"),
        "--override-data", json.dumps(values), "--error-on-conflict",
        "apply", "--parent-dirs", "--include=dirs,files",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    targets = [destination / ".local/bin/synergy-handoff",
               destination / ".local/bin/synergy-handoff-setup",
               destination / "Library/LaunchAgents/dev.dotfiles.synergy-handoff.plist",
               destination / ".config/synergy-handoff/config.json"]
    assert [target.exists() for target in targets] == [expected] * 4
    if expected:
        assert all(target.stat().st_mode & 0o111 for target in targets[:2])
        assert targets[-1].stat().st_mode & 0o777 == 0o600
        assert json.loads(targets[-1].read_text())["enabled"] is True
        assert plistlib.loads(targets[-2].read_bytes())["Label"] == LABEL
    assert not (destination / "Library/Application Support/dotfiles/synergy-handoff").exists()


@pytest.mark.parametrize("enabled", [True, False])
def test_real_activation_hook_executes_only_quoted_managed_setup(tmp_path, enabled):
    home = tmp_path / "Owner's Home & Tools"
    setup = home / ".local/bin/synergy-handoff-setup"
    setup.parent.mkdir(parents=True)
    setup.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n")
    setup.chmod(0o700)
    text = render(HOOK, chezmoi={"os": "darwin", "homeDir": str(home)}, synergy_handoff_enabled=enabled)
    syntax = subprocess.run(["bash", "-n"], input=text, capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr
    result = subprocess.run(["bash"], input=text, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "activate\n"


@pytest.mark.parametrize("changed", [
    {"synergy_handoff_enabled": False},
    {"synergy_handoff_python": "/opt/Other Python/python3.12"},
    {"synergy_app_path": "/Applications/Other Synergy.app"},
])
def test_onchange_hook_changes_when_effective_job_or_configuration_changes(changed):
    assert render(HOOK, **changed) != render(HOOK)


@pytest.mark.parametrize("platform,machine", [("darwin", "macbook"), ("linux", "mac-mini"), ("linux", "omarchy")])
def test_activation_hook_cannot_call_setup_outside_mac_mini(platform, machine):
    text = render(HOOK, chezmoi={"os": platform, "homeDir": "/nonexistent/home"}, machine_type=machine)
    result = subprocess.run(["bash"], input=text, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.fixture
def activation(tmp_path):
    home = tmp_path / "Owner's Home & Tools"
    tools = tmp_path / "fake tools"
    tools.mkdir()
    python = tools / "existing python3.12"
    python.symlink_to(sys.executable)
    job = home / f"Library/LaunchAgents/{LABEL}.plist"
    job.parent.mkdir(parents=True)
    job.write_text(render(JOB, chezmoi={"os": "darwin", "homeDir": str(home)}, synergy_handoff_python=str(python)))
    helper = home / ".local/bin/synergy-handoff"
    helper.parent.mkdir(parents=True)
    helper.write_text(
        "import json,os,pathlib,sys\n"
        "root=pathlib.Path(os.environ['FAKE_TOOLS'])\n"
        "with (root/'helper.jsonl').open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n"
        "print(json.dumps({'status':'fixture-only'}))\n"
    )
    fakes = {
        "/usr/bin/uname": "#!/bin/sh\nprintf 'Darwin\\n'\n",
        "/usr/bin/id": "#!/bin/sh\nprintf '501\\n'\n",
        "/usr/bin/plutil": f"#!{sys.executable}\nimport plistlib,sys\nplistlib.load(open(sys.argv[-1],'rb'))\n",
        "/usr/libexec/PlistBuddy": f"#!{sys.executable}\n" + """import plistlib,sys
data=plistlib.load(open(sys.argv[-1],'rb'))
for key in sys.argv[2].removeprefix('Print :').split(':'):
    data=data[int(key)] if isinstance(data,list) else data[key]
print(str(data).lower() if isinstance(data,bool) else data)
""",
        "/bin/launchctl": f"#!{sys.executable}\n" + """import json,os,pathlib,sys
root=pathlib.Path(os.environ['FAKE_TOOLS'])
with (root/'calls.jsonl').open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
""",
    }
    text = SETUP.read_text()
    for original, contents in fakes.items():
        executable = tools / Path(original).name
        executable.write_text(contents)
        executable.chmod(0o700)
        text = text.replace(original, shlex.quote(str(executable)))
    setup = home / ".local/bin/synergy-handoff-setup"
    setup.write_text(text)
    setup.chmod(0o700)

    def run(*arguments):
        return subprocess.run(["bash", str(setup), *arguments],
                              env={**os.environ, "HOME": str(home), "FAKE_TOOLS": str(tools)},
                              capture_output=True, text=True)

    def calls(name="calls.jsonl"):
        path = tools / name
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    return run, calls, job, helper, home


def test_setup_activation_changes_only_handoff_job_and_preserves_managed_files(activation):
    run, calls, job, helper, _ = activation
    before = {path: path.read_bytes() for path in [job, helper]}
    result = run("activate")
    assert result.returncode == 0, result.stderr
    assert calls() == [
        ["enable", "gui/501/" + LABEL],
        ["bootout", "gui/501/" + LABEL],
        ["bootstrap", "gui/501", str(job)],
    ]
    assert calls("helper.jsonl") == []
    assert {path: path.read_bytes() for path in before} == before


def test_setup_status_reads_helper_without_touching_launchd(activation):
    run, calls, _, _, _ = activation
    result = run("status")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"status": "fixture-only"}
    assert calls("helper.jsonl") == [["status"]]
    assert calls() == []


def test_disabled_setup_unloads_only_handoff_without_running_apps(activation):
    run, calls, job, _, _ = activation
    data = plistlib.loads(job.read_bytes())
    data["Disabled"] = True
    job.write_bytes(plistlib.dumps(data))
    result = run("activate")
    assert result.returncode == 0, result.stderr
    assert calls() == [["disable", "gui/501/" + LABEL], ["bootout", "gui/501/" + LABEL]]
    assert calls("helper.jsonl") == []


def test_disabled_setup_retains_job_until_owned_restoration_finishes(activation):
    run, calls, job, _, home = activation
    data = plistlib.loads(job.read_bytes())
    data["Disabled"] = True
    job.write_bytes(plistlib.dumps(data))
    journal = home / "Library/Application Support/dotfiles/synergy-handoff/lease.json"
    journal.parent.mkdir(mode=0o700, parents=True)
    journal.write_text('{"schema":1,"phase":"paused"}\n')
    journal.chmod(0o600)
    before = journal.read_bytes()
    result = run("activate")
    assert result.returncode != 0
    assert calls() == []
    assert calls("helper.jsonl") == []
    assert journal.read_bytes() == before


def test_missing_runtime_refuses_activation_before_any_job_mutation(activation):
    run, calls, _, helper, _ = activation
    helper.unlink()
    result = run("activate")
    assert result.returncode != 0
    assert calls() == []


def test_setup_script_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(SETUP)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
