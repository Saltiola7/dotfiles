# Singleton Raindrop MCP connector

Owner: dotfiles maintainer. Method Revision: 3.29. Context: host tool maintenance.
Engineering Profile: [../PROFILE.md](../PROFILE.md). Risk: routine. Modules: core
and Python for isolated regression tests. Delivery: managed local launcher,
feature-branch draft PR and explicitly scoped host activation.

## Domain and scope

The existing Raindrop bridge translates local MCP stdio to the authenticated
Raindrop HTTP endpoint using the already-cached mcp-remote 0.15.2 package. Each
client launch currently keeps an npm launcher and Node connector alive. Repeated
clients multiply those long-lived processes even when their sessions are idle.
A connector lease admits one live bridge per authentication cache. A contender
exits immediately instead of opening another connector or waiting in a queue.

The lease belongs to the directly executed Node connector, not a separate shell,
npm parent, persistent watchdog or new background service. The installed runtime,
proxy package, endpoint, HTTP-only transport, authentication timeout and credential
cache keep their current owners and meaning. No package is downloaded or installed.

Owned files: dot_local/bin/executable_raindrop-mcp, tests/test_raindrop_mcp.py,
this feature and the bounded context README/CHANGELOG. Codex configuration is a
separate narrow activation step owned by the primary after review. No global
configuration, unrelated MCP, profile, dependency, token content or backup state
is changed by implementation.

## Behavior

| Given | When | Required outcome |
|---|---|---|
| Warm pinned package cache and no owner | Client launches connector | Transient offline resolution exits, then launcher PID becomes the single Node bridge |
| Existing owner holds the lease | Another client launches | Contender exits with status 75 before invoking npx or touching authentication |
| Current bridge owns descriptor 9 | Its startup shell has already execed | Descriptor and exclusive lease remain attached to the Node PID |
| Bridge receives stdio EOF or SIGINT | Bridge exits | Lease releases; next launch succeeds using the retained lock inode |
| Bridge is killed with SIGKILL | Kernel closes its descriptors | Next launch succeeds without stale-PID cleanup or a leftover guardian |
| Pin is absent from extracted cache or resolver fails | Client launches | Clear stderr failure, no network installation, no long-lived child and no MCP stdout noise |
| Explicit authentication-cache environment exists | Connector launches | Same cache value reaches proxy; no alternate sign-in directory is selected |
| No explicit authentication-cache environment | Connector launches | Export the documented Codex-home fallback consistently for lock and proxy |
| Caller is inside an arbitrary repository | Connector resolves package | Resolver uses private cache directory; final proxy retains caller working directory |
| Unsupported host, missing tool, invalid directory or unusable executable | Client launches | Fail clearly before proxy starts; preserve credentials and unrelated files |

## Interface

`raindrop-mcp` takes no arguments. It executes the resolved package entry point
with these existing arguments, preserving their order:

```text
https://api.raindrop.io/rest/v2/ai/mcp --transport http-only --auth-timeout 300
```

`MCP_REMOTE_CONFIG_DIR` remains unchanged when explicitly set. When absent or
empty, export `${CODEX_HOME:-$HOME/.codex}/mcp-auth/raindrop`. The cache directory
must be absolute; reject a relative directory instead of changing where existing
credentials resolve. Production activation retains
`/Volumes/ext/state/codex/home/mcp-auth/raindrop`.

Inside that cache, keep `raindrop-mcp.lock` and open it privately without truncating
or unlinking its inode. Use native macOS `lockf -s -t 0 9` against inherited file
descriptor 9. Successful lock acquisition precedes every npx invocation. A busy
lease returns 75 without a resolver or proxy. Do not treat lock ownership as an
MCP multiplexing service: a second simultaneous client is intentionally rejected.

Resolve the already-installed entry point using the pinned, offline, noninstalling
command below from a subshell whose working directory is the authentication cache:

```text
npx --offline --no --package=mcp-remote@0.15.2 --call 'command -v mcp-remote'
```

Require one absolute, executable result. npm documents exact matching for specified
package versions; `--no` rejects missing packages and `--offline` disallows network
resolution. Never add `--yes`, fetch a replacement, run an installer, or choose
an unpinned global entry point on failure. A prewarmed extracted cache is an
operational prerequisite; cold-cache provisioning remains a separately authorized
existing package-owner task.

