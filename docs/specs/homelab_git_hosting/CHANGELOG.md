# Changes

## PI-FORGEJO-001 — 2026-10-13

Declared and deployed signature/checksum-pinned Forgejo 15.0.10 LTS ARM64 with
SQLite, private owner configuration, loopback web/Git and capped user service.
Closed registration and locked installer; generated credentials remain private.
Private Git push/clone and complete encrypted Borg restore into isolated Forgejo
matched repository bytes/privacy, with anonymous access denied. Original service
state recovered; existing Samba/RustFS/backup paths preserved. Scoped tests and
live results retained in cycle. No sustained capacity or cloud-restore guarantee;
no Gate Exceptions requested. Intended delivery: reviewed PR/merge into dotfiles;
actual commits and outcome retained in cycle and final output.
