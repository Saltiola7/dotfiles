"""Offline checks for the narrowly scoped macOS Synergy recovery jobs."""
import json
import os
import plistlib
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
RECOVERY = ROOT / "dot_local/bin/executable_synergy-recovery"
SETUP = ROOT / "dot_local/bin/executable_synergy-setup"
APP = "/Applications/Synergy.app"
IDENTITY = "501|100|50|Mon Oct 19 10:00:00 2026|/tmp/synergy-core|Mon Oct 19 09:00:00 2026"

CLOSING = ["SecureSocket::freeSSL()", "SocketMultiplexer::removeSocket()",
           "ArchMultithreadPosix::waitCondVar()", "__psynch_cvwait"]
WRITING = ["SocketMultiplexer::serviceThread()", "TCPSocket::serviceConnected()",
           "SecureSocket::doWrite()",
           "SecureSocket::secureWrite()", "std::__1::mutex::lock()", "__psynch_mutexwait"]


def branch(names, leaf_count=1000):
    return "\n".join("+ " + "! " * i + f"{leaf_count if i == len(names) - 1 else 1000} {name}"
                     for i, name in enumerate(names))


def sample(closing=CLOSING, writing=WRITING, leaf_count=1000, same_thread=False):
    second = "" if same_thread else "1000 Thread_200: service\n"
    return (f"Process: synergy-core [100]\nPath: {APP}/Contents/MacOS/synergy-core\n"
            "Parent Process: synergy-service [50]\nCall graph:\n"
            "1000 Thread_100: main\n" + branch(closing) + "\n" + second
            + branch(writing, leaf_count) + "\nTotal number in stack: 1000\n")


def classify(tmp_path, text, pid="100", parent="50", app=APP):
    path = tmp_path / "sample.txt"
    path.write_text(text)
    return subprocess.run(["bash", str(RECOVERY), "--classify-sample", str(path),
                           pid, parent, app], capture_output=True, text=True)


@pytest.mark.parametrize("text,code", [
    (sample(), 0),
    (sample(leaf_count=900), 0),
    (sample(closing=["CFRunLoopRun()"], writing=["poll()"]), 1),
    (sample(writing=["poll()"]), 1),
    (sample(closing=list(reversed(CLOSING))), 1),
    (sample(leaf_count=899), 1),
    (sample(same_thread=True), 1),
    (sample().replace(branch(CLOSING), branch(CLOSING[:1]) + "\n+ 1000 unrelated()\n"
                      + branch(CLOSING[1:])), 1),
    (sample(closing=["CFRunLoopRun()"], writing=["poll()"])
     + "\n".join(CLOSING + WRITING), 1),
    (sample().replace("synergy-core [100]", "synergy-core [101]"), 2),
    (sample().replace("synergy-service [50]", "synergy-service [51]"), 2),
    (sample().replace(f"Path: {APP}", "Path: /tmp/Synergy.app"), 2),
    (sample().split("Total number in stack:")[0], 2),
])
def test_classifier_requires_two_dominant_ordered_thread_trees(tmp_path, text, code):
    result = classify(tmp_path, text)
    assert result.returncode == code, result.stderr