After the resolver exits, execute that entry point directly with `exec` and the
fixed arguments. Its existing Node shebang selects the installed Node runtime.
Descriptor 9 must survive both transitions and remain open on that same PID. Stdin,
stdout and stderr remain the MCP client's streams; launcher diagnostics use only
stderr and never print tokens, authentication JSON, headers or arbitrary resolver
output. The resolver subshell must not change the final proxy's working directory.

## Contracts and validation

The operating system owns lease lifetime. Never remove or replace a live lock
file, maintain a PID liveness heuristic, or release the lease before Node exits.
Retain the inode across normal and abnormal exits. A queryless contender must
finish promptly without starting npm or Node. Failed resolution and exec must
release all launcher ownership naturally, allowing recovery on a later attempt.

Run configured pytest with isolated HOME/cache fixtures and fake offline resolver.
Use the actual installed Node interpreter to verify `fs.fstatSync(9)`, lock-file
identity, launcher-to-Node PID equality and lease ownership. Exercise concurrent
launches, resolver failure, empty/relative/nonexecutable output, missing tools,
unchanged argv/cache/cwd, EOF, SIGINT and SIGKILL recovery. Tests never read live
credentials or contact Raindrop. Before source implementation, demonstrate failing
regression evidence. Validate Bash syntax, diff cleanliness and targeted chezmoi
rendering. Native macOS locking is authoritative; portable CI may provide an
equivalent inherited-descriptor lock adapter when lockf is absent.

## Deployment, operation and rollback

The primary preserves source, installed launcher and native configuration
preimages. Recheck freshness before each targeted source reconciliation and
chezmoi apply. Install only the reviewed launcher; preserve unrelated dirty source
and never apply all dotfiles. Configure the native client to use the installed
launcher with no arguments and the same explicit authentication-cache environment.

Existing running MCP contexts keep their old process command until their owner
restarts or refreshes that context. Changing configuration does not replace live
connectors. Do not kill unrelated sessions or delete auth state. Before activation,
the primary must account for existing legacy bridges and coordinate their scoped
closure so they cannot coexist outside the new lease.

After activation, inspect the actual long-lived bridge PID: no persistent npm or
shell guardian, descriptor 9 references the retained lock, one live connector,
and a second invocation fails before resolution. Verify authenticated MCP
initialization and a read-only tool listing without printing credentials. Record
health, startup error path, owner and rollback evidence in the private Cycle Record.

Rollback restores only matching launcher/configuration preimages after checking
for newer edits. Close the owned connector before switching launch methods; do
not remove the lock inode while any new connector may still own it. Preserve
credentials, package cache and unrelated connectors. Native macOS owns lockf;
existing npm/Node owners maintain the pinned proxy and runtime. A future runtime
or proxy update requires descriptor-lifetime and MCP smoke qualification again.

## Lifecycle

Domain, Behavior, Spec, Contract, Test-driven implementation, Refactor,
Review/Integrate, Deploy, Operate and Maintain/Retire are required. Release is not
applicable: this change publishes no package. No gate exception is requested.
Private cycle evidence records live gates, exact commits, deployment and actual
Final Push outcome. README holds the stable interface and CHANGELOG records the
completed outcome without credentials or machine-private auth content.

## Visual Evidence

State: required; the Behavior table specifies idle, owned, rejected and released
lease outcomes. Review question: which process owns admission, and which exits
allow another connector? Canonical source: this feature's Behavior, Interface and
Contracts and validation sections.

Boundary, interaction, data/trust, schema, dependency/deployment and quantitative:
not_applicable; the existing single-host stdio/HTTP bridge and credential boundary
are retained, no persistent domain schema is added, and state/table prose fully
expresses resolution ordering and exec ownership without another diagram.

**Text Equivalent:** a launcher acquires the per-cache kernel lease before offline
resolution. A busy contender exits immediately. Resolution exits before direct
exec transfers the owning PID and descriptor to Node. EOF, SIGINT or SIGKILL
closes ownership and admits a later launch, retaining the same lock inode.
Owner: dotfiles maintainer. Update this contract when admission, package ownership,
proxy arguments, authentication-cache selection or descriptor lifetime changes.
