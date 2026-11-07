import json
import importlib.machinery
import importlib.util
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
