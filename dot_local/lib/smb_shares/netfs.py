"""Minimal macOS NetFS boundary; callers bound native work in subprocesses.

Authentication stays in macOS NetAuth. This module never queries credentials,
selects guest authentication, presents authentication UI, or unmounts volumes.
"""
import ctypes
import ipaddress
import os
import re
import sys
from urllib.parse import quote, urlsplit


class StatFS(ctypes.Structure):
    """Darwin's modern 64-bit-inode statfs ABI, from sys/mount.h."""
    _fields_ = [
        ('f_bsize', ctypes.c_uint32), ('f_iosize', ctypes.c_int32),
        ('f_blocks', ctypes.c_uint64), ('f_bfree', ctypes.c_uint64),
        ('f_bavail', ctypes.c_uint64), ('f_files', ctypes.c_uint64),
        ('f_ffree', ctypes.c_uint64), ('f_fsid', ctypes.c_int32 * 2),
        ('f_owner', ctypes.c_uint32), ('f_type', ctypes.c_uint32),
        ('f_flags', ctypes.c_uint32), ('f_fssubtype', ctypes.c_uint32),
        ('f_fstypename', ctypes.c_char * 16),
        ('f_mntonname', ctypes.c_char * 1024),
        ('f_mntfromname', ctypes.c_char * 1024),
        ('f_flags_ext', ctypes.c_uint32), ('f_reserved', ctypes.c_uint32 * 7),
    ]


