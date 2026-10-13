"""Preparation boundary tests; never operate on a physical disk."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'dot_local/bin/executable_pi-bootstrap'
MANIFEST = ROOT / 'private_dot_config/pi-bootstrap/manifest.json'
BACKEND = ROOT / 'dot_local/lib/pi-bootstrap'


def module():
    loader = importlib.machinery.SourceFileLoader('pi_bootstrap', str(CLI))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    value = importlib.util.module_from_spec(spec)
    loader.exec_module(value)
    return value


def test_manifest_policy_and_tampering():
    m = module()
    policy = json.loads(MANIFEST.read_text())
    m.validate_manifest(policy)
    policy['sudo'] = 'passwordless'
    with pytest.raises(m.Invalid): m.validate_manifest(policy)
    policy = json.loads(MANIFEST.read_text())
    policy['password'] = 'SECRET_CANARY'
    with pytest.raises(m.Invalid): m.validate_manifest(policy)


def test_private_keys_and_multiline_rejected():
    m = module()
    with pytest.raises(m.Invalid): m.public_key('-----BEGIN OPENSSH PRIVATE KEY-----')
    with pytest.raises(m.Invalid): m.public_key('ssh-ed25519 bad\nssh-ed25519 bad')
    with pytest.raises(m.Invalid): m.public_key('ssh-ed25519 bad')


def test_wrong_image_fails_before_backend(tmp_path):
    image = tmp_path / 'Fedora-Minimal-44-1.7.aarch64.raw.xz'
    image.write_bytes(b'not fedora')
    key = tmp_path / 'key.pub'
    key.write_text('PRIVATE_KEY_CANARY')
    r = subprocess.run([sys.executable, str(CLI), '--manifest', str(MANIFEST),
                        'plan', '--image', str(image), '--key', str(key)], capture_output=True, text=True)
    assert r.returncode == 2
    assert 'PRIVATE_KEY_CANARY' not in r.stdout + r.stderr


def test_verify_detects_artifact_change(tmp_path):
    m = module()
    image = tmp_path / 'prepared.raw'
    image.write_bytes(b'candidate')
    receipt = dict(schema_version=1, target='pi400', base_sha256=m.PIN,
                   prepared_sha256=m.digest(image), host_key_fingerprint='SHA256:test', checks=['offline-filesystem'])
    (tmp_path / 'receipt.json').write_text(json.dumps(receipt))
    assert m.verify_output(tmp_path)['target'] == 'pi400'
    image.write_bytes(b'tampered')
    with pytest.raises(m.Invalid): m.verify_output(tmp_path)


def test_backend_is_unprivileged_and_first_boot_is_guest_bound():
    backend = (BACKEND / 'prepare.py').read_text()
    assert 'debugfs' in backend and 'e2fsck' in backend
    import ast
    tree = ast.parse(backend)
    assert not any(isinstance(n, ast.List) and n.elts and isinstance(n.elts[0], ast.Constant) and n.elts[0].value in {'sudo', 'mount', 'losetup', 'chroot'} for n in ast.walk(tree))
    grow = (BACKEND / 'first-boot.sh').read_text()
    assert 'findmnt' in grow and 'PARTN' in grow and 'partx' in grow
    assert '/dev/disk' not in grow
    assert not list(ROOT.glob('run_*pi*'))


def test_flash_requires_explicit_plan():
    r = subprocess.run([sys.executable, str(CLI), 'flash'], capture_output=True, text=True)
    assert r.returncode == 2


@pytest.mark.parametrize('profile,installed', [('mac-mini', True), ('macbook', True), ('omarchy', False)])
def test_chezmoi_profile_boundary(tmp_path, profile, installed):
    import shutil
    source = tmp_path / 'source'; home = tmp_path / 'home'; home.mkdir()
    for relative in ('.chezmoiignore', 'dot_local/bin/executable_pi-bootstrap',
                     'private_dot_config/pi-bootstrap/manifest.json',
                     'dot_local/lib/pi-bootstrap/prepare.sh', 'dot_local/lib/pi-bootstrap/prepare.py',
                     'dot_local/lib/pi-bootstrap/first-boot.sh'):
        dest = source / relative; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    base = ['chezmoi', '--source', str(source), '--destination', str(home),
            '--config', '/dev/null', '--config-format', 'toml', '--override-data',
            json.dumps({'machine_type': profile}), '--persistent-state', str(tmp_path / 'state.db')]
    if installed:
        r = subprocess.run([*base, 'apply', '--parent-dirs', '--exclude', 'scripts',
                            str(home / '.local/bin/pi-bootstrap'), str(home / '.local/lib/pi-bootstrap'),
                            str(home / '.config/pi-bootstrap/manifest.json')], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert (home / '.local/bin/pi-bootstrap').stat().st_mode & 0o111
        assert (home / '.local/lib/pi-bootstrap/prepare.py').read_bytes() == (BACKEND / 'prepare.py').read_bytes()
    else:
        r = subprocess.run([*base, 'managed'], capture_output=True, text=True)
        assert r.returncode == 0 and 'pi-bootstrap' not in r.stdout
