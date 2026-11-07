"""Run failure-path Lua contracts in the installed pinned Neovim, offline."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def qualify(binary: str, restore: Path) -> None:
    for build_error, parser_ok, expected in ((True, True, False), (False, False, False), (False, True, True)):
        with tempfile.TemporaryDirectory(prefix='remote-editor-contract-') as scratch:
            home = Path(scratch)
            site = home / '.local/share/nvim/site/parser'
            site.mkdir(parents=True)
            (site / 'lua.so').write_bytes(b'controlled parser seam; not native parser evidence')
            harness = home / 'contract.lua'
            harness.write_text('''
local sha = string.rep("a", 40)
vim.env.LAZY = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
vim.fn.readfile = function() return { '{"fixture":{"branch":"main","commit":"' .. sha .. '"},"late-plugin":{"branch":"main","commit":"' .. sha .. '"}}' } end
local lock_manager = { lock = {}, _loaded = false, update = function() error("incremental update would drop late lock entry") end }
package.preload["lazy.manage.lock"] = function() return lock_manager end
package.preload["lazy"] = function() return {
  restore = function(opts)
    assert(opts.wait and vim.opt.loadplugins:get())
    assert(lock_manager._loaded and lock_manager.lock["late-plugin"].commit == sha)
  end,
  load = function() end,
} end
package.preload["lazy.core.config"] = function() return { plugins = { fixture = { dir = "/fixture" }, ["late-plugin"] = {dir = "/late-fixture"} } } end
package.preload["lazy.core.plugin"] = function() return { has_errors = function() return BUILD_ERROR end } end
vim.system = function() return { wait = function() return { code = 0, stdout = sha .. "\\n" } end } end
package.preload["nvim-treesitter"] = function() return {
  install = function() return { wait = function() return PARSER_OK end } end,
} end
package.preload["nvim-treesitter.config"] = function() return { norm_languages = function() return {"lua"} end } end
vim.treesitter.language.add = function(name, opts)
  assert(name == "remote_workspace_verify_lua" and opts.symbol_name == "lua")
  return true
end
local dofile_real = dofile
dofile = function(path)
  if path:match("/init.lua$") then
    lock_manager.update() -- Simulated incremental install round must be read-only.
    assert(lock_manager.lock["late-plugin"].commit == sha)
    return
  end
  return dofile_real(path)
end
dofile_real(RESTORE)
'''.replace('BUILD_ERROR', str(build_error).lower()).replace('PARSER_OK', str(parser_ok).lower())
                .replace('RESTORE', json.dumps(str(restore.resolve()))))
            environment = {key: value for key, value in os.environ.items() if not key.startswith(('NVIM', 'LAZY'))}
            environment.update(HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                XDG_DATA_HOME=str(home / '.local/share'), XDG_STATE_HOME=str(home / '.local/state'),
                XDG_CACHE_HOME=str(home / '.cache'), NVIM_APPNAME='nvim')
            result = subprocess.run([binary, '--headless', '-i', 'NONE', '-u', 'NONE', '-l', str(harness)],
                cwd=home, env=environment, capture_output=True, text=True, timeout=30)
            assert (result.returncode == 0) == expected, 'headless editor error contract did not hold'
    print('pinned Neovim matching-HEAD build failure and parser failure contracts verified')


if __name__ == '__main__':
    qualify(sys.argv[1], Path(sys.argv[2]))
