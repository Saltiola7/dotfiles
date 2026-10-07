# Host tool maintenance

Engineering Profile: [PROFILE.md](PROFILE.md). Authority: SSD toolchain recovery
Initiative in dotfiles-ai, INT-003, INT-012 and INT-022. Current slice:
host-sdk-shell-resolution. Risk: elevated; delivery: draft PR and targeted host
deployment. No unresolved product decision remains for this bounded slice.

## Outcome and scope

Select the already-installed standalone Google Cloud SDK consistently in fresh
Bash and Zsh interactive and noninteractive login shells. The standalone SDK owns
the invoked commands; chezmoi owns PATH declarations. The primary's uncommitted
changes are independent evidence and must not be overwritten.

This slice writes only dot_common_profile.tmpl, dot_zprofile.tmpl, affected tests,
and this context's documentation. It does not install, uninstall or update either
SDK, modify cloud accounts, contact cloud services, change uv selection, alter AI
launcher guards, remove Colima hooks or activate guests. Those remain later work.

## Behavior and contract

| Given | When | Required outcome |
|---|---|---|
| Healthy SDK under HOME/google-cloud-sdk | Fresh Bash or Zsh login shell starts, interactive or not | gcloud resolves to that SDK before Homebrew |
| SDK bin already occurs later in inherited PATH | Shell initializes | Standalone precedence is restored, not skipped because the entry exists |
| No executable standalone gcloud | Shell initializes | No nonexistent SDK directory is introduced and existing selection survives |
| Shell initializes repeatedly | PATH is evaluated | Effective SDK selection remains stable; no network or installer runs |
| Managed AI guards and external state | SDK PATH changes | Existing OpenCode/Codex guards and state variables retain their behavior |
| Linux/guest overlay | Configuration renders | No new macOS SDK activation is introduced |

Use native PATH assignment guarded by executable presence. Avoid adding aliases,
functions, wrappers or installing dependencies. Do not source the full interactive
common profile merely to fix noninteractive Zsh; limit its login-file change to
the SDK path. Preserve existing completion setup. A bare non-login shell inherits
its caller's environment; do not introduce BASH_ENV or Zsh global startup hooks.

## Validation and deployment

Before implementation, reproduce the inherited-PATH failure using fake executable
directories and isolated HOME, without real cloud credentials. Cover both shells,
present/absent SDK, and repeated initialization. Run affected pytest suites:
tests/test_terminal_environment.py and tests/test_ai_config_ownership.py plus the
focused regression. Validate rendered Bash/Zsh syntax. Real host validation checks
command resolution only; do not invoke kubectl or cloud authentication.

Deploy only reviewed common-profile and Zsh-profile targets after reconciling the
existing MISE_DATA_DIR hunk; preserve it even though it is outside this slice.
Retain preimages before targeted apply. A second targeted apply must be empty.
Rollback restores only those configuration preimages after checking for newer
edits; no credentials, databases, SDK installations or sessions are replaced.

## Gate ledger

Domain, Behavior, Spec, Contract, Test-driven implementation, Refactor,
Review/Integrate, Deploy, Operate and Maintain/Retire: required, pending.
Release: not_applicable; no published package. No gate exception is requested.

## Visual Evidence

State: required; the behavior transition table above is canonical.
Boundary, interaction, data/trust, schema, dependency/deployment, quantitative:
not_applicable; bounded source ownership and ordered validation are explicit prose,
with no new data transport, persistent schema or runtime topology.

**Text Equivalent:** when a healthy standalone SDK exists, shell initialization
gives it precedence even if inherited PATH already contains it. When absent,
initialization preserves existing selection. No installer or cloud operation runs.
Owner: dotfiles maintainer. Update this table when shell or selection scope changes.
