import fcntl
import importlib.machinery
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).parents[1]
MANAGED_ASSETS = {
    ".local/bin/quickshell", ".local/bin/omarchy-shell-maintenance",
    ".config/omarchy-host/context-menu-guard/guard.h",
    ".config/omarchy-host/context-menu-guard/plugin.cpp",
    ".config/omarchy/plugins/dotfiles.context-menu-guard/manifest.json",
    ".config/omarchy/plugins/dotfiles.context-menu-guard/Service.qml",
    ".config/systemd/user/omarchy-shell-log-maintenance.service",
    ".config/systemd/user/omarchy-shell-log-maintenance.timer",
    ".config/systemd/user/timers.target.wants/omarchy-shell-log-maintenance.timer",
}


@pytest.mark.parametrize("profile,system,architecture,eligible", [
    ("omarchy", "linux", "amd64", True),
    ("omarchy", "linux", "arm64", False),
    ("omarchy", "darwin", "arm64", False),
    ("mac-mini", "darwin", "arm64", False),
    ("lmsh", "linux", "amd64", False),
    ("fedora-server", "linux", "amd64", False),
])
def test_profile_inventory_and_plugin_declaration(tmp_path, profile, system, architecture, eligible):
    command = ["chezmoi", "--source", str(ROOT), "--config", "/dev/null",
               "--config-format", "toml", "--persistent-state", str(tmp_path / "state.db"),
               "--override-data", json.dumps({"machine_type": profile,
                   "chezmoi": {"os": system, "arch": architecture}})]
    result = subprocess.run([*command, "managed", "--include", "files,symlinks"],
                            text=True, capture_output=True, check=True)
    assets = set(result.stdout.splitlines())
    assert MANAGED_ASSETS <= assets if eligible else not (MANAGED_ASSETS & assets)
    scripts = subprocess.run([*command, "managed", "--include", "scripts"],
                             text=True, capture_output=True, check=True).stdout.splitlines()
    owned_scripts = {"build-omarchy-shell.sh", "configure-omarchy-shell.sh"}
    assert owned_scripts <= set(scripts) if eligible else not owned_scripts.intersection(scripts)
    if profile == "omarchy":
        rendered = subprocess.run([*command, "execute-template"],
            input=(ROOT / "private_dot_config/omarchy/shell.json.tmpl").read_text(),
            text=True, capture_output=True, check=True).stdout
        assert json.loads(rendered)["plugins"] == (
            [{"id": "dotfiles.context-menu-guard"}] if eligible else [])


def load_script(name):
    path = ROOT / "dot_local/bin" / f"executable_{name}"
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture
def maintenance():
    return load_script("omarchy-shell-maintenance")


@pytest.fixture
def paths(tmp_path):
    runtime = tmp_path / "runtime with spaces"
    runtime.mkdir(mode=0o700)
    (runtime / "quickshell/by-id").mkdir(parents=True)
    return runtime, tmp_path / "private archives"


def instance(runtime, identifier="dead1", content=b"synthetic diagnostic\n"):
    directory = runtime / "quickshell/by-id" / identifier
    directory.mkdir()
    (directory / "instance.lock").write_bytes(b"")
    (directory / "log.qslog").write_bytes(content)
    return directory, {"id": identifier, "pid": 99999999,
                       "config_path": "/usr/share/omarchy/shell/shell.qml"}


def test_dead_logs_are_verified_archived_privately_and_reclaimed(maintenance, paths):
    runtime, archives = paths
    directory, entry = instance(runtime)
    unrelated = runtime.parent / "crashes/original/log.qslog.log"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"original crash evidence")
    result = maintenance.prune_logs(runtime, archives, [entry], now=1000)
    assert result["archived"] == 1
    assert not (directory / "log.qslog").exists()
    saved = next(archives.glob("instance-*.zip"))
    assert archives.stat().st_mode & 0o777 == 0o700
    assert saved.stat().st_mode & 0o777 == 0o600
    with zipfile.ZipFile(saved) as archive:
        assert archive.read("log.qslog") == b"synthetic diagnostic\n"
        assert json.loads(archive.read("manifest.json"))["files"]["log.qslog"]["size"] > 0
    assert unrelated.read_bytes() == b"original crash evidence"
    before = saved.read_bytes()
    assert maintenance.prune_logs(runtime, archives, [entry], now=1001)["archived"] == 0
    assert saved.read_bytes() == before


