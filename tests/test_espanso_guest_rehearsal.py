"""A real chezmoi apply of the Espanso slice into an isolated home, with system commands faked."""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_espanso_match_sync import BASE, GIT_ENV, World

ROOT = Path(__file__).parents[1]
pytestmark = pytest.mark.skipif(platform.machine() != "aarch64", reason="guest recipe is arm64-only")
FAKES = {
    "sudo": '#!/bin/sh\necho "sudo $*" >> "$REHEARSAL_LOG"\n'
            'case " $* " in *" pacman -U "*) printf \'#!/bin/sh\\nexit 0\\n\' > "$REHEARSAL_BIN/espanso"\n'
            '  chmod 755 "$REHEARSAL_BIN/espanso" ;; esac\n',
    "pacman": '#!/bin/sh\nif [ "$1" = -Q ]; then\n  case "$2" in python|curl|git|podman|deskflow) exit 0;; esac\n'
              '  exit 1\nfi\necho "pacman $*" >> "$REHEARSAL_LOG"\n',
    "makepkg": '#!/bin/sh\necho "makepkg $*" >> "$REHEARSAL_LOG"\n'
               ': > espanso-wayland-2.4.1-1-aarch64.pkg.tar.zst\n',
    "getcap": '#!/bin/sh\necho "/usr/bin/espanso cap_dac_override+p"\n',
    "systemctl": '#!/bin/sh\necho "systemctl $*" >> "$REHEARSAL_LOG"\n'
                 'case " $* " in\n'
                 '  *" is-active "*" graphical-session.target ") exit 0 ;;\n'
                 '  *" is-active "*" espanso.service ") exit 3 ;;\n'
                 '  *" start espanso.service ") [ -f "$HOME/.config/espanso/match/base.yml" ] '
                 '&& echo matches-present-at-start >> "$REHEARSAL_LOG" ;;\n'
                 'esac\nexit 0\n',
}
# Only the Espanso slice and the installer it needs; unrelated guest scripts stay out.
SLICE = {
    "run_onchange_after_install-omarchy-apps.sh": ("render", "run_onchange_after_install-omarchy-apps.tmpl"),
    "run_after_load-espanso-matches.sh": ("render", "run_after_load-espanso-matches.sh.tmpl"),
    "run_onchange_after_start-espanso.sh": ("render", "run_onchange_after_start-espanso.sh.tmpl"),
    "dot_config/omarchy-apps/recipes.json": ("render", "private_dot_config/omarchy-apps/recipes.json.tmpl"),
    "dot_config/espanso/config/default.yml.tmpl": ("copy", "private_dot_config/espanso/config/default.yml.tmpl"),
    "dot_config/systemd/user/espanso.service": ("copy", "private_dot_config/systemd/user/espanso.service"),
    "dot_config/systemd/user/graphical-session.target.wants/symlink_espanso.service": (
        "copy", "private_dot_config/systemd/user/graphical-session.target.wants/symlink_espanso.service"),
    "dot_local/bin/executable_espanso-match-sync": ("copy", "dot_local/bin/executable_espanso-match-sync"),
    "dot_local/bin/executable_omarchy-apps": ("copy", "dot_local/bin/executable_omarchy-apps"),
    "dot_config/omarchy-apps/repository.txt": ("copy", "private_dot_config/omarchy-apps/repository.txt"),
    "dot_local/lib/omarchy-apps/recipes/espanso-wayland/PKGBUILD": (
        "copy", "dot_local/lib/omarchy-apps/recipes/espanso-wayland/PKGBUILD"),
    "dot_local/lib/omarchy-apps/recipes/espanso-wayland/espanso-wayland.install": (
        "copy", "dot_local/lib/omarchy-apps/recipes/espanso-wayland/espanso-wayland.install"),
}


def test_guest_apply_installs_then_deploys_matches_then_starts(tmp_path):
    world = World(tmp_path)
    log, commands, source = tmp_path / "calls.log", tmp_path / "bin", tmp_path / "slice"
    commands.mkdir()
    for name, body in FAKES.items():
        (commands / name).write_text(body)
    for present in ("pycharm", "rustdesk", "wfica", "zen"):
        (commands / present).write_text("#!/bin/sh\nexit 0\n")
    for path in commands.iterdir():
        path.chmod(0o755)

    data = {
        "machine_type": "omarchy-try", "name": "Test User", "email": "test@example.com",
        "atuin_sync_address": "https://api.atuin.sh", **{"espanso_enabled": True},
        "espanso_private_checkout": str(world.checkout),
        "espanso_private_origin": str(world.origin),
        "chezmoi": {"os": "linux", "arch": "arm64", "homeDir": str(world.home),
                    "hostname": "try-omarchy"},
    }
    chezmoi = ["chezmoi", "-S", str(ROOT), "--config", "/dev/null", "--config-format", "toml",
               "--override-data", json.dumps(data)]
    for target, (kind, name) in SLICE.items():
        if kind == "copy":
            text = (ROOT / name).read_text()
        else:
            text = subprocess.run(chezmoi + ["execute-template"], input=(ROOT / name).read_text(),
                                  capture_output=True, text=True, check=True).stdout
        path = source / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def apply():
        return subprocess.run(
            ["chezmoi", "-S", str(source), "--config", "/dev/null", "--config-format", "toml",
             "--override-data", json.dumps(data), "--persistent-state", str(tmp_path / "state.boltdb"),
             "--cache", str(tmp_path / "cache"), "apply"],
            # XDG variables are exported on real desktops; keep every default under the scratch home.
            env={**os.environ, **GIT_ENV, "HOME": str(world.home),
                 "XDG_CONFIG_HOME": str(world.home / ".config"), "XDG_STATE_HOME": str(world.home / ".local/state"),
                 "XDG_CACHE_HOME": str(world.home / ".cache"),
                 "PATH": f"{commands}:{Path(shutil.which('chezmoi')).parent}:/usr/bin:/bin",
                 "ESPANSO_BIN": str(commands / "espanso"), "REHEARSAL_LOG": str(log),
                 "REHEARSAL_BIN": str(commands)},
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

    first = apply()
    assert first.returncode == 0, first.stderr
    settings = (world.config_root / "config/default.yml").read_text()
    assert settings.endswith("keyboard_layout:\n  layout: fi\n")
    assert (world.home / ".config/systemd/user/espanso.service").is_file()
    wants = world.home / ".config/systemd/user/graphical-session.target.wants/espanso.service"
    assert wants.is_symlink() and os.readlink(wants) == "../espanso.service"
    assert world.live() == BASE.encode()

    calls = log.read_text().splitlines()
    package = next(i for i, call in enumerate(calls) if call.startswith("sudo pacman -U --needed "))
    start = calls.index("systemctl --user start espanso.service")
    assert calls.index("makepkg --noconfirm --cleanbuild") == package - 1 < start, calls
    # The real sync ran before the first daemon start, so Espanso never generates its sample.
    assert "matches-present-at-start" in calls
    assert not [p for p in (world.home / ".local/state/omarchy-apps").iterdir() if p.is_dir()]

    before = world.snapshot()
    assert apply().returncode == 0
    assert world.snapshot() == before
    assert log.read_text().splitlines().count("systemctl --user start espanso.service") == 1
