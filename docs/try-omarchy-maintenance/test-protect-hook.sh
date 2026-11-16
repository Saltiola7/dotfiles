#!/bin/bash
set -euo pipefail
w=$(mktemp -d /tmp/omarchy-hook-test.XXXXXXXX)
trap 'rm -rf -- "$w"' EXIT
root=$w/root
mkdir -p "$root/usr/bin" "$root/usr/share/fixture" "$root/etc/pacman.d/hooks" "$root/var/lib/pacman" "$root/var/cache/pacman/pkg" "$root/var/log" "$w/gpg"
printf 'int main(void){return 1;}\n' | gcc -x c -static -o "$root/usr/bin/false" -
printf '[options]\nArchitecture = aarch64\nSigLevel = Never\n' > "$w/pacman.conf"
for version in 1 2; do
 stage=$w/stage$version
 mkdir -p "$stage/usr/share/fixture"
 printf 'pkgname = fixture-protected\npkgbase = fixture-protected\npkgver = %s-1\npkgdesc = Isolated hook test\nsize = 1\narch = any\nbuilddate = 1\npackager = test\n' "$version" > "$stage/.PKGINFO"
 printf '%s\n' "$version" > "$stage/usr/share/fixture/version"
 bsdtar -C "$stage" -cf "$w/pkg$version.tar" .PKGINFO usr
 done
args=(--root "$root" --dbpath "$root/var/lib/pacman" --cachedir "$root/var/cache/pacman/pkg" --hookdir "$root/etc/pacman.d/hooks" --gpgdir "$w/gpg" --logfile "$root/var/log/pacman.log" --config "$w/pacman.conf")
pacman "${args[@]}" -U --noconfirm --nodeps --noscriptlet "$w/pkg1.tar" >/dev/null
cat > "$root/etc/pacman.d/hooks/00-preserve.hook" <<'HOOK'
[Trigger]
Operation = Upgrade
Type = Package
Target = fixture-protected
[Action]
Description = Preserve fixture recovery
When = PreTransaction
Exec = /usr/bin/false
AbortOnFail
HOOK
if pacman "${args[@]}" -U --noconfirm --nodeps --noscriptlet "$w/pkg2.tar" >"$w/upgrade.log" 2>&1; then
 echo 'FAIL: package transaction was not blocked.' >&2; exit 1
fi
[[ $(cat "$root/usr/share/fixture/version") == 1 ]] || { echo 'FAIL: installed fixture changed.' >&2; exit 1; }
pacman "${args[@]}" -Q fixture-protected | grep -q '^fixture-protected 1-1$'
for version in 1 2; do
 stage=$w/ordinary$version
 mkdir -p "$stage/usr/share/fixture-ordinary"
 printf 'pkgname = fixture-ordinary\npkgbase = fixture-ordinary\npkgver = %s-1\npkgdesc = Isolated ordinary package\nsize = 1\narch = any\nbuilddate = 1\npackager = test\n' "$version" > "$stage/.PKGINFO"
 printf '%s\n' "$version" > "$stage/usr/share/fixture-ordinary/version"
 bsdtar -C "$stage" -cf "$w/ordinary$version.tar" .PKGINFO usr
 pacman "${args[@]}" -U --noconfirm --nodeps --noscriptlet "$w/ordinary$version.tar" >/dev/null
 done
[[ $(cat "$root/usr/share/fixture-ordinary/version") == 2 ]] || { echo 'FAIL: ordinary upgrade did not complete.' >&2; exit 1; }
printf 'PASS: protected upgrade blocked; unrelated package upgraded normally.\n'
