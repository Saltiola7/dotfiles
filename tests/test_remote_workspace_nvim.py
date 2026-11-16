import json
import importlib.machinery
import importlib.util
import os
import subprocess
import pytest
from pathlib import Path

ROOT = Path(__file__).parents[1]
PARSERS = {'bash', 'python', 'lua', 'vim', 'vimdoc', 'json', 'yaml', 'toml', 'markdown', 'sql'}


def test_headless_restore_uses_locked_plugins_and_verifies_ten_native_parsers():
    script = (ROOT / 'private_dot_config/remote-workspace/restore-nvim.lua').read_text()
    for parser in PARSERS:
        assert '"' + parser + '"' in script
    for text in ('restore', 'wait = true', ':wait(300000)', 'vim.treesitter.language.add',
                 'git', 'rev-parse', 'HEAD', 'cquit 1'):
        assert text in script
    assert 'Lazy update' not in script
    assert 'remote owner AstroNvim ten parsers verified' in script
    assert script.index('vim.opt.loadplugins = true') < script.index('dofile(config')
    assert 'assert(require("nvim-treesitter").install' in script
    assert 'norm_languages' in script
    assert 'remote_workspace_verify_' in script and 'symbol_name = lang' in script
    assert 'has_errors(plugin)' in script
    assert script.index('lock_manager._loaded = true') < script.index('dofile(config')
    assert 'lock_manager.lock = vim.deepcopy(lock)' in script
    assert 'lock_manager.update = function() end' in script


def test_editor_setup_keeps_lock_and_uses_overlay_private_cli():
    script = (ROOT / 'dot_local/bin/executable_remote-workspace-nvim').read_text()
    assert '.local/libexec/remote-workspace' in script
    assert 'lazy-lock.json' in script
    assert 'before != lock.read_bytes()' in script
    assert "'-u', 'NONE', '-l'" in script
    assert "'-i', 'NONE'" in script
    assert "'symbolic-ref', 'refs/remotes/origin/HEAD'" in script
    lock = json.loads((ROOT / 'private_dot_config/nvim/lazy-lock.json').read_text())
    assert lock['nvim-treesitter']['commit'] == '4916d6592ede8c07973490d9322f187e07dfefac'


def test_remote_plugin_override_keeps_mason_on_demand():
    script = (ROOT / 'private_dot_config/nvim/lua/plugins/remote-workspace.lua').read_text()
    assert 'opts.run_on_start = false' in script
    assert 'opts.ensure_installed = {}' in script
    assert 'opts.automatic_installation = false' in script


