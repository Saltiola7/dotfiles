# Host maintenance changelog

## 2026-10-07 — SSD-HOST-SDK-BOOTSTRAP

- Added macOS ARM64 standalone SDK bootstrap after Homebrew's before-stage
  prerequisite installation. Verified baseline archive is used only when absent;
  healthy newer installations and extra components remain unchanged.
- Existing unhealthy paths, bad checksums, missing Python, installer failures and
  concurrent destination creation fail without overwriting user state. Installation
  uses isolated HOME/config, disables Python installation and shell-profile edits,
  and retains failed staging evidence. Other platforms remain unchanged.
- Validation: 33 affected pytest cases passed; shell syntax passed; real verified
  archive installation and repeated hook execution passed in an empty home. Live
  targeted chezmoi apply was a healthy-install no-op and repeated cleanly.
- Archived old Homebrew SDK and receipt, verified its six component IDs are covered
  by the standalone installation's nine, then used native non-zap uninstall with
  dependency autoremove disabled. Inactive old SDK directory and external backup
  remain retained. Four Bash/Zsh login modes select standalone gcloud, bq and gsutil.
- Implementation Gate Commit: `2b9e560`. No gate exceptions; package release not
  applicable. Intended Final Push: feature branch and draft PR into main; actual
  delivery result remains in the Cycle Record.

## 2026-10-07 — SSD-HOST-SDK-SHELL

- Restored standalone Google SDK precedence in Bash and Zsh, including
  noninteractive login shells and SDK paths inherited behind Homebrew.
- Guarded PATH updates on an executable SDK; missing/nonexecutable candidates
  preserve selection. Existing completion, AI guards and external-state settings
  remain intact. No SDK, credential or cloud resource was changed.
- Regression evidence: seven failing cases before implementation; affected SDK,
  terminal and AI ownership pytest suites pass afterward. Rendered Bash/Zsh syntax
  passes. Four host login modes select the standalone SDK; repeat targeted apply
  has no drift. Configuration preimages retained privately.
- Implementation Gate Commit: `00a6f0d`. No gate exceptions. Release not applicable.
  Intended Final Push: feature branch and draft PR into main; actual delivery
  result is retained in the Cycle Record.
