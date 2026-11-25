"""Exercise the restore Lua in pinned Neovim with offline plugin/parser seams."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REQUIRED = ('bash', 'python', 'lua', 'vim', 'vimdoc', 'json', 'yaml', 'toml', 'markdown', 'sql')
EXPANDED = (*REQUIRED, 'markdown_inline')
STAGES = ('owner-init', 'plugin-restore', 'plugin-verify', 'parser-build', 'parser-verify')
PROOF = 'remote owner AstroNvim ten parsers verified'
FAILURE = 'remote owner AstroNvim restore/parser verification failed'
CASES = {
    'plugin-build': ('plugin-verify', 'locked plugin restore/build failed'),
    'parser-install': ('parser-build', 'parser installation failed'),
    'success': ('parser-verify', None),
}
HARNESS = '''\
local root = vim.env.REMOTE_WORKSPACE_LAZY_ROOT
local plugins = {}
local sha = { ["lazy.nvim"] = string.rep("a", 40), ["nvim-treesitter"] = string.rep("b", 40) }
for name in pairs(sha) do plugins[name] = { dir = root .. "/" .. name } end
local lock_manager = { update = function() error("incremental update would drop the late import") end }
package.preload["lazy.manage.lock"] = function() return lock_manager end
package.preload["lazy"] = function() return {
  restore = function(opts)
    assert(opts.wait and vim.opt.loadplugins:get())
    assert(lock_manager._loaded and lock_manager.lock["nvim-treesitter"].commit == sha["nvim-treesitter"])
  end,
  load = function(opts) assert(vim.deep_equal(opts.plugins, {"nvim-treesitter"})) end,
} end
package.preload["lazy.core.config"] = function() return { plugins = plugins } end
package.preload["lazy.core.plugin"] = function() return { has_errors = function(plugin)
  return vim.env.CONTRACT_CASE == "plugin-build" and plugin == plugins["nvim-treesitter"]
end } end
vim.system = function(args)
  local name = vim.fn.fnamemodify(args[3], ":t")
  assert(vim.deep_equal(args, {"git", "-C", plugins[name].dir, "rev-parse", "HEAD"}))
  return { wait = function(_, ms) assert(ms == 5000); return {code = 0, stdout = sha[name]} end }
end
local required = vim.json.decode(vim.env.CONTRACT_REQUIRED)
package.preload["nvim-treesitter"] = function() return {
  install = function(langs, options)
    assert(vim.deep_equal(langs, required) and options.max_jobs == 2)
    return { wait = function(_, ms) assert(ms == 300000); return vim.env.CONTRACT_CASE ~= "parser-install" end }
  end,
} end
package.preload["nvim-treesitter.config"] = function() return { norm_languages = function(langs, options)
  assert(vim.deep_equal(langs, required) and options.unsupported)
  table.insert(langs, "markdown_inline")
  return langs
end } end
local pending = {}
vim.treesitter.language.add = function(name, opts)
  local lang = opts.symbol_name
  assert(name == "remote_workspace_verify_" .. lang and not pending[name])
  assert(opts.path == vim.fn.stdpath("data") .. "/site/parser/" .. lang .. ".so")
  pending[name] = lang
  return true
end
vim.treesitter.get_string_parser = function(source, alias)
  assert(source == "")
  return { parse = function()
    assert(vim.fn.writefile({assert(pending[alias])}, vim.env.CONTRACT_TRACE, "a") == 0)
    pending[alias] = nil
    return {true}
  end }
end
dofile(vim.env.CONTRACT_RESTORE)
'''


def check_result(case: str, returncode: int, output: str, parsed: list[str]) -> None:
    stage, reason = CASES[case]
    markers = ['remote editor stage ' + label for label in STAGES[:STAGES.index(stage) + 1]]
    markers.extend((FAILURE, 'remote editor invariant ' + reason) if reason else (PROOF,))
    observed = [line for line in output.splitlines() if line.startswith(('remote editor ', 'remote owner '))]
    if (returncode != (1 if reason else 0) or observed != markers
            or sorted(parsed) != ([] if reason else sorted(EXPANDED))):
        raise AssertionError(f'{case}: expected exit, stage/invariant or completion/parse witnesses not observed')


def qualify(binary: str, restore: Path) -> None:
    for case in CASES:
        with tempfile.TemporaryDirectory(prefix='remote-editor-contract-') as scratch:
            home = Path(scratch)
            xdg = home / '.local/state/remote-workspace/editor-attempts/attempt-0001/candidate'
            xdg.mkdir(parents=True, mode=0o700)
            (xdg / 'nvim').mkdir(mode=0o700)
            root = xdg / 'nvim/lazy'
            root.mkdir(mode=0o700)
            runtime = home / 'runtime'
            runtime.mkdir(mode=0o700)
            config = home / '.config/nvim'
            config.mkdir(parents=True)
            pins = {'lazy.nvim': {'branch': 'main', 'commit': 'a' * 40},
                    'nvim-treesitter': {'branch': 'main', 'commit': 'b' * 40}}
            for name in pins:
                (root / name).mkdir()
            (config / 'lazy-lock.json').write_text(json.dumps(pins))
            # The pinned manager must not prune the late import's entry in this round.
            (config / 'init.lua').write_text('assert(_G.remote_workspace_verifying)\n'
                                            'require("lazy.manage.lock").update()\n')
            site = xdg / 'nvim/site/parser'
            site.mkdir(parents=True)
            for language in EXPANDED:
                (site / (language + '.so')).write_bytes(b'synthetic parser seam')
            harness = home / 'contract.lua'
            harness.write_text(HARNESS)
            trace = home / 'parsed'
            environment = dict(PATH=os.defpath, HOME=str(home), XDG_CONFIG_HOME=str(config.parent),
                               XDG_DATA_HOME=str(xdg), XDG_STATE_HOME=str(home / 'state'),
                               XDG_CACHE_HOME=str(home / 'cache'), NVIM_APPNAME='nvim',
                               TMPDIR=str(runtime), XDG_RUNTIME_DIR=str(runtime),
                               REMOTE_WORKSPACE_LAZY_ROOT=str(root), LAZY=str(root / 'lazy.nvim'),
                               CONTRACT_RESTORE=str(restore.resolve()), CONTRACT_CASE=case,
                               CONTRACT_REQUIRED=json.dumps(REQUIRED), CONTRACT_TRACE=str(trace))
            result = subprocess.run([binary, '--headless', '-i', 'NONE', '-u', 'NONE', '-l', str(harness)],
                                    cwd=home, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, timeout=30)
            check_result(case, result.returncode, result.stdout, trace.read_text().splitlines() if trace.exists() else [])
    print('offline Lua contract verified: plugin-build rejection, parser-install rejection and complete parse proof')


if __name__ == '__main__':
    qualify(sys.argv[1], Path(sys.argv[2]))
