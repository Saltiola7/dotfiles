#!/usr/bin/env python3
"""Reject an absent, wrong, or substituted backup mount before Borg can write."""
import json
import subprocess
import sys

def check(expected_uuid, mountpoint):
    result = subprocess.run(
        ["findmnt", "--json", "--mountpoint", mountpoint,
         "--output", "TARGET,UUID,FSTYPE"], capture_output=True, text=True)
    if result.returncode:
        return False
    try:
        filesystems = json.loads(result.stdout)["filesystems"]
        expected = {"target": mountpoint, "uuid": expected_uuid, "fstype": "ext4"}
        return bool(filesystems) and all(item == expected for item in filesystems)
    except (ValueError, KeyError, TypeError):
        return False

if __name__ == "__main__":
    sys.exit(0 if len(sys.argv) == 3 and check(sys.argv[1], sys.argv[2]) else 1)
