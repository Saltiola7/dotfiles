import importlib.machinery
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
PATH = ROOT / "private_dot_config/omarchy-host/backup/executable_check_mount.py"
spec = importlib.util.spec_from_loader("backup_mount", importlib.machinery.SourceFileLoader("backup_mount", str(PATH)))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

@pytest.mark.parametrize("filesystems,returncode,allowed", [
    ([{"target": "/mnt/backup", "uuid": "expected", "fstype": "ext4"}], 0, True),
    ([{"target": "/mnt/backup", "uuid": "wrong", "fstype": "ext4"}], 0, False),
    ([{"target": "/", "uuid": "expected", "fstype": "ext4"}], 0, False),
    ([{"target": "/mnt/backup", "uuid": "expected", "fstype": "btrfs"}], 0, False),
    ([{"target": "/mnt/backup", "uuid": "expected", "fstype": "ext4"}] * 2, 0, True),
    ([{"target": "/mnt/backup", "uuid": "expected", "fstype": "ext4"},
      {"target": "/mnt/backup", "uuid": "wrong", "fstype": "ext4"}], 0, False),
    ([], 1, False),
])
def test_backup_rejects_absent_or_substituted_mount(monkeypatch, filesystems, returncode, allowed):
    def run(args, **kwargs):
        assert "--mountpoint" in args
        return SimpleNamespace(returncode=returncode, stdout=json.dumps({"filesystems": filesystems}))
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.check("expected", "/mnt/backup") == allowed

def test_backup_rejects_malformed_mount_metadata(monkeypatch):
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="not json"))
    assert not module.check("expected", "/mnt/backup")
