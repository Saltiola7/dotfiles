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

## FORGEJO-HTTPS-001 — 2026-10-19

Investigated Tailscale certificate issuance: private logs recorded rejected ACME
orders and control-plane DNS record-write HTTP 500 errors. The existing daemon
subsequently obtained a valid certificate without local configuration changes.
Trusted health/login and anonymous API denial now pass from both Pi and Mac;
precise earlier CA validation cause remains unproven. Certificate issuance is no
longer deferred; first owner browser login/password change remains pending.

Added source-managed, non-root `pi-forgejo-setup https-check` with default TLS
trust/hostname validation, fixed endpoints, disabled environment proxies, rejected
redirects, response limits, socket timeouts and sanitized failures. Explicit
network enrollment now requires this readiness proof and preserves routes when
issuance fails. Regression tests cover TLS/provider failures, unsafe names,
redirects, health payloads, anonymous denial and existing-route preservation.
Documented safe provider recovery and rate-limit handling; no daemon restart,
certificate-cache removal, public exposure, credential change or sudo needed.
Python/Cloud/Security modules apply; no release artifact or dependency change.
Intended delivery: checked dotfiles PR/merge; actual commits, final checks and
deployment receipt retained in private cycle evidence.
