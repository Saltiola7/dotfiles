# Engineering Profile

Internal infrastructure; operator-owned. Fedora ARM64, Samba, systemd and SELinux
enforcing. Cloud and Security modules apply; risk elevated. Configuration is
declared in chezmoi with explicit privileged setup, never implicit apply hooks.
Authority: isolated chezmoi rendering, scoped pytest, Samba testparm, actual
authenticated SMB read/write and denied-access checks. Release is not applicable
because no package is published. All kernel, review, deploy, operate and
maintenance gates are required and pending.


The context README is the authoritative behavior, trust and recovery contract.
