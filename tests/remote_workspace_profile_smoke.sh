#!/bin/bash
set -euo pipefail

owner_source=${1:?owner source required}
incoming_shared=${2:?shared source required}
export HOME=/home/owner
export PATH="/tmp/test-bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export DOTFILES_AI_SYSTEMCTL=/tmp/test-bin/systemctl

fail() { printf 'UBI smoke: %s\n' "$1" >&2; exit 1; }
absent() { [[ ! -e "$1" && ! -L "$1" ]]; }
absent "$HOME" || fail 'a fresh disposable home is required'
dnf install -qy curl findutils git gzip tar xz python3 gcc gcc-c++ binutils make lsof
install -d -m 0700 "$HOME"
install -d -m 0700 "$HOME/.local/share" "$HOME/.config/dotfiles-ai"
shared_revision=$(git -C "$incoming_shared" rev-parse HEAD)
test "$shared_revision" = d9fec2457b0c1f65e644f921ae7a4e97b21b3c59
shared_source="$HOME/.local/share/chezmoi-dotfiles-ai"
test ! -e "$shared_source"
git clone --no-hardlinks "$incoming_shared" "$shared_source"
git -C "$shared_source" remote set-url origin https://github.com/Saltiola7/dotfiles-ai.git
git -C "$shared_source" checkout --detach "$shared_revision"
shared_config="$HOME/.config/dotfiles-ai/chezmoi.toml"
install -d -m 0755 /tmp/test-bin /usr/local/bin
cat >"$DOTFILES_AI_SYSTEMCTL" <<'EOF'
#!/bin/bash
# Userland fixture only, never a systemd boot witness.
if [[ $* == '--user start opencode-shared.service' ]]; then
  (
    cd "$HOME"
    "$HOME/.local/bin/opencode" serve --service --hostname 127.0.0.1 --port 0 &
    service_pid=$!
    wait "$service_pid"
  ) </dev/null >/dev/null 2>&1 &
fi
exit 0
EOF
chmod 0755 "$DOTFILES_AI_SYSTEMCTL"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cat >"$shared_config" <<EOF
sourceDir = "$shared_source"
persistentState = "$HOME/.local/state/dotfiles-ai/chezmoi.boltdb"

[data.dotfiles_ai.remote_user_environment]
enabled = true

[data.dotfiles_ai.herdr]
launchagent = false
host_enabled = false

[data.dotfiles_ai.workspaces]
schema_version = 1
root = "$HOME/.local/state/worktrees"
EOF
chmod 0600 "$shared_config"
owner_data='{"machine_type":"remote-workspace","name":"Test User","email":"personal@example.invalid","work_email":"work@example.invalid","personal_email":"personal@example.invalid","atuin_sync_address":"https://api.atuin.sh"}'

export DOTFILES_AI_SOURCE="$shared_source" DOTFILES_AI_CONFIG="$shared_config"
bootstrap="$shared_source/dot_local/bin/executable_remote-user-bootstrap"
printf '%s  %s\n' 89da48232d9352a2eee2dd953fa29d42b7e358a4c2490a59e45cee899d4af666 "$bootstrap" | sha256sum -c -
python3 "$bootstrap" bootstrap "$shared_revision"
chezmoi -S "$shared_source" -D "$HOME" -c "$shared_config" managed --include files,scripts | sort >"$tmp/shared-rendered"
chezmoi -S "$owner_source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" managed --include files,scripts | sort >"$tmp/owner-rendered"
comm -12 "$tmp/shared-rendered" "$tmp/owner-rendered" >"$tmp/rendered-intersection"
test ! -s "$tmp/rendered-intersection"

for target in yazi ya fd fzf 7zz zoxide direnv rg nvim; do
    test ! -e "$HOME/.local/bin/$target"
done
find "$HOME" \( -type f -o -type l \) -print | sort >"$tmp/shared-installed"
chezmoi -S "$shared_source" -D "$HOME" -c "$shared_config" managed --include files |
  while IFS= read -r target; do
    test ! -f "$HOME/$target" || sha256sum "$HOME/$target"
  done >"$tmp/shared-managed-hashes"

