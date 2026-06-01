# Changelog: Kitty-PyCharm Workspace Integration

All notable changes to the Kitty workspace system.

## [2026-06-01]

### Changed
- Graduated spec to DBSCTR directory format (README + BACKLOG + CHANGELOG)
- Added Behavior Scenarios section (workspace launch, snapshot, session resumption)

## [2026-05-15]

### Added
- Pane tab move keymaps (commits `a24bfb4`, `bc9b6dc`)

## [2026-04-20]

### Added
- Initial implementation: PyCharm External Tool integration via `kitty-workspace`
- OpenCode session binding via `opencode-kitty` with map/seed mechanism
- Snapshot save (F16) and restore (extra-tab layering)
- `kitty-query.py` shared logic module (11 typer subcommands, PEP 723 inline deps)
- 160 unit tests covering all pure-logic functions
- CI via GitHub Actions (Python 3.12 + 3.13)
- Stale binding purge on workspace open
- Generic fallback for projects without `build_*` functions
- Debug logging (`KITTY_WORKSPACE_DEBUG=1`)
