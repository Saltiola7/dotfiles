# Parallels Fedora Workstation Engineering Profile

| Field | Default |
|---|---|
| Deliverable | Single-operator Parallels Fedora desktop lifecycle and personal chezmoi workstation profile |
| Owner | Dotfiles owner |
| Languages/frameworks | Go templates, POSIX shell/Bash, TOML, JSON, Python tests, Homebrew, DNF, Flatpak, and Parallels CLI |
| Modules | Security, Data, Cloud |
| Runtime/platform support | Apple Silicon macOS 26 host; Parallels Desktop 27 Pro; Fedora Workstation 44 aarch64 GNOME; chezmoi |
| Interfaces | `fedora-parallels` host command, `fedora-update`, `fedora-reset-cache`, personal `machine_type`, VM and mount configuration |
| Compatibility | Existing macOS and `lmsh` renders remain unchanged; VM/data state is never replaced implicitly; Parallels CLI syntax is verified from the installed release |
| Trust/data | Host projects and guest credentials are sensitive; full external share is read-only; Git share is read-write; private guest state remains outside Git |
| Delivery | Feature branch, draft pull request, and exact approved local deployment after affected gates pass |
| Operations | Storage preflight, VM profiles, Parallels Tools verification, update/reboot recovery, state preservation, explicit cache reset, and rebuild guidance |
| Authorities | Apple, Fedora, Parallels, and application vendor documentation; rendered target inventory; shell syntax; pytest; installed CLI help; live host/guest smokes |

This is internal single-operator infrastructure rather than a separately
published product. Durable operator outcomes and journeys are specified in the
context README, so a separate Product Intent artifact is not required.
