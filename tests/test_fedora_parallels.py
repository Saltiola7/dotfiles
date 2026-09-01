import os
import plistlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
COMMAND = ROOT / "dot_local/bin/executable_fedora-parallels"


def run_command(*args, env=None):
    return subprocess.run(
        ["/bin/sh", str(COMMAND), *args],
        cwd=ROOT,
        env=os.environ | (env or {}),
        capture_output=True,
        text=True,
    )


def fake_diskutil(tmp_path, info, apfs=None, ext_info=None, internal_info=None):
    payload = tmp_path / "info.plist"
    payload.write_bytes(plistlib.dumps(info))
    apfs_payload = tmp_path / "apfs.plist"
    apfs_payload.write_bytes(plistlib.dumps(apfs or {}))
    ext_payload = tmp_path / "ext.plist"
    ext_payload.write_bytes(plistlib.dumps(ext_info or info))
    internal_payload = tmp_path / "internal.plist"
    internal_payload.write_bytes(plistlib.dumps(internal_info or info))
    log = tmp_path / "diskutil.log"
    command = tmp_path / "diskutil"
    command.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$DISKUTIL_LOG"\n'
        'case "$*" in\n'
        '  "info -plist $EXT_MOUNT_PATH") cat "$DISKUTIL_EXT_INFO" ;;\n'
        '  "info -plist $INTERNAL_DEVICE_PATH") cat "$DISKUTIL_INTERNAL_INFO" ;;\n'
        '  "info -plist $PARALLELS_VOLUME_PATH") [ "${PARALLELS_INFO_FAIL:-}" != 1 ] || exit 1; cat "$DISKUTIL_INFO" ;;\n'
        '  "info -plist "*) cat "$DISKUTIL_INFO" ;;\n'
        '  "apfs list -plist disk9") cat "$DISKUTIL_APFS" ;;\n'
        '  *) exit 64 ;;\n'
        "esac\n"
    )
    command.chmod(0o755)
    return command, payload, apfs_payload, ext_payload, internal_payload, log


def test_declares_pinned_safe_host_foundation():
    assert 'cask "parallels"' in (ROOT / "Brewfile").read_text()
    script = COMMAND.read_text()
    for value in (
        "fedora-parallels",
        "162ba3c552a2d241c7c63ec26777af0255ee1b5a135adc0be986ceed999933ef",
        "36F612DCF27F7D1A48A835E4DBFCF71C6D9F90A6",
        "65AF3638-96BB-4F56-8259-38EA49F3F7DF",
        "936D6900-611B-4CA7-9C85-CC3FCD0B90E0",
        "--cpus 6 --memsize 12288",
        "--mode ro",
        "--mode rw",
        'grep -Fxq "SHA256 ($FEDORA_ISO) = $FEDORA_SHA256"',
        'grep -Fq "[GNUPG:] VALIDSIG $FEDORA_FINGERPRINT "',
        'addVolume "$APFS_CONTAINER" APFS Parallels -quota "$VOLUME_QUOTA_BYTES"',
    ):
        assert value in script
    for destructive in ("eraseDisk", "deleteVolume", "deleteContainer", "prlctl delete"):
        assert destructive not in script


def test_help_and_unknown_command_are_non_mutating():
    help_result = run_command("help")
    assert help_result.returncode == 0
    for command in ("doctor", "prepare-storage", "prepare-image", "create", "profile", "status", "verify"):
        assert command in help_result.stdout

    unknown = run_command("destroy")
    assert unknown.returncode != 0
    assert "unknown command" in unknown.stderr


def test_prepare_storage_refuses_wrong_external_volume(tmp_path):
    diskutil, payload, apfs_payload, ext_payload, internal_payload, log = fake_diskutil(
        tmp_path,
        {
            "APFSContainerReference": "disk9",
            "APFSContainerFree": 400_000_000_000,
            "FilesystemType": "apfs",
            "MountPoint": "/Volumes/ext",
            "VolumeName": "ext",
            "VolumeUUID": "WRONG",
            "Encryption": False,
            "Internal": False,
        },
    )
    result = run_command(
        "prepare-storage",
        env={
            "FEDORA_PARALLELS_DISKUTIL": str(diskutil),
            "DISKUTIL_INFO": str(payload),
            "DISKUTIL_APFS": str(apfs_payload),
            "DISKUTIL_EXT_INFO": str(ext_payload),
            "DISKUTIL_INTERNAL_INFO": str(internal_payload),
            "EXT_MOUNT_PATH": "/Volumes/ext",
            "DISKUTIL_LOG": str(log),
        },
    )
    assert result.returncode != 0
    assert "volume identity" in result.stderr
    assert "addVolume" not in log.read_text()


