# dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

macOS-focused configuration for development workstations. Secrets are managed via 1Password CLI and age encryption — nothing sensitive is stored in plain text in this repo.

## Not for direct use

This repository is not meant to be cloned or applied directly. It's published as a reference for how I structure my environment. Machine-specific differences are handled via chezmoi templates.

## What's in here

- Shell configuration (bash/zsh)
- Terminal emulator (kitty)
- Editor (neovim/AstroNvim)
- Window manager (AeroSpace)
- Keyboard remapping (Karabiner)
- Tmux, starship prompt, atuin, direnv, git, ssh
- Homebrew dependencies (Brewfile)

## Tests

Unit tests for kitty workspace scripts (session serialization/deserialization):

```bash
python3 -m venv /tmp/dotfiles-test-venv
source /tmp/dotfiles-test-venv/bin/activate
pip install pytest
pytest tests/ -v
```

CI runs on push/PR via GitHub Actions.
