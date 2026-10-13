from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    loader = SourceFileLoader("pi_rustfs", str(ROOT / "dot_local/bin/executable_pi-rustfs-setup"))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def test_unknown_archive_rejected(tmp_path):
    archive = tmp_path / "payload.zip"
    archive.write_bytes(b"not the approved payload")
    with pytest.raises(ValueError, match="checksum"):
        load().verify_archive(archive)


def test_symlink_data_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "data"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        load().ordinary_path(link)


def test_secrets_created_privately_and_preserved(tmp_path):
    target = tmp_path / "credential"
    module = load()
    module.secret_file(target)
    first = target.read_bytes()
    module.secret_file(target)
    assert target.read_bytes() == first
    assert target.stat().st_mode & 0o777 == 0o600


def test_unknown_unit_refused_before_binary_replacement(tmp_path, monkeypatch):
    module = load()
    monkeypatch.setattr(module.os, "getuid", lambda: 1000)
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.platform, "machine", lambda: "aarch64")
    original_read = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda p, *a, **k: "ID=fedora\n" if str(p) == "/etc/os-release" else original_read(p, *a, **k))
    monkeypatch.setattr(module, "verify_archive", lambda p: None)
    monkeypatch.setattr(module.shutil, "disk_usage", lambda p: type("Usage", (), {"free": 100 * 1024**3})())
    monkeypatch.setattr(module.subprocess, "check_output", lambda args, **k: "rustfs 1.0.1\n" if args[-1] == "--version" else b"{}")
    binary = tmp_path / ".local/bin/rustfs"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"existing verified binary")
    unit = tmp_path / ".config/systemd/user/rustfs.service"
    unit.parent.mkdir(parents=True)
    unit.write_text("unknown existing service")
    source = tmp_path / "source"
    source.mkdir()
    (source / "rustfs.service").write_text("declared service")
    with pytest.raises(ValueError, match="Existing service differs"):
        module.install(tmp_path / "archive", source, tmp_path)
    assert binary.read_bytes() == b"existing verified binary"
    assert unit.read_text() == "unknown existing service"
    assert not (tmp_path / ".local/share/rustfs").exists()
