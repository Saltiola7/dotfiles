#!/usr/bin/env python3
"""Unprivileged offline ext4 editor. Owns only its private staging files."""
from __future__ import annotations
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

PIN = 'aebf1cb693fbdbd45837980b3be6becbd34c321ff937c49e582244eaa2f48aaf'
BASE = 'Fedora-Minimal-44-1.7.aarch64.raw.xz'
ROOT_START = 4638720
ROOT_SIZE = 6291456


class Invalid(ValueError):
    pass


def check(condition: bool, reason: str) -> None:
    if not condition: raise Invalid(reason)


def run(args: list[str], data: str | None = None) -> str:
    result = subprocess.run(args, input=data, capture_output=True, text=True)
    check(result.returncode == 0, 'backend command failed')
    return result.stdout


def sha(path: Path) -> str:
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


class Ext4:
    """Commands use fixed guest destinations and generated safe staging names."""
    def __init__(self, root: Path, stage: Path):
        self.root, self.stage, self.counter = root, stage, 0

    def debug(self, command: str, write: bool = False) -> str:
        args = ['debugfs', *(['-w'] if write else []), '-R', command, str(self.root)]
        result = subprocess.run(args, capture_output=True, text=True)
        # debugfs can exit zero for invalid commands; inspect diagnostic text.
        bad = ('File not found', 'Command not found', 'already exists', 'while opening',
               'Usage:', 'Could not allocate', 'Permission denied')
        check(result.returncode == 0 and not any(x in result.stderr for x in bad), 'ext4 operation failed')
        return result.stdout

    def exists(self, destination: str) -> bool:
        r = subprocess.run(['debugfs', '-R', 'stat ' + destination, str(self.root)], capture_output=True, text=True)
        return r.returncode == 0 and 'Inode:' in r.stdout

    def read(self, destination: str) -> str:
        self.counter += 1
        output = self.stage / f'read-{self.counter}'
        self.debug(f'dump {destination} {output}')
        check(output.is_file(), 'expected image file unavailable')
        return output.read_text()

    def metadata(self, destination: str, mode: int, uid: int = 0, gid: int = 0) -> None:
        for field, value in [('mode', '0' + format(mode, 'o')), ('uid', str(uid)), ('gid', str(gid))]:
            self.debug(f'set_inode_field {destination} {field} {value}', True)

    def mkdir(self, destination: str, mode: int = 0o40755, uid: int = 0, gid: int = 0) -> None:
        if not self.exists(destination): self.debug('mkdir ' + destination, True)
        self.metadata(destination, mode, uid, gid)

    def write(self, destination: str, content: str | bytes, mode: int = 0o100644,
              uid: int = 0, gid: int = 0) -> None:
        self.counter += 1
        source = self.stage / f'write-{self.counter}'
        source.write_bytes(content.encode() if isinstance(content, str) else content)
        source.chmod(0o600)
        if self.exists(destination): self.debug('rm ' + destination, True)
        self.debug(f'write {source} {destination}', True)
        self.metadata(destination, mode, uid, gid)
        check(self.exists(destination), 'image write verification failed')

    def link(self, destination: str, target: str) -> None:
        if self.exists(destination): self.debug('rm ' + destination, True)
        self.debug(f'symlink {destination} {target}', True)


