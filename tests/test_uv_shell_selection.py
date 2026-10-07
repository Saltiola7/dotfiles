import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
FRAGMENT = ROOT / ".chezmoitemplates/uv-path.sh"


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize("state", ["clean", "inherited", "other-version", "missing-marker",
                                  "missing-mise", "failed-lookup", "missing-uvx"])
def test_uv_only_selection(tmp_path, shell, state):
    executable = shutil.which(shell)
    if not executable:
        pytest.skip(f"{shell} unavailable")
    assert FRAGMENT.exists(), "uv selection is not shared by login profiles"
    external = tmp_path / "external state"
    store = external / "xdg/data/mise"
    selected = store / "installs/uv" / ("other" if state == "other-version" else "current") / "bin"
    selected.mkdir(parents=True)
    tools = tmp_path / "local bin"
    tools.mkdir()
    home = tmp_path / "home with spaces"
    home.mkdir()
    for directory, names in [(tools, ["uv", "uvx", "python3", "node", "codex", "gcloud"]),
                             (selected, ["uv"] if state == "missing-uvx" else ["uv", "uvx"])]:
        for name in names:
            p = directory / name
            p.write_text("#!/bin/sh\nexit 0\n")
            p.chmod(0o755)
    if state != "missing-marker":
        (external / ".dotfiles-ai-state").touch()
    if state != "missing-mise":
        mise = tools / "mise"
        mise.write_text('#!/bin/sh\n[ "$*" = "which uv" ] || exit 91\n' +
                        ('exit 1\n' if state == "failed-lookup" else f'printf "%s\\n" "{selected}/uv"\n'))
        mise.chmod(0o755)
    text = FRAGMENT.read_text()
    assert text.startswith('{{ if eq .machine_type "mac-mini" -}}\n')
    fragment = text.split("\n", 1)[1].rsplit("{{ end", 1)[0]
    fragment = fragment.replace("/Volumes/ext/state", str(external))
    path = str(tools) + (":" + str(selected) if state == "inherited" else "")
    script = fragment + '\n' + fragment + '\nfor tool in uv uvx python3 node codex gcloud; do command -v "$tool"; done\nprintf "%s\\n" "${MISE_DATA_DIR-unset}"\n'
    r = subprocess.run([executable, "-f", "-c", script], capture_output=True, text=True,
                       env={"HOME": str(home), "PATH": path, "MISE_DATA_DIR": str(store)})
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    expected = selected if state in {"clean", "inherited", "other-version"} else tools
    assert lines[:2] == [str(expected / name) for name in ["uv", "uvx"]]
    assert lines[2:6] == [str(tools / name) for name in ["python3", "node", "codex", "gcloud"]]
    assert lines[6] == ("unset" if state == "missing-marker" else str(store))


def test_both_profiles_include_uv_selection():
    for name in ["dot_common_profile.tmpl", "dot_zprofile.tmpl"]:
        assert '{{ includeTemplate "uv-path.sh" . }}' in (ROOT / name).read_text()
