"""Check shared SSH configuration without contacting a host."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_operator_fragments_resolve_outside_mac_mini(tmp_path):
    if not shutil.which("chezmoi") or not shutil.which("ssh"):
        pytest.skip("requires chezmoi and OpenSSH")
    config = tmp_path / "empty.toml"
    config.touch()
    source = tmp_path / "source"
    source.mkdir()
    fragments = tmp_path / ".ssh/config.d"
    fragments.mkdir(parents=True)
    (fragments / "test").write_text(
        "Host fixture-iap\n    HostName fixture.invalid\n    ProxyCommand /bin/false\n"
    )
    template = ROOT / "private_dot_ssh/private_config.tmpl"
    command = [
        "chezmoi", "-c", str(config), "-S", str(source), "-D", str(tmp_path),
        "execute-template",
    ]

    def render():
        return subprocess.run(
            command, input=template.read_text(), text=True, check=True,
            capture_output=True, env={**os.environ, "HOME": str(tmp_path)},
        ).stdout

    rendered = render()
    assert "\nMatch all\nInclude config.d/*\n" in rendered
    # OpenSSH resolves relative includes against the real user's home.
    isolated = tmp_path / "ssh.conf"
    isolated.write_text(rendered.replace("Include config.d/*", f'Include "{fragments}/*"'))

    def effective(alias):
        return subprocess.run(
            ["ssh", "-G", "-F", str(isolated), alias],
            text=True, check=True, capture_output=True,
        ).stdout.splitlines()

    assert "hostname fixture.invalid" in effective("fixture-iap")
    assert "proxycommand /bin/false" in effective("fixture-iap")
    assert "proxycommand /bin/false" not in effective("mac-mini")
    assert "proxycommand /bin/false" not in effective("unrelated.invalid")
    fragments.rename(tmp_path / "parked")
    assert "\nInclude config.d/*\n" not in render()
