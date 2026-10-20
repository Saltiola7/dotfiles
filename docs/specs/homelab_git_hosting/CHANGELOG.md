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

## Verification refresh — 2026-10-19

After offline SSD recovery, private Git push/clone and complete encrypted Borg
restore passed again using the source-managed helpers. Services and backup timer
remain active, root is writable and repeated role apply preserves private state.
Tailnet Git transport is reachable. HTTPS forwarding is configured, but Tailscale's
ACME certificate order returns `invalid`; authenticated browser access remains
unverified. No TLS verification bypass or insecure-cookie fallback is enabled.
Do not describe certificate issuance or first owner login as completed. Review
certificate-provider recovery separately; retain the private listener and keys.

The owner explicitly approved deferred HTTPS verification on 2026-10-19 while
allowing checked source delivery. Deploy/Operate retain this exception until
valid HTTPS health and owner browser login are verified. Git and encrypted
restore remain verified; no certificate-provider root cause is claimed.
