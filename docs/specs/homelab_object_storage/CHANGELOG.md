# Changes

## PI-S3-001 — 2026-10-12

Installed checksum-pinned RustFS 1.0.1 ARM64 as capped Pi owner service with
separate data/private credentials and private S3 forwarding. Fixed default console
listener to loopback. Anonymous and physical-LAN access denied; signed S3 and
isolated DVC push/fresh-cache pull matched, including after reboot. Samba preserved.

Added separate hash-locked DVC 3.67.1/S3 client; generic DVC/projects unchanged.
Scoped tests and live checks retained in cycle. No production throughput,
redundancy or object-backup claim. No Gate Exceptions requested. Intended delivery:
reviewed draft PR and merge; actual commit/push retained in cycle/final output.