def main() -> None:
    os.umask(0o077)
    stage = Path(sys.argv[1]).resolve()
    check(re.fullmatch(r'/home/tis\.guest/\.local/state/pi-bootstrap/run-[A-Za-z0-9]+', str(stage)) is not None,
          'unexpected staging directory')
    check(stage.stat().st_uid == os.getuid() and stage.stat().st_mode & 0o077 == 0, 'unsafe staging permissions')
    os.chdir(stage)
    manifest = json.loads((stage / 'manifest.json').read_text())
    check(manifest['target'] == 'pi400' and manifest['sha256'] == PIN and manifest['owner'] == 'tis', 'policy mismatch')
    check(shutil.disk_usage(stage).free > 14 * 1024**3, 'insufficient isolated staging capacity')
    compressed = stage / BASE
    check(sha(compressed) == PIN, 'base hash mismatch in backend')
    password = json.loads(sys.stdin.read(65536))['password']
    check(isinstance(password, str) and len(password) >= 12 and '\n' not in password, 'invalid owner password')
    verifier = run(['openssl', 'passwd', '-6', '-stdin'], password + '\n').strip()
    password = ''
    check(verifier.startswith('$6$'), 'password hashing failed')
    candidate = stage / 'prepared.raw'
    check(not candidate.exists(), 'candidate already exists')
    with lzma.open(compressed, 'rb') as source, candidate.open('xb') as output:
        shutil.copyfileobj(source, output, 1024 * 1024)
    check(candidate.stat().st_size == 5596250112, 'unexpected raw image size')
    partition = json.loads(run(['sfdisk', '--json', str(candidate)]))['partitiontable']
    check(partition['label'] == 'dos' and partition['sectorsize'] == 512, 'partition table mismatch')
    parts = partition['partitions']
    check(len(parts) == 3 and parts[2]['start'] == ROOT_START and parts[2]['size'] == ROOT_SIZE,
          'root partition geometry mismatch')
    root = stage / 'root.ext4'
    with candidate.open('rb') as source, root.open('xb') as output:
        source.seek(ROOT_START * 512)
        remaining = ROOT_SIZE * 512
        while remaining:
            chunk = source.read(min(remaining, 1024 * 1024)); check(bool(chunk), 'truncated root partition')
            output.write(chunk); remaining -= len(chunk)
    run(['e2fsck', '-fn', str(root)])
    fs = Ext4(root, stage)
    os_release = fs.read('/usr/lib/os-release')
    check('VERSION_ID=44' in os_release and 'ID=fedora' in os_release, 'guest OS mismatch')
    passwd = fs.read('/etc/passwd'); shadow = fs.read('/etc/shadow'); group = fs.read('/etc/group')
    check(not any(line.split(':')[0] == 'tis' or line.split(':')[2] == '1000' for line in passwd.splitlines()), 'owner account or UID already allocated')
    check(not any(line.split(':')[0] == 'tis' or line.split(':')[2] == '1000' for line in group.splitlines()), 'owner GID already allocated')
    fs.write('/etc/passwd', passwd.rstrip() + '\ntis:x:1000:1000:Owner:/home/tis:/bin/bash\n')
    fs.write('/etc/shadow', shadow.rstrip() + f'\ntis:{verifier}:{int(time.time() // 86400)}:0:99999:7:::\n', 0o100000)
    verifier = ''
    groups = group.splitlines(); found = False
    for index, line in enumerate(groups):
        values = line.split(':')
        if values[0] == 'wheel':
            values[3] = ','.join(filter(None, [values[3], 'tis'])); groups[index] = ':'.join(values); found = True
    check(found, 'wheel group unavailable')
    fs.write('/etc/group', '\n'.join(groups) + '\ntis:x:1000:\n')
    fs.mkdir('/home/tis', 0o40700, 1000, 1000); fs.mkdir('/home/tis/.ssh', 0o40700, 1000, 1000)
    key = (stage / 'authorized_keys').read_text()
    check(key.startswith('ssh-ed25519 ') and key.count('\n') == 1, 'public key mismatch')
    fs.write('/home/tis/.ssh/authorized_keys', key, 0o100600, 1000, 1000)
    fs.mkdir('/etc/ssh/sshd_config.d')
    fs.write('/etc/ssh/sshd_config.d/00-pi-bootstrap.conf',
             'PubkeyAuthentication yes\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nAuthenticationMethods publickey\nHostKey /etc/ssh/ssh_host_ed25519_key\n')
    check('Include /etc/ssh/sshd_config.d/*.conf' in fs.read('/etc/ssh/sshd_config'), 'sshd drop-in include unavailable')
    fs.mkdir('/etc/sudoers.d')
    rule = 'Defaults:tis authenticate\ntis ALL=(ALL:ALL) PASSWD: ALL\n'
    rule_check = stage / 'sudo-rule-check'; rule_check.write_text(rule)
    run(['visudo', '-cf', str(rule_check)])
    fs.write('/etc/sudoers.d/99-pi-bootstrap', rule, 0o100440)
    for kind in ('rsa', 'ecdsa', 'ed25519'):
        for suffix in ('', '.pub'):
            dest = f'/etc/ssh/ssh_host_{kind}_key{suffix}'
            if fs.exists(dest): fs.debug('rm ' + dest, True)
    run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(stage / 'host-key')])
    fingerprint = run(['ssh-keygen', '-lf', str(stage / 'host-key.pub')]).split()[1]
    fs.write('/etc/ssh/ssh_host_ed25519_key', (stage / 'host-key').read_bytes(), 0o100600)
    fs.write('/etc/ssh/ssh_host_ed25519_key.pub', (stage / 'host-key.pub').read_bytes())
    fs.write('/etc/machine-id', '')
    fs.write('/etc/hostname', 'pi400\n')
    for name in ('initial-setup.service', 'initial-setup-reconfiguration.service'):
        fs.link('/etc/systemd/system/' + name, '/dev/null')
    check(fs.exists('/etc/systemd/system/multi-user.target.wants/sshd.service'), 'sshd not enabled in base')
    check(fs.exists('/etc/systemd/system/multi-user.target.wants/NetworkManager.service'), 'NetworkManager not enabled in base')
    selinux = fs.read('/etc/selinux/config')
    check('SELINUX=enforcing' in selinux, 'SELinux must remain enforcing')
    fs.write('/.autorelabel', '-F\n', 0o100600)
    for tool in ('sfdisk', 'partx', 'resize2fs', 'lsblk', 'findmnt'):
        check(any(fs.exists(prefix + tool) for prefix in ('/usr/bin/', '/usr/sbin/')), 'first-boot tool unavailable')
    fs.mkdir('/usr/local/libexec')
    fs.write('/usr/local/libexec/pi-bootstrap-grow', (stage / 'first-boot.sh').read_bytes(), 0o100755)
    fs.write('/etc/systemd/system/pi-bootstrap-grow.service', '''[Unit]
Description=Grow only the live Pi root partition and filesystem
After=local-fs.target
ConditionPathExists=!/var/lib/pi-bootstrap/grown
[Service]
Type=oneshot
ExecStart=/usr/local/libexec/pi-bootstrap-grow
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
''')
    fs.link('/etc/systemd/system/multi-user.target.wants/pi-bootstrap-grow.service', '/etc/systemd/system/pi-bootstrap-grow.service')
    check(fs.read('/home/tis/.ssh/authorized_keys') == key, 'installed public key mismatch')
    check('PasswordAuthentication no' in fs.read('/etc/ssh/sshd_config.d/00-pi-bootstrap.conf'), 'SSH policy mismatch')
    check('PASSWD: ALL' in fs.read('/etc/sudoers.d/99-pi-bootstrap'), 'owner privilege policy mismatch')
    attrs = fs.debug('stat /home/tis/.ssh/authorized_keys')
    check(re.search(r'User:\s+1000\s+Group:\s+1000', attrs) is not None and '0600' in attrs,
          'public key inode attributes mismatch')
    run(['e2fsck', '-fn', str(root)])
    with root.open('rb') as source, candidate.open('r+b') as output:
        output.seek(ROOT_START * 512); shutil.copyfileobj(source, output, 1024 * 1024)
    candidate.chmod(0o600)
    receipt = dict(schema_version=1, target='pi400', base_sha256=PIN,
                   prepared_sha256=sha(candidate), host_key_fingerprint=fingerprint,
                   checks=['publisher-verified-input', 'offline-filesystem', 'account-uid-gid',
                           'key-owner-mode', 'key-only-ssh', 'password-required-sudo', 'SELinux-enforcing-relabel',
                           'initial-setup-masked', 'first-boot-growth-installed'], physical_boot='unverified')
    (stage / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (stage / 'receipt.json').chmod(0o600)


if __name__ == '__main__':
    try:
        main()
    except Invalid as error:
        print('pi-bootstrap backend: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
    except (OSError, ValueError, KeyError, IndexError):
        # Never display raw input, shadow, passwords, private keys or command output.
        print('pi-bootstrap backend: preparation failed; private staging retained', file=sys.stderr)
        raise SystemExit(2)
