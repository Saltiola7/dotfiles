import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_borg_backup_targets_mini_with_keepalive_and_guarded_prune():
    script = (ROOT / "dot_local/bin/executable_mbp-omarchy-borg-backup").read_text()
    assert "tis@mac-mini" in script
    assert "ServerAliveInterval=15" in script and "ServerAliveCountMax=4" in script
    assert "--glob-archives" in script and "mbp-omarchy-*" in script
    assert "/home/tis" in script


def test_systemd_units_schedule_nightly_backup():
    service = (ROOT / "private_dot_config/systemd/user/mbp-omarchy-borg-backup.service").read_text()
    timer = (ROOT / "private_dot_config/systemd/user/mbp-omarchy-borg-backup.timer").read_text()
    assert "%h/.local/bin/mbp-omarchy-borg-backup" in service
    assert "OnCalendar=*-*-* 04:00:00" in timer
    assert "Persistent=true" in timer


def test_ignore_gates_mbp_omarchy_targets_to_the_laptop():
    ignore = (ROOT / ".chezmoiignore").read_text()
    assert 'hasPrefix "mbp-omarchy" .chezmoi.hostname' in ignore
    for target in (
        ".local/bin/mbp-omarchy-borg-backup",
        ".config/systemd/user/mbp-omarchy-borg-backup.service",
        ".config/systemd/user/mbp-omarchy-borg-backup.timer",
    ):
        assert target in ignore


def test_asahi_hardware_script_guards_and_applies_idempotently():
    script = (ROOT / "run_onchange_after_mbp-asahi-hardware.sh.tmpl").read_text()
    assert 'hasPrefix "mbp-omarchy" .chezmoi.hostname' in script
    assert "[[ -t 0 ]]" in script  # sudo needs a terminal; stay silent otherwise
    assert "90-mbp-backlight.rules" in script
    assert "90-kbd-backlight-off.rules" in script
    assert "usermod -aG video" in script
    assert "tiny-dfr" in script
