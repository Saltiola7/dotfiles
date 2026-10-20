"""Exercise terminal routing without contacting Herdr or starting a desktop app."""
import json
import os
from pathlib import Path
import pty
import shlex
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[1]
DISPATCHER = ROOT / "dot_local/bin/executable_omarchy-herdr-shell"
PLAIN = ROOT / "dot_local/bin/executable_kitty-plain"


def recorder(path, label):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['STARTUP_CALLS'], 'a') as output:\n"
        f"    output.write(json.dumps({{'command': {label!r}, 'args': sys.argv[1:], "
        "'shell': os.environ.get('SHELL'), 'sentinel': os.environ.get('STARTUP_SENTINEL')}) + '\\n')\n"
        "raise SystemExit(int(os.environ.get('SYSTEMCTL_EXIT', '0')) if "
        f"{label!r} == 'systemctl' else 0)\n"
    )
    path.chmod(0o700)


@pytest.fixture
def terminal(tmp_path):
    home = tmp_path / "User Home & Tools"
    home.mkdir()
    tools = tmp_path / "native tools"
    tools.mkdir()
    calls = tmp_path / "calls.jsonl"
    shell = tools / "real-shell"
    native = tools / "herdr"
    local = home / ".local/bin/herdr"
    recorder(shell, "shell")
    recorder(tools / "systemctl", "systemctl")
    # Always replace the native fallback, so no fixture can contact real Herdr.
    script = tmp_path / "dispatcher"
    script.write_text(DISPATCHER.read_text().replace('"/usr/bin/herdr"', f'"{native}"'))
    env = {key: value for key, value in os.environ.items() if key != "HERDR_ENV"}
    env.update(HOME=str(home), SHELL=str(shell), STARTUP_CALLS=str(calls),
               PATH=str(tools) + os.pathsep + os.environ.get("PATH", ""),
               STARTUP_SENTINEL="literal $value and spaces")

    def run(*args, tty=True, stdin_tty=True, stdout_tty=True, **overrides):
        calls.unlink(missing_ok=True)
        master, slave = pty.openpty()
        try:
            process = subprocess.Popen(
                ["/usr/bin/bash", str(script), *args], env={**env, **overrides},
                stdin=slave if tty and stdin_tty else subprocess.DEVNULL,
                stdout=slave if tty and stdout_tty else subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                _, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise
        finally:
            os.close(slave)
            os.close(master)
        assert process.returncode == 0, stderr.decode()
        recorded = [json.loads(line) for line in calls.read_text().splitlines()]
        assert all(call["shell"] == str(shell) for call in recorded)
        assert all(call["sentinel"] == env["STARTUP_SENTINEL"] for call in recorded)
        return recorded, stderr.decode()

    return run, local, native


def test_default_terminal_starts_service_then_prefers_local_herdr(terminal):
    run, local, native = terminal
    recorder(local, "local-herdr")
    recorder(native, "native-herdr")
    calls, error = run()
    assert [(call["command"], call["args"]) for call in calls] == [
        ("systemctl", ["--user", "start", "herdr.service"]), ("local-herdr", []),
    ]
    assert not error


@pytest.mark.parametrize("local_present", [False, True])
def test_native_herdr_handles_missing_or_nonexecutable_local_binary(terminal, local_present):
    run, local, native = terminal
    if local_present:
        local.parent.mkdir(parents=True)
        local.write_text("not executable\n")
        local.chmod(0o600)
    recorder(native, "native-herdr")
    calls, _ = run()
    assert [call["command"] for call in calls] == ["systemctl", "native-herdr"]


def test_explicit_shell_arguments_are_forwarded_verbatim_even_with_a_tty(terminal):
    run, local, _ = terminal
    recorder(local, "local-herdr")
    args = ("-l", "-i", "-c", "printf '%s' '$literal; unchanged'", "shell name", "")
    calls, _ = run(*args)
    assert [(call["command"], call["args"]) for call in calls] == [("shell", list(args))]


def test_terminal_inside_herdr_never_attaches_again(terminal):
    run, local, _ = terminal
    recorder(local, "local-herdr")
    calls, _ = run(HERDR_ENV="1")
    assert [(call["command"], call["args"]) for call in calls] == [("shell", [])]


@pytest.mark.parametrize("input_tty,output_tty", [(False, True), (True, False), (False, False)])
def test_noninteractive_streams_do_not_start_a_server(terminal, input_tty, output_tty):
    run, local, _ = terminal
    recorder(local, "local-herdr")
    calls, _ = run(stdin_tty=input_tty, stdout_tty=output_tty)
    assert [call["command"] for call in calls] == ["shell"]


def test_missing_herdr_opens_shell_without_starting_service(terminal):
    run, _, _ = terminal
    calls, error = run()
    assert [call["command"] for call in calls] == ["shell"]
    assert "Herdr is unavailable" in error


def test_failed_service_opens_shell_without_launching_an_unmanaged_server(terminal):
    run, local, _ = terminal
    recorder(local, "local-herdr")
    calls, error = run(SYSTEMCTL_EXIT="7")
    assert [call["command"] for call in calls] == ["systemctl", "shell"]
    assert "background service could not start" in error


def test_missing_shell_environment_keeps_explicit_command_working():
    environment = {key: value for key, value in os.environ.items() if key != "SHELL"}
    result = subprocess.run(
        ["/usr/bin/bash", str(DISPATCHER), "-c", "printf '%s' explicit-command"],
        env=environment, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "explicit-command"


def test_plain_launcher_bypasses_default_shell_and_preserves_kitty_arguments(tmp_path):
    binary = tmp_path / "native kitty"
    recorder(binary, "kitty")
    script = tmp_path / "kitty-plain"
    script.write_text(PLAIN.read_text().replace("/usr/bin/kitty", shlex.quote(str(binary))))
    calls = tmp_path / "calls.jsonl"
    args = ["--directory", "/tmp/working directory", "bash", "-c", "printf '%s' '$value'", ""]
    result = subprocess.run(
        ["/usr/bin/bash", str(script), *args],
        env={**os.environ, "STARTUP_CALLS": str(calls)}, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 0, result.stderr
    call = json.loads(calls.read_text())
    assert call["command"] == "kitty"
    assert call["args"] == ["--override", "shell=.", *args]
