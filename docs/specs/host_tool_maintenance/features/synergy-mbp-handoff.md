# Handoff: Synergy/Waynergy for mbp-omarchy (and Try Omarchy) — 2026-11-16

Status: FAILED to add mbp-omarchy to the mini's Synergy 3 server. This note
records everything the next session needs so it does not re-derive it.

## Topology

- **mac mini M4 Pro** (`tis@mac-mini`, tailscale 100.73.117.118, LAN
  192.168.100.95) — main work machine, macOS + Backblaze + **Try Omarchy VM**
  (UTM; the VM's `machine_type` is `omarchy-try` in this repo). Runs the
  **Synergy 3 server** (com.symless.synergy3, TLS, port 24800).
- **HP omarchy** (`tis@omarchy`, tailscale 100.86.125.94) — working synergy
  client, screen name `omarchy-5849dc63`, via `omarchy-waynergy.service`.
- **mbp-omarchy** (`tis@192.168.100.86` LAN, tailscale 100.108.46.101, M1
  MacBookPro17,1) — daily driver. Waynergy client BUILT, INSTALLED, and
  running (`omarchy-waynergy.service`), reporting name `mbp-omarchy`
  (via `waynergy_client_name` data key). Cannot connect: the server does not
  know its screen name.

## Server mechanics (verified)

- Server config: `~/Library/Preferences/Synergy/synergy.conf` — **generated
  artifact**, regenerated from the GUI database whenever the synergy3 service
  (re)starts the core. Hand edits survive a bare `pkill synergy-core` respawn
  but die on `launchctl kickstart` of the service. Editing it is a dead end.
- GUI database: Electron Local Storage LevelDB under
  `~/Library/Application Support/Synergy/` — locked/binary; not touched
  (the working HP integration depends on this app staying healthy).
- TLS: server cert `~/Library/Preferences/Synergy/synergyCert.pem`;
  client-fingerprint allowlist **`~/Library/Preferences/Synergy/tls/trusted-clients`**
  (plain file, live-reloaded per connection, format `v2:sha256:<UPPERCASE-SHA256>`
  per line). The mbp-omarchy fingerprint `D8808C84...DF84A2` IS added and the
  TLS handshake passes; only the screen-name lookup fails after it.
- Server log: `~/Library/Logs/Synergy/synergy.jsonl` (shows
  "unrecognised client: mbp-omarchy" after TLS passes).

## What was tried and failed on the Synergy 3 GUI (mini)

1. Add computer by bare name `mbp-omarchy` — "hostname failed" (name resolves
   fine via Tailscale MagicDNS, so the dialog is NOT doing system DNS; likely
   probing for a listening client).
2. `mbp-omarchy.local` — rejected.
3. Adding by IP (`100.108.46.101`) — rejected.
4. Holding a dummy TCP listener on the MBP's 24800 during the add (nc loop) —
   still rejected. The probe is not a plain TCP connect, or validation is
   stricter.
5. No free-text screen/grid editor exists in this build ("drag a screen" is
   not available); the HP's entry predates whatever the GUI now requires.
6. `synergy-core.conf` `externalConfig=true` — see generated artifact above.

## What works on the client side (mbp-omarchy)

- `waynergy-omarchy 0.0.17-4` builds on aarch64 (PKGBUILD arch fixed, PR #83).
- `omarchy-waynergy.service` enabled; config `~/.config/waynergy/config.ini`
  with `name = mbp-omarchy`; server cert pinned at
  `~/.config/Synergy/synergyCert.pem` -> `~/.config/waynergy/tls/cert`.
- Fingerprint approved server-side. The ONLY missing piece is the server
  screen entry.
- Do NOT regenerate certificates in the Synergy GUI — it invalidates every
  client's trust at once.

## Avenues for the next session (in order of promise)

1. **Try Omarchy VM as the client instead** (user's suggestion): the VM runs
   Hyprland and this repo carries the `omarchy-try` machine_type with its own
   input/guest integration preserved. Try adding a screen for the VM — if the
   GUI rejects it too, the blocker is confirmed app-side and version/general,
   not name-specific.
2. **Identity reuse test**: have a client report the already-trusted name
   `omarchy-5849dc63` (waynergy `name =` config) with the HP offline. If the
   server accepts it, the screen-name gate is the only blocker and cloning
   identity is viable short-term (unacceptable long-term: name collision).
3. **Synergy 3 update/downgrade**: the GUI's add flow may be a regression —
   check Symless release notes; the HP entry proves an older flow allowed
   arbitrary names.
4. **Alternative**: gliff PR #135 (VNC client for gliff) would obsolete the
   mini-side Synergy dependency for this link entirely. Also worth checking
   whether Synergy 3 exports/imports server configs (a settings export from a
   machine where a screen CAN be added, edited offline, re-imported).
5. If everything fails: mbp->mini control already works via RustDesk
   (raw scancodes + Colemak DH layout swapped on the mini's menubar), and
   mini->mbp works via RustDesk reverse (MBP global layout is fi, matching
   the mini keyboard). Those are the working fallbacks today.

## Related repo state (all merged)

- PR #83/#84/#85/#86/#87: waynergy aarch64 build, apply-integration
  (`run_always_install-waynergy.sh`), omarchy allowlist re-includes,
  run_always semantics for TTY-gated scripts.
- `run_always_disable-fcitx5-mbp.sh`, uwsm env: fcitx5 fully retired on
  mbp-omarchy (it rewrote typed symbols).
- Backlog: SYNERGY-MBP-TRY-001.
