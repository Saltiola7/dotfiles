"""Native SMB requests preserve authentication and mount-identity boundaries."""
import ctypes
import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'dot_local/lib/smb_shares/netfs.py'


def load_module():
    spec = importlib.util.spec_from_file_location('smb_netfs_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Function:
    def __init__(self, implementation):
        self.implementation = implementation
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.implementation(*args)


class FakeLibraries:
    """Represent CF objects as pointers without loading macOS frameworks."""
    def __init__(self, module):
        self.module = module
        self.objects = {}
        self.released = []
        self.next_pointer = 100
        self.url_for_mount = {}
        self.mount_status = 0
        self.mounted_array = 0
        self.rows = []
        self.table = None
        self.cf = type('FakeCF', (), {})()
        self.netfs = type('FakeNetFS', (), {})()
        self.libc = type('FakeLibC', (), {})()
        self.cf.CFStringCreateWithCString = Function(self.create_string)
        self.cf.CFURLCreateWithString = Function(lambda _a, string, _b: self.store(self.objects[string]))
        self.cf.CFURLCreateFromFileSystemRepresentation = Function(
            lambda _a, path, _size, _directory: self.store(path.decode()))
        self.cf.CFURLGetString = Function(lambda url: self.store(self.objects[url]))
        self.cf.CFStringGetCString = Function(self.copy_string)
        self.cf.CFDictionaryCreateMutable = Function(lambda *_args: self.store({}))
        self.cf.CFDictionarySetValue = Function(self.set_value)
        self.cf.CFRelease = Function(lambda pointer: self.released.append(pointer))
        self.netfs.NetFSCopyURLForRemountingVolume = Function(self.copy_mount_url)
        self.netfs.NetFSMountURLSync = Function(self.mount)
        self.libc.getmntinfo = Function(self.getmntinfo)

    def store(self, value):
        self.next_pointer += 1
        self.objects[self.next_pointer] = value
        return self.next_pointer

    def create_string(self, _allocator, value, _encoding):
        return self.store(value.decode())

    def copy_string(self, string, output, capacity, _encoding):
        encoded = self.objects[string].encode()
        if len(encoded) >= capacity:
            return False
        ctypes.memmove(output, encoded + b'\0', len(encoded) + 1)
        return True

    def set_value(self, dictionary, key, value):
        self.objects[dictionary][self.objects[key]] = self.objects[value]

    def copy_mount_url(self, local_url):
        value = self.url_for_mount.get(self.objects[local_url])
        return self.store(value) if value is not None else None

    def mount(self, *_args):
        self.mounted_array = self.store('mountpoint array')
        ctypes.cast(_args[-1], ctypes.POINTER(ctypes.c_void_p))[0] = self.mounted_array
        return self.mount_status

    def getmntinfo(self, output, flags):
        self.table = (self.module.StatFS * len(self.rows))()
        for index, row in enumerate(self.rows):
            self.table[index].f_fstypename = row.get('type', 'smbfs').encode()
            self.table[index].f_mntonname = row['mountpoint'].encode()
            self.table[index].f_mntfromname = row.get('source', '').encode()
            self.table[index].f_owner = row.get('owner', 501)
        ctypes.cast(output, ctypes.POINTER(ctypes.POINTER(self.module.StatFS)))[0] = self.table
        return len(self.rows)

    def native(self):
        return self.module.Native(core_foundation=self.cf, netfs=self.netfs,
                                  libc=self.libc, dictionary_callbacks=(None, None))


def test_import_never_loads_native_libraries(monkeypatch):
    monkeypatch.setattr(ctypes, 'CDLL', lambda *_a, **_k: pytest.fail('eager native library load'))
    module = load_module()
    assert callable(module.mounted_shares)
    assert callable(module.mount_share)


def test_native_refuses_unsupported_runtime(monkeypatch):
    module = load_module()
    monkeypatch.setattr(sys, 'platform', 'linux')
    with pytest.raises(RuntimeError, match='macOS'):
        module.Native()


def test_modern_statfs_layout_matches_darwin_sdk():
    module = load_module()
    assert ctypes.sizeof(module.StatFS) == 2168
    assert module.StatFS.f_owner.offset == 56
    assert module.StatFS.f_fstypename.offset == 72
    assert module.StatFS.f_mntonname.offset == 88
    assert module.StatFS.f_mntfromname.offset == 1112


def test_native_signatures_preserve_pointer_width_and_signed_status():
    module = load_module()
    libraries = FakeLibraries(module)
    libraries.native()
    pointer = ctypes.c_void_p
    assert libraries.netfs.NetFSMountURLSync.argtypes == [pointer] * 6 + [ctypes.POINTER(pointer)]
    assert libraries.netfs.NetFSMountURLSync.restype is ctypes.c_int
    assert libraries.netfs.NetFSCopyURLForRemountingVolume.restype is pointer
    assert libraries.libc.getmntinfo.argtypes == [ctypes.POINTER(ctypes.POINTER(module.StatFS)), ctypes.c_int]


def test_mount_delegates_credentials_to_system_and_suppresses_ui():
    module = load_module()
    libraries = FakeLibraries(module)
    native = libraries.native()
    libraries.mount_status = -6602
    assert native.mount_share('pi.example.ts.net', 'example', 'Shared Folder') == -6602
    request = libraries.netfs.NetFSMountURLSync.calls[0]
    url, mountpoint, user, password, options, mount_options, _result = request
    assert libraries.objects[url] == 'smb://pi.example.ts.net/Shared%20Folder'
    assert libraries.objects[user] == 'example'
    assert mountpoint is None and password is None and mount_options is None
    assert libraries.objects[options] == {'UIOption': 'NoUI'}
    assert libraries.mounted_array in libraries.released
    assert all(value in libraries.released for value in [url, user, options])


def test_ipv6_host_uses_brackets_without_userinfo_in_url():
    module = load_module()
    libraries = FakeLibraries(module)
    libraries.native().mount_share('fd00::1', 'example', 'Shared')
    url = libraries.netfs.NetFSMountURLSync.calls[0][0]
    assert libraries.objects[url] == 'smb://[fd00::1]/Shared'


@pytest.mark.parametrize('host,user,share', [
    ('smb://server', 'example', 'Shared'),
    ('user:secret@server', 'example', 'Shared'),
    ('server/path', 'example', 'Shared'),
    ('server', 'example\0', 'Shared'),
    ('server', 'example', '../Shared'),
])
def test_mount_refuses_unsafe_components_before_native_request(host, user, share):
    module = load_module()
    libraries = FakeLibraries(module)
    with pytest.raises(RuntimeError):
        libraries.native().mount_share(host, user, share)
    assert not libraries.netfs.NetFSMountURLSync.calls


def test_mount_inventory_uses_cached_table_and_native_identity(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.os, 'getuid', lambda: 501)
    libraries = FakeLibraries(module)
    libraries.rows = [
        {'type': 'apfs', 'mountpoint': '/'},
        {'mountpoint': '/Volumes/Shared'},
        {'mountpoint': '/Volumes/Other', 'owner': 502,
         'source': '//example@other.example.ts.net/Shared'},
    ]
    libraries.url_for_mount['/Volumes/Shared'] = 'smb://example@pi.example.ts.net/Shared'
    assert libraries.native().mounted_shares() == [{
        'url': 'smb://example@pi.example.ts.net/Shared',
        'mountpoint': '/Volumes/Shared', 'owner': 501,
    }, {
        'url': 'smb://example@other.example.ts.net/Shared',
        'mountpoint': '/Volumes/Other', 'owner': 502,
    }]
    assert libraries.libc.getmntinfo.calls[0][1] == 2  # MNT_NOWAIT
    assert len(libraries.netfs.NetFSCopyURLForRemountingVolume.calls) == 1
    assert len(libraries.released) == 2  # created file URL and copied server URL


@pytest.mark.parametrize('url', [None, '', 'file:///Volumes/Shared',
                               'smb://example:secret@server/Shared', 'smb://server/'])
def test_unidentified_or_credential_bearing_own_smb_mount_fails_closed(monkeypatch, url):
    module = load_module()
    monkeypatch.setattr(module.os, 'getuid', lambda: 501)
    libraries = FakeLibraries(module)
    libraries.rows = [{'mountpoint': '/Volumes/Shared'}]
    libraries.url_for_mount['/Volumes/Shared'] = url
    with pytest.raises(RuntimeError) as error:
        libraries.native().mounted_shares()
    assert 'secret' not in str(error.value)


def test_failed_mount_table_does_not_claim_no_existing_shares():
    module = load_module()
    libraries = FakeLibraries(module)
    with pytest.raises(RuntimeError):
        libraries.native().mounted_shares()


def test_foreign_owner_mount_uses_only_cached_identity(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.os, 'getuid', lambda: 501)
    libraries = FakeLibraries(module)
    libraries.rows = [{'mountpoint': '/Volumes/Shared-1', 'owner': 0,
                       'source': '//example@pi.example.ts.net/Shared'}]
    assert libraries.native().mounted_shares() == [{
        'url': 'smb://example@pi.example.ts.net/Shared',
        'mountpoint': '/Volumes/Shared-1', 'owner': 0,
    }]
    assert not libraries.netfs.NetFSCopyURLForRemountingVolume.calls
    assert not libraries.cf.CFURLCreateFromFileSystemRepresentation.calls


@pytest.mark.parametrize('source', ['', 'missing', '//server/',
                                    '//example:secret@server/Shared',
                                    '//server/Shared?password=secret',
                                    '//server/Shared#secret'])
def test_foreign_owner_identity_failure_is_safe_and_never_queries_path(monkeypatch, source):
    module = load_module()
    monkeypatch.setattr(module.os, 'getuid', lambda: 501)
    libraries = FakeLibraries(module)
    libraries.rows = [{'mountpoint': '/Volumes/Shared', 'owner': 0,
                       'source': source}]
    with pytest.raises(RuntimeError) as error:
        libraries.native().mounted_shares()
    assert 'secret' not in str(error.value)
    assert not libraries.netfs.NetFSCopyURLForRemountingVolume.calls
