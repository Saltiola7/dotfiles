# Self-hosted Atuin

The Mac Mini runs Atuin `18.17.1` in Colima with SQLite. Docker publishes only
to Mac loopback; Tailscale Serve owns tailnet HTTPS at
`https://mac-mini.tail62e96c.ts.net`. Client databases, keys, sessions, server
state, and backups stay outside Git.

## Deploy

Inspect storage before starting the existing Colima profile:

```sh
colima start
docker system df
mkdir -p ~/.local/share/atuin-server
docker compose -f ~/.config/atuin-server/compose.yaml config
ATUIN_OPEN_REGISTRATION=true docker compose \
  -f ~/.config/atuin-server/compose.yaml up -d
curl -fsS http://127.0.0.1:8888/healthz
tailscale serve --bg --https=443 http://127.0.0.1:8888
```

Use a disposable account and isolated HOME before migrating production. Verify
Mac and both Lima clients can sync harmless commands through the tailnet URL.

## Migrate

1. Sync the hosted client and back up `~/.config/atuin` plus
   `~/.local/share/atuin`.
2. Store `atuin key` in 1Password without logging it.
3. Change the client endpoint, log out without deleting the hosted account, and
   register the production account on this server while retaining the key.
4. Sync existing records and verify representative history from a second client.
5. Restart Compose without `ATUIN_OPEN_REGISTRATION=true`; the default is false.

The client does not dual-write. Keep the hosted account and pre-cutover backup
until cold restore passes.

## Operate

```sh
docker compose -f ~/.config/atuin-server/compose.yaml ps
curl -fsS http://127.0.0.1:8888/healthz
tailscale serve status
```

When the server is unavailable, clients continue local capture and search and
upload durable local records after service returns. Do not copy active client
Atuin state between machines.

## Backup And Restore

Stop the container, archive the complete server directory, restart it, and keep
the archive outside the Mac Mini. Copying only `atuin.db` while WAL is active is
not a valid cold backup.

```sh
docker compose -f ~/.config/atuin-server/compose.yaml stop
tar -czf /approved/off-host/path/atuin-server-$(date +%Y%m%d%H%M%S).tgz \
  -C ~/.local/share atuin-server
docker compose -f ~/.config/atuin-server/compose.yaml start
```

Restore only while stopped and validate the restored directory with a separate
container and `/healthz` before replacing live state.

## Retire

Sync every client, take a final cold backup, stop the container, clear Tailscale
Serve, revoke sessions, and retain or delete encrypted SQLite state according to
the operator's explicit decision. Never delete the hosted account or encryption
key as part of routine service retirement.
