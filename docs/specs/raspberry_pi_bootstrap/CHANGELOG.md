# Changelog

## 2026-10-12 — Pi image preparation

Implemented maintained macOS plan/prepare/verify commands and an unprivileged
Lima ext4 editor. Publisher signatures and pinned hashes guard input; the guest
uses key-only SSH and password-required sudo. Prepared images and receipts stay
private. Backend sudo policy and existing services are preserved; no physical
disk writes are implemented in this slice.

Validation: 32 combined topology/bootstrap affected-scope tests, real isolated ext4 read/write/ownership and
filesystem checks, and a full Fedora image integration preparation passed.
Host installation, actual-input plan, final owner-password candidate identity
and private file permissions passed. Existing Lima services remain healthy;
disposable-credential integration staging was removed. Draft PR delivery is the
Final Push target. Physical boot,
filesystem growth and target administration are unverified until the flash/boot
slice. No gate exceptions are approved.

Gate commits: `f871aea` (contract), `7ce1516` (implementation/tests),
`3f828fc` (refactor), `d18cb07` (topology integration).
Intended delivery: feature branch and draft PR to `Saltiola7/dotfiles`, then
merge after checks under the owner's explicit merge instruction. Owner recovery
and seven-day staging retention are documented in README; review Fedora support
before 2027-05-19.
