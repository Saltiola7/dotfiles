---
schema_version: 1
id: AUTH-019
slug: yazi-terminal-file-manager
context: shell_auth_startup
title: Install Yazi with portable cwd integration and Catppuccin Mocha
kind: story
state: done
priority: medium
points: 5
depends_on: []
relations: []
owns:
  - .chezmoiignore
  - .github/workflows/test.yml
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
completed: 2026-08-26
commits:
  - 5a4a345e57b6d3e61c394076f9c9dc2daf6eaf7a
  - 9aa14a99a1286af45cb4627d91b1e83435ff0c3d
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

- Red-first regression evidence `ev-44c2e67dd21843f081eb355019121eb0`
  failed before implementation; all 176 tests pass afterward.
- Rendered Bash and Zsh syntax checks and Xonsh compilation pass. The focused
  wrapper test proves valid cwd adoption and unchanged-cwd behavior.
- Both Macs run Homebrew Yazi `26.8.15`; both Fedora arm64 guests run pinned
  Yazi `26.8.15`, fd `10.5.0`, fzf `0.74.3`, and 7-Zip `26.02` after every
  downloaded archive passed its SHA-256 check.
- All four targets list official Catppuccin Mocha revision `20b47bf`. Kitty
  `0.48.2` exposes its `icat` adapter without a configuration change.
- The bounded MacBook apply has no remaining diff, both Mac shell files pass
  syntax/compile checks, and both guest deployments pass version smokes.

## Risks

Yazi flavors remain beta. Guest preview capabilities intentionally differ from
macOS, and pinned binaries require periodic review.

## Review

Package ownership, shell safety, checksums, target restrictions, and direct
deployments were reviewed. No AI configuration, Kitty configuration, privileged
guest provisioning, or unrelated managed target entered the diff.
