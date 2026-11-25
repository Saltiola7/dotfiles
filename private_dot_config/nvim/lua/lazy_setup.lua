-- The two promotion renames and the final startup aren't an atomic operation.
-- Only a helper-created data generation carries this marker. If interrupted
-- with that generation selected, ordinary opens stay usable in plain Neovim
-- instead of running its plugins. Unmarked installations take the usual path.
local uv = vim.uv or vim.loop
local marker = vim.fn.stdpath("data") .. "/.remote-workspace-generation"
if uv.fs_lstat(marker) and not _G.remote_workspace_verifying then
  local function small_json(path)
    local info = assert(uv.fs_lstat(path))
    assert(info.type == "file" and info.nlink == 1 and info.size <= 65536)
    return vim.json.decode(table.concat(vim.fn.readfile(path), "\n"))
  end
  local ok, accepted = pcall(function()
    local generation = small_json(marker).generation
    assert(type(generation) == "string" and generation:match("^attempt%-%d%d%d%d$"))
    local state = vim.fn.fnamemodify(vim.fn.stdpath("state"), ":h") .. "/remote-workspace/"
    local record = small_json(state .. "editor-attempts/" .. generation .. "/record.json")
    local ready = uv.fs_lstat(state .. "editor-ready.json")
    return record.version == 2 and record.state == "accepted" and ready and ready.type == "file"
      and ready.nlink == 1 and ready.size > 0
  end)
  if not ok or not accepted then
    vim.opt.loadplugins = false
    vim.api.nvim_echo({ { "Remote editor preparation incomplete; plugins disabled", "WarningMsg" } }, false, {})
    return
  end
end

require("lazy").setup({
  {
    "AstroNvim/AstroNvim",
    version = "^6", -- Remove version tracking to elect for nightly AstroNvim
    import = "astronvim.plugins",
    opts = { -- AstroNvim options must be set here with the `import` key
      mapleader = " ", -- This ensures the leader key must be configured before Lazy is set up
      maplocalleader = ",", -- This ensures the localleader key must be configured before Lazy is set up
      icons_enabled = true, -- Set to false to disable icons (if no Nerd Font is available)
      pin_plugins = nil, -- Default will pin plugins when tracking `version` of AstroNvim, set to true/false to override
      update_notifications = true, -- Enable/disable notification about running `:Lazy update` twice to update pinned plugins
    },
  },
  { import = "community" },
  { import = "plugins" },
} --[[@as LazySpec]], {
  -- Configure any other `lazy.nvim` configuration options here
  -- Preparation uses the ordinary stdpath("data")/lazy in an isolated XDG
  -- data home. A verification startup may load, but must never install.
  install = { missing = not vim.g.remote_workspace_check_only, colorscheme = { "astrotheme", "habamax" } },
  ui = { backdrop = 100 },
  performance = {
    rtp = {
      -- disable some rtp plugins, add more to your liking
      disabled_plugins = {
        "gzip",
        "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "zipPlugin",
      },
    },
  },
} --[[@as LazyConfig]])