@pytest.fixture
def recovery(tmp_path):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    fixture = tmp_path / "sample.txt"
    fixture.write_text(sample())
    identity = tmp_path / "identity"
    identity.write_text(IDENTITY + "\n")
    actions = tmp_path / "actions"
    calls = tmp_path / "candidate-calls"
    harness = f'''source {shlex.quote(str(RECOVERY))}
state_dir="$STATE_DIR"
app_path=/Applications/Synergy.app
recovery_enabled=true
current_time() {{ printf '%s\\n' "$TEST_NOW"; }}
candidate_identity() {{
    local count=0
    [[ ! -f "$CALL_FILE" ]] || read -r count <"$CALL_FILE"
    count=$((count+1)); printf '%s\\n' "$count" >"$CALL_FILE"
    if (( CHANGE_AT > 0 && count >= CHANGE_AT )); then
        printf '%s\\n' changed-identity
    else
        cat "$IDENTITY_FILE"
    fi
}}
sample_core() {{
    [[ "$SAMPLE_FAIL" == 0 ]] || return 1
    cp "$SAMPLE_FILE" "$2"
}}
terminate_core() {{ printf '%s\\n' "$*" >>"$ACTION_FILE"; set_status recovery-requested; return "$TERM_RC"; }}
check_once
'''

    def run(now=1000, text=None, **options):
        if text is not None:
            fixture.write_text(text)
        calls.unlink(missing_ok=True)
        env = {**os.environ, "STATE_DIR": str(state), "TEST_NOW": str(now),
               "SAMPLE_FILE": str(fixture), "IDENTITY_FILE": str(identity),
               "ACTION_FILE": str(actions), "CALL_FILE": str(calls),
               "SAMPLE_FAIL": "0", "CHANGE_AT": "0", "TERM_RC": "0",
               **{key: str(value) for key, value in options.items()}}
        result = subprocess.run(["bash", "-c", harness], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        return (state / "status").read_text().split()[1]

    return run, state, identity, actions


@pytest.mark.parametrize("separation,expected", [(29, "suspect"), (30, "recovery-requested"),
                                                (180, "recovery-requested"), (181, "suspect")])
def test_recovery_requires_two_observations_in_window(recovery, separation, expected):
    run, state, _, actions = recovery
    assert run() == "suspect"
    assert not actions.exists()
    assert run(1000 + separation) == expected
    assert actions.exists() == (expected == "recovery-requested")
    if actions.exists():
        assert actions.read_text().splitlines() == [f"{IDENTITY} 100"]
        assert not (state / "pending").exists()
        assert (state / "cooldown").read_text().strip() == str(1000 + separation)


@pytest.mark.parametrize("kind,expected", [("healthy", "checked-no-deadlock"), ("failure", "sample-unavailable"),
                                           ("unrecognized", "sample-unrecognized")])
def test_non_deadlock_observation_clears_pending(recovery, kind, expected):
    run, state, _, actions = recovery
    assert run() == "suspect"
    options = {"SAMPLE_FAIL": 1} if kind == "failure" else {}
    text = sample(writing=["poll()"]) if kind == "healthy" else None
    if kind == "unrecognized":
        text = "truncated diagnostic\n"
    assert run(1060, text=text, **options) == expected
    assert not (state / "pending").exists()
    assert not actions.exists()


@pytest.mark.parametrize("age,expected", [(299, "cooldown"), (300, "suspect"), (-1, "cooldown")])
def test_cooldown_and_clock_rollback_never_signal(recovery, age, expected):
    run, state, _, actions = recovery
    (state / "cooldown").write_text("1000\n")
    assert run(1000 + age) == expected
    assert not actions.exists()


def test_changed_process_identity_needs_new_observations(recovery):
    run, _, identity, actions = recovery
    assert run() == "suspect"
    identity.write_text(IDENTITY.replace("10:00:00", "10:01:00") + "\n")
    assert run(1060) == "suspect"
    assert not actions.exists()


@pytest.mark.parametrize("change_at", [2, 3])
def test_identity_is_rechecked_before_any_termination(recovery, change_at):
    run, state, _, actions = recovery
    assert run() == "suspect"
    assert run(1060, CHANGE_AT=change_at) == "identity-changed"
    assert not actions.exists()
    assert not (state / "pending").exists()


def test_no_candidate_never_samples_or_signals(recovery):
    run, state, identity, actions = recovery
    assert run() == "suspect"
    identity.write_text("")
    assert run(1060) == "no-owned-core"
    assert not (state / "pending").exists()
    assert not actions.exists()


@pytest.mark.parametrize("missing", ["none", "gui", "owned-core", "owned-service", "ambiguous-core"])
def test_candidate_identity_requires_gui_and_one_same_user_service_core(tmp_path, missing):
    uid = os.getuid()
    lines = [f"{uid} 10 1 Mon Oct 19 09:00:00 2026 {APP}/Contents/MacOS/Synergy",
             f"{uid} 50 10 Mon Oct 19 09:00:00 2026 {APP}/Contents/MacOS/synergy-service",
             f"{uid} 100 50 Mon Oct 19 10:00:00 2026 /tmp/synergy-core"]
    if missing == "gui":
        lines.pop(0)
    elif missing == "owned-core":
        lines[2] = lines[2].replace(str(uid), str(uid + 1), 1)
    elif missing == "owned-service":
        lines[1] = lines[1].replace(str(uid), str(uid + 1), 1)
    elif missing == "ambiguous-core":
        lines.append(f"{uid} 101 50 Mon Oct 19 10:00:00 2026 /tmp/synergy-core")
    snapshot = tmp_path / "ps.txt"
    snapshot.write_text("\n".join(lines) + "\n")
    script = (f"source {shlex.quote(str(RECOVERY))}; app_path={shlex.quote(APP)}; "
              f"process_snapshot() {{ cat {shlex.quote(str(snapshot))}; }}; candidate_identity")
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    if missing == "none":
        assert result.stdout.strip() == IDENTITY.replace("501|", f"{uid}|", 1)
    else:
        assert not result.stdout.strip()








@pytest.mark.parametrize("case", ["same", "changed-pid", "changed-start", "gui-quit", "term-fails", "changed-before-kill"])
def test_real_termination_escalates_only_for_unchanged_core(tmp_path, case):
    source = tmp_path / "recovery-without-delay"
    source.write_text(RECOVERY.read_text().replace("/bin/sleep 2", ":"))
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    calls = tmp_path / "signals"
    changed = {
        "changed-pid": IDENTITY.replace("|100|", "|101|"),
        "changed-start": IDENTITY.replace("10:00:00", "10:01:00"),
        "gui-quit": "",
    }.get(case, IDENTITY)
    script = f'''source {shlex.quote(str(source))}
state_dir={shlex.quote(str(state))}
now=1000
current_time() {{ printf '1002\\n'; }}
candidate_identity() {{
    local count=0
    [[ ! -f "$state_dir/candidates" ]] || read -r count <"$state_dir/candidates"
    count=$((count + 1)); printf '%s\\n' "$count" >"$state_dir/candidates"
    if [[ "$CASE" == changed-before-kill && "$count" == 2 ]]; then printf 'changed\\n';
    else printf '%s\\n' "$CANDIDATE"; fi
}}
signal_core() {{
    printf '%s %s\\n' "$1" "$2" >>{shlex.quote(str(calls))}
    if [[ "$1" == TERM && "$CASE" == term-fails ]]; then return 1; fi
    if [[ "$1" == KILL ]]; then
        [[ "$(cat "$state_dir/cooldown")" == 1002 ]] || return 99
        printf 'cooldown-before-kill\\n' >>{shlex.quote(str(calls))}
    fi
}}
terminate_core {shlex.quote(IDENTITY)} 100
'''
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                            env={**os.environ, "CASE": case, "CANDIDATE": changed})
    assert result.returncode == 0, result.stderr
    expected = ["TERM 100"]
    if case == "same":
        expected += ["KILL 100", "cooldown-before-kill"]
    assert calls.read_text().splitlines() == expected
    status = (state / "status").read_text().split()[1]
    assert status == {"same": "forced-recovery-requested", "term-fails": "signal-failed"}.get(case, "recovery-requested")


