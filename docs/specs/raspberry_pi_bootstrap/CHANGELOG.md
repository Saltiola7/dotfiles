# Changelog

## 2026-10-12 — Guarded StoreJet flash and initial headless boot

Implemented explicit macOS flash-plan and flash commands. A short-lived private
plan binds the prepared image, external whole-disk identity and original header;
matching approval, private files, fresh identity checks and bounded full readback
guard the physical write. Ordinary chezmoi apply never flashes a disk.

Validation: 50 affected-scope tests passed. The owner executed the approved sudo
flash; all 5,596,250,112 image bytes passed readback verification and the SSD was
ejected. Initial headless Pi 400 USB boot and receipt-bound SSH host authentication
passed over direct IPv6 Ethernet. Fedora 44 aarch64, expanded USB root, successful
growth service, enforcing SELinux and active SSH/NetworkManager were observed.
Noninteractive sudo was refused as required; interactive owner-password sudo
rebooted successfully. A new boot ID confirmed fresh boot, persistent SSH identity,
expanded root and enforcing SELinux. Permanent networking, Tailscale enrollment
and delivery remain pending; no closure is claimed.

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
