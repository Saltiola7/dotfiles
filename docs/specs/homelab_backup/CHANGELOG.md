# Changes

## PI-BORG-001 — 2026-10-12

Declared and deployed encrypted Borg 1.4.5 backups from Pi ordinary folders to a
new dedicated repository on existing Mac-connected disk. Guarded exact mount
identity, restricted fresh Pi-generated SSH identity, private recovery material,
restore prerequisite and 7/4/6 retention. Isolated restore matched; normal job
and daily timer catch-up after fresh reboot passed. Local scoped tests passed;
exact validation totals and commits are retained in the cycle record.

Backblaze drive selection observed; new repository upload and cloud restore remain
unverified follow-up. No offsite guarantee or full-system/object-store backup
claim. No Gate Exceptions requested. Intended delivery: reviewed draft PR and
merge into personal dotfiles main; actual push is recorded in cycle/final output.


## PI-RUSTFS-BACKUP-001 — 2026-10-13

Added pinned frozen RustFS captures to existing encrypted Borg archives, preserving
ordinary sources and retention. Original service-state recovery, stop-post hook,
private staging and explicit enrollment are declared. Isolated recovered RustFS
returned matching signed S3 bytes/metadata and denied anonymous retrieval; Samba
stayed available. Failure-first regression and scoped integration checks passed.
No cloud restore or production replacement claim; no Gate Exceptions. Intended
reviewed PR/merge delivery, with exact commits and outcomes in cycle record.
