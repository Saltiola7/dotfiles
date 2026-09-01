#!/bin/bash
set -euo pipefail

owner_source=${1:?owner source required}
shared_source=${2:?shared source required}
export HOME=/home/owner
export PATH="/tmp/test-bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export DOTFILES_AI_SYSTEMCTL=/tmp/test-bin/systemctl

dnf install -qy curl findutils git gzip tar xz
install -d -m 0700 "$HOME"
install -d -m 0755 /tmp/test-bin /usr/local/bin
printf '#!/bin/sh\nexit 0\n' >"$DOTFILES_AI_SYSTEMCTL"
chmod 0755 "$DOTFILES_AI_SYSTEMCTL"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL --retry 3 --retry-all-errors \
  https://github.com/twpayne/chezmoi/releases/download/v2.69.4/chezmoi_2.69.4_linux_amd64.tar.gz \
  -o "$tmp/chezmoi.tgz"
printf '%s  %s\n' 5054cf09cb2993725f525c8bb6ec3ff8625489ecfc061e019c17e737e7c7057b "$tmp/chezmoi.tgz" | sha256sum -c -
tar -xzf "$tmp/chezmoi.tgz" -C "$tmp" chezmoi
install -m 0755 "$tmp/chezmoi" /usr/local/bin/chezmoi

cat >"$tmp/shared.toml" <<EOF
sourceDir = "$shared_source"
persistentState = "$HOME/.local/state/dotfiles-ai/chezmoi.boltdb"

[data.dotfiles_ai.remote_user_environment]
enabled = true

[data.dotfiles_ai.herdr]
launchagent = false
host_enabled = false
EOF
owner_data='{"machine_type":"remote-workspace","name":"Test User","email":"test@example.com","atuin_sync_address":"https://api.atuin.sh"}'

chezmoi -S "$shared_source" -D "$HOME" -c "$tmp/shared.toml" apply
chezmoi -S "$shared_source" -D "$HOME" -c "$tmp/shared.toml" managed --include files,scripts | sort >"$tmp/shared-rendered"
chezmoi -S "$owner_source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" managed --include files,scripts | sort >"$tmp/owner-rendered"
comm -12 "$tmp/shared-rendered" "$tmp/owner-rendered" >"$tmp/rendered-intersection"
test ! -s "$tmp/rendered-intersection"

for target in yazi ya fd fzf 7zz; do
    test ! -e "$HOME/.local/bin/$target"
done
find "$HOME" \( -type f -o -type l \) -print | sort >"$tmp/shared-installed"

cp -a "$owner_source" "$tmp/owner-source"
rm -rf "$tmp/owner-source/.git"
git -C "$tmp/owner-source" init -q
git -C "$tmp/owner-source" config user.name Test
git -C "$tmp/owner-source" config user.email test@example.com
git -C "$tmp/owner-source" add .
git -C "$tmp/owner-source" commit -qm baseline
baseline=$(git -C "$tmp/owner-source" rev-parse HEAD)

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
  --override-data "$owner_data" apply
printf '%s\n' \
  "$HOME/.config/yazi/package.toml" \
  "$HOME/.config/yazi/theme.toml" \
  "$HOME/.local/bin/yazi" \
  "$HOME/.local/bin/ya" \
  "$HOME/.local/bin/fd" \
  "$HOME/.local/bin/fzf" \
  "$HOME/.local/bin/7zz" >"$tmp/owner-installed"
find "$HOME/.config/yazi/flavors" \( -type f -o -type l \) -print >>"$tmp/owner-installed"
sort -o "$tmp/owner-installed" "$tmp/owner-installed"
comm -12 "$tmp/shared-installed" "$tmp/owner-installed" >"$tmp/installed-intersection"
test ! -s "$tmp/installed-intersection"
"$HOME/.local/bin/yazi" --version | grep -F 'Version: 26.8.15'
"$HOME/.local/bin/ya" --version | grep -F 'Version: 26.8.15'
"$HOME/.local/bin/fd" --version | grep -F 'fd 10.5.0'
"$HOME/.local/bin/fzf" --version | grep -F '0.74.3'
"$HOME/.local/bin/7zz" | grep -F '7-Zip (z) 26.02'

chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" apply >"$tmp/second-apply"
test ! -s "$tmp/second-apply"
test -z "$(chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml --override-data "$owner_data" status)"

printf '[flavor]\ndark = "catppuccin-latte"\n' >"$tmp/owner-source/private_dot_config/yazi/theme.toml"
git -C "$tmp/owner-source" add private_dot_config/yazi/theme.toml
git -C "$tmp/owner-source" commit -qm update
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" apply
git -C "$tmp/owner-source" checkout -q "$baseline"
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" apply
chezmoi -S "$tmp/owner-source" -D "$HOME" --config /dev/null --config-format toml \
  --override-data "$owner_data" managed --include files,scripts | sort >"$tmp/rollback-rendered"
cmp "$tmp/owner-rendered" "$tmp/rollback-rendered"
cmp "$HOME/.config/yazi/theme.toml" "$tmp/owner-source/private_dot_config/yazi/theme.toml"
sha256sum -c "$tmp/preserved"
