# Remote Owner Overlay (RRW-007B / F02)

## Authority, profile overrides and ownership

The owner's 2026-11-07 INT-075 decision extends INT-043 under merged coordinator
#495. This successor supersedes the historical Yazi-only scope in README/PROFILE;
other profiles and previous delivery evidence retain their original contracts.
Risk is elevated: executable/plugin supply chain, identity and credential-helper
preservation. Python, shell and security modules apply. Required gates include
the Development Kernel, Review/Integrate, disposable Deploy/Operate and
Maintain/Retire. No standalone package release is produced.

The overlay is optional, explicitly per user, after foundation readiness. Never
infer enrollment or identity from OS Login. Foundation retains Bash startup,
Starship binary/init/default config, agent runtimes and authentication tools.
Fork A owns live pins, preview, approved rollout/apply and VM operations. This
source does not authorize them, and never copies credentials between users.

## Inputs and Git identity

Use explicit local `[data]` values: `machine_type = "remote-workspace"`, `name`,
`work_email`, `personal_email`. The existing `email` initialization field remains
for compatibility but is not a routing fallback. Identity values are local data,
not committed public defaults. Fork A selects the optional source repository
and full merged pin separately from foundation; no new foundation feature flag
or automatic source enrollment is added.

Manage four private `~/.config/git/remote-workspace*.inc` files. A bounded native
Git updater adds only their top-level include path, once. Never manage
`~/.gitconfig` or alter gh credential-helper entries. Preserve unrelated global
settings, unknown includes and repeated-apply bytes. Refuse unsafe global paths,
symlinks/hardlinks, malformed config and invalid identity inputs.

Native `includeIf hasconfig:remote.*.url` routes GitHub `mgmri-dge` and
`Superformula` remotes to work email, and `Saltiola7` to personal email. Cover
HTTPS and SSH/scp URL forms. All remotes are considered; mixed work/personal
ownership clears identity and fails commit selection rather than choosing an
incidental remote order. Unknown ownership is also unconfigured. Native
repository-local identity overrides still follow Git precedence.

## Pinned tools and shell

Ship checksum-verified x86_64 user-local zoxide 0.10.0, direnv 2.38.2,
ripgrep 15.2.0 and Neovim 0.12.6, including Neovim's matching runtime.
The owner additionally approved private tree-sitter CLI 0.26.1 as the locked
editor's required build dependency; no npm or Rust toolchain is added. Exact
release URLs/hashes live in `~/.config/remote-workspace/tools.json`.

Verify downloaded bytes before extraction. Use retained tool generations under
`~/.local/share/remote-workspace/tools/`, with inventories checked on reapply.
Four user commands link from `~/.local/bin`; the build CLI links only from
`~/.local/libexec/remote-workspace/tree-sitter`. Refuse unknown existing regular
binaries or foreign links rather than silently replacing owner work. Keep older
generations; cleanup is not part of apply. Tampered inventories/generations fail.

The owner prompt is `~/.config/remote-workspace/starship.toml`, selected with
`STARSHIP_CONFIG` by `~/.bashrc.d/40-remote-workspace.sh`. Foundation still owns
`~/.config/starship.toml` and the one Starship initialization. The snippet supplies
only portable `vim=nvim`, `python=python3`, `py=python3` aliases, private CLI PATH,
and guarded zoxide/direnv hooks. Do not manage `.bashrc`, source the whole personal
profile, run `direnv allow`, or include awslogin, GUI `sf`, credential-backed `ch`,
duplicate mise/Atuin/Starship initialization or terminal-scanner side effects.

## First-open AstroNvim readiness

Deliver the owner's committed `private_dot_config/nvim` and unchanged
`lazy-lock.json`. Bootstrap Lazy at its locked commit, retaining locked branch
metadata. Refuse dirty existing plugin repositories; do not reset owner changes.
Headless setup explicitly enables plugin loading, restores locked plugins and
verifies every selected plugin SHA. Lock drift or startup errors fail apply.

Await builds for bash, python, lua, vim, vimdoc, json, yaml, toml, markdown and
sql, including dependencies selected by the locked Treesitter generation (such
as markdown_inline). Require the install result to succeed and load each actual
compiled file under a fresh validation alias, avoiding a builtin parser false
pass. Then require a second real owner-config startup without installation work.
The host supplies gcc, g++ and make. Other language parsers and Mason servers
remain on demand; the remote-only plugin override disables eager Mason installs.

Setup publishes a private editor readiness/file manifest only after success.
Do not interpret script-text tests as native parser proof. Missing compilers,
download/restore/build failures, timeout, plugin mismatch or invalid libraries
block apply. Keep diagnostics bounded; native plugin output can contain private
paths. Operator review is required for local work or changed managed locks.

## Qualification, rollback and maintenance

Before any live owner apply, compare the exact final merged foundation/overlay
managed sets and actual installed/runtime file manifests. Shared directories are
allowed; shared file ownership, ancestor replacement and redirected links are
not. The Git include update is native integration, not ownership of global Git.
Keep foundation-managed file hashes unchanged across overlay apply/rollback.

Required evidence: explicit Git routing and mixed/unknown rejection; synthetic
post-login gh state with native setup-git/credential fill before and after two
applies (network blocked for credential calls); exact asset/hash/version checks;
headless locked plugin restore and real parser builds/loads; second-start/reapply
checks; shell guards and alias selection; existing-profile rendering; configured
full pytest and affected Python analysis; native UBI10 paired apply/rollback.
Live VM/SELinux/systemd acceptance remains separate. Current exact results and
gate exceptions belong in the cycle, not an assumed source-level pass.

Rollback touches only overlay-owned files and preserves global Git helpers,
history, keys, source state and unrelated files. Never recursively delete shared
plugin/cache storage to repair a failure. Maintain release hashes, compiler/CLI
compatibility and plugin lock together. Final handoff reports both merged SHAs,
bootstrap checksum, exact inputs and completed native evidence.

## Visual Evidence

| Concern | Decision / review question |
|---|---|
| Boundary | required: flow table; which source owns each file? |
| Interaction | required: flow table; what completes before first open? |
| State | required: flow table; how are existing helpers preserved? |
| Data/trust | required: flow table; where do identities and downloads enter? |
| Schema | not_applicable: scalar local inputs and existing native formats |
| Dependency/deployment | required: flow table; what must qualify before apply? |
| Quantitative | not_applicable: no benchmark claim |

| Input/action | Owner | Output / invariant |
|---|---|---|
| Explicit foundation setup | Foundation | Shared shell, Starship and agents |
| Explicit identities + GitHub remotes | Overlay includes/native Git | Routed identity; native gh helper retained |
| Reviewed asset hashes | Overlay installer | Four commands, private build CLI and retained runtime generations |
| Owner lock + compiler prerequisites | Headless setup | Locked plugins and loadable required parsers/dependencies |
| Optional owner snippet | Overlay | Portable hooks and separate prompt; no shared-file takeover |
| Exact final source/file inventories | Paired validator | Disjointness before live owner apply |

**Text Equivalent:** Foundation owns shared startup and Starship. The optional
overlay consumes explicit identity data and verified assets, retains gh helpers,
restores the owner's locked editor and builds parsers before first open. Exact
file disjointness is a precondition for live apply. Canonical sources: allowlist,
installers, owner lock and paired tests. Owner: personal dotfiles maintainer.
Update whenever routing, ownership, dependencies or setup ordering change.
