# Changelog: herdr_remote_access

All notable changes to this bounded context.

## [2026-11-19]

### HERDR-REMOTE-001 — Outcome

- Uniform `herdr --remote <alias>` attach: one `private_dot_ssh/private_config.tmpl`
  renders the five MagicDNS aliases identically on every controller
  (mbp-omarchy, try-omarchy, mac-mini); legacy macOS globals and operator
  `config.d/*` fragments render behind stat/darwin guards.
- Raw tailnet address removed from public source; encrypted `id_rsa` stays
  darwin-scoped and never renders on Linux controllers.
- Validation: red/green `ssh -G` alias probes; targeted chezmoi apply on all
  three controllers (mode 600); cross-controller transport probes rc=0;
  attach chains reached running Herdr servers on mbp-omarchy, old-omarchy,
  try-omarchy and mac-mini (harness TTY limit stops at rendering, operator
  visual smoke pending); repository suite 884 passed / 14 skipped; CI green
  on branch `herdr-remote-001` at `a6d7106`.
- Exceptions: hp-omarchy attach pending operator enablement (Tailscale SSH
  `sudo tailscale up --ssh`, herdr install, one `ssh -t hp-omarchy herdr`
  server start); visual TUI smoke per alias pending operator terminal.
- Gate commits: `8ab42af`, `2631ed3`, `86c4285`, `a6d7106`.
- Deployment: applied on three controllers; host keys accepted per alias;
  cross-controller public keys wired (try, mbp, mac-mini).
- Final Push: draft PR from `herdr-remote-001` into `main`; result reported
  after push.
