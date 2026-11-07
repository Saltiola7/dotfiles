import json
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