baseline=$(git -C "$owner_source" rev-parse HEAD)
git clone --no-hardlinks "$owner_source" "$tmp/owner-source"
git -C "$tmp/owner-source" checkout -q --detach "$baseline"
printf 'UBI qualification: owner %s with foundation %s\n' "$baseline" "$shared_revision"
git -C "$tmp/owner-source" config user.name Test
git -C "$tmp/owner-source" config user.email test@example.com
owner() {
  chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
    --persistent-state "$HOME/.local/state/remote-workspace/chezmoi.boltdb" --override-data "$owner_data" "$@"
}
check_pair() {
  test "$(git -C "$tmp/owner-source" rev-parse HEAD)" = "$baseline"
  test "$(git -C "$shared_source" rev-parse HEAD)" = "$shared_revision"
  git -C "$tmp/owner-source" diff --quiet HEAD --
  git -C "$shared_source" diff --quiet HEAD --
  cmp "$owner_source/private_dot_config/nvim/lazy-lock.json" "$HOME/.config/nvim/lazy-lock.json"
  sha256sum -c "$tmp/shared-managed-hashes" >/dev/null
}

# Native post-login fixture state, not a real provider login. Network is blocked
# for native auth setup/helper calls only; public tool/plugin downloads stay enabled.
install -d -m 0700 "$HOME/.config/gh"
cat >"$HOME/.config/gh/hosts.yml" <<'EOF'
github.com:
    user: fixture-owner
    oauth_token: fixture-not-a-real-token
    git_protocol: https
    users:
        fixture-owner:
            oauth_token: fixture-not-a-real-token
EOF
chmod 0600 "$HOME/.config/gh/hosts.yml"
blocked() {
  env HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 ALL_PROXY=http://127.0.0.1:9 \
    NO_PROXY= GH_CONFIG_DIR="$HOME/.config/gh" GIT_CONFIG_NOSYSTEM=1 \
    GIT_CONFIG_GLOBAL="$HOME/.gitconfig" GIT_CEILING_DIRECTORIES="$HOME" \
    GIT_TERMINAL_PROMPT=0 "$@"
}
(
  cd "$HOME"
  blocked gh auth setup-git --hostname github.com
  blocked git config --global custom.preserved yes
)
git config --file "$HOME/.gitconfig" --get-all credential.https://github.com.helper >"$tmp/gh-helpers"
credential_roundtrip() {
  (
    cd "$HOME"
    printf 'protocol=https\nhost=github.com\nusername=fixture-owner\n\n' |
      blocked git credential fill |
      python3 -c 'import sys; value=sys.stdin.read(); assert "password=fixture-not-a-real-token" in value'
  )
}
credential_roundtrip

install -d -m 0700 "$HOME/.ssh" "$HOME/.local/share/atuin" "$HOME/.config/opencode" "$HOME/.config/remote-workspace"
printf keep >"$HOME/.ssh/id_test"
printf keep >"$HOME/.local/share/atuin/history.db"
printf keep >"$HOME/.config/opencode/auth.json"
printf keep >"$HOME/.config/remote-workspace/unmanaged-note"
printf keep >"$HOME/unrelated"
printf '%s\n' \
  "$HOME/.ssh/id_test" \
  "$HOME/.local/share/atuin/history.db" \
  "$HOME/.config/opencode/auth.json" \
  "$HOME/.config/remote-workspace/unmanaged-note" \
  "$HOME/unrelated" | xargs sha256sum >"$tmp/preserved"

state="$HOME/.local/state/remote-workspace"
ready="$state/editor-ready.json"
attempts="$state/editor-attempts"
first="$attempts/attempt-0001"
second="$attempts/attempt-0002"
data="$HOME/.local/share/nvim"
absent "$ready" && absent "$attempts" && absent "$data" ||
  fail 'expected no prior owner editor or parser preparation'

# Give promotion a real, clean locked preimage to retain. No ready record,
# parser binaries or generated files are seeded. Capture its bytes BEFORE apply.
previous_lazy="$data/lazy/lazy.nvim"
pin=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["lazy.nvim"]["commit"])' \
  "$tmp/owner-source/private_dot_config/nvim/lazy-lock.json")
