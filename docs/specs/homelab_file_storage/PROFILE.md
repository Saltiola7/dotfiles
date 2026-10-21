# Engineering Profile

Owner-operated private file sharing across Fedora ARM64 Pi, Omarchy Linux and
personal macOS clients. Samba, SELinux/systemd on Pi, existing private-LAN and
Tailscale firewall policy on Omarchy, macOS NetFS/Keychain and per-user launchd
for client reconnection. Python 3.12+ standard-library client automation and
Bash provisioning; Python, Cloud and Security modules apply. Risk is elevated.

Chezmoi owns one shared Samba policy/template and a logical share catalog.
Existing installed server configuration paths remain compatible. Private
endpoints and usernames remain in owner-only local connection bindings; SMB
passwords remain with Samba and macOS Keychain. No credential extraction,
public ingress, automatic privileged provisioning or data migration is allowed.

Kernel, review/integrate, deploy, operate and maintain/retire gates are required.
Release is not applicable: no package is published. Authorities are configured
pytest on Python 3.12–3.14, isolated chezmoi rendering/profile tests, shell/plist
syntax checks, Samba testparm, exact policy parity, macOS launchd readiness,
noninteractive SMB mount/retry/idempotence, authenticated isolated file roundtrip
and denied-access checks. No new runtime package is needed. The operator owns
manual credential enrollment, privileged server activation when needed,
rollback, OS/Samba/Tailscale maintenance and eventual retirement.

The context README and SAMBA-RECONNECT.md define behavior and recovery.
