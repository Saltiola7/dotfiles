# Local MGM Bedrock retirement

## Authority and scope

This approved retirement contract supersedes the active-deployment requirements
in the historical aws_creds README for the coordinated desktop-controls slice.
Owner: dotfiles maintainer. Home: personal dotfiles repository. The existing
refresh wrapper, LaunchAgent and reactive SketchyBar auth implementation remain
available as inactive source for possible Vertex adaptation. No Vertex behavior
is implemented here.

Remove only this Mac's MGM/Bedrock setup. Preserve the Backblaze B2 profile and
credentials, shared AWS CLI, unrelated AWS profiles and caches, browser sessions,
1Password data and every cloud resource. Do not use global `aws sso logout`,
delete the whole AWS directory, or uninstall a CLI shared with Backblaze.

## Engineering and security profile

Internal long-lived macOS configuration; Bash, chezmoi templates and bounded
Python stdlib credential-file handling. Elevated risk; Security module required.
Assets are local SSO/session credentials and unrelated Backblaze credentials.
Trust boundary: managed source must not consume, print, copy into Git or expose
live secret values. Use exact profile/session ownership and cached account/session
attribution. Unknown or shared cache ownership is preserved and reported as a gap.
No network authentication, cloud mutation, privileged installer or new dependency.

Authorities: existing pytest fixture checks, shell syntax, chezmoi render/diff,
launchctl service status, source review and metadata-only local postconditions.
The accompanying host profile supplies gate applicability and delivery ownership.

## Behavior and contracts

- Given the old LaunchAgent or reactive poller is deployed, retirement unloads
  and disables the exact MGM service, removes the AWS bar item, and stops only
  positively identified MGM auth processes. Subsequent login, reload or chezmoi
  apply cannot restart the retired automation.
- Given shared AWS configuration, remove only the MGM Bedrock profile and its
  now-unreferenced SSO session. Preserve all unrelated sections and credentials.
  Validate inputs before mutation, write config atomically with restricted
  permissions, and refuse symlinks/ambiguous ownership rather than following them.
- Given attributable MGM SSO/CLI caches, delete only those entries. Never print
  credential contents. Unmatched entries survive. Missing files are an idempotent
  success; malformed configuration aborts before writes.
- Given future Vertex work, the old CLI wrapper, LaunchAgent definition and
  reactive auth source remain in repository-only archive paths. They are neither
  installed on PATH nor sourced by the active bar or startup hooks.
- Given new shells, no default MGM AWS profile/region or `awslogin` alias is set.
  Existing shells may retain inherited values; report that they need restarting.

## Affected paths and ordering

Own `dot_common_profile.tmpl`, `dot_xonshrc.tmpl`, AWS source under
`private_Library/LaunchAgents`, `dot_local/bin`, SketchyBar items/plugins, the
AWS load hook, `.chezmoiignore`/`.chezmoiremove`, a bounded retirement helper/hook,
`docs/_archive/aws-auth/`, focused retirement tests and context completion docs.
The coordinated host slice owns the shared `sketchybarrc` include removal.

Order: preview exact targets; disable/unload the MGM service and prevent poller
execution; remove managed MGM runtime entries; remove attributable local config
and caches; apply shell defaults; reload and inspect. Deployed configs and archive
source must agree that retirement is permanent until explicitly redesigned.

## Validation and recovery

Fixture checks must prove that mixed MGM/Backblaze configuration preserves B2
values, unknown caches survive, malformed input and symlinks fail safely, repeated
retirement converges and no active source path can reload the archived automation.
Run existing shared-shell ownership/startup tests when editing their templates.
Live checks inspect only profile names, equality postconditions and service/item
presence. No actual cloud call is required to prove local retirement.

Credential deletion is intentional and not backed up into Git or logs. Reuse
would require explicitly restoring configuration and authenticating again;
archived code alone cannot recover deleted tokens. Cloud-side sessions are not
claimed revoked by local cache deletion. Generic AWS CLI remains available for B2.

## Visual Evidence

Interaction: required, ordered table below. Boundary, state, data/trust, schema,
dependency/deployment and quantitative: not_applicable; exact local ownership,
preservation and recovery constraints above are clearer than an additional diagram.

| Step | Authority | Observable postcondition |
| --- | --- | --- |
| Disable scheduling and polling | launchctl and managed bar source | No new MGM auth execution |
| Remove active targets, preserve source | chezmoi and Git archive | Source retained; runtime entry points absent |
| Prune exact local identity | Validated local config/cache metadata | MGM gone; Backblaze unchanged |
| Reload and inspect | launchctl, SketchyBar and shell configuration | Retired paths stay inactive |

Text Equivalent: disable MGM execution first, preserve code outside deployment,
remove only attributable local identity, then verify that reload cannot reactivate
it and Backblaze is unchanged. Source: this contract; owner: dotfiles maintainer;
update trigger: a change to deletion scope, ownership or deployment ordering.
