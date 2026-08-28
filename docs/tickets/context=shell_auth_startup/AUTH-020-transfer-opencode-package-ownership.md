---
schema_version: 1
id: AUTH-020
slug: transfer-opencode-package-ownership
context: shell_auth_startup
title: Transfer OpenCode package ownership
kind: story
state: ready
priority: high
points: 2
depends_on: []
relations: []
owns:
  - Brewfile
  - dot_common_profile.tmpl
  - tests/test_terminal_environment.py
reads:
  - /Volumes/ext/git/Personal/dotfiles-ai/Brewfile
parallel_safe: false
validation:
  - uv run --group test pytest tests/test_terminal_environment.py -q
  - rendered Bash and Zsh syntax checks
  - live OpenCode wrapper version check
created: 2026-08-27
updated: 2026-08-27
completed: null
commits: []
jira_publications: []
migration: null
---

## Outcome

Remove duplicate OpenCode CLI package ownership while preserving the personal
desktop cask and local wrapper precedence.

## Context

`dotfiles-ai` now owns the official Homebrew CLI formula. This personal source
must not reinstall it, but later PATH updates must not bypass the local wrapper
that centralizes runtime state.

## Scope

Remove the CLI tap and formula, retain `opencode-desktop`, and expose the local
wrapper through a command-guarded shell function.

## Non-Goals

Do not uninstall OpenCode, change its managed configuration, or alter desktop
application ownership.

## Acceptance Criteria

- The Brewfile contains no OpenCode CLI tap or formula.
- The OpenCode desktop cask remains.
- Bash and Zsh invoke `~/.local/bin/opencode` after later PATH prepends.
- Wrapper arguments remain unchanged.

## Evidence

Record red-first wrapper evidence, terminal tests, rendered shell syntax, and a
live version check.

## Risks

The wrapper depends on `dotfiles-ai` continuing to manage the local executable.
Its absence falls back to normal command resolution.

## Review

Confirm single package ownership, desktop retention, and argument safety.