def test_profile_refuses_running_vm(tmp_path):
    volume = tmp_path / "Parallels"
    volume.mkdir()
    diskutil, payload, apfs_payload, ext_payload, internal_payload, log = fake_diskutil(
        tmp_path,
        {
            "APFSContainerReference": "disk9",
            "FilesystemType": "apfs",
            "MountPoint": str(volume),
            "VolumeName": "Parallels",
            "Encryption": False,
            "Internal": False,
            "VolumeUUID": "PARALLELS-UUID",
        },
    )
    prlctl_log = tmp_path / "prlctl.log"
    prlctl = tmp_path / "prlctl"
    prlctl.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$PRLCTL_LOG"\n'
        'case "$1" in --help) printf "prlctl version 27.0.0\\n" ;; list) printf "fedora-parallels running\\n" ;; set) ;; *) exit 64 ;; esac\n'
    )
    prlctl.chmod(0o755)
    prlsrvctl = tmp_path / "prlsrvctl"
    prlsrvctl.write_text(
        '#!/bin/sh\nprintf \'{"status":"ACTIVE","edition":"pro","cpu_total":32,"max_memory":131072}\\n\'\n'
    )
    prlsrvctl.chmod(0o755)
    result = run_command(
        "profile",
        "daily",
        env={
            "FEDORA_PARALLELS_DISKUTIL": str(diskutil),
            "FEDORA_PARALLELS_PRLCTL": str(prlctl),
            "FEDORA_PARALLELS_PRLSRVCTL": str(prlsrvctl),
            "FEDORA_PARALLELS_VOLUME": str(volume),
            "DISKUTIL_INFO": str(payload),
            "DISKUTIL_APFS": str(apfs_payload),
            "DISKUTIL_EXT_INFO": str(ext_payload),
            "DISKUTIL_INTERNAL_INFO": str(internal_payload),
            "EXT_MOUNT_PATH": "/Volumes/ext",
            "DISKUTIL_LOG": str(log),
            "PRLCTL_LOG": str(prlctl_log),
        },
    )
    assert result.returncode != 0
    assert "must be stopped" in result.stderr
    assert "set " not in prlctl_log.read_text()


def test_prepare_storage_refuses_unmounted_duplicate(tmp_path):
    ext_mount = tmp_path / "ext"
    ext_mount.mkdir()
    parallels_volume = tmp_path / "Parallels"
    diskutil, payload, apfs_payload, ext_payload, internal_payload, log = fake_diskutil(
        tmp_path,
        {},
        {
            "Containers": [
                {
                    "APFSContainerUUID": "936D6900-611B-4CA7-9C85-CC3FCD0B90E0",
                    "CapacityFree": 400_000_000_000,
                    "Volumes": [
                        {
                            "Name": "Parallels",
                            "APFSVolumeUUID": "UNMOUNTED-UUID",
                            "CapacityQuota": 214_748_364_800,
                            "Roles": [],
                        }
                    ],
                }
            ]
        },
        ext_info={
            "APFSContainerReference": "disk9",
            "FilesystemType": "apfs",
            "MountPoint": str(ext_mount),
            "VolumeName": "ext",
            "VolumeUUID": "65AF3638-96BB-4F56-8259-38EA49F3F7DF",
            "Encryption": False,
            "Internal": False,
        },
    )
    result = run_command(
        "prepare-storage",
        env={
            "FEDORA_PARALLELS_EXT_MOUNT": str(ext_mount),
            "FEDORA_PARALLELS_VOLUME": str(parallels_volume),
            "FEDORA_PARALLELS_DISKUTIL": str(diskutil),
            "DISKUTIL_INFO": str(payload),
            "DISKUTIL_APFS": str(apfs_payload),
            "DISKUTIL_EXT_INFO": str(ext_payload),
            "DISKUTIL_INTERNAL_INFO": str(internal_payload),
            "DISKUTIL_LOG": str(log),
            "EXT_MOUNT_PATH": str(ext_mount),
            "PARALLELS_VOLUME_PATH": str(parallels_volume),
            "PARALLELS_INFO_FAIL": "1",
        },
    )
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert "addVolume" not in log.read_text()