def test_editor_failure_diagnostics_only_admit_literal_labels():
    loader = importlib.machinery.SourceFileLoader('remote_editor', str(ROOT / 'dot_local/bin/executable_remote-workspace-nvim'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    error = module.EditorSetupFailure(1, 'private-path/token\nremote editor stage plugin-verify\n'
        'remote editor stage private-secret\nremote editor invariant locked plugin absent\n')
    assert str(error) == 'editor exit 1; stage plugin-verify; locked plugin absent'
    assert 'private' not in str(module.EditorSetupFailure(1, 'private-path/token'))
    for reason in ('installed lazy identity differs from lock', 'unsafe plugin link',
                   'plugin contains local work; refusing restore', 'editor compiler prerequisite missing'):
        assert module.preparation_reason(ValueError(reason)) == reason
    for error in (ValueError('private-path/token'), OSError('private-path/token'),
                  KeyError('private-path/token'), RuntimeError('unsafe plugin link')):
        assert module.preparation_reason(error) == 'unclassified preparation failure'
    entries = {'fixture-b': {}, 'fixture-a': {}}
    assert module.dirty_summary('fixture-b', entries, ' M private/token\n?? private/untracked') == (
        'remote editor dirty lock-index 2; tracked 1; untracked 1')
    assert module.dirty_summary('private-plugin', entries, '?? secret') == (
        'remote editor dirty lock-index 0; tracked 0; untracked 1')
    assert 'private' not in module.dirty_summary('private-plugin', entries, ' M private/token')


def editor_module():
    loader = importlib.machinery.SourceFileLoader('receipt_editor', str(ROOT / 'dot_local/bin/executable_remote-workspace-nvim'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_generated_tags_require_new_install_then_exact_receipt(tmp_path, monkeypatch):
    core = editor_module()
    plugin = tmp_path / 'plugin'
    (plugin / 'doc').mkdir(parents=True)
    tags = plugin / 'doc/tags'
    tags.write_text('generated help tags\n')
    revision = 'a' * 40
    monkeypatch.setattr(core, 'run', lambda *args, **kw: revision if 'rev-parse' in args else '?? doc/tags')
    with pytest.raises(ValueError):
        core.plugin_receipt(plugin, revision, None, newly_installed=False, env={})
    receipt = core.plugin_receipt(plugin, revision, None, newly_installed=True, env={})
    assert receipt['commit'] == revision
    assert core.plugin_receipt(plugin, revision, receipt, newly_installed=False, env={}) == receipt
    tags.write_text('owner edited tags\n')
    with pytest.raises(ValueError):
        core.plugin_receipt(plugin, revision, receipt, newly_installed=False, env={})
    assert tags.read_text() == 'owner edited tags\n'


@pytest.mark.parametrize('status', [' M doc/help.txt', '?? owner-note', '?? doc/tags\n?? owner-note'])
def test_generated_receipt_never_admits_other_changes(tmp_path, monkeypatch, status):
    core = editor_module()
    monkeypatch.setattr(core, 'run', lambda *args, **kw: 'a' * 40 if 'rev-parse' in args else status)
    with pytest.raises(ValueError):
        core.plugin_receipt(tmp_path, 'a' * 40, None, newly_installed=True, env={})


def test_receipt_requires_private_single_link_lock_binding(tmp_path):
    core = editor_module()
    target = tmp_path / 'receipt.json'
    target.write_text(json.dumps({'lock_sha256': 'a' * 64, 'generated_tags': {}}))
    target.chmod(0o600)
    assert core.read_receipts(target, 'a' * 64) == {}
    with pytest.raises(ValueError):
        core.read_receipts(target, 'b' * 64)
    os.link(target, tmp_path / 'retained-link')
    with pytest.raises(ValueError):
        core.read_receipts(target, 'a' * 64)


def test_native_git_generated_tags_and_owner_changes(tmp_path):
    core = editor_module()
    env = {**os.environ, 'HOME': str(tmp_path), 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_COUNT': '1',
           'GIT_CONFIG_KEY_0': 'commit.gpgsign', 'GIT_CONFIG_VALUE_0': 'false'}
    plugin = tmp_path / 'plugin'
    plugin.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(plugin), *args], env=env, text=True).strip()
    git('init', '-q')
    (plugin / 'doc').mkdir()
    helpfile = plugin / 'doc/fixture.txt'
    helpfile.write_text('*fixture* fixture help\n')
    git('add', '.')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
    revision = git('rev-parse', 'HEAD')
    tags = plugin / 'doc/tags'
    tags.write_text('fixture\tfixture.txt\t/*fixture*\n')
    receipt = core.plugin_receipt(plugin, revision, None, newly_installed=True, env=env)
    assert core.plugin_receipt(plugin, revision, receipt, newly_installed=False, env=env) == receipt
    helpfile.write_text('owner change\n')
    with pytest.raises(ValueError):
        core.plugin_receipt(plugin, revision, receipt, newly_installed=False, env=env)
    assert helpfile.read_text() == 'owner change\n'
    assert tags.read_text() == 'fixture\tfixture.txt\t/*fixture*\n'


def test_receipt_contract_documents_narrow_generated_output():
    text = (ROOT / 'docs/specs/remote_workspace_profile/OWNER_EXPANSION.md').read_text()
    assert '`doc/tags`' in text and 'preexisting dirty plugins still refuse' in text


def test_missing_receipted_plugin_refuses_before_restore(tmp_path, monkeypatch):
    core = editor_module()
    plugin = tmp_path / 'plugin'
    (plugin / 'doc').mkdir(parents=True)
    (plugin / 'doc/tags').write_text('generated tags\n')
    revision = 'a' * 40
    monkeypatch.setattr(core, 'run', lambda *args, **kw: revision if 'rev-parse' in args else '?? doc/tags')
    receipt = core.plugin_receipt(plugin, revision, None, newly_installed=True, env={})
    entries = {'plugin': {'commit': revision}}
    core.validate_existing_receipts(tmp_path, entries, {'plugin': receipt}, env={})
    plugin.rename(tmp_path / 'retained-plugin')
    with pytest.raises(ValueError):
        core.validate_existing_receipts(tmp_path, entries, {'plugin': receipt}, env={})
    assert not plugin.exists()
    assert (tmp_path / 'retained-plugin/doc/tags').read_text() == 'generated tags\n'
