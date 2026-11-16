#!/bin/bash
set -euo pipefail
[[ $EUID == 0 && $(uname -m) == aarch64 ]] || { echo 'Run as root inside the ARM64 Omarchy guest.' >&2; exit 1; }
[[ -f /etc/pacman.conf && -d /etc/pacman.d/hooks ]] || { echo 'Expected pacman configuration is missing.' >&2; exit 1; }
target=/etc/pacman.d/hooks/00-try-omarchy-preserve-factory.hook
work=$(mktemp -d /tmp/omarchy-guard-install.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cat > "$work/guard.hook" <<'HOOK'
[Trigger]
Operation = Upgrade
Type = Package
Target = try-omarchy

[Action]
Description = Try Omarchy upgrade blocked: review factory recovery preservation
When = PreTransaction
Exec = /usr/bin/false
AbortOnFail
HOOK
if [[ -e $target || -L $target ]]; then
  [[ -f $target && ! -L $target ]] && cmp -s "$work/guard.hook" "$target" || {
    echo "Existing guard differs; refusing to replace $target." >&2; exit 1;
  }
  echo 'Recovery-preservation guard is already installed.'
else
  install -o root -g root -m 0644 "$work/guard.hook" "$target"
  cmp -s "$work/guard.hook" "$target"
  echo "Installed $target"
fi
printf '%s\n' 'A try-omarchy package upgrade will stop the entire transaction for review before any package changes.'
printf '%s\n' 'Other package updates are unaffected unless included in the same stopped transaction.'
printf '%s\n' 'To remove this guard after review: sudo mv /etc/pacman.d/hooks/00-try-omarchy-preserve-factory.hook /etc/pacman.d/00-try-omarchy-preserve-factory.hook.disabled'
