"""Behavioral tests for public-safe, read-only homelab declarations."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'dot_local/bin/executable_homelab'
DECLARATION = ROOT / 'private_dot_config/homelab/targets.json'


def target(name, parent=None):
    return dict(id=name, kind='physical' if parent is None else 'vm',
                architecture='arm64', role='test', owner='personal-dotfiles',
                lifecycle='active', parent_id=parent, evidence_status='observed', notes='')


@pytest.fixture
def inventory():
    return dict(schema_version=1, targets=[target('host'), target('guest', 'host')],
                edges=[], observations=[dict(target_id='guest', source='owner',
                    observed_at='2000-01-01T00:00:00+00:00', state='offline')])


def run(tmp_path, inventory, *args, extra=()):
    path = tmp_path / 'inventory.json'
    path.write_text(json.dumps(inventory))
    return subprocess.run([sys.executable, str(CLI), '--inventory', str(path),
                           *extra, *args], capture_output=True, text=True)


def test_validate_and_unassigned_stale_target(tmp_path, inventory):
    assert run(tmp_path, inventory, 'validate').returncode == 0
    r = run(tmp_path, inventory, 'inspect', 'guest')
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data['target']['parent_id'] == 'host'
    assert data['observation']['state'] == 'offline'
    assert data['freshness'] == 'stale'
    assert data['workload_assignment'] == 'unassigned'
    assert len(inventory['targets']) == 2


@pytest.mark.parametrize('mutation', ['duplicate', 'cycle', 'dangling', 'field', 'schema',
                                      'edge', 'timestamp', 'boolean-schema'])
def test_fail_closed(tmp_path, inventory, mutation):
    if mutation == 'duplicate': inventory['targets'].append(copy.deepcopy(inventory['targets'][0]))
    if mutation == 'cycle': inventory['targets'][0]['parent_id'] = 'guest'
    if mutation == 'dangling': inventory['targets'][1]['parent_id'] = 'missing'
    if mutation == 'field': inventory['targets'][0]['password'] = 'CANARY_PRIVATE'
    if mutation == 'schema': inventory['schema_version'] = 99
    if mutation == 'boolean-schema': inventory['schema_version'] = True
    if mutation == 'edge': inventory['edges'] = [dict(source='host', target='missing', type='depends_on', status='declared')]
    if mutation == 'timestamp': inventory['observations'][0]['observed_at'] = 'yesterday'
    r = run(tmp_path, inventory, 'inspect', 'guest')
    assert r.returncode == 2
    assert r.stdout == ''
    assert 'CANARY_PRIVATE' not in r.stderr


def test_private_binding_explicit_only(tmp_path, inventory):
    overlay = tmp_path / 'bindings.json'
    overlay.write_text(json.dumps(dict(schema_version=1, bindings={
        'guest': dict(method='ssh', endpoint='PRIVATE_CANARY', user='OWNER_CANARY')})))
    overlay.chmod(0o600)
    extra = ('--bindings', str(overlay))
    for args in [('targets',), ('topology',), ('inspect', 'guest')]:
        r = run(tmp_path, inventory, *args, extra=extra)
        assert r.returncode == 0
        assert 'PRIVATE_CANARY' not in r.stdout + r.stderr
        assert 'OWNER_CANARY' not in r.stdout + r.stderr
    r = run(tmp_path, inventory, 'inspect', 'guest', '--private', extra=extra)
    assert json.loads(r.stdout)['binding']['endpoint'] == 'PRIVATE_CANARY'
    assert run(tmp_path, inventory, 'inspect', 'guest', '--private').returncode == 2
    overlay.chmod(0o644)
    assert run(tmp_path, inventory, 'validate', extra=extra).returncode == 2


def test_private_symlink_and_unknown_binding_rejected(tmp_path, inventory):
    overlay = tmp_path / 'bindings.json'
    overlay.write_text(json.dumps(dict(schema_version=1, bindings={'absent': dict(method='local')})))
    overlay.chmod(0o600)
    assert run(tmp_path, inventory, 'validate', extra=('--bindings', str(overlay))).returncode == 2
    link = tmp_path / 'link.json'
    link.symlink_to(overlay)
    assert run(tmp_path, inventory, 'validate', extra=('--bindings', str(link))).returncode == 2


def test_deterministic_topology_and_read_only(tmp_path, inventory):
    original = copy.deepcopy(inventory)
    first = run(tmp_path, inventory, 'topology')
    inventory['targets'].reverse()
    second = run(tmp_path, inventory, 'topology')
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert 'accTitle:' in first.stdout and 'Text Equivalent' in first.stdout
    assert 'hosts' in first.stdout and 'guest' in first.stdout and 'host' in first.stdout
    assert json.loads((tmp_path / 'inventory.json').read_text()) == inventory
    assert original['targets'][0]['id'] == 'host'


def test_duplicate_json_keys_rejected(tmp_path):
    path = tmp_path / 'duplicate.json'
    path.write_text('{"schema_version":1,"schema_version":1,"targets":[],"edges":[],"observations":[]}')
    r = subprocess.run([sys.executable, str(CLI), '--inventory', str(path), 'validate'], capture_output=True, text=True)
    assert r.returncode == 2 and r.stdout == ''


def test_shipped_inventory_is_truthful(tmp_path):
    declaration = json.loads(DECLARATION.read_text())
    ids = {t['id'] for t in declaration['targets']}
    assert {'mac-mini', 'macbook-pro', 'hp-envy', 'pi400', 'personal-sandbox', 'pi-system-ssd', 'omarchy-arm', 'atuin-server', 'pm-postgres'} <= ids
    assert run(tmp_path, declaration, 'validate').returncode == 0
    assert next(t for t in declaration['targets'] if t['id'] == 'pi400')['lifecycle'] == 'planned'
    assert not {'endpoint', 'password', 'serial', 'tailscale_identity'} & set(declaration)


def test_cli_has_no_mutating_adapters():
    import ast
    tree = ast.parse(CLI.read_text())
    imports = {n.name for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}
    assert not {'subprocess', 'socket', 'urllib', 'requests'} & imports
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {'eval', 'exec'} for n in ast.walk(tree))


@pytest.mark.parametrize('profile', ['mac-mini', 'omarchy'])
def test_chezmoi_installs_only_inventory_artifacts(tmp_path, profile):
    import shutil
    source = tmp_path / 'source'
    home = tmp_path / 'home'
    home.mkdir()
    for relative in ('.chezmoiignore', 'dot_local/bin/executable_homelab',
                     'private_dot_config/homelab/targets.json'):
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    # Unselected source scripts must never execute during this bounded apply.
    (source / 'run_before_probe.sh').write_text('#!/bin/sh\nexit 99\n')
    args = ['chezmoi', '--source', str(source), '--destination', str(home),
            '--config', '/dev/null', '--config-format', 'toml', '--override-data',
            json.dumps({'machine_type': profile}), '--persistent-state', str(tmp_path / 'state.db'),
            'apply', '--parent-dirs', '--exclude', 'scripts', str(home / '.local/bin/homelab'),
            str(home / '.config/homelab/targets.json')]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    executable = home / '.local/bin/homelab'
    assert executable.stat().st_mode & 0o111
    assert (home / '.config/homelab/targets.json').read_bytes() == DECLARATION.read_bytes()
    assert subprocess.run([sys.executable, str(executable), '--inventory', str(home / '.config/homelab/targets.json'), 'validate'], capture_output=True).returncode == 0


@pytest.mark.parametrize('value', ['bad\nlabel', '<script>syntax</script>'])
def test_labels_cannot_inject_mermaid(tmp_path, inventory, value):
    inventory['targets'][0]['role'] = value
    r = run(tmp_path, inventory, 'topology')
    if '\n' in value:
        assert r.returncode == 2
    else:
        assert r.returncode == 0 and '<script>' not in r.stdout.split('```')[1]
