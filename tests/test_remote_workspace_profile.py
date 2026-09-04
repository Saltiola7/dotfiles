import json
import os
import subprocess
import tomllib

import pytest
from pathlib import Path


ROOT = Path(__file__).parents[1]
DATA = {
    "machine_type": "remote-workspace",
    "name": "Test User",
    "email": "test@example.com",
    "atuin_sync_address": "https://api.atuin.sh",
}
REMOTE_TARGETS = {
    ".config/yazi/package.toml",
    ".config/yazi/theme.toml",
    "install-remote-workspace-yazi.sh",
    "install-yazi-flavor.sh",
}


def text(path):
    return (ROOT / path).read_text()


def managed(source, data):
    return set(
        subprocess.run(
            [
                "chezmoi",
                "-S",
                str(source),
                "--config",
                "/dev/null",
                "--config-format",
                "toml",
                "--override-data",
                json.dumps(data),
                "managed",
                "--include",
                "files,scripts",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )


def test_remote_workspace_is_explicit_and_yazi_only():
    config = text(".chezmoi.toml.tmpl")
    assert "macbook/mac-mini/lmsh/remote-workspace" in config
    assert managed(ROOT, DATA) == REMOTE_TARGETS
    tomllib.loads(text("private_dot_config/yazi/package.toml"))
    tomllib.loads(text("private_dot_config/yazi/theme.toml"))


def test_remote_workspace_installer_pins_x86_64_assets():
    installer = text("run_onchange_install-remote-workspace-yazi.sh.tmpl")
    assets = {
        "yazi-x86_64-unknown-linux-musl.zip": "a6702034790afcdbb546b73b288c9b184a751fa3f2f17f0ad4d26fc302fb8d45",
        "fd-v10.5.0-x86_64-unknown-linux-gnu.tar.gz": "a1259cd129636efbc3fef123525c1b49e88fe5088c012630983c310e52fdfa95",
        "fzf-0.74.3-linux_amd64.tar.gz": "3501a595e4b5c40a6b047340a0e8f805c46fd4e61ef95ef8a136ba8c61cf6f22",
        "7z2602-linux-x64.tar.xz": "41aaba7b1235304ab5aa0624530c67ae829496cd29e875925271efdccc28c03e",
    }
    for asset, digest in assets.items():
        assert asset in installer
        assert digest in installer
    for forbidden in ("sudo", "dnf", "atuin", "starship", "opencode", "podman"):
        assert forbidden not in installer.lower()


def test_existing_profiles_still_render():
    for machine_type in ("macbook", "mac-mini", "lmsh"):
        assert managed(ROOT, DATA | {"machine_type": machine_type})


def test_shared_rendered_targets_are_disjoint_when_source_is_provided():
    shared_source = os.environ.get("DOTFILES_AI_SOURCE")
    if not shared_source:
        pytest.skip("DOTFILES_AI_SOURCE is required for cross-source proof")
    shared = managed(
        Path(shared_source),
        {"dotfiles_ai": {"remote_user_environment": {"enabled": True}}},
    )
    assert managed(ROOT, DATA).isdisjoint(shared)
