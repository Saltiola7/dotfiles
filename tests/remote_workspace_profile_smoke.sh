#!/bin/bash
set -euo pipefail

owner_source=${1:?owner source required}
shared_source=${2:?shared source required}
export HOME=/home/owner
export PATH="/tmp/test-bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export DOTFILES_AI_SYSTEMCTL=/tmp/test-bin/systemctl

dnf install -qy curl findutils git gzip tar xz python3 gcc gcc-c++ make lsof
install -d -m 0700 "$HOME"
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
cat >"$tmp/shared.toml" <<EOF
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
chmod 0600 "$tmp/shared.toml"
owner_data='{"machine_type":"remote-workspace","name":"Test User","email":"personal@example.invalid","work_email":"work@example.invalid","personal_email":"personal@example.invalid","atuin_sync_address":"https://api.atuin.sh"}'

export DOTFILES_AI_SOURCE="$shared_source" DOTFILES_AI_CONFIG="$tmp/shared.toml"
python3 "$shared_source/dot_local/bin/executable_remote-user-bootstrap" bootstrap "$(git -C "$shared_source" rev-parse HEAD)"
chezmoi -S "$shared_source" -D "$HOME" -c "$tmp/shared.toml" managed --include files,scripts | sort >"$tmp/shared-rendered"
chezmoi -S "$owner_source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" managed --include files,scripts | sort >"$tmp/owner-rendered"
comm -12 "$tmp/shared-rendered" "$tmp/owner-rendered" >"$tmp/rendered-intersection"
test ! -s "$tmp/rendered-intersection"

for target in yazi ya fd fzf 7zz zoxide direnv rg nvim; do
    test ! -e "$HOME/.local/bin/$target"
done
find "$HOME" \( -type f -o -type l \) -print | sort >"$tmp/shared-installed"
chezmoi -S "$shared_source" -D "$HOME" -c "$tmp/shared.toml" managed --include files |
  while IFS= read -r target; do
    test ! -f "$HOME/$target" || sha256sum "$HOME/$target"
  done >"$tmp/shared-managed-hashes"

cp -a "$owner_source" "$tmp/owner-source"
rm -rf "$tmp/owner-source/.git"
git -C "$tmp/owner-source" init -q
git -C "$tmp/owner-source" config user.name Test
git -C "$tmp/owner-source" config user.email test@example.com
git -C "$tmp/owner-source" add .
git -C "$tmp/owner-source" commit -qm baseline
baseline=$(git -C "$tmp/owner-source" rev-parse HEAD)

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

install -d -m 0700 "$HOME/.ssh" "$HOME/.local/share/atuin" "$HOME/.config/opencode"
printf keep >"$HOME/.ssh/id_test"
printf keep >"$HOME/.local/share/atuin/history.db"
printf keep >"$HOME/.config/opencode/auth.json"
printf keep >"$HOME/unrelated"
printf '%s\n' \
  "$HOME/.ssh/id_test" \
  "$HOME/.local/share/atuin/history.db" \
  "$HOME/.config/opencode/auth.json" \
  "$HOME/unrelated" | xargs sha256sum >"$tmp/preserved"

chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --persistent-state "$HOME/.local/state/remote-workspace/chezmoi.boltdb" --override-data "$owner_data" apply
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
python3 "$owner_source/tests/remote_workspace_nvim_contract.py" "$HOME/.local/bin/nvim" \
  "$HOME/.config/remote-workspace/restore-nvim.lua"
credential_roundtrip
git config --file "$HOME/.gitconfig" --get-all credential.https://github.com.helper >"$tmp/gh-helpers-after"
cmp "$tmp/gh-helpers" "$tmp/gh-helpers-after"
test "$(git config --file "$HOME/.gitconfig" --get custom.preserved)" = yes
cp "$HOME/.gitconfig" "$tmp/gitconfig-first"
printf 'native gh helper survives optional overlay apply\n'

chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --persistent-state "$HOME/.local/state/remote-workspace/chezmoi.boltdb" --override-data "$owner_data" apply >"$tmp/second-apply"
cmp "$HOME/.gitconfig" "$tmp/gitconfig-first"
credential_roundtrip
test "$(chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --persistent-state "$HOME/.local/state/remote-workspace/chezmoi.boltdb" --override-data "$owner_data" status)" = \
  "$(printf ' R configure-remote-workspace-git.sh\n R zz-remote-workspace-nvim.sh')"

printf '[flavor]\ndark = "catppuccin-latte"\n' >"$tmp/owner-source/private_dot_config/yazi/theme.toml"
git -C "$tmp/owner-source" add private_dot_config/yazi/theme.toml
git -C "$tmp/owner-source" commit -qm update
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --persistent-state "$HOME/.local/state/remote-workspace/chezmoi.boltdb" --override-data "$owner_data" apply
git -C "$tmp/owner-source" checkout -q "$baseline"
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --persistent-state "$HOME/.local/state/remote-workspace/chezmoi.boltdb" --override-data "$owner_data" apply
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" managed --include files,scripts | sort >"$tmp/rollback-rendered"
cmp "$tmp/owner-rendered" "$tmp/rollback-rendered"
cmp "$HOME/.config/yazi/theme.toml" "$tmp/owner-source/private_dot_config/yazi/theme.toml"
sha256sum -c "$tmp/preserved"
sha256sum -c "$tmp/shared-managed-hashes" >/dev/null
printf 'owner overlay locked editor, credential preservation, disjoint reapply and rollback verified\n'
