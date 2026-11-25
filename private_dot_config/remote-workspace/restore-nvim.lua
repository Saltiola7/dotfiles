-- Explicit overlay apply only. The same native checks run after a real -u
-- owner startup, without installing or rewriting anything in that mode.
local ok = xpcall(function()
  local errors = 0
  local notify = vim.notify
  vim.notify = function(message, level, options)
    if level == vim.log.levels.ERROR then errors = errors + 1 end
    return notify(message, level, options)
  end
  local config = vim.fn.stdpath("config")
  local root = vim.fn.stdpath("data") .. "/lazy"
  local verify_only = vim.g.remote_workspace_check_only
  local lock = vim.json.decode(table.concat(vim.fn.readfile(config .. "/lazy-lock.json"), "\n"))
  if not verify_only then
    assert(root == vim.env.REMOTE_WORKSPACE_LAZY_ROOT and vim.env.LAZY == root .. "/lazy.nvim")
    assert(vim.fn.stdpath("data") ~= vim.env.HOME .. "/.local/share/nvim",
      "headless editor reported an error")
    vim.opt.loadplugins = true
    -- Preserve the locked map across Lazy's incremental import rounds.
    vim.opt.rtp:prepend(vim.env.LAZY)
    local lock_manager = require("lazy.manage.lock")
    lock_manager.lock = vim.deepcopy(lock)
    lock_manager._loaded = true
    lock_manager.update = function() end
    _G.remote_workspace_verifying = true
    io.stderr:write("remote editor stage owner-init\n")
    dofile(config .. "/init.lua")
    io.stderr:write("remote editor stage plugin-restore\n")
    require("lazy").restore({ wait = true, show = false })
  elseif not _G.remote_workspace_verifying then
    error("headless editor reported an error")
  end
  io.stderr:write("remote editor stage plugin-verify\n")
  local plugins = require("lazy.core.config").plugins
  for name in pairs(plugins) do assert(lock[name], "locked plugin identity mismatch") end
  for name, entry in pairs(lock) do
    local plugin = assert(plugins[name], "locked plugin absent")
    assert(plugin.dir == root .. "/" .. name, "locked plugin identity mismatch")
    assert(not require("lazy.core.plugin").has_errors(plugin), "locked plugin restore/build failed")
    local result = vim.system({ "git", "-C", plugin.dir, "rev-parse", "HEAD" }, { text = true }):wait(5000)
    assert(result.code == 0 and vim.trim(result.stdout) == entry.commit, "locked plugin identity mismatch")
  end
  local parsers = { "bash", "python", "lua", "vim", "vimdoc", "json", "yaml", "toml", "markdown", "sql" }
  require("lazy").load({ plugins = { "nvim-treesitter" } })
  if not verify_only then
    io.stderr:write("remote editor stage parser-build\n")
    assert(require("nvim-treesitter").install(vim.deepcopy(parsers), { max_jobs = 2 }):wait(300000),
      "parser installation failed")
  end
  local expanded = require("nvim-treesitter.config").norm_languages(vim.deepcopy(parsers), { unsupported = true })
  local parser_dir = vim.fn.stdpath("data") .. "/site/parser/"
  io.stderr:write("remote editor stage parser-verify\n")
  local seen = {}
  for _, lang in ipairs(expanded) do
    assert(type(lang) == "string" and lang:match("^[a-z][a-z0-9_]*$") and not seen[lang],
      "required parser cannot load")
    local path = parser_dir .. lang .. ".so"
    local file = vim.uv.fs_lstat(path)
    assert(file and file.type == "file" and file.nlink == 1 and file.size > 0, "required compiled parser absent")
    -- Unique aliases prevent an already-loaded builtin/owner parser from
    -- bypassing the supplied compiled file. Use its original exported symbol.
    local alias = "remote_workspace_verify_" .. lang
    assert(not vim._ts_has_language(alias), "required parser cannot load")
    assert(vim.treesitter.language.add(alias,
      { path = path, symbol_name = lang }), "required parser cannot load")
    assert(vim.treesitter.get_string_parser("", alias):parse()[1], "required parser cannot load")
    seen[lang] = true
  end
  for _, lang in ipairs(parsers) do assert(seen[lang], "required compiled parser absent") end
  assert(seen.markdown_inline, "required compiled parser absent") -- pinned markdown dependency
  assert(vim.v.errmsg == "" and errors == 0 and (not verify_only or _G.remote_setup_errors == 0),
    "headless editor reported an error")
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
io.stderr:write("\nremote owner AstroNvim ten parsers verified\n")
io.stderr:flush()
vim.cmd("qa!")
