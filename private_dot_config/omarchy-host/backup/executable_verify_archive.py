#!/usr/bin/env python3
"""Fail the daily job if existing critical files are absent from its archive."""
import json
from pathlib import Path
import subprocess
import sys

def missing_paths(expected, archived):
    return set(expected) - {path.removeprefix("./").lstrip("/") for path in archived}

def main():
    repo = "/mnt/omarchy-backup/borg"
    names = json.loads(subprocess.check_output(["borg", "list", "--last", "1", "--json", repo]))
    archive = names["archives"][-1]["name"]
    expected = [path.lstrip("/") for path in Path("/etc/omarchy-backup/required-files.txt").read_text().splitlines() if Path(path).is_file()]
    if not expected:
        raise RuntimeError("No critical files available to verify")
    process = subprocess.Popen(["borg", "list", "--format", "{path}{NL}", repo + "::" + archive], stdout=subprocess.PIPE, text=True)
    remaining = missing_paths(expected, (line.rstrip("\n") for line in process.stdout))
    if process.wait():
        raise RuntimeError("Cannot read archive file inventory")
    if remaining:
        raise RuntimeError("Critical backup files missing: " + ", ".join(sorted(remaining)))
    print("Critical-file backup coverage verified.")

if __name__ == "__main__":
    main()