install -d -m 0700 "$data/lazy"
git init -q "$previous_lazy"
git -C "$previous_lazy" fetch -q --depth 1 https://github.com/folke/lazy.nvim.git "$pin"
git -C "$previous_lazy" checkout -q --detach "$pin"
test "$(git -C "$previous_lazy" rev-parse HEAD)" = "$pin"
cp -a --reflink=auto -- "$data" "$tmp/previous-data"
previous_id=$(stat -c '%d:%i' "$data")
check_previous() {
  test "$(stat -c '%d:%i' "$1")" = "$previous_id" || fail 'previous normal root replaced or lost'
  diff -qr --no-dereference "$tmp/previous-data" "$1" >/dev/null ||
    fail 'previous normal root missing, added or changed bytes'
}

# The helper sets its own PATH. These links live only in its disposable HOME.
# Inject only at SQL grammar compilation, not during unrelated Lazy/plugin builds.
fixture="$tmp/compiler"
install -d -m 0700 "$fixture"
printf '#error RRW_UBI_CONTROLLED_PARSER_FAULT\n' >"$fixture/reject.h"
for tool in cc c++ gcc g++; do
  test -x "/usr/bin/$tool"
  absent "$HOME/.local/bin/$tool" || fail 'compiler fixture would replace an existing tool'
  install -m 0700 "$owner_source/tests/remote_workspace_ubi_compiler.sh" "$fixture/$tool"
  ln -s "$fixture/$tool" "$HOME/.local/bin/$tool"
done

if owner apply >"$tmp/failed-apply.log" 2>&1; then
  fail 'first apply succeeded with the parser compiler fault armed'
fi
stage=$(sed -nE 's/^remote owner editor setup failed: editor exit [0-9]+; stage (owner-init|plugin-restore|plugin-verify|parser-build|parser-verify|native-command); .*/\1/p' "$tmp/failed-apply.log")
grep -Fsxq 'compiler rejected SQL parser.c' "$fixture/rejected" ||
  fail "first apply did not reach the intended compiler rejection (stage ${stage:-unreported})"
# Depending on the install task's wait result, Lua can report the build failure
# itself or the subsequent mandatory check for the missing compiled file.
grep -Eq '^remote owner editor setup failed: editor exit [1-9][0-9]*; stage (parser-build; parser installation failed|parser-verify; required compiled parser absent)$' "$tmp/failed-apply.log" ||
  fail "compiler fault fired but did not produce the expected parser failure (stage ${stage:-unreported})"
