"""Flash safety boundaries and regular-file simulation; never access real disks."""
import hashlib
import io
import json
import time
from pathlib import Path

import pytest
import importlib.machinery
import importlib.util
import os


def module():
    root=Path(__file__).resolve().parents[1]
    path=os.environ.get('PI_BOOTSTRAP_TEST_CLI', str(root/'dot_local/bin/executable_pi-bootstrap'))
    loader=importlib.machinery.SourceFileLoader('pi_flash_test', path)
    spec=importlib.util.spec_from_loader(loader.name,loader)
    value=importlib.util.module_from_spec(spec); loader.exec_module(value)
    return value


def disk():
    return dict(DeviceIdentifier='disk4', DeviceNode='/dev/disk4', WholeDisk=True,
                Internal=False, Writable=True, BusProtocol='USB', MediaName='Transcend',
                TotalSize=512110190592, DeviceTreePath='trusted-usb-path')


@pytest.mark.parametrize('field,value', [('Internal', True), ('WholeDisk', False),
    ('Writable', False), ('MediaName', 'other'), ('BusProtocol', 'PCI'),
    ('TotalSize', 1000), ('DeviceNode', '/dev/disk4s1'), ('DeviceIdentifier', 'disk5')])
def test_wrong_disk_rejected(field, value):
    m=module(); d=disk(); d[field]=value
    with pytest.raises(m.Invalid): m.disk_identity(d, '/dev/disk4')


def test_disk_identity_and_drift():
    m=module(); identity=m.disk_identity(disk(), '/dev/disk4')
    assert identity['DeviceNode']=='/dev/disk4'
    changed=disk(); changed['DeviceTreePath']='different-port'
    assert m.disk_identity(changed, '/dev/disk4') != identity


def test_plan_expiry_and_approval():
    m=module()
    p=dict(schema_version=1,target='pi400', image='/private/candidate.raw',
           image_size=1024,image_sha256='a'*64, disk=m.disk_identity(disk(),'/dev/disk4'),
           header_sha256='b'*64, created_at=int(time.time()), expires_at=int(time.time())+1800)
    approval=m.plan_digest(p)
    m.validate_flash_plan(p,approval)
    with pytest.raises(m.Invalid):m.validate_flash_plan(p,'c'*64)
    p['expires_at']=int(time.time())-1
    with pytest.raises(m.Invalid):m.validate_flash_plan(p,m.plan_digest(p))


def test_regular_file_write_readback_preserves_tail(tmp_path):
    m=module(); data=b'Pi-image'*128
    image=tmp_path/'image'; image.write_bytes(data)
    target=tmp_path/'disk'; target.write_bytes(b'?'*2048)
    with image.open('rb') as source, target.open('r+b',buffering=0) as device:
        result=m.write_and_verify(source,device,len(data),hashlib.sha256(data).hexdigest())
    assert result==hashlib.sha256(data).hexdigest()
    assert target.read_bytes()==data+b'?'*1024


def test_bad_image_rejected_before_write(tmp_path):
    m=module(); image=tmp_path/'image';image.write_bytes(b'x'*1024)
    target=tmp_path/'disk'; target.write_bytes(b'?'*1024)
    with image.open('rb') as source,target.open('r+b',buffering=0) as device:
        with pytest.raises(m.Invalid):m.write_and_verify(source,device,1024,'a'*64)
    assert target.read_bytes()==b'?'*1024


def test_readback_mismatch_is_failure(tmp_path):
    m=module(); data=b'x'*1024
    class Corrupt(io.BytesIO):
        def fileno(self): return 1
        def read(self,n=-1): return b'?'*len(super().read(n))
    with pytest.raises(m.Invalid):
        m.write_and_verify(io.BytesIO(data),Corrupt(b'?'*1024),1024,hashlib.sha256(data).hexdigest(),flush=lambda _:None)


def test_partial_write_never_succeeds():
    m=module(); data=b'x'*1024
    class Broken(io.BytesIO):
        def write(self,value): raise OSError('simulated device failure')
    with pytest.raises(OSError):
        m.write_and_verify(io.BytesIO(data),Broken(),1024,hashlib.sha256(data).hexdigest(),flush=lambda _:None)


def test_bootstrap_help_declares_guarded_flash():
    m=module()
    assert callable(m.flash_plan) and callable(m.flash)
    source=Path(m.__file__).read_text()
    assert "unmountDisk" in source and "eject" in source
    assert 'StrictHostKeyChecking=no' not in source


def test_size_mismatch_rejected_before_write():
    m=module(); source=io.BytesIO(b'x'*1024); device=io.BytesIO(b'?'*1024)
    with pytest.raises(m.Invalid):
        m.write_and_verify(source,device,512,hashlib.sha256(b'x'*1024).hexdigest(),flush=lambda _:None)
    assert device.getvalue()==b'?'*1024


@pytest.mark.parametrize('drift', ['header', 'disk'])
def test_flash_identity_drift_never_unmounts(tmp_path, monkeypatch, drift):
    import argparse
    m=module(); image=tmp_path/'prepared.raw'; image.write_bytes(b'x'*1024)
    p=dict(schema_version=1,target='pi400',image=str(image),image_size=1024,
           image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
           disk=m.disk_identity(disk(),'/dev/disk4'),header_sha256='b'*64,
           created_at=int(time.time()),expires_at=int(time.time())+1800)
    plan=tmp_path/'plan.json'; plan.write_text(json.dumps(p))
    monkeypatch.setattr(m,'operator_uid',lambda:1000)
    monkeypatch.setattr(m,'private_file',lambda *_:None)
    monkeypatch.setattr(m,'verify_output',lambda _:dict(prepared_sha256=p['image_sha256']))
    current=dict(p['disk'])
    if drift=='disk':current['DeviceTreePath']='other-port'
    monkeypatch.setattr(m,'disk_info',lambda _:current)
    monkeypatch.setattr(m,'header_digest',lambda _:('c'*64 if drift=='header' else p['header_sha256']))
    def forbidden(*_):raise AssertionError('must not invoke disk mutation')
    monkeypatch.setattr(m,'command',forbidden)
    with pytest.raises(m.Invalid):m.flash(argparse.Namespace(plan=plan,approve_plan=m.plan_digest(p)))
