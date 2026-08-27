---
schema_version: 1
id: AUTH-019
slug: yazi-terminal-file-manager
context: shell_auth_startup
title: Install Yazi with portable cwd integration and Catppuccin Mocha
kind: story
state: ready
priority: medium
points: 5
depends_on: []
relations: []
owns:
  - Brewfile
  - dot_common_profile.tmpl
  - dot_xonshrc.tmpl
  - private_dot_config/yazi
  - run_onchange_install-lmsh-terminal.sh.tmpl
  - run_onchange_after_install-yazi-flavor.sh.tmpl
  - tests/test_terminal_environment.py
reads:
  - private_dot_config/kitty/kitty.conf
  - docs/specs/shell_auth_startup
parallel_safe: false
validation:
  - uv run --group test pytest tests/test_terminal_environment.py -v
  - rendered Bash, Zsh, Xonsh, and lmsh installer checks
  - macOS and Fedora arm64 Yazi smoke checks
created: 2026-08-26
updated: 2026-08-26
completed: null
commits: []
jira_publications: []
migration: null
---

## Outcome

Install Yazi on managed macOS workstations and Fedora arm64 guests with a
portable `y` command, locked Catppuccin Mocha styling, and explicit preview
capability boundaries.

## Context

Kitty already supports Yazi's graphics protocol. The personal source owns shell
and terminal packages, while the shared `dotfiles-ai` source must remain
unchanged.

## Scope

Manage the practical Homebrew dependency set, pinned non-root guest binaries,
the upstream cwd wrappers for Bash/Zsh and Xonsh, and the locked official
Catppuccin Mocha flavor.

## Non-Goals

Do not add Yazi plugins or behavioral overrides. Do not install privileged guest
packages or provide guest PDF, video, SVG, or advanced-image previews.

## Acceptance Criteria

- Both macOS machine types install Yazi and the practical dependency set through
  the existing Brewfile flow.
- Both Fedora arm64 guests install pinned Yazi, fd, fzf, and 7-Zip binaries
  without root access.
- Bash, Zsh, and Xonsh `y` wrappers adopt Yazi's final directory only when Yazi
  writes a valid directory.
- Yazi selects a locked official Catppuccin Mocha flavor.
- Kitty and `dotfiles-ai` configuration remain unchanged.

## Evidence

Record focused tests, rendered shell checks, package versions, flavor lock
identity, live Kitty adapter output, and guest smoke results in this ticket.

## Risks

Yazi flavors remain beta. Guest preview capabilities intentionally differ from
macOS, and pinned binaries require periodic review.

## Review

Confirm package ownership, shell safety, checksum verification, and that no AI
configuration or privileged guest provisioning entered the diff.