class Native:
    """Lazily bind system libraries; injectable libraries support boundary tests."""
    def __init__(self, *, core_foundation=None, netfs=None, libc=None,
                 dictionary_callbacks=None):
        if any(library is None for library in (core_foundation, netfs, libc)):
            if sys.platform != 'darwin' or ctypes.sizeof(ctypes.c_void_p) != 8:
                raise RuntimeError('Native SMB access requires 64-bit macOS')
            core_foundation = core_foundation or ctypes.CDLL(
                '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
            netfs = netfs or ctypes.CDLL('/System/Library/Frameworks/NetFS.framework/NetFS')
            libc = libc or ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
        self.cf, self.netfs, self.libc = core_foundation, netfs, libc
        pointer = ctypes.c_void_p
        bindings = [
            (self.cf, 'CFStringCreateWithCString', [pointer, ctypes.c_char_p, ctypes.c_uint32], pointer),
            (self.cf, 'CFURLCreateWithString', [pointer, pointer, pointer], pointer),
            (self.cf, 'CFURLCreateFromFileSystemRepresentation',
             [pointer, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool], pointer),
            (self.cf, 'CFURLGetString', [pointer], pointer),
            (self.cf, 'CFStringGetCString',
             [pointer, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32], ctypes.c_bool),
            (self.cf, 'CFDictionaryCreateMutable',
             [pointer, ctypes.c_long, pointer, pointer], pointer),
            (self.cf, 'CFDictionarySetValue', [pointer, pointer, pointer], None),
            (self.cf, 'CFRelease', [pointer], None),
            (self.netfs, 'NetFSCopyURLForRemountingVolume', [pointer], pointer),
            (self.netfs, 'NetFSMountURLSync',
             [pointer] * 6 + [ctypes.POINTER(pointer)], ctypes.c_int),
        ]
        for library, name, arguments, result in bindings:
            function = getattr(library, name)
            function.argtypes, function.restype = arguments, result
        # Intel exports the inode64-suffixed symbol; ARM64 uses the plain name.
        self.getmntinfo = getattr(self.libc, 'getmntinfo$INODE64', self.libc.getmntinfo)
        self.getmntinfo.argtypes = [ctypes.POINTER(ctypes.POINTER(StatFS)), ctypes.c_int]
        self.getmntinfo.restype = ctypes.c_int
        if dictionary_callbacks is None:
            dictionary_callbacks = tuple(ctypes.addressof((ctypes.c_byte * 1).in_dll(self.cf, name))
                                         for name in ('kCFTypeDictionaryKeyCallBacks',
                                                      'kCFTypeDictionaryValueCallBacks'))
        self.dictionary_callbacks = dictionary_callbacks

    def _string(self, text: str):
        result = self.cf.CFStringCreateWithCString(None, text.encode('utf-8'), 0x08000100)
        if not result:
            raise RuntimeError('Native SMB string allocation failed')
        return result

    def _text(self, string) -> str:
        if not string:
            raise RuntimeError('Native SMB identity unavailable')
        output = ctypes.create_string_buffer(32768)
        if not self.cf.CFStringGetCString(string, output, len(output), 0x08000100):
            raise RuntimeError('Native SMB identity unavailable')
        try:
            return output.value.decode('utf-8')
        except UnicodeError:
            raise RuntimeError('Native SMB identity unavailable') from None

    def _mount_url(self, mountpoint: str) -> str:
        path = mountpoint.encode('utf-8')
        local_url = self.cf.CFURLCreateFromFileSystemRepresentation(None, path, len(path), True)
        if not local_url:
            raise RuntimeError('Native SMB identity unavailable')
        server_url = None
        try:
            server_url = self.netfs.NetFSCopyURLForRemountingVolume(local_url)
            if not server_url:
                raise RuntimeError('Native SMB identity unavailable')
            text = self._text(self.cf.CFURLGetString(server_url))
            try:
                url = urlsplit(text)
                valid = (url.scheme == 'smb' and url.hostname and url.password is None
                         and url.path not in ('', '/') and not url.query and not url.fragment)
            except ValueError:
                valid = False
            if not valid:
                raise RuntimeError('Native SMB identity unavailable')
            return text
        finally:
            if server_url:
                self.cf.CFRelease(server_url)
            self.cf.CFRelease(local_url)

    def mounted_shares(self) -> list[dict]:
        """Return own-user SMB identities, failing closed on unknown identities."""
        table = ctypes.POINTER(StatFS)()
        count = self.getmntinfo(ctypes.byref(table), 2)  # MNT_NOWAIT: cached mount metadata
        if count <= 0 or count > 65536 or not table:
            raise RuntimeError('Native mount inventory unavailable')
        # Copy paths before further library calls: getmntinfo owns its static buffer.
        mounts = []
        for index in range(count):
            row = table[index]
            if row.f_fstypename != b'smbfs' or row.f_owner != os.getuid():
                continue
            try:
                path = row.f_mntonname.decode('utf-8')
            except UnicodeError:
                raise RuntimeError('Native SMB identity unavailable') from None
            if not path.startswith('/'):
                raise RuntimeError('Native SMB identity unavailable')
            mounts.append((path, int(row.f_owner)))
        return [{'url': self._mount_url(path), 'mountpoint': path, 'owner': owner}
                for path, owner in mounts]

    def mount_share(self, host: str, user: str, share: str) -> int:
        """Request default-placement NoUI mounting with system-managed credentials."""
        components = (host, user, share)
        if (not all(isinstance(value, str) and 0 < len(value) <= 255 for value in components)
                or any(any(ord(char) < 32 or ord(char) == 127 for char in value)
                       for value in components)
                or share in ('.', '..') or '/' in share or '\\' in share):
            raise RuntimeError('Invalid SMB mount components')
        if ':' in host:
            try:
                ipaddress.IPv6Address(host)
            except ValueError:
                raise RuntimeError('Invalid SMB mount components') from None
            authority = f'[{host}]'
        elif re.fullmatch(r'[A-Za-z0-9.-]+', host):
            authority = host
        else:
            raise RuntimeError('Invalid SMB mount components')
        owned = []
        mountpoints = ctypes.c_void_p()
        try:
            url_string = self._string(f'smb://{authority}/{quote(share, safe="")}')
            owned.append(url_string)
            url = self.cf.CFURLCreateWithString(None, url_string, None)
            if not url:
                raise RuntimeError('Native SMB URL allocation failed')
            owned.append(url)
            username = self._string(user)
            owned.append(username)
            key = self._string('UIOption')
            owned.append(key)
            no_ui = self._string('NoUI')
            owned.append(no_ui)
            options = self.cf.CFDictionaryCreateMutable(None, 0, *self.dictionary_callbacks)
            if not options:
                raise RuntimeError('Native SMB options allocation failed')
            owned.append(options)
            self.cf.CFDictionarySetValue(options, key, no_ui)
            return int(self.netfs.NetFSMountURLSync(
                url, None, username, None, options, None, ctypes.byref(mountpoints)))
        finally:
            if mountpoints.value:
                self.cf.CFRelease(mountpoints.value)
            for value in reversed(owned):
                self.cf.CFRelease(value)


def mounted_shares() -> list[dict]:
    return Native().mounted_shares()


def mount_share(host: str, user: str, share: str) -> int:
    return Native().mount_share(host, user, share)