absent "$ready" && absent "$first/previous" && absent "$second" || fail 'first failure was selected or published'
check_previous "$data"
check_pair
check_record() {
  python3 - "$1/record.json" "$2" "$3" "$HOME/.config/nvim/lazy-lock.json" "$previous_id" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

record = json.loads(Path(sys.argv[1]).read_bytes())
assert record['state'] == sys.argv[2], 'unexpected attempt state'
assert record['lock_sha256'] == hashlib.sha256(Path(sys.argv[4]).read_bytes()).hexdigest(), 'wrong lock'
tree = Path(sys.argv[3]).stat()
seal = record['candidate']
before = record['normal']
assert f"{before['dev']}:{before['ino']}" == sys.argv[5], 'wrong normal preimage'
assert seal['bytes'] > 0 and seal['entries'] > 0
assert (seal['dev'], seal['ino']) == (tree.st_dev, tree.st_ino), 'seal refers to a different tree'
PY
}
failed_data="$first/candidate/nvim"
check_record "$first" failed_sealed "$failed_data"
test -s "$failed_data/lazy/lazy.nvim/lua/lazy/init.lua"
absent "$failed_data/site/parser/sql.so" || fail 'faulted SQL parser unexpectedly installed'
# The record alone is not evidence of retention. Keep an independent copy of
# the whole failed generation (including real plugin worktrees and Git bytes).
cp -a --reflink=auto -- "$first" "$tmp/failed-generation"
found_tags=false
for tags in "$tmp/failed-generation/candidate/nvim/lazy"/*/doc/tags; do
  [[ -s "$tags" ]] || continue
  indexed=$(git --no-optional-locks -C "${tags%/doc/tags}" ls-files -- doc/tags)
  if [[ -z "$indexed" ]]; then found_tags=true; break; fi
done
[[ $found_tags == true ]] || fail 'failed generation lacks real setup-generated help tags'
failed_id=$(stat -c '%d:%i' "$failed_data")
check_retained() {
  test "$(stat -c '%d:%i' "$failed_data")" = "$failed_id" ||
    fail 'sealed candidate was replaced'
  diff -qr --no-dereference "$tmp/failed-generation" "$first" >/dev/null ||
    fail 'failed generation missing, added or changed bytes'
}
printf 'native parser fault witnessed; failed tree sealed, previous root untouched, readiness absent\n'

# Same source pair, inputs, persistent state and HOME. Removing only the fault
# leaves a transparent observer of actual successful parser compiler invocations.
rm -- "$fixture/reject.h"
owner apply
check_pair
check_retained
check_previous "$second/previous"
check_record "$second" accepted "$data"
test -s "$ready" && test -s "$fixture/compiled" || fail 'retry lacks readiness or fresh compiler output'
absent "$fixture/outside" || fail 'parser built outside private preparation'
cp -a --reflink=auto -- "$data" "$tmp/accepted-data"
cp "$second/record.json" "$tmp/accepted-record"
cp "$ready" "$tmp/ready"

# Independent second process: use the real owner init and ordinary Lazy root.
# Compare symbols observed at compile time with the LOCKED plugin's dependency
# expansion, then load each explicit promoted .so under a fresh alias and parse.
cat >"$tmp/check-startup.lua" <<'LUA'
local data = vim.fn.stdpath("data")
local root = data .. "/lazy"
local lazy = require("lazy.core.config")
assert(lazy.options.root == root)
local lock = vim.json.decode(table.concat(vim.fn.readfile(vim.fn.stdpath("config") .. "/lazy-lock.json"), "\n"))
for name, pin in pairs(lock) do
  local plugin = assert(lazy.plugins[name])
  assert(plugin.dir == root .. "/" .. name)
  local head = vim.system({ "git", "-C", plugin.dir, "rev-parse", "HEAD" }, { text = true }):wait(5000)
  assert(head.code == 0 and vim.trim(head.stdout) == pin.commit)
end
local required = { "bash", "python", "lua", "vim", "vimdoc", "json", "yaml", "toml", "markdown", "sql" }
require("lazy").load({ plugins = { "nvim-treesitter" } })
local expanded = require("nvim-treesitter.config").norm_languages(vim.deepcopy(required), { unsupported = true })
local compiled, loaded = {}, {}
for _, symbol in ipairs(vim.fn.readfile(vim.env.UBI_COMPILED)) do compiled[symbol] = true end
for _, lang in ipairs(expanded) do
  assert(compiled[lang], "no retry compiler output")
  local alias = "ubi_native_check_" .. lang
  local path = data .. "/site/parser/" .. lang .. ".so"
  assert(vim.uv.fs_lstat(path).type == "file")
  assert(vim.treesitter.language.add(alias, { path = path, symbol_name = lang }))
  assert(vim.treesitter.get_string_parser("", alias):parse()[1])
  loaded[lang] = true
end
for _, lang in ipairs(required) do assert(loaded[lang]) end
assert(loaded.markdown_inline) -- a dependency in this lock, not one of the ten
assert(vim.v.errmsg == "" and _G.ubi_start_errors == 0)
assert(vim.fn.writefile(expanded, vim.env.UBI_LOADED) == 0)
LUA
(
  cd "$HOME"
  unset LAZY REMOTE_WORKSPACE_LAZY_ROOT
  export PATH="$HOME/.local/libexec/remote-workspace:$PATH"
  export XDG_CONFIG_HOME="$HOME/.config" XDG_DATA_HOME="$HOME/.local/share"
  export XDG_CACHE_HOME="$HOME/.cache" XDG_STATE_HOME="$HOME/.local/state" NVIM_APPNAME=nvim
  export UBI_CHECK="$tmp/check-startup.lua" UBI_COMPILED="$fixture/compiled" UBI_LOADED="$tmp/loaded"
  timeout 120 "$HOME/.local/bin/nvim" --headless -i NONE \
    --cmd 'lua _G.ubi_start_errors=0; local old=vim.notify; vim.notify=function(m,l,o) if l==vim.log.levels.ERROR then _G.ubi_start_errors=_G.ubi_start_errors+1 end; return old(m,l,o) end' \
    -u "$HOME/.config/nvim/init.lua" \
    '+lua if not pcall(dofile, vim.env.UBI_CHECK) then vim.cmd("cquit 1") end' '+qa!'
) >"$tmp/normal-startup.log" 2>&1 || fail 'real normal-path owner startup or parser proof failed'
test -s "$tmp/loaded" && absent "$fixture/outside" || fail 'normal startup did not load the existing compiled set'
check_pair
while IFS= read -r lang; do
  hash=$(sha256sum "$data/site/parser/$lang.so")
  grep -Fsxq "$lang ${hash%% *}" "$fixture/linked" ||
    fail 'normal-path parser bytes do not match a real retry linker output'
  printf '%s\n' "$hash"
done <"$tmp/loaded" >"$tmp/parser-hashes"
for tool in cc c++ gcc g++; do rm -- "$HOME/.local/bin/$tool"; done
printf 'retry built and normal startup loaded the ten parsers and their locked dependencies\n'

check_generations() {
  check_retained
  check_previous "$second/previous"
  check_record "$second" accepted "$data"
  diff -qr --no-dereference "$tmp/accepted-data" "$data" >/dev/null ||
    fail 'accepted plugin or parser generation missing, added or changed bytes'
  test "$(find "$attempts" -mindepth 1 -maxdepth 1 -printf '%f\n' | sort)" = $'attempt-0001\nattempt-0002' ||
    fail 'ordinary apply started another attempt'
  cmp "$tmp/accepted-record" "$second/record.json"
  cmp "$tmp/ready" "$ready"
  sha256sum -c "$tmp/parser-hashes" >/dev/null
}
printf '%s\n' \
  "$HOME/.config/yazi/package.toml" \
  "$HOME/.config/yazi/theme.toml" \
  "$HOME/.local/bin/yazi" \
  "$HOME/.local/bin/ya" \
  "$HOME/.local/bin/fd" \
  "$HOME/.local/bin/fzf" \
  "$HOME/.local/bin/7zz" >"$tmp/owner-installed"
find "$HOME/.config/yazi/flavors" \( -type f -o -type l \) -print >>"$tmp/owner-installed"
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" managed --include files |
  while IFS= read -r target; do printf '%s\n' "$HOME/$target"; done >>"$tmp/owner-installed"
python3 - <<'PY' >>"$tmp/owner-installed"
import json
from pathlib import Path
home = Path.home()
state = home / '.local/state/remote-workspace'
tools = json.loads((state / 'installed-tools.json').read_text())
for tool in tools.values():
    print(home / tool['executable'])
    for member in (*tool['files'], '.verified-files.json'):
        print(home / tool['generation'] / member)
editor = json.loads((state / 'editor-ready.json').read_text())
assert editor['generation'] == 'attempt-0002'
for path in editor['files']:
    print(home / path)
for path in state.rglob('*'):
    if path.is_file() or path.is_symlink():
        print(path)
PY
sort -o "$tmp/owner-installed" "$tmp/owner-installed"
comm -12 "$tmp/shared-installed" "$tmp/owner-installed" >"$tmp/installed-intersection"
test ! -s "$tmp/installed-intersection"
sha256sum -c "$tmp/shared-managed-hashes" >/dev/null
printf 'final candidate foundation/overlay managed and installed files disjoint\n'
"$HOME/.local/bin/yazi" --version | grep -F 'Version: 26.8.15'
"$HOME/.local/bin/ya" --version | grep -F 'Version: 26.8.15'
"$HOME/.local/bin/fd" --version | grep -F 'fd 10.5.0'
"$HOME/.local/bin/fzf" --version | grep -F '0.74.3'
"$HOME/.local/bin/7zz" | grep -F '7-Zip (z) 26.02'
"$HOME/.local/bin/zoxide" --version | grep -F 'zoxide 0.10.0'
"$HOME/.local/bin/direnv" version | grep -Fx '2.38.2'
"$HOME/.local/bin/rg" --version | grep -F 'ripgrep 15.2.0'
"$HOME/.local/bin/nvim" --version | grep -F 'NVIM v0.12.6'
"$HOME/.local/libexec/remote-workspace/tree-sitter" --version | grep -F 'tree-sitter 0.26.1'
# Additional offline Lua error contracts, separate from the native proof above.
python3 "$owner_source/tests/remote_workspace_nvim_contract.py" "$HOME/.local/bin/nvim" \
  "$HOME/.config/remote-workspace/restore-nvim.lua"
credential_roundtrip
git config --file "$HOME/.gitconfig" --get-all credential.https://github.com.helper >"$tmp/gh-helpers-after"
cmp "$tmp/gh-helpers" "$tmp/gh-helpers-after"
test "$(git config --file "$HOME/.gitconfig" --get custom.preserved)" = yes
cp "$HOME/.gitconfig" "$tmp/gitconfig-first"
printf 'native gh helper survives optional overlay apply\n'

owner apply >"$tmp/second-apply"
check_pair
check_generations
cmp "$HOME/.gitconfig" "$tmp/gitconfig-first"
credential_roundtrip
test "$(owner status)" = \
  "$(printf ' R configure-remote-workspace-git.sh\n R zz-remote-workspace-nvim.sh')"

# Introduce one disposable overlay-owned file so rollback exercises removal,
# not just replacement of a theme's bytes. Its unmanaged sibling must survive.
extra_source=private_dot_config/remote-workspace/private_ubi-rollback-probe
extra_target=.config/remote-workspace/ubi-rollback-probe
absent "$HOME/$extra_target" && absent "$tmp/owner-source/$extra_source" || fail 'rollback fixture collides'
printf 'temporary owner target\n' >"$tmp/owner-source/$extra_source"
printf '[flavor]\ndark = "catppuccin-latte"\n' >"$tmp/owner-source/private_dot_config/yazi/theme.toml"
git -C "$tmp/owner-source" add private_dot_config/yazi/theme.toml "$extra_source"
git -C "$tmp/owner-source" commit -qm update
owner apply
cmp "$tmp/owner-source/private_dot_config/yazi/theme.toml" "$HOME/.config/yazi/theme.toml"
owner managed --include files >"$tmp/update-files"
grep -Fxq "$extra_target" "$tmp/update-files"
cmp "$tmp/owner-source/$extra_source" "$HOME/$extra_target"
check_generations
sha256sum -c "$tmp/preserved" >/dev/null
sha256sum -c "$tmp/shared-managed-hashes" >/dev/null
# Roll back the disposable overlay revision only. All three tree snapshots
# above predate the update; compare both again on this same HOME after rollback.
owner destroy --force "$HOME/$extra_target"
absent "$HOME/$extra_target" || fail 'retired overlay target still installed'
git -C "$tmp/owner-source" checkout -q "$baseline"
owner apply
absent "$HOME/$extra_target" || fail 'retired target unexpectedly restored'
check_pair
check_generations
cmp "$HOME/.gitconfig" "$tmp/gitconfig-first"
credential_roundtrip
owner managed --include files,scripts | sort >"$tmp/rollback-rendered"
cmp "$tmp/owner-rendered" "$tmp/rollback-rendered"
cmp "$HOME/.config/yazi/theme.toml" "$tmp/owner-source/private_dot_config/yazi/theme.toml"
sha256sum -c "$tmp/preserved"
sha256sum -c "$tmp/shared-managed-hashes" >/dev/null
printf 'owner overlay locked editor, credential preservation, disjoint reapply and rollback verified\n'