def render_template(path, **data):
    values = {"chezmoi": {"os": "darwin", "homeDir": "/Users/Owner's & <Tools>"},
              "machine_type": "mac-mini", "synergy_app_path": APP, **data}
    init = ["--init"] if path == ".chezmoi.toml.tmpl" else []
    result = subprocess.run(["chezmoi", "--config", "/dev/null", "--config-format", "toml",
                             "--source", str(ROOT), "--override-data", json.dumps(values),
                             "execute-template", *init, "--file", str(ROOT / path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize("label", ["login", "recovery"])
@pytest.mark.parametrize("enabled", [True, False])
def test_declarative_plists_render_escaped_arguments_and_bounded_jobs(label, enabled):
    app = '/Applications/Team & "Friends" <Synergy>.app'
    home = "/Users/Owner's & <Tools>"
    text = render_template(f"private_Library/LaunchAgents/dev.dotfiles.synergy-{label}.plist.tmpl",
                           synergy_app_path=app, synergy_recovery_enabled=enabled)
    plist = plistlib.loads(text.encode())
    assert plist["Label"] == f"dev.dotfiles.synergy-{label}"
    assert plist["LimitLoadToSessionType"] == "Aqua"
    assert plist["RunAtLoad"] is True
    assert plist["Umask"] == 63
    assert plist["Disabled"] is (not enabled)
    assert "KeepAlive" not in plist
    if label == "login":
        assert plist["ProgramArguments"] == ["/usr/bin/open", "-g", "-a", app]
        assert "StartInterval" not in plist
    else:
        assert plist["ProgramArguments"] == [f"{home}/.local/bin/synergy-recovery"]
        assert plist["StartInterval"] == 60
        assert plist["ProcessType"] == "Background"
        assert plist["EnvironmentVariables"] == {"SYNERGY_RECOVERY_CONTEXT": "launchd"}


@pytest.mark.parametrize("enabled", [True, False])
def test_declarative_configuration_keeps_explicit_enable_value(enabled):
    app = '/Applications/Team & Friends.app'
    text = render_template("private_dot_config/synergy-recovery/private_config.tmpl",
                           synergy_recovery_enabled=enabled, synergy_app_path=app)
    assert text.splitlines() == [str(enabled).lower(), app]


@pytest.fixture
def activation(tmp_path):
    home = tmp_path / "User Home & Friends"
    tools = tmp_path / "fake tools"
    tools.mkdir()
    app = tmp_path / "Applications/Team & Friends.app"
    executables = app / "Contents/MacOS"
    executables.mkdir(parents=True)
    for name in ("Synergy", "synergy-service", "synergy-core"):
        path = executables / name
        path.write_text("#!/bin/sh\nexit 99\n")
        path.chmod(0o700)
    config = home / ".config/synergy-recovery/config"
    config.parent.mkdir(parents=True)
    config.write_text("true\n" + str(app) + "\n")
    agents = home / "Library/LaunchAgents"
    agents.mkdir(parents=True)
    for label in ("login", "recovery"):
        relative = f"private_Library/LaunchAgents/dev.dotfiles.synergy-{label}.plist.tmpl"
        rendered = render_template(relative, chezmoi={"os": "darwin", "homeDir": str(home)},
                                   synergy_app_path=str(app))
        (agents / f"dev.dotfiles.synergy-{label}.plist").write_text(rendered)
    bin_dir = home / ".local/bin"
    bin_dir.mkdir(parents=True)
    recovery = bin_dir / "synergy-recovery"
    recovery.write_bytes(RECOVERY.read_bytes())
    recovery.chmod(0o700)
    fakes = {
        "/usr/bin/uname": "#!/bin/sh\nprintf 'Darwin\\n'\n",
        "/bin/sleep": "#!/bin/sh\nexit 0\n",
        "/usr/bin/plutil": f"#!{sys.executable}\nimport plistlib,sys\n"
                              "with open(sys.argv[-1], 'rb') as f: plistlib.load(f)\n",
        "/usr/bin/shasum": f"#!{sys.executable}\nimport hashlib,sys\n"
                              "print(hashlib.sha256(open(sys.argv[-1], 'rb').read()).hexdigest() + '  ' + sys.argv[-1])\n",
        "/bin/launchctl": f"#!{sys.executable}\n" + r'''import json, os, pathlib, sys
root = pathlib.Path(os.environ["FAKE_LAUNCHD"])
args = sys.argv[1:]
with (root / "calls.jsonl").open("a") as f: f.write(json.dumps(args) + "\n")
jobfile = root / "jobs.json"
jobs = set(json.loads(jobfile.read_text())) if jobfile.exists() else set()
verb = args[0]
if verb == "print": sys.exit(0 if args[1].split("/")[-1] in jobs else 1)
if verb == "bootstrap": jobs.add(pathlib.Path(args[2]).stem)
if verb == "bootout": jobs.discard(args[1].split("/")[-1])
jobfile.write_text(json.dumps(sorted(jobs)))
if verb == "kickstart":
    state = pathlib.Path(os.environ["HOME"]) / "Library/Application Support/dotfiles/synergy-recovery"
    (state / "status").write_text("1000 checked-no-deadlock context=" + os.environ["FAKE_CONTEXT"] + " at=2026-10-19T00:00:00Z\n")
''',
    }
    setup_text = SETUP.read_text()
    for original, body in fakes.items():
        fake = tools / Path(original).name
        fake.write_text(body)
        fake.chmod(0o700)
        setup_text = setup_text.replace(original, shlex.quote(str(fake)))
    setup = bin_dir / "synergy-setup"
    setup.write_text(setup_text)
    setup.chmod(0o700)
    state = home / "Library/Application Support/dotfiles/synergy-recovery"

    def run(context="launchd", operation="activate"):
        env = {**os.environ, "HOME": str(home), "FAKE_LAUNCHD": str(tools), "FAKE_CONTEXT": context}
        result = subprocess.run(["bash", str(setup), operation], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        return result.stdout

    def calls():
        return [json.loads(line) for line in (tools / "calls.jsonl").read_text().splitlines()]

    return run, calls, home, config, agents, state, app


def managed_files(home):
    paths = [home / ".config/synergy-recovery/config", *list((home / "Library/LaunchAgents").glob("*.plist")),
             *list((home / ".local/bin").iterdir())]
    return {str(path): path.read_bytes() for path in paths}


def test_activation_is_idempotent_and_reloads_only_changed_plist(activation):
    run, calls, home, _, agents, state, _ = activation
    before = managed_files(home)
    for _ in range(2):
        assert "checked-no-deadlock context=launchd" in run()
    assert sum(call[0] == "bootstrap" for call in calls()) == 2
    assert not any(call[0] == "bootout" for call in calls())
    assert len(list(state.glob("loaded-*.sha256"))) == 2
    assert managed_files(home) == before
    changed = agents / "dev.dotfiles.synergy-recovery.plist"
    plist = plistlib.loads(changed.read_bytes())
    plist["Nice"] = 5
    changed.write_bytes(plistlib.dumps(plist))
    before = managed_files(home)
    run()
    bootstrap = [call for call in calls() if call[0] == "bootstrap"]
    bootout = [call for call in calls() if call[0] == "bootout"]
    assert len(bootstrap) == 3
    assert len(bootout) == 1
    assert bootstrap[-1][-1].endswith("dev.dotfiles.synergy-recovery.plist")
    assert bootout[0][-1].endswith("dev.dotfiles.synergy-recovery")
    assert managed_files(home) == before
    assert not list(home.rglob(".install.*"))


@pytest.mark.parametrize("context", ["launchd", "manual"])
def test_activation_requires_sampling_from_launchd_context(activation, context):
    run, _, _, _, _, _, _ = activation
    output = run(context=context)
    assert f"checked-no-deadlock context={context}" in output
    assert ("has not yet verified" in output) == (context != "launchd")


def test_disabled_activation_unloads_jobs_without_changing_managed_files(activation):
    run, calls, home, config, _, state, app = activation
    run()
    (state / "pending").write_text("old observation\n")
    config.write_text("false\n" + str(app) + "\n")
    before = managed_files(home)
    run()
    assert managed_files(home) == before
    assert not (state / "pending").exists()
    assert not list(state.glob("loaded-*.sha256"))
    for label in ("login", "recovery"):
        suffix = f"dev.dotfiles.synergy-{label}"
        assert any(call[0] == "disable" and call[-1].endswith(suffix) for call in calls())
        assert any(call[0] == "bootout" and call[-1].endswith(suffix) for call in calls())


def test_disabled_managed_config_prevents_watchdog_process_inspection(tmp_path):
    home = tmp_path / "home"
    config = home / ".config/synergy-recovery/config"
    config.parent.mkdir(parents=True)
    config.write_text("false\n/Applications/Synergy.app\n")
    state = home / "Library/Application Support/dotfiles/synergy-recovery"
    state.mkdir(parents=True)
    (state / "pending").write_text("old observation\n")
    uname = tmp_path / "uname"
    uname.write_text("#!/bin/sh\nprintf 'Darwin\\n'\n")
    uname.chmod(0o700)
    source = tmp_path / "recovery"
    source.write_text(RECOVERY.read_text().replace("/usr/bin/uname", shlex.quote(str(uname))))
    marker = tmp_path / "unexpected-action"
    script = f'''source {shlex.quote(str(source))}
candidate_identity() {{ touch {shlex.quote(str(marker))}; }}
sample_core() {{ touch {shlex.quote(str(marker))}; }}
signal_core() {{ touch {shlex.quote(str(marker))}; }}
main
'''
    result = subprocess.run(["bash", "-c", script], env={**os.environ, "HOME": str(home)},
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()
    assert not (state / "pending").exists()


@pytest.mark.parametrize("enabled", [None, True, False])
def test_chezmoi_initial_config_defaults_enable_without_overwriting_false(enabled):
    data = {"name": "Test User", "email": "test@example.invalid", "atuin_sync_address": "https://example.invalid"}
    if enabled is not None:
        data["synergy_recovery_enabled"] = enabled
    rendered = render_template(".chezmoi.toml.tmpl", **data)
    config = tomllib.loads(rendered)
    assert config["data"]["synergy_recovery_enabled"] is (True if enabled is None else enabled)
    assert config["data"]["synergy_app_path"] == APP


@pytest.mark.parametrize("enabled", [True, False])
def test_real_activation_hook_uses_rendered_context_and_quoted_managed_helper(tmp_path, enabled):
    home = tmp_path / "Owner's Home & Tools"
    helper = home / ".local/bin/synergy-setup"
    helper.parent.mkdir(parents=True)
    helper.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n")
    helper.chmod(0o700)
    text = render_template("run_onchange_after_load-synergy-launchagents.sh.tmpl",
                           chezmoi={"os": "darwin", "homeDir": str(home)},
                           synergy_recovery_enabled=enabled)
    opposite = render_template("run_onchange_after_load-synergy-launchagents.sh.tmpl",
                               chezmoi={"os": "darwin", "homeDir": str(home)},
                               synergy_recovery_enabled=not enabled)
    assert text != opposite
    result = subprocess.run(["bash"], input=text, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "activate\n"


@pytest.mark.parametrize("platform,machine", [("darwin", "macbook"), ("linux", "mac-mini"), ("linux", "omarchy")])
def test_activation_hook_does_nothing_outside_mac_mini(platform, machine):
    text = render_template("run_onchange_after_load-synergy-launchagents.sh.tmpl",
                           chezmoi={"os": platform, "homeDir": "/nonexistent/home"},
                           machine_type=machine)
    assert "exec " not in text
    result = subprocess.run(["bash"], input=text, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not result.stdout


def test_source_subset_apply_creates_parents_and_roundtrips_enabled_state(tmp_path):
    destination = tmp_path / "Fresh Home"
    destination.mkdir()
    source = tmp_path / "isolated source"
    source.mkdir()
    sources = [
        "dot_local/bin/executable_synergy-recovery",
        "dot_local/bin/executable_synergy-setup",
        "private_dot_config/synergy-recovery/private_config.tmpl",
        "private_Library/LaunchAgents/dev.dotfiles.synergy-login.plist.tmpl",
        "private_Library/LaunchAgents/dev.dotfiles.synergy-recovery.plist.tmpl",
    ]
    for relative in [*sources, ".chezmoiignore"]:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / relative).read_bytes())
    hook = "run_onchange_after_load-synergy-launchagents.sh.tmpl"
    # Execute the actual delivery selection safely: the real hook is tested
    # separately, and this isolated hook records runs without loading services.
    (source / hook).write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' '{{ .synergy_recovery_enabled }}' >> "
        '{{ printf "%s/hook-runs" .chezmoi.homeDir | shellQuote }}\n'
    )
    for enabled in (True, False):
        data = {"chezmoi": {"os": "darwin", "homeDir": str(destination)},
                "machine_type": "mac-mini", "synergy_recovery_enabled": enabled,
                "synergy_app_path": APP}
        result = subprocess.run([
            "chezmoi", "--config", "/dev/null", "--config-format", "toml",
            "--source", str(source), "--destination", str(destination),
            "--persistent-state", str(tmp_path / "chezmoi-state.boltdb"),
            "--override-data", json.dumps(data), "--error-on-conflict",
            "--source-path", "apply", "--parent-dirs", "--include=dirs,files,scripts",
            *[str(source / path) for path in [*sources, hook]],
        ], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        config = destination / ".config/synergy-recovery/config"
        assert config.read_text().splitlines() == [str(enabled).lower(), APP]
        assert config.stat().st_mode & 0o777 == 0o600
        for label in ("login", "recovery"):
            path = destination / f"Library/LaunchAgents/dev.dotfiles.synergy-{label}.plist"
            assert plistlib.loads(path.read_bytes())["Disabled"] is (not enabled)
        for name in ("synergy-recovery", "synergy-setup"):
            assert (destination / f".local/bin/{name}").stat().st_mode & 0o111
        assert not (destination / "Library/Application Support/dotfiles/synergy-recovery").exists()
    assert (destination / "hook-runs").read_text().splitlines() == ["true", "false"]
