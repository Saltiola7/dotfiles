# AstroNvim Setup Specification

**Status:** Stable
**Created:** 2026-04-13
**Replaces:** LazyVim starter (backed up at `~/.config/nvim.lazyvim.bak`)

## Overview

AstroNvim v6 with catppuccin-mocha colorscheme. Near-stock template with only two files customized. Standard vim keybindings (no Colemak remapping). Managed independently from chezmoi for now.

## File Map

| Path | Purpose | Modified? |
|------|---------|-----------|
| `~/.config/nvim/init.lua` | Bootstraps lazy.nvim, calls `lazy_setup` and `polish` | No (template stock) |
| `~/.config/nvim/lua/lazy_setup.lua` | Configures lazy.nvim with AstroNvim + user plugins | No |
| `~/.config/nvim/lua/community.lua` | AstroCommunity plugin imports | **Yes** - activated, added catppuccin |
| `~/.config/nvim/lua/plugins/astroui.lua` | AstroUI configuration (theme, icons, highlights) | **Yes** - activated, set catppuccin-mocha |
| `~/.config/nvim/lua/plugins/astrocore.lua` | AstroCore config (keymaps, options, autocmds) | No (template stock, inactive) |
| `~/.config/nvim/lua/plugins/astrolsp.lua` | LSP configuration | No (template stock, inactive) |
| `~/.config/nvim/lua/plugins/mason.lua` | Mason package manager config | No (template stock, inactive) |
| `~/.config/nvim/lua/plugins/none-ls.lua` | Formatting/linting config | No (template stock, inactive) |
| `~/.config/nvim/lua/plugins/treesitter.lua` | Treesitter parser config | No (template stock, inactive) |
| `~/.config/nvim/lua/plugins/user.lua` | User plugin specs | No (template stock, inactive) |
| `~/.config/nvim/lua/polish.lua` | Final arbitrary Lua executed last | No (template stock) |

### Backups

| Backup | Contents |
|--------|----------|
| `~/.config/nvim.bak/` | Original hand-written config with Colemak-DH keybindings |
| `~/.config/nvim.lazyvim.bak/` | Previous LazyVim starter setup |
| `~/.local/share/nvim.bak/` | LazyVim plugin data |
| `~/.local/state/nvim.bak/` | LazyVim state |
| `~/.cache/nvim.bak/` | LazyVim cache |

## Architecture

AstroNvim is a neovim plugin (not a fork). It sits inside the lazy.nvim plugin manager and provides a curated set of plugins with sensible defaults.

```
init.lua
  └── lua/lazy_setup.lua
        ├── AstroNvim (core plugin collection)
        ├── lua/community.lua          ← imports from AstroCommunity
        │     ├── catppuccin colorscheme
        │     └── lua language pack
        └── lua/plugins/*.lua          ← user overrides
              └── astroui.lua          ← sets catppuccin-mocha as colorscheme
```

Only two files were changed from the template:

**`lua/community.lua`** - Removed the `if true then return {} end` guard. Added catppuccin colorscheme import. This file is loaded before `lua/plugins/` so community specs take precedence as defaults that user plugins can override.

**`lua/plugins/astroui.lua`** - Removed the guard and all commented-out examples. Set `colorscheme = "catppuccin-mocha"`. This is the single line that controls the active theme.

### Why catppuccin-mocha

Kitty and the terminal environment use catppuccin-mocha. Using the same palette in nvim means status lines, tab bars, and editor chrome don't clash visually.

### Why standard vim keybindings (no Colemak-DH)

The old `nvim.bak` config remapped n/e/i/o to hjkl for Colemak-DH. This is no longer needed because navigation is handled at the hardware level via a ZSA keyboard with custom layers. Keeping standard vim bindings means muscle memory transfers to any machine, documentation and tutorials apply directly, and plugins that assume hjkl work without remapping.

### Why AstroNvim over LazyVim

Switching from LazyVim to AstroNvim for the AstroCommunity ecosystem, which provides language packs and plugin configurations as importable community modules. The migration was clean since the LazyVim setup was near-stock with no meaningful customizations.

## Reproduction

From a fresh machine with neovim installed (`brew install neovim`):

```bash
# 1. Backup any existing config
mv ~/.config/nvim ~/.config/nvim.bak
mv ~/.local/share/nvim ~/.local/share/nvim.bak
mv ~/.local/state/nvim ~/.local/state/nvim.bak
mv ~/.cache/nvim ~/.cache/nvim.bak

# 2. Clone AstroNvim template
git clone --depth 1 https://github.com/AstroNvim/template ~/.config/nvim
rm -rf ~/.config/nvim/.git

# 3. Activate community.lua - replace the file contents with:
cat > ~/.config/nvim/lua/community.lua << 'EOF'
-- AstroCommunity: import any community modules here
-- We import this file in `lazy_setup.lua` before the `plugins/` folder.
-- This guarantees that the specs are processed before any user plugins.

---@type LazySpec
return {
  "AstroNvim/astrocommunity",
  { import = "astrocommunity.colorscheme.catppuccin" },
  { import = "astrocommunity.pack.lua" },
  -- import/override with your plugins folder
}
EOF

# 4. Set colorscheme in astroui.lua - replace the file contents with:
cat > ~/.config/nvim/lua/plugins/astroui.lua << 'EOF'
-- AstroUI provides the basis for configuring the AstroNvim User Interface
-- Configuration documentation can be found with `:h astroui`

---@type LazySpec
return {
  "AstroNvim/astroui",
  ---@type AstroUIOpts
  opts = {
    colorscheme = "catppuccin-mocha",
  },
}
EOF

# 5. First launch - plugins will auto-install (~30 seconds)
nvim
```

On first interactive launch, Mason will install `tree-sitter-cli` and Lazy will clone all plugin repos. This takes about 30 seconds on a decent connection.

## Known Issues / Gotchas

- **First launch installs everything.** Running `nvim --headless -c "qall"` triggers plugin installation but Mason will warn about tree-sitter-cli being interrupted. The first real interactive `nvim` session finishes the job cleanly.

- **Template files are guarded.** Every file in the template has `if true then return {} end` on line 1. You must remove this line to activate a file. Only `community.lua` and `astroui.lua` have been activated so far.

- **lazy-lock.json pins versions.** After the first launch, `~/.config/nvim/lazy-lock.json` is created with pinned plugin versions. Run `:Lazy sync` to update.

- **Not managed by chezmoi.** The `~/.config/nvim/` directory is standalone. The dotfiles repo only has `alias vim='nvim'` referencing neovim. If the config needs to be portable across machines, it should be added to chezmoi later.

## Future Work

- Add language packs via AstroCommunity (e.g., `astrocommunity.pack.python`, `astrocommunity.pack.typescript`)
- Add the nvim config to chezmoi as `private_dot_config/nvim/`
- Evaluate AstroCommunity plugin for copilot/AI completion integration
- Custom keymaps in `astrocore.lua` as workflow-specific needs emerge
