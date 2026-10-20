# Storage deployment discovery

The operator approved two additional bounded contexts in personal dotfiles:
`homelab_file_storage` owns Pi Samba and ordinary folders, and `homelab_backup`
owns encrypted versioned Borg recovery to a dedicated Mac-connected external
disk folder. Existing topology owns their observed and desired hosting edges.

Pi is primary and can run continuously. Access is private through Tailscale;
connected-only clients are sufficient. Baserow remains deferred. No file
migration, disk reformatting, existing share replacement or HP backup changes
are authorized by this slice.

RustFS was initially research-only. The operator subsequently requested its
installation on Pi for DVC/S3 use. It must use separate
data storage and credentials from Samba and have bounded resources. Do not
interpret a candidate service as deployed. A separate object-storage contract
will own its S3 endpoint, image identity, credentials and recovery.

Dependencies: Pi profile deployment remains incomplete; Samba package and service
are absent. SELinux is enforcing. Destination is an existing APFS external disk;
its identity stays private. HP Borg/borgmatic timer and last successful run were
observed. Mac personal Lima currently hosts Atuin and PostgreSQL; both must be
preserved. Actual backup direction, constrained credentials and destination
mount checks must be verified before deployment.

Samba was deployed and verified in merged PR #38, including fresh startup.
Backup and RustFS remain pending. Authoritative source is
the two context READMEs; topology diagrams are updated after hosting is selected
and verification distinguishes planned from observed state.
