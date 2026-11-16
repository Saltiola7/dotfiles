#!/bin/bash
set -euo pipefail
w=$(mktemp -d /tmp/omarchy-share-unit-test.XXXXXXXX)
trap 'rm -rf -- "$w"' EXIT
mkdir -p "$w/bin" "$w/device" "$w/mounts" "$w/root"
export TEST_ROOT="$w" PATH="$w/bin:/usr/bin:/bin"
python3 - "$w" <<'PY'
from pathlib import Path
import sys
w=Path(sys.argv[1]);s=(Path.home()/'Exchange/mount-project-shares.sh').read_text()
s=s.replace('/sys/bus/virtio/drivers/9pnet_virtio',str(w/'device'))
s=s.replace('/Volumes/ext',str(w/'root/ext'))
s=s.replace('/usr/bin/omarchy-native-mac-share',str(w/'bin/native'))
assert '/Volumes/ext' not in s and '/sys/bus/virtio/drivers/9pnet_virtio' not in s
(w/'testscript').write_text(s);(w/'testscript').chmod(0o700)
PY
cat > "$w/bin/mountpoint" <<'MOCK'
#!/bin/bash
p=${@: -1}; for f in "$TEST_ROOT"/mounts/*; do [[ -f $f ]] || continue; [[ $(cat "$f") == "$p" ]] && exit 0; done; exit 1
MOCK
cat > "$w/bin/findmnt" <<'MOCK'
#!/bin/bash
p=${@: -1}; for f in "$TEST_ROOT"/mounts/*; do [[ -f $f ]] || continue; if [[ $(cat "$f") == "$p" ]]; then basename "$f"; exit 0; fi; done; exit 1
MOCK
cat > "$w/bin/umount" <<'MOCK'
#!/bin/bash
p=$1; for f in "$TEST_ROOT"/mounts/*; do [[ -f $f ]] || continue; if [[ $(cat "$f") == "$p" ]]; then rm "$f"; exit 0; fi; done; exit 1
MOCK
cat > "$w/bin/native" <<'MOCK'
#!/bin/bash
[[ ${OMARCHY_MAC_SHARE_TAG:-} != ${TEST_FAIL_TAG:-no-failure} ]] || exit 1
mkdir -p "$OMARCHY_MAC_SHARE_MOUNT_POINT"
printf '%s\n' "$OMARCHY_MAC_SHARE_MOUNT_POINT" > "$TEST_ROOT/mounts/$OMARCHY_MAC_SHARE_TAG"
MOCK
chmod +x "$w/bin/"*
fakeroot bash "$w/testscript" >/dev/null
[[ -z $(find "$w/mounts" -type f -print -quit) ]]
printf 'PASS: no devices leaves mounts unchanged.\n'
i=0
for tag in host-git host-worktrees host-dbsctr host-discovery; do
 ((i+=1)); mkdir "$w/device/virtio$i"; printf '%s\0' "$tag" > "$w/device/virtio$i/mount_tag"
done
fakeroot bash "$w/testscript" >/dev/null
[[ $(find "$w/mounts" -type f | wc -l) -eq 4 ]]
printf 'PASS: all four offered tags mount at their intended paths.\n'
fakeroot bash "$w/testscript" >/dev/null
[[ $(find "$w/mounts" -type f | wc -l) -eq 4 ]]
printf 'PASS: repeated start preserves existing correct mounts.\n'
rm -f "$w/mounts/"*
printf 'do-not-hide\n' > "$w/root/ext/git/existing"
if fakeroot bash "$w/testscript" >/dev/null 2>&1; then echo 'FAIL: covered nonempty path' >&2; exit 1; fi
[[ -f "$w/root/ext/git/existing" && -z $(find "$w/mounts" -type f -print -quit) ]]
printf 'PASS: nonempty mount point is refused.\n'
rm "$w/root/ext/git/existing"
export TEST_FAIL_TAG=host-dbsctr
if fakeroot bash "$w/testscript" >/dev/null 2>&1; then echo 'FAIL: mount failure ignored' >&2; exit 1; fi
[[ -z $(find "$w/mounts" -type f -print -quit) ]]
printf 'PASS: a later mount failure rolls back earlier mounts.\n'
unset TEST_FAIL_TAG
rmdir "$w/root/ext/git"
ln -s "$w/root/elsewhere" "$w/root/ext/git"
if fakeroot bash "$w/testscript" >/dev/null 2>&1; then echo 'FAIL: followed symlink mount point' >&2; exit 1; fi
[[ -L "$w/root/ext/git" && -z $(find "$w/mounts" -type f -print -quit) ]]
printf 'PASS: symlink mount point is refused.\n'
