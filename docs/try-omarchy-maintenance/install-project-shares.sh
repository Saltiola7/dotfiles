#!/bin/bash
set -euo pipefail
[[ $EUID == 0 && $(uname -m) == aarch64 ]] || { echo 'Run as root in the ARM64 guest.' >&2; exit 1; }
source_dir=$(cd "$(dirname "$0")" && pwd -P)
work=$(mktemp -d /tmp/omarchy-project-install.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cp "$source_dir/mount-project-shares.sh" "$work/mount-project-shares.sh"
cp "$source_dir/project-shares.service" "$work/project-shares.service"
printf '%s  %s\n' 1beeb91964b7618f0ebed8c6b4dedf80446f8416f6758ce3db7a49bde0fcc45e "$work/mount-project-shares.sh" fa6a6168cbb7620c41c3dacfdd8bd4f61ccf7c813854d7ef9b0be007135e4393 "$work/project-shares.service" | sha256sum -c --status || {
 echo 'Share installer inputs do not match the reviewed files.' >&2; exit 1;
}
script=/usr/local/libexec/try-omarchy-mount-projects
unit=/etc/systemd/system/try-omarchy-project-shares.service
for pair in "$work/mount-project-shares.sh:$script" "$work/project-shares.service:$unit"; do
 src=${pair%%:*}; dst=${pair#*:}
 if [[ -e $dst || -L $dst ]]; then
  [[ -f $dst && ! -L $dst ]] && cmp -s "$src" "$dst" || { echo "Refusing to replace existing file: $dst" >&2; exit 1; }
 fi
done
install -d -o root -g root -m 0755 /usr/local/libexec
[[ -e $script ]] || install -o root -g root -m 0755 "$work/mount-project-shares.sh" "$script"
[[ -e $unit ]] || install -o root -g root -m 0644 "$work/project-shares.service" "$unit"
systemctl daemon-reload
systemctl enable --now try-omarchy-project-shares.service
printf 'Project-share service installed. It mounts only offered project tags.\n'
