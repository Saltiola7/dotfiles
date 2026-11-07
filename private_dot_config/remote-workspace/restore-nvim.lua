-- Explicit overlay apply only. Errors must reach the caller as nonzero status.
local ok = xpcall(function()
  local errors = 0
  local notify = vim.notify
  vim.notify = function(message, level, options)
    if level == vim.log.levels.ERROR then errors = errors + 1 end
    return notify(message, level, options)
  end
  local config = vim.fn.stdpath("config")
  local lock = vim.json.decode(table.concat(vim.fn.readfile(config .. "/lazy-lock.json"), "\n"))
  vim.opt.loadplugins = true
  io.stderr:write("remote editor stage owner-init\n")
  dofile(config .. "/init.lua")
  io.stderr:write("remote editor stage plugin-restore\n")
  require("lazy").restore({ wait = true, show = false })
  io.stderr:write("remote editor stage plugin-verify\n")
  local plugins = require("lazy.core.config").plugins
  for name, entry in pairs(lock) do
    local plugin = assert(plugins[name], "locked plugin absent")
    assert(not require("lazy.core.plugin").has_errors(plugin), "locked plugin restore/build failed")
    local result = vim.system({ "git", "-C", plugin.dir, "rev-parse", "HEAD" }, { text = true }):wait(5000)
    assert(result.code == 0 and vim.trim(result.stdout) == entry.commit, "locked plugin identity mismatch")
  end
  local parsers = { "bash", "python", "lua", "vim", "vimdoc", "json", "yaml", "toml", "markdown", "sql" }
  require("lazy").load({ plugins = { "nvim-treesitter" } })
  io.stderr:write("remote editor stage parser-build\n")
  assert(require("nvim-treesitter").install(parsers, { max_jobs = 2 }):wait(300000), "parser installation failed")
  local expanded = require("nvim-treesitter.config").norm_languages(parsers, { unsupported = true })
  local parser_dir = vim.fn.stdpath("data") .. "/site/parser/"
  io.stderr:write("remote editor stage parser-verify\n")
  for _, lang in ipairs(expanded) do
    local path = parser_dir .. lang .. ".so"
    assert(vim.uv.fs_stat(path), "required compiled parser absent")
    -- Unique aliases prevent an already-loaded builtin/owner parser from
    -- bypassing the supplied compiled file. Use its original exported symbol.
    assert(vim.treesitter.language.add("remote_workspace_verify_" .. lang,
      { path = path, symbol_name = lang }), "required parser cannot load")
  end
  assert(vim.v.errmsg == "" and errors == 0, "headless editor reported an error")
end, function(error)
  -- Native plugin errors may contain local paths; keep published diagnostics bounded.
  io.stderr:write("remote owner AstroNvim restore/parser verification failed\n")
  for _, reason in ipairs({ "locked plugin absent", "locked plugin restore/build failed",
    "locked plugin identity mismatch", "parser installation failed", "required compiled parser absent",
    "required parser cannot load", "headless editor reported an error" }) do
    if tostring(error):find(reason, 1, true) then
      io.stderr:write("remote editor invariant " .. reason .. "\n")
      break
    end
  end
end)
if not ok then vim.cmd("cquit 1") end
print("remote owner AstroNvim ten parsers verified")
vim.cmd("qa!")
