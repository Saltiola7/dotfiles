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
    "work_email": "work@example.invalid",
    "personal_email": "personal@example.invalid",
    "atuin_sync_address": "https://api.atuin.sh",
}
REMOTE_TARGETS = {
    ".config/yazi/package.toml",
    ".config/yazi/theme.toml",
    "install-remote-workspace-yazi.sh",
    "install-yazi-flavor.sh",
    ".bashrc.d/40-remote-workspace.sh",
    ".local/bin/remote-workspace-git",
    ".local/bin/remote-workspace-tools",
    ".local/bin/remote-workspace-nvim",
    ".config/git/remote-workspace.inc",
    ".config/git/remote-workspace-work.inc",
    ".config/git/remote-workspace-personal.inc",
    ".config/git/remote-workspace-conflict.inc",
    ".config/remote-workspace/tools.json",
    ".config/remote-workspace/restore-nvim.lua",
    ".config/remote-workspace/starship.toml",
    "configure-remote-workspace-git.sh",
    "install-01-remote-workspace-tools.sh",
    "zz-remote-workspace-nvim.sh",
}
REMOTE_TARGETS |= {'.config/nvim/' + path for path in (
    '.luarc.json', '.neoconf.json', '.stylua.toml', 'README.md', 'init.lua', 'lazy-lock.json',
    'neovim.yml', 'selene.toml', 'lua/community.lua', 'lua/lazy_setup.lua', 'lua/polish.lua',
    'lua/plugins/astrocore.lua', 'lua/plugins/astrolsp.lua', 'lua/plugins/astroui.lua',
    'lua/plugins/mason.lua', 'lua/plugins/none-ls.lua', 'lua/plugins/remote-workspace.lua',
    'lua/plugins/treesitter.lua', 'lua/plugins/user.lua')}


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


def test_ubi_qualification_uses_an_exact_shared_revision_and_existing_smoke():
    workflow = text(".github/workflows/remote-workspace-ubi.yml")
    assert "container: registry.access.redhat.com/ubi10/ubi" in workflow
    assert "repository: Saltiola7/dotfiles-ai" in workflow
    assert "persist-credentials: false" in workflow
    assert "tests/remote_workspace_profile_smoke.sh" in workflow
    assert "DOTFILES_AI_SOURCE" in workflow
    assert "timeout-minutes:" in workflow
    # An immutable public source revision is required; final paired acceptance
    # additionally verifies that the selected RRW-002 revision has merged.
    import re
    assert re.search(r"ref: [0-9a-f]{40}\s", workflow)


def test_expanded_contract_keeps_private_inputs_and_source_ownership():
    contract = text('docs/specs/remote_workspace_profile/OWNER_EXPANSION.md')
    for required in ('work_email', 'personal_email', 'STARSHIP_CONFIG', '0.26.1',
                     '## Visual Evidence', '**Text Equivalent:**', 'markdown_inline'):
        assert required in contract
    for document in ('README.md', 'CHANGELOG.md'):
        assert 'RRW-007B' in text('docs/specs/remote_workspace_profile/' + document)
    assert '.gitconfig' not in REMOTE_TARGETS
    assert '.bashrc' not in REMOTE_TARGETS
    assert '.config/starship.toml' not in REMOTE_TARGETS
    workflow = text('.github/workflows/test.yml')
    assert workflow.count('"private_dot_config/nvim/**"') == 2
    assert 'gcc-c++' in text('.github/workflows/remote-workspace-ubi.yml')


def test_paired_fixture_keeps_bootstrap_source_and_config_under_home():
    smoke = text('tests/remote_workspace_profile_smoke.sh')
    assert 'git clone --no-hardlinks' in smoke
    assert 'shared_source="$HOME/.local/share/chezmoi-dotfiles-ai"' in smoke
    assert 'shared_config="$HOME/.config/dotfiles-ai/chezmoi.toml"' in smoke
    assert 'remote set-url origin https://github.com/Saltiola7/dotfiles-ai.git' in smoke
    workflow = text('.github/workflows/remote-workspace-ubi.yml')
    assert 'export DOTFILES_AI_SOURCE="$GITHUB_WORKSPACE/shared"' in workflow
