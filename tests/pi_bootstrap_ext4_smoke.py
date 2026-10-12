"""Run with existing Linux e2fsprogs; edits only a temporary 16 MiB filesystem."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location('pi_editor', sys.argv[1])
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)
with tempfile.TemporaryDirectory(prefix='pi-ext4-check-') as temporary:
    stage = Path(temporary)
    root = stage / 'fixture.ext4'
    with root.open('wb') as file: file.truncate(16 * 1024 * 1024)
    subprocess.run(['mkfs.ext4', '-q', '-F', str(root)], check=True)
    fs = editor.Ext4(root, stage)
    fs.mkdir('/home'); fs.mkdir('/home/tis', 0o40700, 1000, 1000)
    fs.mkdir('/home/tis/.ssh', 0o40700, 1000, 1000)
    fs.write('/home/tis/.ssh/authorized_keys', 'public-test-key\n', 0o100600, 1000, 1000)
    assert fs.read('/home/tis/.ssh/authorized_keys') == 'public-test-key\n'
    details = fs.debug('stat /home/tis/.ssh/authorized_keys')
    assert '0600' in details and editor.re.search(r'User:\s+1000\s+Group:\s+1000', details)
    fs.write('/home/tis/.ssh/authorized_keys', 'updated\n', 0o100600, 1000, 1000)
    assert fs.read('/home/tis/.ssh/authorized_keys') == 'updated\n'
    fs.mkdir('/etc'); fs.mkdir('/etc/systemd'); fs.mkdir('/etc/systemd/system')
    fs.link('/etc/systemd/system/initial-setup.service', '/dev/null')
    assert fs.exists('/etc/systemd/system/initial-setup.service')
    try:
        fs.debug('dump /missing ' + str(stage / 'missing'))
    except editor.Invalid:
        pass
    else:
        raise AssertionError('missing file must fail despite debugfs exit status')
    subprocess.run(['e2fsck', '-fn', str(root)], check=True, capture_output=True)
print('rootless ext4 smoke passed')
