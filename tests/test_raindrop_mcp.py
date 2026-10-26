"""Verify Raindrop admission and descriptor ownership at process boundaries."""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "dot_local/bin/executable_raindrop-mcp"
PROXY_ARGS = ["https://api.raindrop.io/rest/v2/ai/mcp", "--transport", "http-only",
              "--auth-timeout", "300"]
RESOLVER_ARGS = ["--offline", "--no", "--package=mcp-remote@0.15.2", "--call",
                 "command -v mcp-remote"]


@pytest.fixture
def bridge(tmp_path):
    node = shutil.which("node")
    assert node, "the existing Node runtime is required for descriptor ownership tests"
    tools = tmp_path / "bin"
    tools.mkdir()
    proxy = tmp_path / "cached package" / "mcp-remote"
    proxy.parent.mkdir()
    started = tmp_path / "started.json"
    calls = tmp_path / "resolver.jsonl"
    auth = tmp_path / "private auth"
    caller = tmp_path / "caller repository"
    caller.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    proxy.write_text('''#!/usr/bin/env node
const fs = require('node:fs');
const stat = fs.fstatSync(9, {bigint: true});
fs.writeFileSync(process.env.STARTED, JSON.stringify({
  pid: process.pid, ppid: process.ppid, cwd: process.cwd(),
  args: process.argv.slice(2), cache: process.env.MCP_REMOTE_CONFIG_DIR,
  dev: String(stat.dev), ino: String(stat.ino)
}));
if (process.env.PROXY_WAIT === '1') {
  process.on('SIGINT', () => process.exit(0));
  process.stdin.on('data', data => process.stdout.write(data));
  process.stdin.on('end', () => process.exit(0));
  process.stdin.resume();
}
''')
    proxy.chmod(0o755)
    npx = tools / "npx"
    npx.write_text(f'''#!{sys.executable}
import json, os, sys
with open(os.environ["RESOLVER_CALLS"], "a") as stream:
    stream.write(json.dumps({{"pid": os.getpid(), "cwd": os.getcwd(), "args": sys.argv[1:]}}) + "\\n")
if os.environ.get("RESOLVER_FAIL"):
    print("private resolver detail", file=sys.stderr)
    sys.exit(1)
print(os.environ.get("RESOLVER_RESULT", os.environ["PROXY_PATH"]))
''')
    npx.chmod(0o755)
    uname = tools / "uname"
    uname.write_text('#!/bin/bash\nprintf "%s\\n" "${FAKE_SYSTEM:-Darwin}"\n')
    uname.chmod(0o755)
    (tools / "node").symlink_to(node)
    (tools / "mkdir").symlink_to(shutil.which("mkdir"))
    lockf = shutil.which("lockf")
    if lockf:
        (tools / "lockf").symlink_to(lockf)
    else:
        portable_lockf = tools / "lockf"
        portable_lockf.write_text(f'''#!{sys.executable}
import fcntl, sys
try:
    fcntl.flock(int(sys.argv[-1]), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(75)
''')
        portable_lockf.chmod(0o755)
    # A global command must never replace the exact resolver result.
    other = tools / "mcp-remote"
    other.write_text('#!/bin/bash\nprintf "wrong executable\\n"\nexit 99\n')
    other.chmod(0o755)
    env = os.environ | {
        "HOME": str(home), "PATH": str(tools),
        "MCP_REMOTE_CONFIG_DIR": str(auth), "CODEX_HOME": str(tmp_path / "codex"),
        "STARTED": str(started), "RESOLVER_CALLS": str(calls),
        "PROXY_PATH": str(proxy), "PROXY_WAIT": "0",
    }
    env.pop("NODE_OPTIONS", None)
    env.pop("NODE_PATH", None)
    processes = []

    def launch(*args, remove=(), **extra):
        selected = env | extra
        for key in remove:
            selected.pop(key, None)
        process = subprocess.Popen(["/bin/bash", str(LAUNCHER), *args], cwd=caller,
                                   env=selected, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
        processes.append(process)
        return process

    def run(*args, **extra):
        process = launch(*args, **extra)
        out, err = process.communicate(timeout=5)
        return SimpleNamespace(returncode=process.returncode, stdout=out, stderr=err,
                               pid=process.pid)

    def resolved():
        return [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []

    def await_proxy(process):
        deadline = time.monotonic() + 3
        while not started.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert started.exists(), f"proxy did not start (launcher status {process.poll()})"
        record = json.loads(started.read_text())
        assert record["pid"] == process.pid, "launcher did not directly exec the Node proxy"
        return record

    yield SimpleNamespace(launch=launch, run=run, resolved=resolved,
                          await_proxy=await_proxy, started=started, env=env,
                          auth=auth, proxy=proxy, tools=tools, caller=caller,
                          directory=tmp_path, home=home)
    for process in processes:
        if process.poll() is None:
            process.kill()
        if process.stdin and process.stdin.closed:
            process.stdin = None
        process.communicate(timeout=5)


def test_preserves_proxy_interface_and_direct_node_descriptor(bridge):
    result = bridge.run()
    assert result.returncode == 0, result.stderr
    record = json.loads(bridge.started.read_text())
    assert record["pid"] == result.pid
    assert record["ppid"] == os.getpid()
    assert record["args"] == PROXY_ARGS
    assert record["cache"] == str(bridge.auth)
    assert record["cwd"] == str(bridge.caller)
    assert result.stdout == ""
    resolver, = bridge.resolved()
    assert resolver["args"] == RESOLVER_ARGS
    assert resolver["cwd"] == str(bridge.auth)
    lock = bridge.auth / "raindrop-mcp.lock"
    assert (record["dev"], record["ino"]) == (str(lock.stat().st_dev), str(lock.stat().st_ino))
    assert lock.stat().st_mode & 0o777 == 0o600
    assert bridge.auth.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("codex_home", [True, False])
def test_fallback_cache_export_is_consistent(bridge, codex_home):
    removed = ("MCP_REMOTE_CONFIG_DIR",) if codex_home else ("MCP_REMOTE_CONFIG_DIR", "CODEX_HOME")
    result = bridge.run(remove=removed)
    assert result.returncode == 0, result.stderr
    base = Path(bridge.env["CODEX_HOME"]) if codex_home else bridge.home / ".codex"
    expected = str(base / "mcp-auth/raindrop")
    assert json.loads(bridge.started.read_text())["cache"] == expected
    assert bridge.resolved()[0]["cwd"] == expected


def test_rejects_arguments_before_resolution(bridge):
    result = bridge.run("--debug")
    assert result.returncode == 64
    assert result.stdout == ""
    assert bridge.resolved() == []


def test_rejects_relative_cache_before_resolution(bridge):
    result = bridge.run(MCP_REMOTE_CONFIG_DIR="relative/auth")
    assert result.returncode != 0
    assert result.stdout == ""
    assert bridge.resolved() == []
    assert not (bridge.caller / "relative").exists()


def test_rejects_unsupported_host_before_resolution(bridge):
    result = bridge.run(FAKE_SYSTEM="Linux")
    assert result.returncode != 0
    assert result.stdout == ""
    assert bridge.resolved() == []


@pytest.mark.parametrize("tool", ["lockf", "npx", "node"])
def test_missing_tool_fails_before_resolution(bridge, tool):
    (bridge.tools / tool).unlink()
    result = bridge.run()
    assert result.returncode != 0
    assert result.stdout == ""
    assert bridge.resolved() == []


def test_resolution_failure_is_private_and_recoverable(bridge):
    result = bridge.run(RESOLVER_FAIL="1")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "private resolver detail" not in result.stderr
    assert "mcp-remote@0.15.2" in result.stderr
    assert not bridge.started.exists()
    result = bridge.run()
    assert result.returncode == 0, result.stderr
    assert len(bridge.resolved()) == 2


@pytest.mark.parametrize("kind", ["empty", "relative", "nonexecutable", "multiple"])
def test_invalid_resolver_result_never_execs(bridge, kind):
    invalid = bridge.directory / "not executable"
    invalid.write_text("not a program")
    value = {"empty": "", "relative": "mcp-remote", "nonexecutable": str(invalid),
             "multiple": str(bridge.proxy) + "\nextra"}[kind]
    result = bridge.run(RESOLVER_RESULT=value)
    assert result.returncode != 0
    assert result.stdout == ""
    assert not bridge.started.exists()


def test_contender_exits_before_resolver_while_node_owns_lease(bridge):
    first = bridge.launch(PROXY_WAIT="1")
    record = bridge.await_proxy(first)
    assert first.poll() is None
    result = bridge.run()
    assert result.returncode == 75
    assert result.stdout == ""
    assert len(bridge.resolved()) == 1
    assert first.poll() is None
    assert json.loads(bridge.started.read_text())["pid"] == record["pid"]


@pytest.mark.parametrize("exit_kind", ["eof", "interrupt", "kill"])
def test_node_exit_releases_retained_inode(bridge, exit_kind):
    first = bridge.launch(PROXY_WAIT="1")
    record = bridge.await_proxy(first)
    lock = bridge.auth / "raindrop-mcp.lock"
    inode = lock.stat().st_ino
    if exit_kind == "eof":
        first.stdin.close()
        first.stdin = None
    elif exit_kind == "interrupt":
        first.send_signal(signal.SIGINT)
    else:
        first.kill()
    first.wait(timeout=5)
    assert first.returncode == (-signal.SIGKILL if exit_kind == "kill" else 0)
    assert lock.exists()
    assert lock.stat().st_ino == inode
    bridge.started.unlink()
    second = bridge.run()
    assert second.returncode == 0, second.stderr
    new_record = json.loads(bridge.started.read_text())
    assert new_record["pid"] == second.pid
    assert new_record["pid"] != record["pid"]
    assert new_record["ino"] == record["ino"]
    assert len(bridge.resolved()) == 2


def test_stdio_is_preserved(bridge):
    process = bridge.launch(PROXY_WAIT="1")
    bridge.await_proxy(process)
    process.stdin.write('{"jsonrpc":"2.0","id":1}\n')
    process.stdin.flush()
    assert process.stdout.readline() == '{"jsonrpc":"2.0","id":1}\n'
    process.stdin.close()
    process.stdin = None
    assert process.wait(timeout=5) == 0


def test_existing_cache_and_lock_contents_are_preserved(bridge):
    bridge.auth.mkdir(mode=0o700)
    marker = bridge.auth / "existing-cache-marker"
    marker.write_text("leave existing cache unchanged")
    lock = bridge.auth / "raindrop-mcp.lock"
    lock.write_text("retained lock inode")
    lock.chmod(0o600)
    inode = lock.stat().st_ino
    result = bridge.run()
    assert result.returncode == 0, result.stderr
    assert marker.read_text() == "leave existing cache unchanged"
    assert lock.read_text() == "retained lock inode"
    assert lock.stat().st_ino == inode
