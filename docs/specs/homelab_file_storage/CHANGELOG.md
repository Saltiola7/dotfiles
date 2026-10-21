# Changes

## SAMBA-RECONNECT-001 — 2026-10-20

Centralized Pi and Omarchy Samba policy and the public logical share catalog.
Added a personal macOS LaunchAgent that independently retries Pi and HP every
60 seconds through native NoUI NetFS, with private local endpoint bindings and
system-managed authentication. Existing server configuration bytes and access
boundaries are preserved. The ARM guest remains manual and unverified.

Fresh Pi and HP mounts and isolated bidirectional SMB byte checks passed;
launchd ran successfully and both mounts were reused. A CCC-created root-owned
Pi mount was identified and preserved; the owner stopped CCC, then Pi remount
passed. Foreign-owner conflicts now fail closed. Source regressions passed 72
focused tests; the wider Mac-compatible suite passed before the final guard.
The unchanged Linux-only desktop fixture requires the full configured Linux CI
matrix before merge. Cold login/wake and credential-unlock behavior remain
unobserved, with no security gate exception. Source commits e1c6dd0, 0386669 and
31c82fe precede final runbook closure. No server restart or new dependency was
needed. Intended Final Push: draft PR to Saltiola7/dotfiles main, followed by
merge under the operator's standing instruction after exact-head CI checks.
Actual push/merge and deployment receipts remain in the private Cycle Record.

## PI-SAMBA-001 — 2026-10-12

Declared and deployed authenticated Pi Samba over private Tailscale TCP forwarding.
Direct binding to the non-broadcast interface failed and was replaced with
loopback binding plus Serve, preserving private-only access. Owner privately
enrolled SMB credentials. Authenticated browse/upload/download/delete and content
equality passed; anonymous share access and physical LAN access were denied.
Fresh reboot preserved service, forwarding and SELinux enforcement.

Scoped pytest passed 23 tests; Bash syntax and candidate testparm passed.
Implementation commit e5c174e preceded the observed binding fix. No exceptions
approved. Phone/Finder UI and throughput are unverified. Backup and S3 deployment
remain separate work. Intended delivery: draft PR to personal dotfiles main;
actual push/merge is recorded in the cycle and completion response.
