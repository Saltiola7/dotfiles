# dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

macOS-focused configuration for development workstations. Secrets are managed via 1Password CLI and age encryption — nothing sensitive is stored in plain text in this repo.

## Not for direct use

This repository is not meant to be cloned or applied directly. It's published as a reference for how I structure my environment. Machine-specific differences are handled via chezmoi templates.

## What's in here

- Shell configuration (bash/zsh)
- Terminal emulator (kitty)
- Editors (neovim/AstroNvim, Zed)
- Window manager (AeroSpace)
- Keyboard remapping (Karabiner)
- Tmux, starship prompt, atuin, direnv, git, ssh
- Homebrew dependencies (Brewfile)

## Zed

Zed stable is installed by the Brewfile (`brew install --cask zed`). Chezmoi
manages `~/.config/zed/settings.json` from `private_dot_config/zed/settings.json`.
Automatic update checks are disabled so Homebrew owns application updates;
run `brew upgrade --cask zed` to update it. Launch it with `zed .`.

To deploy only Zed settings after installing the cask:

```bash
chezmoi apply --exclude=scripts ~/.config/zed
```

The Brewfile also includes `age`, required to decrypt existing managed SSH files.

### Notes and appearance

Zed automatically installs Catppuccin, Catppuccin Icons, and Markdown Oxide.
Both the editor and icons use Catppuccin Mocha. Markdown uses the
Obsidian-inspired [Markdown Oxide](https://zed.dev/extensions/markdown-oxide)
language server, wraps at 100 columns, and does not reformat notes on save.
Open your notes folder as a project so the server can resolve links across files.

- `Cmd+Shift+B`: toggle the built-in outline panel.
- `Cmd+Shift+O`: navigate headings/symbols in the current file.
- Command palette: `markdown: open preview to the side`.
- Use Markdown links or `[[wiki links]]` for connected notes.

This provides a Markdown editing companion for a notes vault, not Logseq's
block database or the full Neorg environment. No Neorg/Norg extension was
listed in the Zed extension registry when checked on 2026-10-01.

### AI authentication

AI credentials are not stored in these dotfiles. Authentication remains a
per-machine setup:

- For Zed's native agent and inline assistant, run `agent: open settings`,
  then configure the desired LLM provider. API keys entered there are stored
  in the system keychain. Provider environment variables are also supported
  and take precedence over saved keys.
- For Codex, Claude, or OpenCode as an external agent, run `zed: acp registry`,
  install the agent, and start its thread. The agent owns its authentication
  and billing; follow its login prompt if needed. Native Zed provider keys
  do not automatically authenticate these external agents.
- Existing CLI credentials may be reused when the agent supports them and
  runs with the same configuration/home directory. Login reuse has not been
  verified on this machine. A shell's lazy `secret` command does not by itself
  inject credentials into an already-running Zed process.

References: [API access](https://zed.dev/docs/ai/use-api-access),
[external agents](https://zed.dev/docs/ai/external-agents).

## Tests

Unit tests for kitty workspace scripts (session serialization/deserialization):

```bash
python3 -m venv /tmp/dotfiles-test-venv
source /tmp/dotfiles-test-venv/bin/activate
pip install pytest
pytest tests/ -v
```

CI runs on push/PR via GitHub Actions.
