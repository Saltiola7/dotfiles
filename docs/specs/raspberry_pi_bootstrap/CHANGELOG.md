# Changelog

## 2026-10-12 — Pi image preparation (delivery pending)

Implemented maintained macOS plan/prepare/verify commands and an unprivileged
Lima ext4 editor. Publisher signatures and pinned hashes guard input; the guest
uses key-only SSH and password-required sudo. Prepared images and receipts stay
private. Backend sudo policy and existing services are preserved; no physical
disk writes are implemented in this slice.

Validation: 13 affected-scope tests, real isolated ext4 read/write/ownership and
filesystem checks, and a full Fedora image integration preparation passed.
Host installation and actual-input plan passed. Final owner-password candidate,
release verification and draft PR delivery remain pending. Physical boot,
filesystem growth and target administration are unverified until the flash/boot
slice. No gate exceptions are approved.

Kernel commits: `f871aea` (contract), `7ce1516` (implementation/tests).
Intended delivery: feature branch and draft PR to `Saltiola7/dotfiles`, then
merge after checks under the owner's explicit merge instruction. Owner recovery
and seven-day staging retention are documented in README; review Fedora support
before 2027-05-19.
