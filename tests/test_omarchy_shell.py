import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_managed_agents_survive_later_runtime_path_updates(tmp_path):
    rendered = subprocess.run(
        ["chezmoi", "-S", str(ROOT), "--config", "/dev/null", "--config-format", "toml",
         "--override-data", json.dumps({"machine_type": "omarchy"}), "execute-template"],
        input=(ROOT / "dot_bashrc.tmpl").read_text(), capture_output=True, text=True, check=True,
    ).stdout
    rc = tmp_path / "bashrc"
    rc.write_text(rendered)
    managed = tmp_path / ".local/bin"
    competitor = tmp_path / "mise-bin"
    managed.mkdir(parents=True)
    competitor.mkdir()
    for name in ("codex", "opencode", "herdr", "wt"):
        for directory, output in ((managed, "managed"), (competitor, "competing")):
            executable = directory / name
            executable.write_text(f"#!/bin/sh\necho {output}-{name}\n")
            executable.chmod(0o755)
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; export PATH="$2:$PATH"; codex; opencode; herdr; wt',
         "test", str(rc), str(competitor)],
        env={**os.environ, "HOME": str(tmp_path)}, capture_output=True, text=True, check=True,
    )
    assert result.stdout.splitlines() == [f"managed-{name}" for name in ("codex", "opencode", "herdr", "wt")]