def test_profile_changes_only_a_stopped_vm(tmp_path):
    volume = tmp_path / "Parallels"
    volume.mkdir()
    diskutil, payload, apfs_payload, ext_payload, internal_payload, log = fake_diskutil(
        tmp_path,
        {
            "APFSContainerReference": "disk9",
            "FilesystemType": "apfs",
            "MountPoint": str(volume),
            "VolumeName": "Parallels",
            "Encryption": False,
            "Internal": False,
            "VolumeUUID": "PARALLELS-UUID",
        },
    )
    prlctl_log = tmp_path / "prlctl.log"
    prlctl = tmp_path / "prlctl"
    prlctl.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$PRLCTL_LOG"\n'
        'case "$1" in --help) printf "prlctl version 27.0.0\\n" ;; list) printf "fedora-parallels stopped\\n" ;; set) ;; *) exit 64 ;; esac\n'
    )
    prlctl.chmod(0o755)
    prlsrvctl = tmp_path / "prlsrvctl"
    prlsrvctl.write_text(
        '#!/bin/sh\nprintf \'{"status":"ACTIVE","edition":"pro","cpu_total":32,"max_memory":131072}\\n\'\n'
    )
    prlsrvctl.chmod(0o755)
    result = run_command(
        "profile",
        "heavy",
        env={
            "FEDORA_PARALLELS_DISKUTIL": str(diskutil),
            "FEDORA_PARALLELS_PRLCTL": str(prlctl),
            "FEDORA_PARALLELS_PRLSRVCTL": str(prlsrvctl),
            "FEDORA_PARALLELS_VOLUME": str(volume),
            "DISKUTIL_INFO": str(payload),
            "DISKUTIL_APFS": str(apfs_payload),
            "DISKUTIL_EXT_INFO": str(ext_payload),
            "DISKUTIL_INTERNAL_INFO": str(internal_payload),
            "EXT_MOUNT_PATH": "/Volumes/ext",
            "DISKUTIL_LOG": str(log),
            "PRLCTL_LOG": str(prlctl_log),
        },
    )
    assert result.returncode == 0, result.stderr
    assert "set fedora-parallels --cpus 8 --memsize 20480" in prlctl_log.read_text()


