#!/bin/bash
set -euo pipefail
w=$(mktemp -d /tmp/omarchy-update-test.XXXXXXXX)
trap 'rm -rf -- "$w"' EXIT
mkdir -p "$w/bin" "$w/home/.local/bin" "$w/runtime" "$w/backup"
export TEST_ORIGINAL_HOME="$HOME"
export TEST_ROOT="$w" HOME="$w/home" XDG_RUNTIME_DIR="$w/runtime" PATH="$w/bin:/usr/bin:/bin"
cp /etc/pacman.d/hooks/00-try-omarchy-preserve-factory.hook "$w/guard.hook"
printf '#!/bin/bash\nexit 0\n' > "$HOME/.local/bin/try-omarchy-efi-audit"
chmod +x "$HOME/.local/bin/try-omarchy-efi-audit"
cat > "$w/bin/sudo" <<'MOCK'
#!/bin/bash
case "$1" in
 /bin/bash)
  count=0; [[ ! -f $TEST_ROOT/audit-count ]] || read -r count < "$TEST_ROOT/audit-count"
  ((count+=1)); printf '%s\n' "$count" > "$TEST_ROOT/audit-count"
  if [[ ${TEST_MODE:-} == fail && $count == 2 ]]; then exit 7; fi
  ;;
 mktemp) printf '%s/backup\n' "$TEST_ROOT" ;;
 snapper) printf '42\n' ;;
 tar|sh) ;;
 *) exit 98 ;;
esac
MOCK
cat > "$w/bin/fake-base-boot" <<'MOCK'
#!/bin/bash
exit 0
MOCK
cat > "$w/bin/fake-restart" <<'MOCK'
#!/bin/bash
# OMARCHY_UPDATE_UNATTENDED
MOCK
cat > "$w/bin/fake-update" <<'MOCK'
#!/bin/bash
set -u
[[ ${OMARCHY_UPDATE_UNATTENDED:-} == 1 ]] || exit 99
if [[ ${TEST_MODE:-} == missing ]]; then exit 0; fi
boot_verified=1
omarchy-update-boot || boot_verified=0
(( boot_verified )) || exit 1
MOCK
chmod +x "$w/bin/"*
python3 - "$w" <<'PY'
from pathlib import Path
import os,sys
w=Path(sys.argv[1]); s=(Path(os.environ['TEST_ORIGINAL_HOME'])/'.local/bin/try-omarchy-update').read_text()
s=s.replace('/etc/pacman.d/hooks/00-try-omarchy-preserve-factory.hook',str(w/'guard.hook'))
s=s.replace('/usr/bin/omarchy-update-restart',str(w/'bin/fake-restart'))
s=s.replace('/usr/bin/omarchy-update-boot',str(w/'bin/fake-base-boot'))
s=s.replace('/usr/bin/omarchy-update',str(w/'bin/fake-update'))
(w/'wrapper').write_text(s); (w/'wrapper').chmod(0o700)
PY
for mode in success fail missing; do
 export TEST_MODE=$mode
 rm -f "$w/audit-count"
 if script -qefc "$w/wrapper" /dev/null > "$w/$mode.log" 2>&1; then result=0; else result=$?; fi
 case "$mode:$result" in
  success:0|fail:1|missing:1) ;;
  *) printf 'FAIL: %s returned %s\n' "$mode" "$result" >&2; cat "$w/$mode.log" >&2; exit 1 ;;
 esac
 case $mode in
  success) rg -q 'Update and final EFI audit passed' "$w/$mode.log" ;;
  fail) rg -q 'Do not reboot' "$w/$mode.log" ;;
  missing) rg -q 'final EFI audit did not run' "$w/$mode.log" ;;
 esac
 printf 'PASS: %s\n' "$mode"
done
