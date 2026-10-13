"""Private share planning must fail before privilege or filesystem mutation."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "dot_local/bin/executable_pi-samba-setup"


def test_plan_is_read_only(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(["bash", str(SETUP), "--plan", "--home", str(home)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "tailscale0" in result.stdout
    assert "SELinux" in result.stdout
    assert list(home.iterdir()) == []


def test_symlink_share_refused(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (home / "Shared").symlink_to(outside, target_is_directory=True)
    result = subprocess.run(["bash", str(SETUP), "--plan", "--home", str(home)],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert list(outside.iterdir()) == []


def test_unknown_option_refused(tmp_path):
    result = subprocess.run(["bash", str(SETUP), "--allow-public"],
                            capture_output=True, text=True)
    assert result.returncode == 2
