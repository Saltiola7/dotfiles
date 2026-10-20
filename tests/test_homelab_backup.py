from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    loader = SourceFileLoader("homelab_backup", str(ROOT / "dot_local/bin/executable_homelab-backup"))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def test_substituted_disk_refused_without_creating_repo(tmp_path, monkeypatch):
    module = load()
    cfg = {"mount": str(tmp_path), "volume_uuid": "expected", "repository": str(tmp_path / "Homelab-Backups/pi400")}
    monkeypatch.setattr(module, "volume_info", lambda p: {"Mounted": True, "MountPoint": str(tmp_path), "VolumeUUID": "different", "FreeSpace": 100 * 1024**3})
    with pytest.raises(ValueError, match="identity"):
        module.destination_guard(cfg)
    assert not (tmp_path / "Homelab-Backups").exists()


def test_symlink_repository_refused(tmp_path, monkeypatch):
    module = load()
    (tmp_path / "Homelab-Backups").symlink_to(tmp_path.parent)
    cfg = {"mount": str(tmp_path), "volume_uuid": "expected", "repository": str(tmp_path / "Homelab-Backups/pi400")}
    monkeypatch.setattr(module, "volume_info", lambda p: {"Mounted": True, "MountPoint": str(tmp_path), "VolumeUUID": "expected", "FreeSpace": 100 * 1024**3})
    with pytest.raises(ValueError, match="symlink"):
        module.destination_guard(cfg)


def test_private_config_required(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text("{}")
    cfg.chmod(0o644)
    with pytest.raises(ValueError, match="private"):
        load().read_config(cfg)


def test_native_apfs_plist_without_mounted_flag(tmp_path, monkeypatch):
    module = load()
    cfg = {"mount": str(tmp_path), "volume_uuid": "expected", "repository": str(tmp_path / "Homelab-Backups/pi400")}
    monkeypatch.setattr(module, "volume_info", lambda p: {"MountPoint": str(tmp_path), "VolumeUUID": "expected", "APFSContainerFree": 100 * 1024**3, "FreeSpace": 0})
    assert module.destination_guard(cfg) == Path(cfg["repository"])
    assert not Path(cfg["repository"]).exists()


def test_conflicting_backup_key_permissions_preserved(tmp_path):
    module = load()
    auth = tmp_path / "authorized_keys"
    public = "ssh-ed25519 test-key backup-only"
    auth.write_text(public + "\n")
    expected = 'restrict,command="/owned/serve" ' + public + "\n"
    with pytest.raises(ValueError, match="permissions differ"):
        module.authorize_key(auth, public, expected)
    assert auth.read_text() == public + "\n"


def test_backup_key_enrollment_preserves_other_keys(tmp_path):
    module = load()
    auth = tmp_path / "authorized_keys"
    original = "ssh-ed25519 other-key existing-owner\n"
    auth.write_text(original)
    public = "ssh-ed25519 test-key backup-only"
    expected = 'restrict,command="/owned/serve" ' + public + "\n"
    module.authorize_key(auth, public, expected)
    module.authorize_key(auth, public, expected)
    assert auth.read_text() == original + expected


def test_rustfs_symlink_refused_before_service_change(tmp_path, monkeypatch):
    module = load()
    monkeypatch.setattr(module.Path, 'home', lambda: tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    root = tmp_path / '.local/share/rustfs'
    root.parent.mkdir(parents=True)
    root.symlink_to(outside)
    calls = []
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *a, **k: calls.append(a))
    with pytest.raises(ValueError, match='symlink'):
        module.rustfs_plan()
    assert calls == []


def test_unclean_stop_does_not_copy_and_recovers(tmp_path, monkeypatch):
    module = load()
    monkeypatch.setattr(module.Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(module, 'rustfs_plan', lambda: (tmp_path / 'data', tmp_path / 'binary', tmp_path / 'unit'))
    monkeypatch.setattr(module, 'rustfs_active', lambda: True)
    calls = []
    def control(*args):
        calls.append(args)
    monkeypatch.setattr(module, 'rustfs_control', control)
    monkeypatch.setattr(module, 'rustfs_clean_stop', lambda: False)
    monkeypatch.setattr(module, 'rustfs_ready', lambda: None)
    with pytest.raises(ValueError, match='clean'):
        module.rustfs_capture()
    assert ('start',) in calls
    assert not list(tmp_path.rglob('capture.json'))


def test_previously_inactive_rustfs_not_started(tmp_path, monkeypatch):
    module = load()
    monkeypatch.setattr(module.Path, 'home', lambda: tmp_path)
    data=tmp_path/'data';data.mkdir()
    (data/'data').mkdir();(data/'private').mkdir()
    binary=tmp_path/'binary';binary.write_bytes(b'pinned')
    unit=tmp_path/'unit';unit.write_text('owned service')
    monkeypatch.setattr(module, 'rustfs_plan', lambda: (data,binary,unit))
    monkeypatch.setattr(module, 'rustfs_active', lambda: False)
    monkeypatch.setattr(module, 'rustfs_clean_stop', lambda: True)
    calls=[]
    monkeypatch.setattr(module, 'rustfs_control', lambda *a: calls.append(a))
    snap=module.rustfs_capture()
    assert (snap/'capture.json').is_file()
    assert not calls


def test_forgejo_failed_stop_recovers_without_copy(tmp_path,monkeypatch):
    module=load();monkeypatch.setattr(module.Path,'home',lambda:tmp_path)
    monkeypatch.setattr(module,'forgejo_plan',lambda:(tmp_path/'root',tmp_path/'binary',tmp_path/'unit'))
    calls=[]
    def output(args,**kw):
        return 'active\n' if args[-1]=='--value' else 'ActiveState=inactive\nMainPID=0\nResult=timeout\nExecMainCode=2\nExecMainStatus=9\n'
    monkeypatch.setattr(module.subprocess,'check_output',output)
    monkeypatch.setattr(module.subprocess,'run',lambda args,**kw:calls.append(args))
    monkeypatch.setattr(module,'forgejo_ready',lambda:None)
    with pytest.raises(ValueError,match='clean stop'):module.forgejo_capture()
    assert ['systemctl','--user','start','forgejo.service'] in calls
    assert not list(tmp_path.rglob('capture.json'))