def test_native_posix_lock_protects_a_live_instance(maintenance, paths):
    runtime, archives = paths
    directory, entry = instance(runtime)
    child = subprocess.Popen(
        [sys.executable, "-u", "-c",
         "import fcntl,sys; f=open(sys.argv[1],'r+'); fcntl.lockf(f,fcntl.LOCK_EX); "
         "print('locked'); sys.stdin.readline()", str(directory / "instance.lock")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        assert child.stdout.readline().strip() == "locked"
        result = maintenance.prune_logs(runtime, archives, [entry], now=1000)
        assert result["skipped_live"] == 1
        assert (directory / "log.qslog").read_bytes() == b"synthetic diagnostic\n"
        assert not list(archives.glob("instance-*.zip"))
    finally:
        child.communicate("\n", timeout=5)


@pytest.mark.parametrize("kind", ["identifier", "directory", "log", "hardlink", "foreign-config"])
def test_unsafe_or_unowned_targets_are_preserved(maintenance, paths, kind):
    runtime, archives = paths
    directory, entry = instance(runtime)
    outside = runtime.parent / "outside"
    outside.write_bytes(b"outside data")
    if kind == "identifier":
        entry["id"] = "../outside"
    elif kind == "directory":
        moved = runtime.parent / "moved"
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
    elif kind == "log":
        (directory / "log.qslog").unlink()
        (directory / "log.qslog").symlink_to(outside)
    elif kind == "hardlink":
        (directory / "log.qslog").unlink()
        os.link(outside, directory / "log.qslog")
    else:
        entry["config_path"] = "/another/application/shell.qml"
    maintenance.prune_logs(runtime, archives, [entry], now=1000)
    assert outside.read_bytes() == b"outside data"
    assert (directory / "log.qslog").exists()
    assert not list(archives.glob("instance-*.zip"))


def test_archive_failure_preserves_source_and_removes_partial_output(maintenance, paths, monkeypatch):
    runtime, archives = paths
    directory, entry = instance(runtime)

    def fail(*args, **kwargs):
        raise OSError("synthetic storage failure")

    monkeypatch.setattr(maintenance, "write_archive", fail)
    result = maintenance.prune_logs(runtime, archives, [entry], now=1000)
    assert result["errors"] == 1
    assert (directory / "log.qslog").exists()
    assert not list(archives.glob("*.tmp"))


def test_special_log_file_is_refused_without_waiting_for_a_peer(paths):
    runtime, archives = paths
    directory, entry = instance(runtime)
    (directory / "log.qslog").unlink()
    os.mkfifo(directory / "log.qslog")
    program = ("import runpy,pathlib,sys,json; "
               "m=runpy.run_path(sys.argv[1]); "
               "print(json.dumps(m['prune_logs'](pathlib.Path(sys.argv[2]), "
               "pathlib.Path(sys.argv[3]),json.loads(sys.argv[4]))))")
    result = subprocess.run([sys.executable, "-c", program,
        str(ROOT / "dot_local/bin/executable_omarchy-shell-maintenance"),
        str(runtime), str(archives), json.dumps([entry])],
        timeout=5, text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)["skipped_unsafe"] == 1
    assert (directory / "log.qslog").exists()


def test_replaced_source_is_not_unlinked(maintenance, paths, monkeypatch):
    runtime, archives = paths
    directory, entry = instance(runtime)
    original = maintenance.verify_archive

    def replace_after_verification(*args, **kwargs):
        result = original(*args, **kwargs)
        replacement = directory / "replacement"
        replacement.write_bytes(b"new unrelated log")
        replacement.replace(directory / "log.qslog")
        return result

    monkeypatch.setattr(maintenance, "verify_archive", replace_after_verification)
    result = maintenance.prune_logs(runtime, archives, [entry], now=1000)
    assert result["errors"] == 1
    assert (directory / "log.qslog").read_bytes() == b"new unrelated log"


def test_retry_after_partial_reclaim_uses_the_verified_archive(maintenance, paths, monkeypatch):
    runtime, archives = paths
    directory, entry = instance(runtime)
    (directory / "log.log").write_bytes(b"text diagnostic")
    original = maintenance.os.unlink

    def fail_second(name, *args, **kwargs):
        if name == "log.qslog":
            raise OSError("synthetic unlink failure")
        return original(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(maintenance.os, "unlink", fail_second)
        assert maintenance.prune_logs(runtime, archives, [entry], now=1000)["errors"] == 1
    assert not (directory / "log.log").exists()
    assert (directory / "log.qslog").exists()
    result = maintenance.prune_logs(runtime, archives, [entry], now=1001)
    assert result["errors"] == 0
    assert not (directory / "log.qslog").exists()
    with zipfile.ZipFile(next(archives.glob("instance-*.zip"))) as archive:
        assert archive.read("log.log") == b"text diagnostic"
        assert archive.read("log.qslog") == b"synthetic diagnostic\n"


@pytest.mark.parametrize("manifest", [[], {"version": 1, "files": {"log.qslog": None}}])
def test_malformed_existing_archive_preserves_source(maintenance, paths, manifest):
    runtime, archives = paths
    directory, entry = instance(runtime)
    maintenance.prune_logs(runtime, archives, [], now=1000)
    with zipfile.ZipFile(archives / "instance-dead1.zip", "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("log.qslog", b"synthetic diagnostic\n")
    result = maintenance.prune_logs(runtime, archives, [entry], now=1001)
    assert result["errors"] == 1
    assert (directory / "log.qslog").read_bytes() == b"synthetic diagnostic\n"


def test_archive_limits_and_oversized_archive(maintenance, paths):
    runtime, archives = paths
    for index in range(3):
        _, entry = instance(runtime, f"dead{index}", os.urandom(2048))
        maintenance.prune_logs(runtime, archives, [entry], now=1000 + index, max_archives=2)
    assert len(list(archives.glob("instance-*.zip"))) == 2
    maintenance.prune_logs(runtime, archives, [], now=1002 + 8 * 86400)
    assert not list(archives.glob("instance-*.zip"))
    directory, entry = instance(runtime, "large1", os.urandom(4096))
    maintenance.prune_logs(runtime, archives, [entry], now=1003 + 8 * 86400,
                           max_archive_bytes=100)
    assert not (directory / "log.qslog").exists()
    assert not list(archives.glob("instance-*.zip"))


def test_large_runtime_log_uses_zip64_without_a_large_fixture(maintenance, paths, monkeypatch):
    runtime, archives = paths
    directory, entry = instance(runtime, content=os.urandom(4096))
    monkeypatch.setattr(zipfile, "ZIP64_LIMIT", 512)
    result = maintenance.prune_logs(runtime, archives, [entry], now=1000)
    assert result["errors"] == 0
    assert result["reclaimed_bytes"] == 4096
    assert not (directory / "log.qslog").exists()


def test_manual_and_timer_maintenance_do_not_overlap(maintenance, paths):
    runtime, archives = paths
    directory, entry = instance(runtime)
    archives.mkdir(mode=0o700)
    with (archives / ".maintenance.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = maintenance.prune_logs(runtime, archives, [entry], now=1000)
    assert result["busy"]
    assert (directory / "log.qslog").exists()


def test_archive_root_replacement_cannot_redirect_publication_or_retention(maintenance, paths, monkeypatch):
    runtime, archives = paths
    _, entry = instance(runtime)
    unrelated = runtime.parent / "unrelated"
    unrelated.mkdir(mode=0o700)
    valuable = unrelated / "instance-unrelated.zip"
    valuable.write_bytes(b"unrelated data")
    held = archives.with_name("original archives")
    original = maintenance.archive_instance

    def replace_root(*args, **kwargs):
        archives.rename(held)
        archives.symlink_to(unrelated, target_is_directory=True)
        return original(*args, **kwargs)

    monkeypatch.setattr(maintenance, "archive_instance", replace_root)
    result = maintenance.prune_logs(runtime, archives, [entry], now=1000, max_archives=0)
    assert result["archived"] == 1
    assert result["expired"] == 1
    assert valuable.read_bytes() == b"unrelated data"
    assert set(path.name for path in unrelated.iterdir()) == {valuable.name}
    assert not list(held.glob("instance-*.zip"))


@pytest.mark.parametrize("failed_artifact", ["libdotfilescontextguard.so", "qmldir", "build.json", "activation"])
def test_module_publication_failure_preserves_complete_previous_generation(maintenance, tmp_path, monkeypatch, failed_artifact):
    target = tmp_path / "ContextMenuGuard"

    def record(content):
        return {"owner": "dotfiles.omarchy-shell", "binary_sha256": hashlib.sha256(content).hexdigest()}

    maintenance.publish_module(target, b"previous binary", record(b"previous binary"))
    previous_link = os.readlink(target)
    original_open = maintenance.os.open
    original_replace = maintenance.os.replace

    def fail_open(path, flags, *args, **kwargs):
        if Path(path).name == failed_artifact and flags & os.O_CREAT:
            raise OSError("synthetic publication failure")
        return original_open(path, flags, *args, **kwargs)

    def fail_replace(*args, **kwargs):
        if failed_artifact == "activation":
            raise OSError("synthetic activation failure")
        return original_replace(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(maintenance.os, "open", fail_open)
        patch.setattr(maintenance.os, "replace", fail_replace)
        with pytest.raises(OSError):
            maintenance.publish_module(target, b"new binary", record(b"new binary"))
    assert os.readlink(target) == previous_link
    assert maintenance.module_record(target) == record(b"previous binary")
    assert set(path.name for path in tmp_path.iterdir()) == {target.name, previous_link}
    maintenance.publish_module(target, b"new binary", record(b"new binary"))
    assert maintenance.module_record(target) == record(b"new binary")


@pytest.mark.parametrize("args", [
    ["--version"], ["list", "--all", "--json"],
    ["ipc", "-p", "/usr/share/omarchy/shell", "call", "shell", "listPlugins"],
    ["-p", "/another/shell with spaces"],
])
def test_other_quickshell_invocations_are_passed_through(args):
    launcher = load_script("quickshell")
    environment = {"HOME": "/home/synthetic user", "QML_IMPORT_PATH": "/existing/modules"}
    actual_args, actual_env = launcher.prepare_launch(args, environment)
    assert actual_args == args
    assert actual_env == environment


def test_omarchy_launch_selects_sparse_capture_and_preserves_imports():
    launcher = load_script("quickshell")
    args = ["-n", "-p", "/usr/share/omarchy/shell"]
    environment = {"HOME": "/home/synthetic user", "QML_IMPORT_PATH": "/existing/modules"}
    actual_args, actual_env = launcher.prepare_launch(args, environment)
    assert actual_args == ["--no-detailed-logs", *args]
    assert actual_env["QML_IMPORT_PATH"] == (
        "/home/synthetic user/.local/lib/omarchy-qml:/existing/modules"
    )
    assert environment["QML_IMPORT_PATH"] == "/existing/modules"
