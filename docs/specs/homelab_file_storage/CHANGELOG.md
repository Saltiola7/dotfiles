# Changes

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
