"""Real chezmoi applies of the Espanso slice into an isolated home, with system commands faked."""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_espanso_match_sync import BASE, GIT_ENV, World

ROOT = Path(__file__).parents[1]
pytestmark = pytest.mark.skipif(shutil.which("chezmoi") is None, reason="chezmoi applies the slice")
FAKES = {
    "sudo": '#!/bin/sh\necho "sudo $*" >> "$REHEARSAL_LOG"\n'
            'case " $* " in *" pacman -U "*) printf \'#!/bin/sh\\nexit 0\\n\' > "$REHEARSAL_BIN/espanso"\n'
            '  chmod 755 "$REHEARSAL_BIN/espanso" ;; esac\n',
    "pacman": '#!/bin/sh\nif [ "$1" = -Q ]; then\n  case "$2" in python|curl|git|podman|deskflow) exit 0;; esac\n'
              '  exit 1\nfi\necho "pacman $*" >> "$REHEARSAL_LOG"\n',
    "makepkg": '#!/bin/sh\necho "makepkg $*" >> "$REHEARSAL_LOG"\n'
               ': > espanso-wayland-2.4.1-1-aarch64.pkg.tar.zst\n',
    "getcap": '#!/bin/sh\necho "/usr/bin/espanso cap_dac_override+p"\n',
    # The daemon remembers that it was started, like a real user manager would.
    "systemctl": '#!/bin/sh\necho "systemctl $*" >> "$REHEARSAL_LOG"\n'
                 'case " $* " in\n'
                 '  *" is-active "*" graphical-session.target ") exit 0 ;;\n'
                 '  *" is-active "*" espanso.service ") [ -e "$REHEARSAL_STATE" ] && exit 0\n'
                 '    exit 3 ;;\n'
                 '  *" start espanso.service ") touch "$REHEARSAL_STATE"\n'
                 '    [ -f "$HOME/.config/espanso/match/base.yml" ] '
                 '&& echo matches-present-at-start >> "$REHEARSAL_LOG" ;;\n'
                 'esac\nexit 0\n',
}
# Only the Espanso slice and, for the guest, the installer it needs; other guest scripts stay out.
SLICE = {
    "run_onchange_after_install-omarchy-apps.sh": ("render", "run_onchange_after_install-omarchy-apps.tmpl"),
    "run_after_load-espanso-matches.sh": ("render", "run_after_load-espanso-matches.sh.tmpl"),
    "run_after_start-espanso.sh": ("render", "run_after_start-espanso.sh.tmpl"),
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
SYNC_AND_START = ("run_after_load-espanso-matches.sh", "run_after_start-espanso.sh",
                  "dot_config/espanso/config/default.yml.tmpl", "dot_config/systemd/user/espanso.service",
                  "dot_config/systemd/user/graphical-session.target.wants/symlink_espanso.service",
                  "dot_local/bin/executable_espanso-match-sync")
INSTALLER = tuple(name for name in SLICE if name not in SYNC_AND_START)


class Stage:
    def __init__(self, tmp_path, present=()):
        self.world = World(tmp_path)
        self.log, self.commands, self.source = tmp_path / "calls.log", tmp_path / "bin", tmp_path / "slice"
        self.state, self.tmp_path = tmp_path / "service-active", tmp_path
        self.commands.mkdir()
        for name, body in FAKES.items():
            (self.commands / name).write_text(body)
        for name in present:
            (self.commands / name).write_text("#!/bin/sh\nexit 0\n")
        for path in self.commands.iterdir():
            path.chmod(0o755)
        self.data = {
            "machine_type": "omarchy-try", "name": "Test User", "email": "test@example.com",
            "atuin_sync_address": "https://api.atuin.sh", "espanso_enabled": True,
            "espanso_private_checkout": str(self.world.checkout),
            "espanso_private_origin": str(self.world.origin),
            "chezmoi": {"os": "linux", "arch": "arm64", "homeDir": str(self.world.home),
                        "hostname": "try-omarchy"},
        }

    def write_slice(self, targets):
        for target in targets:
            kind, name = SLICE[target]
            if kind == "copy":
                text = (ROOT / name).read_text()
            else:
                text = subprocess.run(
                    ["chezmoi", "-S", str(ROOT), "--config", "/dev/null", "--config-format", "toml",
                     "--override-data", json.dumps(self.data), "execute-template"],
                    input=(ROOT / name).read_text(), capture_output=True, text=True, check=True,
                ).stdout
            path = self.source / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    def apply(self):
        # XDG variables are exported on real desktops; keep every default under the scratch home.
        return subprocess.run(
            ["chezmoi", "-S", str(self.source), "--config", "/dev/null", "--config-format", "toml",
             "--override-data", json.dumps(self.data), "--persistent-state", str(self.tmp_path / "state.boltdb"),
             "--cache", str(self.tmp_path / "cache"), "apply"],
            env={**os.environ, **GIT_ENV, "HOME": str(self.world.home),
                 "XDG_CONFIG_HOME": str(self.world.home / ".config"),
                 "XDG_STATE_HOME": str(self.world.home / ".local/state"),
                 "XDG_CACHE_HOME": str(self.world.home / ".cache"),
                 "PATH": f"{self.commands}:{Path(shutil.which('chezmoi')).parent}:/usr/bin:/bin",
                 "ESPANSO_BIN": str(self.commands / "espanso"), "REHEARSAL_LOG": str(self.log),
                 "REHEARSAL_BIN": str(self.commands), "REHEARSAL_STATE": str(self.state)},
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []


def assert_settings_and_matches(stage):
    settings = (stage.world.config_root / "config/default.yml").read_text()
    assert settings.endswith("keyboard_layout:\n  layout: fi\n")
    assert (stage.world.home / ".config/systemd/user/espanso.service").is_file()
    wants = stage.world.home / ".config/systemd/user/graphical-session.target.wants/espanso.service"
    assert wants.is_symlink() and os.readlink(wants) == "../espanso.service"
    assert stage.world.live() == BASE.encode()


def test_real_apply_deploys_matches_before_the_service_ever_starts(tmp_path):
    stage = Stage(tmp_path, present=("espanso",))
    stage.write_slice(SYNC_AND_START)
    first = stage.apply()
    assert first.returncode == 0, first.stderr
    assert_settings_and_matches(stage)
    calls = stage.calls()
    start = calls.index("systemctl --user start espanso.service")
    assert calls.index("systemctl --user daemon-reload") < start
    # The real sync ran before the first daemon start, so Espanso never generates its sample.
    assert calls.index("matches-present-at-start") == len(calls) - 1

    before = stage.world.snapshot()
    assert stage.apply().returncode == 0
    assert stage.world.snapshot() == before
    assert stage.calls().count("systemctl --user start espanso.service") == 1


def test_start_is_retried_on_every_apply_until_the_binary_exists(tmp_path):
    stage = Stage(tmp_path)
    stage.write_slice(SYNC_AND_START)
    absent = stage.apply()
    assert absent.returncode == 0, absent.stderr
    assert "missing" in absent.stderr
    assert not [call for call in stage.calls() if "systemctl" in call]
    assert stage.world.live() == BASE.encode()

    (stage.commands / "espanso").write_text("#!/bin/sh\nexit 0\n")
    (stage.commands / "espanso").chmod(0o755)
    present = stage.apply()
    assert present.returncode == 0, present.stderr
    assert "systemctl --user start espanso.service" in stage.calls()


@pytest.mark.skipif(platform.machine() != "aarch64", reason="guest recipe is arm64-only")
def test_guest_apply_installs_the_package_before_the_first_start(tmp_path):
    stage = Stage(tmp_path, present=("pycharm", "rustdesk", "wfica", "zen"))
    stage.write_slice(SLICE)
    first = stage.apply()
    assert first.returncode == 0, first.stderr
    assert_settings_and_matches(stage)
    calls = stage.calls()
    package = next(i for i, call in enumerate(calls) if call.startswith("sudo pacman -U --needed "))
    start = calls.index("systemctl --user start espanso.service")
    build = calls.index("makepkg --noconfirm --cleanbuild")
    dependencies = next(i for i, call in enumerate(calls) if call.startswith("sudo pacman -S --needed "))
    assert dependencies < build == package - 1 < start, calls
    # Omarchy's pacman guard rejects a direct system upgrade; dependencies are a plain sync.
    assert not [call for call in calls if "-Syu" in call], calls
    assert "matches-present-at-start" in calls
    assert not [p for p in (stage.world.home / ".local/state/omarchy-apps").iterdir() if p.is_dir()]
