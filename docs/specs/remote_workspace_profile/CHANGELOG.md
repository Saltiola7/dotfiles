# Remote Workspace Profile Changelog

## 2026-11-07 — Owner overlay expansion (RRW-007B / F02)

- Add explicit work/personal Git routing through private includes without taking
  over global Git or gh helpers. Add four checksum-pinned tools and the separately
  approved private tree-sitter build CLI, owner-locked AstroNvim/parser readiness,
  portable aliases/hooks and a separate STARSHIP_CONFIG. Preserve foundation
  ownership and other profiles. Exact native/paired evidence remains in the cycle;
  live pin, rollout and apply remain Fork A's responsibility.

## 2026-11-04 - RRW-002B RHEL owner overlay qualification

- Added native UBI 10 qualification and profile checks for the explicit
  Yazi-only overlay: target-disjoint installation over the shared foundation,
  preserved macOS/`lmsh` renders, checksum proof, empty second apply and
  rollback preservation.
- Final paired qualification pins the shared foundation to the merged RRW-002
  runtime revision `b8043183c403e49be774d6dbac4cb77c446e9820`; the earlier
  unmerged pin is historical.
- The first UBI run failed because the image lacked `diffutils` for the smoke's
  `cmp` comparison. A supervised mechanical repair added the package to the CI
  container only; overlay behavior and test assertions are unchanged.
- No owner apply, colleague acceptance, live RHEL readiness or credential change
  is claimed; live owner apply remains separately approved.

## 2026-11-02 - RRW-002B RHEL Successor Discovery

- Defined RHEL 10 x86_64 and UBI 10 userland qualification for the existing
  explicit Yazi-only overlay under `rhel-remote-workspace` /
  `rrw-002b-rhel-owner-overlay`. Shared tools, authentication and Atuin history
  remain owned by the separate public foundation.
- Require target-disjointness, preserved macOS/`lmsh` renders, checksum proof,
  empty second apply and rollback preservation. Historical CentOS qualification
  remains recorded; UBI proof cannot establish full live RHEL readiness.
- Discovery only: no installer, target, credential, user home or live runtime
  changed. Implementation, receipt/preflight/exact approval and eventual explicit
  owner apply remain pending. No Gate Exception or colleague acceptance claimed.
- Local Python 3.14 overlay checks passed (4), including cross-source target
  disjointness with an explicit clean shared checkout. The full local suite had
  718 passes and 12 unrelated desktop-startup failures because the Linux fixture
  requires `/usr/bin/bash`, absent on macOS. Linux CI/full-suite acceptance
  remains separate; neither UBI nor live RHEL qualification is claimed.

## 2026-09-01 - Owner Yazi Overlay

- Added explicit `machine_type=remote-workspace` rendering for only Yazi
  package/theme configuration, the locked flavor, and checksum-pinned x86_64
  Yazi, `ya`, fd, fzf, and 7-Zip installation.
- Proved empty rendered and installed intersections with `dotfiles-ai` commit
  `58833a2`, unchanged macOS and `lmsh` rendering, an empty second apply, and
  rollback preservation in disposable CentOS Stream 10 x86_64.
- Full repository pytest passed with 181 tests. No gate exception, release, or
  live owner deployment occurred. Implementation Gate Commit: `d41c639`.
  Intended delivery is a draft pull request to `Saltiola7/dotfiles` `main`.

## 2026-09-01 - Yazi-Only Ownership Readiness

- Assigned Bash, Atuin, and Starship exclusively to the shared `dotfiles-ai`
  foundation and narrowed the personal remote overlay to Yazi configuration,
  flavor, and portable dependencies.
- Required empty rendered and installed target intersections, x86_64 checksum
  proof, idempotency, and rollback without deleting history or authentication.
- No target, user home, credential, history, or runtime changed. RWUE-003 is
  ready for a fresh digest-bound receipt and approval.

## 2026-08-31 - Discovery Contract

- Defined the owner-only CentOS Stream 10 x86_64 terminal overlay, explicit
  activation, deny-by-default target ownership, owner-local Atuin endpoint, and
  rollback behavior. The later closure-readiness decision supersedes its
  overlapping Bash, Atuin, and Starship target set.
- Required zero overlap with `dotfiles-ai` and retained credentials, encryption
  keys, history, account identity, and tailnet identity outside Git and rendered
  shared configuration.
- No personal targets, remote homes, credentials, services, or runtime state
  changed. Implementation remains dependency- and approval-gated.
