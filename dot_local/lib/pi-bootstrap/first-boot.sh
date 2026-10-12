#!/bin/bash
# Runs inside the Pi only. Resolve the actual root partition before expansion.
set -euo pipefail
root_device=$(readlink -f "$(findmnt -n -o SOURCE /)")
[[ -b "$root_device" ]]
[[ "$(lsblk -dn -o PARTN "$root_device" | tr -d ' ')" == 3 ]]
parent=$(lsblk -dn -o PKNAME "$root_device")
[[ "$parent" =~ ^(sd[a-z]+|mmcblk[0-9]+|nvme[0-9]+n[0-9]+)$ ]]
root_disk="/dev/$parent"
[[ -b "$root_disk" ]]
[[ "$(lsblk -dn -o FSTYPE "$root_device")" == ext4 ]]
sfdisk --no-reread --no-tell-kernel -N 3 "$root_disk" <<<' , +'
partx --update --nr 3 "$root_disk"
resize2fs "$root_device"
install -d -m 0700 /var/lib/pi-bootstrap
touch /var/lib/pi-bootstrap/grown
