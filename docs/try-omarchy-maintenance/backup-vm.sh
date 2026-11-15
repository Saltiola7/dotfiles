#!/bin/bash
set -euo pipefail
vm=/Volumes/ext/state/try-omarchy/VM/shell
backups=/Volumes/ext/state/try-omarchy/baselines
if [[ ${1:-} == --vm-dir && ${3:-} == --backup-dir && $# == 4 ]]; then
  vm=$2
  backups=$4
elif (( $# != 0 )); then
  printf 'Usage: %s [--vm-dir DIR --backup-dir DIR]\n' "$0" >&2
  exit 2
fi
[[ $vm == /* && $backups == /* && -d $vm && ! -L $vm && ! -L $backups ]] || {
  echo 'Use existing, absolute, non-symlink VM and backup paths.' >&2; exit 1;
}
for file in disk.img efi-vars.fd vm.json lock; do
  [[ -f $vm/$file && ! -L $vm/$file ]] || { printf 'Missing or unsafe VM file: %s\n' "$file" >&2; exit 1; }
done
[[ -d $backups ]] || { echo 'The backup directory must already exist.' >&2; exit 1; }
exec 9>>"$vm/lock"
/usr/bin/lockf -s -t 0 9 || { echo 'VM is running or its lock is held; shut it down first.' >&2; exit 1; }
umask 077
out=$(mktemp -d "$backups/baseline-$(date +%Y%m%d-%H%M%S)-XXXXXX")
printf '%s\n' 'INCOMPLETE: do not restore this backup.' > "$out/STATUS.txt"
printf 'Cloning stopped VM disk to %s\n' "$out"
cp -c "$vm/disk.img" "$out/disk.img"
cp -p "$vm/efi-vars.fd" "$out/efi-vars.fd"
cp -p "$vm/vm.json" "$out/vm.json"
(
  cd "$out"
  shasum -a 256 efi-vars.fd vm.json > checksums.sha256
)
printf 'Checking disk bytes; this may take several minutes.\n'
cmp -s "$vm/disk.img" "$out/disk.img" || { echo 'Disk comparison failed; backup is incomplete.' >&2; exit 1; }
(
  cd "$out"
  shasum -a 256 -c checksums.sha256
  printf 'Hashing the disk for later integrity checks; this may take several minutes.\n'
  shasum -a 256 disk.img >> checksums.sha256
)
printf 'Complete: disk byte comparison passed and SHA-256 checksums recorded.\nSource: %s\n' "$vm" > "$out/STATUS.txt"
printf 'Backup complete: %s\n' "$out"
