import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from tests.remote_workspace_nvim_contract import EXPANDED, check_result
from tests.remote_workspace_ubi_diagnose import summary


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
    for path in ("tests/remote_workspace_profile_smoke.sh", "tests/remote_workspace_ubi_compiler.sh",
                 "tests/remote_workspace_ubi_diagnose.py",
                 "tests/remote_workspace_nvim_contract.py"):
        assert f'      - "{path}"' in workflow
    assert "DOTFILES_AI_SOURCE" in workflow
    assert "timeout-minutes:" in workflow
    # Exact merged foundation at RRW-007I registration, including the bootstrap
    # bytes the paired native fixture actually executes.
    foundation = 'd9fec2457b0c1f65e644f921ae7a4e97b21b3c59'
    shared_checkout = workflow.split("repository: Saltiola7/dotfiles-ai\n", 1)[1].split("\n      -", 1)[0]
    assert re.findall(r'^\s*ref:\s*(\S+)\s*$', shared_checkout, re.MULTILINE) == [foundation]
    smoke = text('tests/remote_workspace_profile_smoke.sh')
    assert foundation in smoke
    assert '89da48232d9352a2eee2dd953fa29d42b7e358a4c2490a59e45cee899d4af666' in smoke
    assert 'qualification candidate' not in workflow


@pytest.mark.skipif(sys.platform != 'linux' or not Path('/usr/bin/gcc').is_file() or not shutil.which('readelf'),
                    reason='Linux compiler fixture check requires gcc and readelf')
def test_ubi_compiler_witness_distinguishes_fault_and_passes_through_real_build(tmp_path):
    """Test the CI observer, not Neovim or a native Treesitter installation."""
    fixture = tmp_path / 'fixture'
    fixture.mkdir()
    driver = fixture / 'gcc'
    driver.write_text(text('tests/remote_workspace_ubi_compiler.sh'))
    driver.chmod(0o700)
    header = tmp_path / 'tree_sitter/parser.h'
    header.parent.mkdir()
    header.touch()
    parser = tmp_path / 'parser.c'
    c_source = '#include "tree_sitter/parser.h"\nint tree_sitter_LANG(void){return 1;}\n'
    parser.write_text(c_source.replace('LANG', 'sql'))
    home = tmp_path / 'home'
    attempts = home / '.local/state/remote-workspace/editor-attempts'
    env = {'HOME': str(home), 'PATH': '/usr/bin:/bin'}

    def run(*args):
        return subprocess.run([str(driver), *args], cwd=tmp_path, env=env, capture_output=True).returncode

    def begin(number):
        gen = attempts / f'attempt-{number:04d}'
        (gen / 'candidate').mkdir(parents=True)
        (gen / 'record.json').write_text(json.dumps({'state': 'running'}))
        env['XDG_DATA_HOME'] = str(gen / 'candidate')

    cause = fixture / 'reject.h'
    cause.write_text('#error RRW_UBI_CONTROLLED_PARSER_FAULT\n')
    compile_args = ('-fPIC', '-c', 'parser.c', '-o', 'parser.o')
    assert run(*compile_args) == 0  # No running private attempt.
    assert (fixture / 'outside').is_file()
    begin(1)
    parser.write_text(c_source.replace('LANG', 'other'))
    assert run(*compile_args) == 0
    parser.write_text(c_source.replace('LANG', 'sql'))
    assert run(*compile_args, '--invalid-compiler-option') != 0
    assert not (fixture / 'rejected').exists()
    assert run(*compile_args) != 0
    assert (fixture / 'rejected').read_text().splitlines() == ['compiler rejected SQL parser.c']

    cause.unlink()
    begin(2)
    assert run(*compile_args) == 0
    assert run('-shared', 'parser.o', '-o', 'grammar.so') == 0
    digest = hashlib.sha256((tmp_path / 'grammar.so').read_bytes()).hexdigest()
    assert (fixture / 'compiled').read_text().splitlines() == ['sql']
    assert (fixture / 'linked').read_text().splitlines() == [f'sql {digest}']


