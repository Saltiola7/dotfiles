#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Must run as root.' >&2; exit 1; }
[[ -x /usr/bin/omarchy-native-mac-share ]] || { echo 'Try Omarchy share helper is missing.' >&2; exit 1; }
device_root=/sys/bus/virtio/drivers/9pnet_virtio
mounted=()
tag_present() {
  local path value
  shopt -s nullglob
  for path in "$device_root"/virtio*/mount_tag; do
    value=$(tr -d '\000' < "$path")
    if [[ $value == "$1" ]]; then shopt -u nullglob; return 0; fi
  done
  shopt -u nullglob
  return 1
}
mount_one() {
  local tag=$1 dest=$2 path current
  tag_present "$tag" || { printf '%s is not offered; skipping.\n' "$tag"; return 0; }
  path=$dest
  while [[ $path != / ]]; do
    [[ ! -L $path ]] || { echo "Refusing symlink in mount path: $path" >&2; return 1; }
    path=${path%/*}; [[ -n $path ]] || path=/
  done
  if mountpoint -q "$dest"; then
    current=$(findmnt -n -o SOURCE --mountpoint "$dest")
    [[ $current == "$tag" ]] || { echo "Unexpected existing mount at $dest" >&2; return 1; }
    return 0
  fi
  if [[ -e $dest ]]; then
    [[ -d $dest && -z $(find "$dest" -mindepth 1 -maxdepth 1 -print -quit) ]] || {
      echo "Refusing to cover nonempty path: $dest" >&2; return 1;
    }
  fi
  /usr/bin/env OMARCHY_MAC_SHARE_TAG="$tag" OMARCHY_MAC_SHARE_MOUNT_POINT="$dest" \
    /usr/bin/omarchy-native-mac-share --mount || return 1
  current=$(findmnt -n -o SOURCE --mountpoint "$dest") || return 1
  [[ $current == "$tag" ]] || { echo "Failed to verify $tag at $dest" >&2; return 1; }
  mounted+=("$dest")
  printf 'Mounted %s at %s\n' "$tag" "$dest"
}
for pair in \
  'host-git:/Volumes/ext/git' \
  'host-worktrees:/Volumes/ext/state/worktrees' \
  'host-dbsctr:/Volumes/ext/state/dbsctr/worktrees' \
  'host-discovery:/Volumes/ext/state/discovery-worktrees'; do
  if ! mount_one "${pair%%:*}" "${pair#*:}"; then
    for ((i=${#mounted[@]}-1; i>=0; i--)); do umount "${mounted[i]}" || true; done
    exit 1
  fi
done
