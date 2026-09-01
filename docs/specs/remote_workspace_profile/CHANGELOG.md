# Remote Workspace Profile Changelog

## 2026-09-01 - Owner Yazi Overlay

- Added explicit `machine_type=remote-workspace` rendering for only Yazi
  package/theme configuration, the locked flavor, and checksum-pinned x86_64
  Yazi, `ya`, fd, fzf, and 7-Zip installation.
- Proved empty rendered and installed intersections with `dotfiles-ai` commit
  `58833a2`, unchanged macOS and `lmsh` rendering, an empty second apply, and
  rollback preservation in disposable CentOS Stream 10 x86_64.
- Full repository pytest passed with 181 tests. No gate exception, release, or
  live owner deployment occurred. Implementation Gate Commit: `d41c639`.
  Intended delivery is a draft pull request to `Saltiola7/dotfiles` `main`.

## 2026-09-01 - Yazi-Only Ownership Readiness

- Assigned Bash, Atuin, and Starship exclusively to the shared `dotfiles-ai`
  foundation and narrowed the personal remote overlay to Yazi configuration,
  flavor, and portable dependencies.
- Required empty rendered and installed target intersections, x86_64 checksum
  proof, idempotency, and rollback without deleting history or authentication.
- No target, user home, credential, history, or runtime changed. RWUE-003 is
  ready for a fresh digest-bound receipt and approval.

## 2026-08-31 - Discovery Contract

- Defined the owner-only CentOS Stream 10 x86_64 terminal overlay, explicit
  activation, deny-by-default target ownership, owner-local Atuin endpoint, and
  rollback behavior. The later closure-readiness decision supersedes its
  overlapping Bash, Atuin, and Starship target set.
- Required zero overlap with `dotfiles-ai` and retained credentials, encryption
  keys, history, account identity, and tailnet identity outside Git and rendered
  shared configuration.
- No personal targets, remote homes, credentials, services, or runtime state
  changed. Implementation remains dependency- and approval-gated.