def test_offline_lua_contract_rejects_wrong_failure_or_incomplete_success():
    # This tests the harness's decision, not Lua execution or native parsers.
    plugin = ['remote editor stage owner-init', 'remote editor stage plugin-restore', 'remote editor stage plugin-verify']
    parser = [*plugin, 'remote editor stage parser-build']
    failure = 'remote owner AstroNvim restore/parser verification failed'
    build_error = '\n'.join([*plugin, failure, 'remote editor invariant locked plugin restore/build failed'])
    parser_error = '\n'.join([*parser, failure, 'remote editor invariant parser installation failed'])
    check_result('plugin-build', 1, build_error, [])
    check_result('parser-install', 1, parser_error, [])
    with pytest.raises(AssertionError):
        check_result('parser-install', 1, build_error, [])
    with pytest.raises(AssertionError):
        check_result('plugin-build', 1, '', [])
    stages = '\n'.join([*parser, 'remote editor stage parser-verify'])
    success = stages + '\nremote owner AstroNvim ten parsers verified\n'
    check_result('success', 0, success, list(EXPANDED))
    with pytest.raises(AssertionError):
        check_result('success', 0, stages, list(EXPANDED))
    with pytest.raises(AssertionError):
        check_result('success', 0, success, [lang for lang in EXPANDED if lang != 'markdown_inline'])


@pytest.mark.skipif(sys.platform != 'linux', reason='UBI state and ownership preflight')
def test_ubi_first_apply_distinguishes_state_guard_before_any_native_command(tmp_path):
    # Exercise real chezmoi state creation and the real helper entry/lock gate.
    # The lock input is deliberately absent: neither execution can invoke Git.
    chezmoi = shutil.which('chezmoi')
    assert chezmoi is not None
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'dot_probe').write_bytes(b'force the normal persistent-state write')
    (src / 'run_after_zz-remote-workspace-nvim.sh').write_text(
        '#!/bin/sh\nexec "$FIXTURE_PYTHON" "$FIXTURE_EDITOR"\n')
    for name, mode, cause, marker in (
            ('permissive', 0o755, 'editor recovery requires operator review', 'unreported'),
            ('private', 0o700, 'unsafe editor lock', 'inputs')):
        home = tmp_path / name
        state = home / '.local/state/remote-workspace'
        state.parent.mkdir(parents=True)
        if name == 'private':
            state.mkdir(mode=mode)
        env = dict(HOME=str(home), PATH=os.defpath, XDG_CONFIG_HOME=str(home / '.config'),
                   FIXTURE_PYTHON=sys.executable, FIXTURE_EDITOR=str(ROOT / 'dot_local/bin/executable_remote-workspace-nvim'))
        result = subprocess.run([chezmoi, '--color=false', '-S', str(src), '-D', str(home), '--config', '/dev/null',
                                 '--config-format', 'toml', '--persistent-state', str(state / 'chezmoi.boltdb'), 'apply'],
                                cwd=home, env=env, umask=0o022, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=10)
        assert result.returncode != 0 and (state.stat().st_mode & 0o777) == mode
        log = tmp_path / 'private-log'
        log.write_bytes(result.stdout)
        observed = summary(log, home, tmp_path / 'compiler')
        assert f'hook=editor; last-marker={marker}; stage=preflight; cause={cause};' in observed
        assert ('setup-lock' in observed.partition('missing=')[2]) == (name == 'permissive')
        assert not (state / 'editor-attempts').exists() and not (state / 'editor-ready.json').exists()


def test_ubi_diagnostic_reports_fixed_labels_only_from_bounded_log_tail(tmp_path):
    log = tmp_path / 'log'
    secret = b'ghp_TEST_ONLY/private-path'
    log.write_bytes(b'remote editor preparation headless-restore\n' + b'x' * 90000 + b'\n' +
                    b'\x1b[31mchezmoi: install-01-remote-workspace-tools.sh: exit status 1\x1b[0m\n' +
                    b'remote overlay tool installation failed; prior generations retained\n' +
                    b'::error::' + secret + b'\nchezmoi: ' + secret + b': exit status 1\n')
    home = tmp_path / 'empty'
    notice = summary(log, home, tmp_path)
    assert 'hook=tools; last-marker=unreported; stage=unreported; cause=tool installation failed;' in notice
    assert 'tree-sitter' in notice.partition('missing=')[2]
    assert len(notice) < 512 and secret.decode() not in notice and '::' not in notice
    # A genuine native failure is distinguishable from preflight, but neither
    # the diagnostic nor a color-stripped log is the compiler rejection witness.
    prefix = b'remote owner editor setup failed: editor exit 1; stage parser-build; '
    log.write_bytes(b'\x1b[31m' + prefix + b'parser installation failed\x1b[0m\n')
    assert 'stage=parser-build; cause=parser installation failed;' in summary(log, home, tmp_path)
    log.write_bytes(prefix + b'parser installation failed ' + secret + b'\n')
    notice = summary(log, home, tmp_path)
    assert 'stage=unreported; cause=unreported;' in notice and secret.decode() not in notice


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
