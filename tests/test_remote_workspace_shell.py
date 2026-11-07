import os
from pathlib import Path
import subprocess
import tomllib

ROOT = Path(__file__).parents[1]


def test_owner_snippet_exports_prompt_and_portable_aliases_without_credentials(tmp_path):
    snippet = ROOT / 'dot_bashrc.d/40-remote-workspace.sh'
    subprocess.run(['bash', '-n', str(snippet)], check=True)
    result = subprocess.run(['bash', '--noprofile', '--norc', '-c',
        'source "$1"; alias vim; alias python; alias py; printf "%s\\n" "$STARSHIP_CONFIG"',
        'fixture', str(snippet)], env={'HOME': str(tmp_path), 'PATH': os.defpath},
        text=True, capture_output=True, check=True, timeout=10)
    assert "alias vim='nvim'" in result.stdout
    assert "alias python='python3'" in result.stdout
    assert "alias py='python3'" in result.stdout
    assert str(tmp_path / '.config/remote-workspace/starship.toml') in result.stdout
    text = snippet.read_text()
    for forbidden in ('awslogin', 'Screaming', 'op read', 'starship init', 'direnv allow', 'mise activate'):
        assert forbidden not in text


def test_separate_prompt_is_owners_config_not_foundation_takeover():
    actual = tomllib.loads((ROOT / 'private_dot_config/remote-workspace/starship.toml').read_text())
    owner = tomllib.loads((ROOT / 'private_dot_config/starship.toml').read_text())
    assert actual == owner


def test_shell_and_headless_tools_are_explicit_remote_targets():
    text = (ROOT / '.chezmoi.toml.tmpl').read_text()
    assert 'promptStringOnce . "work_email"' in text
    assert 'promptStringOnce . "personal_email"' in text
    smoke = (ROOT / 'tests/remote_workspace_profile_smoke.sh').read_text()
    subprocess.run(['bash', '-n'], input=smoke, text=True, check=True)
    for required in ('sha256sum -c "$tmp/shared-managed-hashes"', 'credential_roundtrip',
                     'editor-ready.json', 'installed-tools.json', 'gcc-c++'):
        assert required in smoke
