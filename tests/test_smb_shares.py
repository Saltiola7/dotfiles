"""Behavioral boundaries for quiet, per-target SMB reconnection."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'dot_local/bin/executable_smb-shares'


@pytest.fixture
def m():
    loader = importlib.machinery.SourceFileLoader('smb_shares_cli_test', str(HELPER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    catalog = tmp_path / 'shares.json'
    public = json.loads((ROOT / '.chezmoidata/samba.json').read_text())['samba']['catalog']
    catalog.write_text(json.dumps(public))
    private = tmp_path / 'private.json'
    private.write_text(json.dumps({'schema_version': 1, 'bindings': {
        'pi400': {'host': 'pi.example.ts.net', 'user': 'owner', 'aliases': []},
        'hp-envy': {'host': 'hp.example.ts.net', 'user': 'owner', 'aliases': ['192.168.50.10']},
    }}))
    private.chmod(0o600)
    return SimpleNamespace(catalog=catalog, bindings=private, state_dir=tmp_path/'state')


def test_central_defaults_and_unbound_targets(m, inputs):
    rows = m.load_catalog(inputs.catalog)
    assert [x['id'] for x in rows if x['reconnect']] == ['pi400', 'hp-envy']
    assert m.load_bindings(inputs.bindings, rows)['pi400']['user'] == 'owner'
    assert m.load_bindings(inputs.bindings.parent/'absent', rows) == {}


@pytest.mark.parametrize('mode', [0o644, 0o640, 0o666])
def test_private_metadata_permissions_rejected(m, inputs, mode):
    inputs.bindings.chmod(mode)
    with pytest.raises(m.Invalid):
        m.load_bindings(inputs.bindings, m.load_catalog(inputs.catalog))


def test_symlink_and_unknown_fields_fail_before_mount(m, inputs):
    link = inputs.bindings.parent/'link'
    link.symlink_to(inputs.bindings)
    with pytest.raises((m.Invalid, OSError)):
        m.load_bindings(link, m.load_catalog(inputs.catalog))
    d = json.loads(inputs.bindings.read_text())
    d['bindings']['pi400']['password'] = 'never-accepted'
    inputs.bindings.write_text(json.dumps(d))
    with pytest.raises(m.Invalid):
        m.load_bindings(inputs.bindings, m.load_catalog(inputs.catalog))


@pytest.mark.parametrize('host', ['smb://host', 'user:secret@host', 'host/path', 'host;open', 'host\nname'])
def test_host_input_cannot_embed_commands_or_credentials(m, host):
    with pytest.raises(m.Invalid):
        m.normal_host(host)


def test_duplicate_json_keys_rejected(m, inputs):
    inputs.bindings.write_text('{"schema_version":1,"schema_version":1,"bindings":{}}')
    with pytest.raises(m.Invalid):
        m.load_bindings(inputs.bindings, m.load_catalog(inputs.catalog))


def test_one_timeout_does_not_suppress_other_host(m, inputs, monkeypatch):
    calls = []
    def worker(target, args):
        calls.append(target)
        return {'status': 'timeout' if target == 'pi400' else 'mounted'}
    monkeypatch.setattr(m, 'call_worker', worker)
    result = m.reconnect(inputs)
    assert result['shares'] == {'pi400': 'timeout', 'hp-envy': 'mounted', 'omarchy-arm': 'manual'}
    assert calls == ['pi400', 'hp-envy']
    assert (inputs.state_dir/'status.json').stat().st_mode & 0o777 == 0o600


def test_unconfigured_host_does_not_call_native(m, inputs, monkeypatch):
    inputs.bindings.unlink()
    monkeypatch.setattr(m, 'call_worker', lambda *_: pytest.fail('must not mount'))
    assert m.reconnect(inputs)['shares']['pi400'] == 'unbound'


def test_overlapping_pass_is_noop(m, inputs, monkeypatch):
    import fcntl
    inputs.state_dir.mkdir(mode=0o700)
    lock = (inputs.state_dir/'lock').open('w')
    os.chmod(lock.name, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    monkeypatch.setattr(m, 'call_worker', lambda *_: pytest.fail('must not mount'))
    try:
        assert m.reconnect(inputs) == {'status': 'busy'}
    finally:
        lock.close()


def test_exact_host_user_and_share_identity_not_mount_basename(m):
    binding = {'host': 'hp.example.ts.net', 'user': 'owner', 'aliases': ['192.168.50.10']}
    good = {'url': 'smb://owner@192.168.50.10/Shared', 'mountpoint': '/Volumes/Shared-9', 'owner': os.getuid()}
    assert m.find_mount([good], binding, 'Shared') == '/Volumes/Shared-9'
    for url in ['smb://owner@other.example.ts.net/Shared', 'smb://other@192.168.50.10/Shared', 'smb://owner@192.168.50.10/Other']:
        row = {**good, 'url': url}
        if 'other@' in url:
            with pytest.raises(m.Invalid): m.find_mount([row], binding, 'Shared')
        else:
            assert m.find_mount([row], binding, 'Shared') is None
    with pytest.raises(m.Invalid):
        m.find_mount([good, good], binding, 'Shared')
    with pytest.raises(m.Invalid):
        m.find_mount([{**good, 'url': 'smb://owner:secret@192.168.50.10/Shared'}], binding, 'Shared')


def test_peer_identity_and_online_gate(m):
    peer = {'DNSName': 'pi.example.ts.net.', 'TailscaleIPs': ['100.90.1.2'], 'Online': True}
    assert m.find_peer('pi.example.ts.net', [peer]) == peer
    assert m.find_peer('100.90.1.2', [peer]) == peer
    assert m.find_peer('untrusted.invalid', [peer]) is None
    assert m.find_peer('pi.example.ts.net', [peer, peer]) is None


def test_dns_outside_verified_peer_is_never_probed(m, monkeypatch):
    monkeypatch.setattr(m.socket, 'getaddrinfo', lambda *_, **kw: [(2,1,6,'',('203.0.113.5',445))])
    monkeypatch.setattr(m.socket, 'socket', lambda *_: pytest.fail('wrong endpoint must not be dialed'))
    assert not m.probe_peer('pi.example.ts.net', {'TailscaleIPs': ['100.90.1.2']})


def test_worker_uses_default_no_ui_adapter_and_rechecks_identity(m, inputs, monkeypatch):
    calls = []
    rows = []
    fake = SimpleNamespace(mounted_shares=lambda: rows[:], mount_share=lambda host,user,share: (
        calls.append((host,user,share)), rows.append({'url':'smb://owner@pi.example.ts.net/Shared',
        'mountpoint':'/Volumes/Shared-2','owner':os.getuid()}), 0)[2])
    monkeypatch.setattr(m, 'native_adapter', lambda: fake)
    monkeypatch.setattr(m, 'tailnet', lambda: ('Running', [{'DNSName':'pi.example.ts.net.', 'Online':True, 'TailscaleIPs':['100.90.1.2']}]))
    monkeypatch.setattr(m, 'probe_peer', lambda *_: True)
    assert m.worker('pi400', inputs) == {'status':'mounted'}
    assert m.worker('pi400', inputs) == {'status':'mounted'}
    assert len(calls) == 1


@pytest.mark.parametrize('state,peer,expected', [('Stopped',True,'tailscale-unavailable'), ('Running',False,'offline')])
def test_worker_offline_preserves_mounts(m, inputs, monkeypatch, state, peer, expected):
    fake = SimpleNamespace(mounted_shares=lambda: [], mount_share=lambda *_: pytest.fail('must not mount'))
    monkeypatch.setattr(m, 'native_adapter', lambda: fake)
    monkeypatch.setattr(m, 'tailnet', lambda: (state,[{'DNSName':'pi.example.ts.net.','Online':peer,'TailscaleIPs':['100.90.1.2']}]))
    assert m.worker('pi400', inputs) == {'status':expected}


def render(path, **data):
    values={'machine_type':'mac-mini','chezmoi':{'os':'darwin','homeDir':"/Users/Owner & Tools"},**data}
    p=subprocess.run(['chezmoi','--source',str(ROOT),'--config','/dev/null','--config-format','toml',
        '--override-data',json.dumps(values),'execute-template','--file',str(ROOT/path)],text=True,capture_output=True)
    assert p.returncode==0,p.stderr
    return p.stdout


def test_job_is_bounded_user_session_with_no_secrets():
    p=plistlib.loads(render('private_Library/LaunchAgents/dev.dotfiles.smb-reconnect.plist.tmpl').encode())
    assert p['RunAtLoad'] is True and p['StartInterval']==60
    assert p['LimitLoadToSessionType']=='Aqua'
    assert p['ProgramArguments']==["/Users/Owner & Tools/.local/bin/smb-shares",'reconnect']
    assert p['Umask']==63 and 'KeepAlive' not in p
    assert p['StandardErrorPath']=='/dev/null'
    assert p['Disabled'] is False
    assert plistlib.loads(render('private_Library/LaunchAgents/dev.dotfiles.smb-reconnect.plist.tmpl',smb_reconnect_enabled=False).encode())['Disabled'] is True


@pytest.mark.parametrize('profile,os_name,expected', [('mac-mini','darwin',True),('macbook','darwin',True),('omarchy','linux',False),('fedora-server','linux',False),('fedora-workstation','linux',False)])
def test_client_profile_isolation(profile, os_name, expected):
    p=subprocess.run(['chezmoi','--source',str(ROOT),'--config','/dev/null','--config-format','toml',
        '--override-data',json.dumps({'machine_type':profile,'chezmoi':{'os':os_name}}),
        'managed','--include','files,symlinks'],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    paths=set(p.stdout.splitlines())
    assert ('.local/bin/smb-shares' in paths) is expected
    assert ('.local/lib/smb_shares/netfs.py' in paths) is expected
    assert ('Library/LaunchAgents/dev.dotfiles.smb-reconnect.plist' in paths) is expected
    assert '.config/samba/private-connections.json' not in paths


def test_native_worker_deadline_and_bad_output_are_safe(m, inputs, monkeypatch):
    seen = []
    def timed(command, **kwargs):
        seen.append((command, kwargs))
        raise subprocess.TimeoutExpired(command, kwargs['timeout'])
    monkeypatch.setattr(m.subprocess, 'run', timed)
    assert m.call_worker('pi400', inputs) == {'status':'timeout'}
    assert seen[0][1]['timeout'] == 20
    assert 'pi.example.ts.net' not in seen[0][0]
    monkeypatch.setattr(m.subprocess, 'run', lambda *_, **kw: SimpleNamespace(returncode=0, stdout=b'{"status":["private-data"]}'))
    assert m.call_worker('pi400', inputs) == {'status':'native-unavailable'}


def test_invalid_saved_state_is_not_echoed(m, inputs):
    inputs.state_dir.mkdir(mode=0o700)
    p=inputs.state_dir/'status.json'
    p.write_text('{"private":"must-never-print"}')
    p.chmod(0o600)
    with pytest.raises(m.Invalid, match='invalid saved status'):
        m.saved_status(inputs)


def test_native_unknown_identity_blocks_mount(m, inputs, monkeypatch):
    def unavailable(): raise RuntimeError('unknown SMB identity')
    fake=SimpleNamespace(mounted_shares=unavailable, mount_share=lambda *_: pytest.fail('must not mount'))
    monkeypatch.setattr(m,'native_adapter',lambda:fake)
    assert m.worker('pi400',inputs)=={'status':'identity-unavailable'}


def test_missing_native_credentials_return_status_without_ui(m, inputs, monkeypatch):
    fake=SimpleNamespace(mounted_shares=lambda:[],mount_share=lambda *_:80)
    monkeypatch.setattr(m,'native_adapter',lambda:fake)
    monkeypatch.setattr(m,'tailnet',lambda:('Running',[{'DNSName':'pi.example.ts.net.','Online':True,'TailscaleIPs':['100.90.1.2']}]))
    monkeypatch.setattr(m,'probe_peer',lambda *_:True)
    assert m.worker('pi400',inputs)=={'status':'needs-login'}


def test_foreign_owner_mount_is_preserved_and_never_reused_or_duplicated(m, inputs, monkeypatch):
    foreign={'url':'smb://owner@pi.example.ts.net/Shared','mountpoint':'/Volumes/Shared-1','owner':os.getuid()+1}
    fake=SimpleNamespace(mounted_shares=lambda:[foreign],mount_share=lambda *_:pytest.fail('foreign mount must not be replaced'))
    monkeypatch.setattr(m,'native_adapter',lambda:fake)
    monkeypatch.setattr(m,'tailnet',lambda:pytest.fail('conflict must stop before network or mount'))
    assert m.worker('pi400',inputs)=={'status':'identity-conflict'}
