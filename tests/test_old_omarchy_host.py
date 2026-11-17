import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "dot_local/bin/executable_old-omarchy-setup"


def chezmoi(host, *args, text=None):
    data = {
        "machine_type": "omarchy",
        "name": "Test User",
        "email": "test@example.com",
        "atuin_sync_address": "https://api.atuin.sh",
        "chezmoi": {
            "os": "linux", "arch": "amd64", "hostname": host,
            "homeDir": "/home/test", "username": "test",
        },
    }
    return subprocess.run(
        ["chezmoi", "-S", str(ROOT), "--config", "/dev/null",
         "--config-format", "toml", "--override-data", json.dumps(data), *args],
        input=text, capture_output=True, text=True, check=True,
    ).stdout


def test_host_files_are_actually_managed_and_isolated():
    targets = {
        ".config/dotfiles-ai/chezmoi.toml",
        ".config/old-omarchy/packages.txt",
        ".config/old-omarchy/authorized_keys",
        ".local/bin/old-omarchy-setup",
        "always_configure-old-omarchy.sh",
    }
    managed = set(chezmoi("old-omarchy", "managed", "--include", "files,scripts").splitlines())
    assert targets <= managed
    for other in ("omarchy", "mbp-omarchy"):
        managed = set(chezmoi(other, "managed", "--include", "files,scripts").splitlines())
        assert not (targets & managed)


def test_ai_config_preserves_existing_owner_and_private_state():
    source = ROOT / "private_dot_config/dotfiles-ai/chezmoi.toml.tmpl"
    rendered = chezmoi("old-omarchy", "execute-template", text=source.read_text())
    assert 'executable = "/usr/bin/herdr"' in rendered
    assert 'root = "/var/lib/dotfiles-ai/test"' in rendered
    assert 'sourceDir = "/home/test/Projects/dotfiles-ai"' in rendered


def test_shell_syntax_and_safe_boot_storage_contract():
    subprocess.run(["bash", "-n", str(HELPER)], check=True)
    script = HELPER.read_text()
    assert '$(hostname -s) == old-omarchy' in script
    assert "/etc/default/limine" in script
    assert "video=HDMI-A-3:1920x1080@60e" in script
    assert "sudo limine-update" in script
    assert "0005001a-5404-a700-ffff-ffffffffffff" in script
    for forbidden in ("mkfs", "wipefs", "sgdisk", "/dev/sda", "pkill", "sudo reboot"):
        assert forbidden not in script


def test_authorized_key_merge_preserves_local_keys_and_is_idempotent(tmp_path):
    source = HELPER.read_text().split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    ssh = tmp_path / ".ssh"
    ssh.mkdir()
    authorized = ssh / "authorized_keys"
    authorized.write_text("ssh-ed25519 LOCAL retained\n")
    manifest = ROOT / "private_dot_config/old-omarchy/authorized_keys"
    env = {**os.environ, "HOME": str(tmp_path)}
    for _ in range(2):
        subprocess.run([sys.executable, "-c", source, str(manifest)], env=env, check=True)
    lines = authorized.read_text().splitlines()
    assert lines[0] == "ssh-ed25519 LOCAL retained"
    assert len(lines) == 5
    assert authorized.stat().st_mode & 0o777 == 0o600


def test_storage_mounts_are_declared_removable_safe_and_ordered_before_ai_apply():
    script = HELPER.read_text()
    assert "d7c7ee45-ee7f-4e73-8075-958b1f488b72" in script
    assert "fe788a68-5558-452a-ab52-6ac6b71bc55b" in script
    for target in ("/srv/storage", "/srv/storage2"):
        assert f"{target} ext4 defaults,nofail,x-systemd.device-timeout=10s" in script
        assert "mountpoint -q" in script
    assert 'grep -q "$uuid" /etc/fstab' in script
    assert script.index("declare -A storage") < script.index("dotfiles-ai/chezmoi.toml")


def test_reconcile_script_is_a_noop_on_other_hosts():
    source = ROOT / "run_always_configure-old-omarchy.sh.tmpl"
    for host in ("omarchy", "mbp-omarchy"):
        rendered = chezmoi(host, "execute-template", text=source.read_text())
        assert rendered.strip() == "#!/usr/bin/env bash\nexit 0"
