# Remote Workspace Profile Changelog

## 2026-08-31 - Discovery Contract

- Defined the owner-only CentOS Stream 10 x86_64 terminal overlay, explicit
  activation, deny-by-default target ownership, owner-local Atuin endpoint, and
  rollback behavior.
- Required zero overlap with `dotfiles-ai` and retained credentials, encryption
  keys, history, account identity, and tailnet identity outside Git and rendered
  shared configuration.
- No personal targets, remote homes, credentials, services, or runtime state
  changed. Implementation remains dependency- and approval-gated.
