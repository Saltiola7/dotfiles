import plistlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dot_local/bin/executable_mbp-borg-backup"
PLIST = ROOT / "private_Library/LaunchAgents/dev.dotfiles.mbp-borg-backup.plist.tmpl"
IGNORE = ROOT / ".chezmoiignore"


def test_script_gates_to_host_and_keeps_alive():
    text = SCRIPT.read_text()
    assert 'hostname -s' in text and "ts-mbp" in text
    assert "ServerAliveInterval=15" in text and "ServerAliveCountMax=4" in text
    assert "--keep-daily 7" in text and "--keep-weekly 4" in text
    assert "--keep-monthly 6" in text
    assert "--glob-archives 'ts-mbp-*'" in text  # golden image shares the repo; prune must not touch it
    assert "ssh://tis@mac-mini/Volumes/ext-2/Users/Shared/mbp-macos/borg" in text


def test_plist_renders_valid_schedule():
    rendered = re.sub(r"\{\{[^}]+\}\}", "/Users/tis", PLIST.read_text())
    data = plistlib.loads(rendered.encode())
    assert data["Label"] == "dev.dotfiles.mbp-borg-backup"
    assert data["StartCalendarInterval"] == {"Hour": 3, "Minute": 0}
    assert data["RunAtLoad"] is False
    assert data["ProgramArguments"] == ["/Users/tis/.local/bin/mbp-borg-backup"]


def test_ignore_gates_both_targets_to_ts_mbp():
    text = IGNORE.read_text()
    assert 'hasPrefix "ts-mbp" .chezmoi.hostname' in text
    assert "Library/LaunchAgents/dev.dotfiles.mbp-borg-backup.plist" in text
    assert ".local/bin/mbp-borg-backup" in text
