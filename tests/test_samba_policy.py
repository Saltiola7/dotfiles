"""One public policy renders compatible Pi, Omarchy and client declarations."""
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PI_WRAPPER = Path('private_dot_config/homelab-file-storage/smb.conf.tmpl')
HP_WRAPPER = Path('private_dot_config/samba/smb.conf.tmpl')
CATALOG_WRAPPER = Path('private_dot_config/samba/shares.json.tmpl')

LEGACY_PI = '''[global]
    server role = standalone server
    security = user
    map to guest = Never
    server min protocol = SMB2
    smb ports = 445
    interfaces = lo
    bind interfaces only = yes
    disable netbios = yes
    load printers = no
    printing = bsd
    printcap name = /dev/null
    disable spoolss = yes

[Shared]
    path = @HOME@/Shared
    valid users = @OWNER@
    guest ok = no
    read only = no
    create mask = 0600
    directory mask = 0700
'''

LEGACY_HP = '''[global]
    server role = standalone server
    security = user
    map to guest = Never
    server min protocol = SMB2
    smb ports = 445
    disable netbios = yes
    load printers = no
    printing = bsd
    printcap name = /dev/null
    disable spoolss = yes

[Shared]
    path = /home/example/Shared
    browseable = yes
    read only = no
    guest ok = no
    valid users = example
    create mask = 0600
    directory mask = 0700
'''

CATALOG = {'schema_version': 1, 'shares': [
    {'id': 'pi400', 'share': 'Shared', 'policy': 'tailscale-only',
     'reconnect': True, 'deployment': 'verified'},
    {'id': 'hp-envy', 'share': 'Shared', 'policy': 'private-lan-and-tailscale',
     'reconnect': True, 'deployment': 'verified'},
    {'id': 'omarchy-arm', 'share': 'Shared', 'policy': 'private-lan-and-tailscale',
     'reconnect': False, 'deployment': 'unverified'},
]}


def render(source, wrapper=None, template=None):
    command = ['chezmoi', '--source', str(source), '--config', '/dev/null',
               '--config-format', 'toml', '--override-data',
               json.dumps({'machine_type': 'omarchy', 'chezmoi': {
                   'homeDir': '/home/example', 'username': 'example'}}),
               'execute-template']
    if wrapper is not None:
        command += ['--file', str(source / wrapper)]
    else:
        command += [template]
    return subprocess.run(command, text=True, capture_output=True, timeout=15)


def test_public_catalog_has_only_logical_metadata_and_settled_defaults():
    data = json.loads((ROOT / '.chezmoidata/samba.json').read_text())
    assert set(data) == {'samba'}
    assert data['samba']['catalog'] == CATALOG


def test_client_catalog_reuses_public_declaration():
    result = render(ROOT, CATALOG_WRAPPER)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == CATALOG


def test_pi_config_preserves_exact_private_only_render_and_runtime_path():
    result = render(ROOT, PI_WRAPPER)
    assert result.returncode == 0, result.stderr
    assert result.stdout == LEGACY_PI
    # The old raw input must not compete with its managed template target.
    assert not (ROOT / 'private_dot_config/homelab-file-storage/smb.conf').exists()


def test_omarchy_config_preserves_exact_owner_share_and_lan_policy():
    result = render(ROOT, HP_WRAPPER)
    assert result.returncode == 0, result.stderr
    assert result.stdout == LEGACY_HP


def test_common_policy_change_reaches_both_existing_server_wrappers(tmp_path):
    for path in [Path('.chezmoidata'), Path('.chezmoitemplates')]:
        shutil.copytree(ROOT / path, tmp_path / path)
    for path in [PI_WRAPPER, HP_WRAPPER]:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, tmp_path / path)
    renderer = tmp_path / '.chezmoitemplates/samba.conf'
    original = renderer.read_text()
    assert original.count('server min protocol = SMB2') == 1
    renderer.write_text(original.replace('server min protocol = SMB2',
                                         'server min protocol = SMB3'))
    for path in [PI_WRAPPER, HP_WRAPPER]:
        result = render(tmp_path, path)
        assert result.returncode == 0, result.stderr
        assert 'server min protocol = SMB3' in result.stdout
        assert 'server min protocol = SMB2' not in result.stdout


def test_shared_renderer_refuses_undefined_transport_policy():
    result = render(ROOT, template='{{ template "samba.conf" (dict "policy" "public" "home" "/home/example" "owner" "example") }}')
    assert result.returncode != 0
    assert 'Unsupported Samba policy' in result.stderr
