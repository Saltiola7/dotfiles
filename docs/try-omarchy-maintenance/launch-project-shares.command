#!/bin/bash
set -euo pipefail
case ${1:-} in
 '') export OMARCHY_QEMU_GPU_DRY_RUN=0 ;;
 --dry-run) export OMARCHY_QEMU_GPU_DRY_RUN=1 ;;
 *) echo 'Usage: launch-identity-fixed.command [--dry-run]' >&2; exit 64 ;;
esac
actual=$(/usr/bin/shasum -a 256 '/Applications/Try Omarchy.app/Contents/Resources/scripts/run-qemu-gpu.sh')
[[ ${actual%% *} == 37bee14bcfe8d847fcaa582fe2fa4673cc082a86abd6916886d0a96f33a2b27d ]] || { echo 'Try Omarchy app changed; refresh and review the compatibility wrapper before launching.' >&2; exit 1; }
export OMARCHY_QEMU_GPU_STATE_ROOT=/Volumes/ext/state/try-omarchy/VM
export OMARCHY_QEMU_GPU_CPUS=10 OMARCHY_QEMU_GPU_MEMORY_MIB=40960 OMARCHY_QEMU_GPU_DISK_GIB=128
export OMARCHY_QEMU_GPU_PORT_FORWARDS=tcp:2224:22
export OMARCHY_QEMU_GPU_SHARED_FOLDER=/Volumes/ext/state/try-omarchy/Exchange
export OMARCHY_QEMU_GPU_IMMERSIVE=1 OMARCHY_QEMU_GPU_NOTCH=0
exec /Volumes/ext/state/try-omarchy/runtime-identity-stable/run-qemu-gpu-projects.sh