def test_create_builds_only_the_approved_stopped_vm(tmp_path):
    volume = tmp_path / "Parallels"
    iso_dir = volume / "ISO"
    iso_dir.mkdir(parents=True)
    iso = iso_dir / "Fedora-Workstation-Live-44-1.7.aarch64.iso"
    iso.write_text("fixture")
    ext_mount = tmp_path / "ext"
    (ext_mount / "git").mkdir(parents=True)
    diskutil, payload, apfs_payload, ext_payload, internal_payload, log = fake_diskutil(
        tmp_path,
        {
            "APFSContainerReference": "disk9",
            "FilesystemType": "apfs",
            "MountPoint": str(volume),
            "VolumeName": "Parallels",
            "Encryption": False,
            "Internal": False,
            "VolumeUUID": "PARALLELS-UUID",
        },
        {
            "Containers": [
                {
                    "APFSContainerUUID": "936D6900-611B-4CA7-9C85-CC3FCD0B90E0",
                    "CapacityFree": 400_000_000_000,
                    "Volumes": [
                        {
                            "Name": "Parallels",
                            "APFSVolumeUUID": "PARALLELS-UUID",
                            "CapacityQuota": 214_748_364_800,
                            "Roles": [],
                        }
                    ],
                }
            ]
        },
        ext_info={
            "APFSContainerReference": "disk9",
            "FilesystemType": "apfs",
            "MountPoint": str(ext_mount),
            "VolumeName": "ext",
            "VolumeUUID": "65AF3638-96BB-4F56-8259-38EA49F3F7DF",
            "Encryption": False,
            "Internal": False,
        },
        internal_info={"Internal": True},
    )
    prlctl_log = tmp_path / "prlctl.log"
    prlctl = tmp_path / "prlctl"
    prlctl.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$PRLCTL_LOG"\n'
        'case "$1" in\n'
        '  --help) printf "prlctl version 27.0.0\\n" ;;\n'
        '  create) printf "%s\\n" "--distribution --dst --no-hdd" ;;\n'
        '  set) printf "%s\\n" "--image --type --size --shf-host-add --path --mode --autostart --startup-view" ;;\n'
        '  list) ;;\n'
        '  *) exit 64 ;;\n'
        'esac\n'
    )
    prlctl.chmod(0o755)
    prlsrvctl = tmp_path / "prlsrvctl"
    prlsrvctl.write_text(
        '#!/bin/sh\nprintf \'{"status":"ACTIVE","edition":"pro","cpu_total":32,"max_memory":131072}\\n\'\n'
    )
    prlsrvctl.chmod(0o755)
    shasum = tmp_path / "shasum"
    shasum.write_text(
        "#!/bin/sh\nprintf '162ba3c552a2d241c7c63ec26777af0255ee1b5a135adc0be986ceed999933ef  %s\\n' \"$3\"\n"
    )
    shasum.chmod(0o755)
    df = tmp_path / "df"
    df.write_text(
        "#!/bin/sh\n"
        'case "$2" in\n'
        '  "$EXT_MOUNT_PATH"|"$EXT_MOUNT_PATH/git") device=/dev/external ;;\n'
        '  *) device=/dev/internal ;;\n'
        'esac\n'
        'printf "Filesystem 1024-blocks Used Available Capacity Mounted on\\n%s 1 1 1 1%% %s\\n" "$device" "$2"\n'
    )
    df.chmod(0o755)
    result = run_command(
        "create",
        env={
            "HOME": str(tmp_path),
            "FEDORA_PARALLELS_DISKUTIL": str(diskutil),
            "FEDORA_PARALLELS_PRLCTL": str(prlctl),
            "FEDORA_PARALLELS_PRLSRVCTL": str(prlsrvctl),
            "FEDORA_PARALLELS_SHASUM": str(shasum),
            "FEDORA_PARALLELS_VOLUME": str(volume),
            "FEDORA_PARALLELS_EXT_MOUNT": str(ext_mount),
            "FEDORA_PARALLELS_DF": str(df),
            "DISKUTIL_INFO": str(payload),
            "DISKUTIL_APFS": str(apfs_payload),
            "DISKUTIL_EXT_INFO": str(ext_payload),
            "DISKUTIL_INTERNAL_INFO": str(internal_payload),
            "EXT_MOUNT_PATH": str(ext_mount),
            "INTERNAL_DEVICE_PATH": "/dev/internal",
            "DISKUTIL_LOG": str(log),
            "PRLCTL_LOG": str(prlctl_log),
        },
    )
    assert result.returncode == 0, result.stderr
    calls = prlctl_log.read_text()
    for expected in (
        "create fedora-parallels --distribution fedora-core --no-hdd",
        "set fedora-parallels --cpus 6 --memsize 12288",
        "set fedora-parallels --autostart off --startup-view fullscreen",
        "--device-add hdd --type expand --size 65536",
        "--device-add hdd --image",
        "--size 163840",
        "--device-set net0 --type shared",
        "--device-set cdrom0 --image",
        "--shf-host-defined off",
        f"--shf-host-add ext --path {ext_mount} --mode ro",
        f"--shf-host-add git --path {ext_mount}/git --mode rw",
        "--shf-host on --shf-host-automount on",
        "--sh-app-host-to-guest off --sh-app-guest-to-host off",
        "--smart-mount off",
        "--shared-cloud off --shared-clipboard on",
        "--share-host-location off --sync-ssh-ids off",
    ):
        assert expected in calls
    assert " start " not in f" {calls} "
    assert " delete " not in f" {calls} "
