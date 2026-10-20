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

class HttpsResponse:
    def __init__(self, body=b'{"status":"pass"}', status=200, content_type='application/json'):
        self.body=body
        self.status=status
        self.headers={'Content-Type':content_type}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,limit): return self.body[:limit]


def https_fixture(monkeypatch, responses=None):
    import json, urllib.error
    m=load()
    monkeypatch.setattr(m.subprocess,'check_output',lambda args,**kwargs:json.dumps({'Self':{'DNSName':'node.private.ts.net.'}}).encode())
    calls=[]
    responses=list(responses if responses is not None else [
        HttpsResponse(),HttpsResponse(b'<html>Login</html>',content_type='text/html'),
        urllib.error.HTTPError('https://node.private.ts.net/api/v1/user',403,'Forbidden',{},None)])
    class Opener:
        def open(self,url,timeout):
            calls.append((url,timeout))
            response=responses.pop(0)
            if isinstance(response,Exception): raise response
            return response
    handlers=[]
    def build(*values):
        handlers.extend(values)
        return Opener()
    monkeypatch.setattr(m.urllib.request,'build_opener',build)
    return m,calls,handlers


def test_https_check_trusts_tls_and_denies_anonymous(monkeypatch,capsys):
    import ssl
    m,calls,handlers=https_fixture(monkeypatch)
    m.https_check()
    assert [url for url,_ in calls]==['https://node.private.ts.net'+p for p in ('/api/healthz','/user/login','/api/v1/user')]
    assert all(timeout==10 for _,timeout in calls)
    tls=next(h for h in handlers if isinstance(h,m.urllib.request.HTTPSHandler))
    assert tls._context.verify_mode==ssl.CERT_REQUIRED and tls._context.check_hostname
    assert next(h for h in handlers if isinstance(h,m.urllib.request.ProxyHandler)).proxies=={}
    assert 'node.private.ts.net' not in capsys.readouterr().out


@pytest.mark.parametrize('body',[b'{"status":"fail"}',b'[]',b'not json',b'x'*65537],ids=['unhealthy','wrong-shape','invalid-json','oversized'])
def test_https_check_rejects_bad_health(monkeypatch,body):
    m,calls,_=https_fixture(monkeypatch,[HttpsResponse(body)])
    with pytest.raises(m.HttpsReadinessError): m.https_check()
    assert len(calls)==1


@pytest.mark.parametrize('kind',['tls','timeout','server','anonymous','redirect','content_type','login'])
def test_https_check_fails_closed_without_retry(monkeypatch,kind):
    import ssl,urllib.error
    good=HttpsResponse()
    login=HttpsResponse(b'<html>Login</html>',content_type='text/html')
    cases={
        'tls':[urllib.error.URLError(ssl.SSLCertVerificationError('private details'))],
        'timeout':[TimeoutError('private details')],
        'server':[urllib.error.HTTPError('private',503,'private details',{},None)],
        'anonymous':[good,login,HttpsResponse(b'{"private":"details"}')],
        'redirect':[HttpsResponse(status=302)],
        'content_type':[HttpsResponse(content_type='text/html')],
        'login':[good,HttpsResponse(b'{}')],
    }
    m,calls,_=https_fixture(monkeypatch,cases[kind])
    with pytest.raises(m.HttpsReadinessError) as caught: m.https_check()
    assert 'private details' not in str(caught.value)
    assert len(calls)==len(cases[kind])


@pytest.mark.parametrize('domain',['https://other.ts.net','other.ts.net/secret','node..ts.net','node.private.ts.net\n','-node.private.ts.net','node.private.example.org','node.private.ts.net:443',None])
def test_https_check_rejects_invalid_node_name(monkeypatch,domain):
    import json
    m,calls,_=https_fixture(monkeypatch)
    monkeypatch.setattr(m.subprocess,'check_output',lambda args,**kwargs:json.dumps({'Self':{'DNSName':domain}}).encode())
    with pytest.raises(m.HttpsReadinessError): m.https_check()
    assert not calls


def test_https_redirect_handler_never_follows(monkeypatch):
    m,_,handlers=https_fixture(monkeypatch)
    m.https_check()
    redirect=next(h for h in handlers if isinstance(h,m.urllib.request.HTTPRedirectHandler))
    with pytest.raises(m.HttpsReadinessError):
        redirect.redirect_request(None,None,302,'Found',{},'http://outside.invalid')


def test_network_configuration_failure_preserves_routes(monkeypatch):
    import json
    m=load();calls=[]
    existing={'TCP':{'445':{'TCPForward':'127.0.0.1:445'},'9000':{'TCPForward':'127.0.0.1:9000'},'2222':{'TCPForward':'127.0.0.1:2222'}}}
    monkeypatch.setattr(m.subprocess,'check_output',lambda args,**kwargs:json.dumps(existing).encode())
    monkeypatch.setattr(m,'run',lambda *args:calls.append(args))
    def fail(): raise m.HttpsReadinessError('HTTPS readiness failed')
    monkeypatch.setattr(m,'https_check',fail)
    with pytest.raises(m.HttpsReadinessError): m.network()
    assert calls==[('sudo','tailscale','serve','--bg','--https=443','http://127.0.0.1:3000')]
