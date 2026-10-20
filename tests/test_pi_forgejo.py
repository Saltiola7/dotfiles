from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import configparser
import pytest
ROOT=Path(__file__).resolve().parents[1]

def load():
    loader=SourceFileLoader('pi_forgejo',str(ROOT/'dot_local/bin/executable_pi-forgejo-setup'))
    module=module_from_spec(spec_from_loader(loader.name,loader));loader.exec_module(module);return module

def test_wrong_binary_refused(tmp_path):
    path=tmp_path/'binary';path.write_bytes(b'unknown payload')
    with pytest.raises(ValueError,match='identity'):load().verify_binary(path)

def test_private_forgejo_settings(tmp_path):
    cfg=configparser.ConfigParser(interpolation=None)
    cfg.read_string('[DEFAULT]\n'+load().make_config(tmp_path,'node.private.ts.net',{'secret':'test','internal':'test','lfs':'test'}))
    assert cfg['server']['HTTP_ADDR']=='127.0.0.1'
    assert cfg['server']['SSH_LISTEN_HOST']=='127.0.0.1'
    assert cfg['server']['START_SSH_SERVER']=='true'
    assert cfg['security']['INSTALL_LOCK']=='true'
    assert cfg['service']['DISABLE_REGISTRATION']=='true'
    assert cfg['service']['REQUIRE_SIGNIN_VIEW']=='true'
    assert cfg['database']['DB_TYPE']=='sqlite3'
    assert cfg['server']['SSH_ROOT_PATH']!=str(tmp_path/'.ssh')

def test_symlink_data_refused(tmp_path):
    outside=tmp_path/'outside';outside.mkdir();link=tmp_path/'forgejo';link.symlink_to(outside)
    with pytest.raises(ValueError,match='symlink'):load().ordinary(link)

@pytest.mark.parametrize('profile,target,allowed',[('fedora-server','pi400',True),('fedora-server','',False),('mac-mini','',False),('macbook','',False),('omarchy','',False)])
def test_managed_forgejo_targets_and_runtime_isolation(tmp_path,profile,target,allowed):
    import shutil,json,subprocess
    source=tmp_path/'source';source.mkdir()
    for relative in ['.chezmoiignore','dot_local/bin/executable_pi-forgejo-setup','dot_local/bin/executable_pi-forgejo-check','private_dot_config/homelab-git-hosting/forgejo.service','private_dot_config/homelab-git-hosting/release.json']:
        dst=source/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,dst)
    runtime=source/'dot_local/share/forgejo/private/app.ini';runtime.parent.mkdir(parents=True);runtime.write_text('synthetic runtime secret')
    r=subprocess.run(['chezmoi','--source',str(source),'--config','/dev/null','--config-format','toml','--override-data',json.dumps({'machine_type':profile,'homelab_target':target}),'--persistent-state',str(tmp_path/'state.db'),'managed','--include','files'],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    targets=set(r.stdout.splitlines())
    assert ('.local/bin/pi-forgejo-setup' in targets)==allowed
    assert ('.config/homelab-git-hosting/forgejo.service' in targets)==allowed
    assert '.local/share/forgejo/private/app.ini' not in targets
