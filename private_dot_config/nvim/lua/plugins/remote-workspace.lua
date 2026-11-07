-- Remote-only target: retain the owner's config, but install language servers on demand.
return {
  { "WhoIsSethDaniel/mason-tool-installer.nvim", opts = function(_, opts)
    opts.ensure_installed = {}
    opts.run_on_start = false
  end },
  { "mason-org/mason-lspconfig.nvim", opts = function(_, opts)
    opts.ensure_installed = {}
    opts.automatic_installation = false
  end },
  { "jay-babu/mason-nvim-dap.nvim", opts = function(_, opts)
    opts.ensure_installed = {}
    opts.automatic_installation = false
  end },
  { "jay-babu/mason-null-ls.nvim", opts = function(_, opts)
    opts.ensure_installed = {}
    opts.automatic_installation = false
  end },
}
