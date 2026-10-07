import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("shell,profile", [
    ("bash", "dot_common_profile.tmpl"),
    ("zsh", "dot_common_profile.tmpl"),
    ("zsh", "dot_zprofile.tmpl"),
])
@pytest.mark.parametrize("sdk_state", ["executable", "missing", "nonexecutable"])
def test_sdk_precedence_with_inherited_path(tmp_path, shell, profile, sdk_state):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} unavailable")
    home = tmp_path / "home with spaces"
    sdk = home / "google-cloud-sdk/bin"
    brew = tmp_path / "brew/bin"
    sdk.mkdir(parents=True)
    brew.mkdir(parents=True)
    (brew / "gcloud").write_text("#!/bin/sh\nexit 0\n")
    (brew / "gcloud").chmod(0o755)
    if sdk_state != "missing":
        (sdk / "gcloud").write_text("#!/bin/sh\nexit 0\n")
        (sdk / "gcloud").chmod(0o755 if sdk_state == "executable" else 0o644)
    # Upstream helper deliberately leaves an already-present directory in place.
    helper = 'case ":$PATH:" in *":$HOME/google-cloud-sdk/bin:"*) ;; *) export PATH="$HOME/google-cloud-sdk/bin:$PATH" ;; esac\n'
    for suffix in ("bash", "zsh"):
        (sdk.parent / f"path.{suffix}.inc").write_text(helper)
    match = re.search(r"# Google Cloud SDK[^\n]*\n(.*?)(?:\n\n|$)",
                      (ROOT / profile).read_text(), re.S)
    block = match.group(1) if match else ""
    block = block.replace("{{ .chezmoi.homeDir }}", str(home))
    inherited = f"{brew}:{sdk}:/usr/bin:/bin" if sdk_state == "executable" else f"{brew}:/usr/bin:/bin"
    script = block + '\ncommand -v gcloud\n' + block + '\ncommand -v gcloud\nprintf "%s\\n" "$PATH"\n'
    result = subprocess.run([executable, "-f", "-c", script], check=True,
                            capture_output=True, text=True,
                            env={"HOME": str(home), "PATH": inherited})
    first, repeated, path = result.stdout.splitlines()
    expected = sdk / "gcloud" if sdk_state == "executable" else brew / "gcloud"
    assert first == repeated == str(expected)
    if sdk_state != "executable":
        assert path == inherited
