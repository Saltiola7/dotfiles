# Try Omarchy: recover Herdr panes at graphical login

Scope: personal `omarchy-try` Linux workstation. The user manager owns Herdr's
lifetime; personal chezmoi owns its graphical-login dependency and interactive
Bash configuration. The existing private pane map and installed OpenCode client
remain operator-owned. Remote-server timers are a different profile.

## Behavior and contract

| Given | When | Result |
|---|---|---|
| Previous login entry is a managed regular file | The reviewed guest targets are applied | `graphical-session.target.wants/herdr-pane-reconcile.service` becomes a relative symlink to `../herdr-pane-reconcile.service`. Applying it does not run the oneshot. |
| Graphical login, mapped layout | The oneshot runs after `herdr.service` | Fill missing tabs/splits in uniquely identified workspaces. Never send keys, signal clients, or run commands inside existing terminals, even on repeat invocation. |
| Fresh interactive Herdr Bash in the default session | Its own startup child proves the root shell PID, foreground terminal, unique workspace/tab, pane ordinal, working directory and a valid local session mapping | Start the existing direct OpenCode binary with the exact session ID as an argument. On exit Bash continues. No terminal input, agent prompt or automatic permissions. |
| Occupied pane, nested shell, noninteractive shell, unknown layout, missing map, unmapped/external directory or ambiguous identity | Login or shell startup | Leave the running program or shell alone. A failed lookup must not fall back to the focused pane, a guessed workspace ID or another directory. |

An already-interactive shell does not need to surrender its terminal for recovery.
Herdr 0.9.5 implements `pane run` as text plus Enter, not an atomic idle check.
The service therefore owns layout only; the first interactive Bash startup owns
its own optional client launch. The map stays private and the source owns no
session IDs or per-machine absolute paths. Missing clients and unsupported shells
remain usable as shells. This is graphical-login recovery, not headless boot.

## Rollout and rollback

Use the personal source. Preview the helper, compatibility command, guest Bash
file, oneshot and login link together. Install the safe executables and unit
before enabling the link. Reload the Linux user manager without starting the
oneshot or restarting Herdr. Check the link with `readlink` and the dependency
with `systemctl --user show graphical-session.target -p Wants`. Verify a real
login separately when the operator chooses; never trigger it to test a patch.
To retire recovery, remove the login dependency and the guest Bash hook before
retiring helpers. Do not restore the former input-sending helper to an enabled
unit. Preserve the private map, Herdr state and all OpenCode sessions.

## Visual Evidence

State, boundary and interaction: required, the transition table above. **Text
equivalent:** chezmoi installs the login link; the user service repairs layout;
only a newly starting, identified root shell can launch its mapped client. All
other panes retain their contents. Data/trust: the private map is read locally,
never copied into public evidence. Schema, deployment diagram and quantitative
chart: not applicable; no map format change, additional service or metric. The
host-maintenance owner updates the table when selection or startup changes.
