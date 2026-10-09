import configparser
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).parents[1]
HELPER = ROOT / 'dot_local/bin/executable_omarchy-zen-profile'


def test_existing_profile_becomes_default_without_replacing_browser_data(tmp_path):
    home = tmp_path / 'home'
    root = home / '.zen'
    original = root / 'omarchy'
    original.mkdir(parents=True)
    settings = original / 'prefs.js'
    settings.write_text('personal-settings')
    alternative = root / 'new-default'
    alternative.mkdir()
    (alternative / 'places.sqlite').write_bytes(b'personal-bookmarks')
    registry = root / 'profiles.ini'
    registry.write_text('[General]\nVersion=2\n[Profile0]\nName=New\n'
                        'IsRelative=1\nPath=new-default\nDefault=1\n'
                        '[InstallABC]\nDefault=new-default\nLocked=1\n')
    (root / 'installs.ini').write_text('[ABC]\nDefault=new-default\nLocked=1\n')
    shim = tmp_path / 'bin'
    shim.mkdir()
    (shim / 'pgrep').write_text('#!/bin/sh\nexit 1\n')
    (shim / 'pgrep').chmod(0o755)
    env = {**os.environ, 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / '.config'),
           'PATH': f'{shim}:{os.environ["PATH"]}'}
    subprocess.run(['bash', str(HELPER)], env=env, check=True, capture_output=True)
    config = configparser.ConfigParser()
    config.read(registry)
    assert config['Profile1']['path'] == 'omarchy'
    assert config['Profile1']['default'] == '1'
    assert 'default' not in config['Profile0']
    assert config['InstallABC']['default'] == 'omarchy'
    assert settings.read_text() == 'personal-settings'
    assert (alternative / 'places.sqlite').read_bytes() == b'personal-bookmarks'
    backups = list((home / '.local/state/omarchy-zen').glob('*/0-profiles.ini'))
    assert len(backups) == 1
    assert 'Default=new-default' in backups[0].read_text()
    before = registry.read_bytes()
    subprocess.run(['bash', str(HELPER)], env=env, check=True, capture_output=True)
    assert registry.read_bytes() == before
    assert len(list((home / '.local/state/omarchy-zen').iterdir())) == 1


def test_running_browser_registry_is_not_modified(tmp_path):
    shim = tmp_path / 'bin'
    shim.mkdir()
    (shim / 'pgrep').write_text('#!/bin/sh\nexit 0\n')
    (shim / 'pgrep').chmod(0o755)
    subprocess.run(['bash', str(HELPER)], check=True, capture_output=True,
                   env={**os.environ, 'HOME': str(tmp_path),
                        'PATH': f'{shim}:{os.environ["PATH"]}'})
    assert not (tmp_path / '.zen').exists()
