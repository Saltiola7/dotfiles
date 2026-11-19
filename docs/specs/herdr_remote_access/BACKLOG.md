# Backlog: herdr_remote_access

**Last updated:** 2026-11-18

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| HERDR-REMOTE-001 | Managed SSH alias config for uniform `herdr --remote` attach across controllers and targets | high | pending | - | `private_dot_ssh/private_config`, `docs/specs/herdr_remote_access/` | `docs/specs/herdr_remote_access/PROFILE.md` | no | single config file plus spec; one owner keeps stanza set identical | M | ssh -G probes, chezmoi diff/apply, live attach smoke |

## Parallel Execution Guide

Tasks that can be worked concurrently (no shared dependencies):

- none; single active item

Tasks that must be sequential (shared models/contracts/migrations):

- HERDR-REMOTE-001 owns the only managed config file; any future alias
  additions serialize behind it.

## Completed

| id | outcome | completed | commit |
|---|---|---|---|
