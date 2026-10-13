"""Headless server allowlist, portable shell and explicit package setup."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'.bashrc', '.bash_profile', '.common_profile', '.config/atuin/config.toml',
            '.config/starship.toml', '.config/homelab/targets.json', '.local/bin/homelab',
            '.config/fedora-server/dnf-packages.txt', '.local/bin/fedora-server-setup'}


def chezmoi(tmp_path, *args):
    home = tmp_path / 'home'; home.mkdir(exist_ok=True)
    return subprocess.run(['chezmoi', '--source', str(ROOT), '--destination', str(home),
        '--config', '/dev/null', '--config-format', 'toml', '--override-data',
        json.dumps({'machine_type':'fedora-server', 'name':'Test', 'email':'test@example.invalid',
                    'atuin_sync_address':'https://example.invalid'}),
        '--persistent-state', str(tmp_path/'state.db'), *args],text=True,capture_output=True)


def test_full_source_server_allowlist(tmp_path):
    r=chezmoi(tmp_path,'managed','--include','files,symlinks'); assert r.returncode==0,r.stderr
    assert set(r.stdout.splitlines()) == EXPECTED
    r=chezmoi(tmp_path,'managed','--include','scripts'); assert r.returncode==0,r.stderr
    assert not r.stdout.strip()


def test_portable_shell_silent_and_secrets_absent(tmp_path):
    r=chezmoi(tmp_path,'apply','--parent-dirs','--exclude','scripts'); assert r.returncode==0,r.stderr
    home=tmp_path/'home'
    text='\n'.join((home/p).read_text() for p in ['.bashrc','.bash_profile','.common_profile'])
    for forbidden in ['/opt/homebrew','Library/Group Containers','AWS_PROFILE','__cleanup_gcp_cache','oh-my-bash']:
        assert forbidden not in text
    r=subprocess.run(['bash','--noprofile','--norc','-c',f'. "{home}/.bash_profile"; printf ready'],
                     env={'HOME':str(home),'PATH':'/usr/bin:/bin'},text=True,capture_output=True)
    assert r.returncode==0 and r.stdout=='ready' and not r.stderr
    assert 'auto_sync = false' in (home/'.config/atuin/config.toml').read_text()


def test_package_plan_excludes_desktop_and_tmux(tmp_path):
    r=chezmoi(tmp_path,'apply','--parent-dirs','--exclude','scripts'); assert r.returncode==0,r.stderr
    home=tmp_path/'home'
    helper=home/'.local/bin/fedora-server-setup'
    r=subprocess.run(['bash',str(helper),'--plan'],env={'HOME':str(home),'PATH':'/usr/bin:/bin'},text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    assert all(x in r.stdout.splitlines() for x in ['chezmoi','git','uv','nodejs24','neovim','atuin'])
    assert not any(x in r.stdout for x in ['tmux','hyprland','libreoffice','obs-studio'])


def test_invalid_package_cannot_be_passed_to_dnf(tmp_path):
    manifest=tmp_path/'packages'; manifest.write_text('--nogpgcheck\n')
    r=subprocess.run(['bash',str(ROOT/'dot_local/bin/executable_fedora-server-setup'),
                      '--plan','--manifest',str(manifest)],text=True,capture_output=True)
    assert r.returncode==2 and 'Invalid package name' in r.stderr


def test_other_profiles_exclude_server_tools(tmp_path):
    for profile in ['mac-mini','lmsh','omarchy','fedora-workstation']:
        r=subprocess.run(['chezmoi','--source',str(ROOT),'--config','/dev/null',
            '--config-format','toml','--override-data',json.dumps({'machine_type':profile}), 'managed',
            '--include','files,symlinks'],text=True,capture_output=True)
        assert r.returncode==0,r.stderr
        assert 'fedora-server' not in r.stdout
