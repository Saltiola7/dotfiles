"""Espanso public machine settings exist only where the operator enabled them."""
import hashlib
import json
import os
import pty
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
CHEZMOI = shutil.which("chezmoi")
pytestmark = pytest.mark.skipif(CHEZMOI is None, reason="chezmoi renders the host profile")

UNIT = ".config/systemd/user/espanso.service"
SYNC = {"load-espanso-matches.sh", ".local/bin/espanso-match-sync"}
LINUX_PUBLIC = {
    ".config/espanso/config/default.yml",
    UNIT,
    ".config/systemd/user/graphical-session.target.wants/espanso.service",
    "start-espanso.sh",
}
MAC_CONFIG = "Library/Application Support/espanso/config/default.yml"
ENABLED = {"espanso_enabled": True}
ENROLL = {"espanso_private_checkout": "/srv/dotfiles-private",
          "espanso_private_origin": "https://forge.example/tis/dotfiles-private.git"}
SOURCE_ARCHIVE = "3121627138be4b1f106b8dfd73fb4b7030ecb44c6a8f4e7628a1174b58e5cfe2"
RECIPE = "dot_local/lib/omarchy-apps/recipes/espanso-wayland"
GUEST_RECIPE = {f".local/lib/omarchy-apps/recipes/espanso-wayland/{name}"
                for name in ("PKGBUILD", "espanso-wayland.install")}


def profile(machine_type, os_name, arch, hostname):
    return {
        "machine_type": machine_type, "name": "Test User", "email": "test@example.com",
        "atuin_sync_address": "https://api.atuin.sh",
        "chezmoi": {"os": os_name, "arch": arch, "homeDir": "/home/test", "hostname": hostname},
    }


GUEST = profile("omarchy-try", "linux", "arm64", "try-omarchy")
HP = profile("omarchy", "linux", "amd64", "hp-omarchy")
MBP = profile("omarchy", "linux", "arm64", "mbp-omarchy")
OLD = profile("omarchy", "linux", "amd64", "old-omarchy")
MAC = profile("mac-mini", "darwin", "arm64", "mac-mini")
MACBOOK = profile("macbook", "darwin", "arm64", "ts-mbp")


def chezmoi(*args, data, source=ROOT, text=None):
    return subprocess.run(
        ["chezmoi", "-S", str(source), "--config", "/dev/null", "--config-format", "toml",
         "--override-data", json.dumps(data), *args],
        capture_output=True, text=True, check=True, input=text,
    ).stdout


def render(path, data):
    return chezmoi("execute-template", data=data, text=(ROOT / path).read_text())


def managed(data, source=ROOT, include="files,scripts,symlinks"):
    return set(chezmoi("managed", "--include", include, data=data, source=source).splitlines())


@pytest.mark.parametrize("data", [GUEST, HP, MBP, OLD, MAC, MACBOOK])
def test_espanso_is_silent_until_the_operator_opts_in(data):
    # The Omarchy unit was already managed before this feature; nothing else appears.
    touched = (LINUX_PUBLIC | SYNC | {MAC_CONFIG} | GUEST_RECIPE) - {UNIT}
    assert managed(data) & touched == set()


@pytest.mark.parametrize("data", [HP, MBP, OLD])
def test_omarchy_unit_stays_managed_as_before(data):
    assert UNIT in managed(data)


def test_enabled_guest_owns_config_unit_enablement_start_and_recipe():
    assert managed({**GUEST, **ENABLED}) - managed(GUEST) == LINUX_PUBLIC | GUEST_RECIPE
    assert managed({**GUEST, **ENABLED, **ENROLL}) - managed(GUEST) == LINUX_PUBLIC | GUEST_RECIPE | SYNC


def test_enrollment_adds_only_the_sync_without_enablement():
    assert managed({**GUEST, **ENROLL}) - managed(GUEST) == SYNC


def test_amd64_guest_and_old_omarchy_stay_out_of_scope():
    guest = profile("omarchy-try", "linux", "amd64", "try-omarchy")
    for data in (guest, OLD):
        assert managed({**data, **ENABLED, **ENROLL}) - managed(data) == set()


@pytest.mark.parametrize("data", [HP, MBP])
def test_enabled_omarchy_hosts_gain_config_enablement_and_start(data):
    assert managed({**data, **ENABLED}) - managed(data) == LINUX_PUBLIC - {UNIT}
    assert managed({**data, **ENABLED, **ENROLL}) - managed(data) == (LINUX_PUBLIC | SYNC) - {UNIT}


def test_mac_mini_manages_only_its_stock_config_when_enabled():
    assert managed({**MAC, **ENABLED}) - managed(MAC) == {MAC_CONFIG}
    assert managed({**MAC, **ENABLED, **ENROLL}) - managed(MAC) == {MAC_CONFIG} | SYNC
    assert managed({**MACBOOK, **ENABLED, **ENROLL}) - managed(MACBOOK) == set()


@pytest.mark.parametrize("leaks", [
    ["private_dot_config/espanso/match/base.yml",
     "private_dot_config/espanso/packages/one/match.yml",
     "private_Library/Application Support/espanso/match/base.yml"],
    ["dot_config/espanso/match/nested/base.yml",
     "Library/Application Support/espanso/packages/base.yml"],
])
def test_match_trees_stay_private_on_every_platform(tmp_path, leaks):
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy(ROOT / ".chezmoiignore", source / ".chezmoiignore")
    for name in leaks:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("matches: []\n")
    for data in (GUEST, HP, MBP, OLD, MAC, MACBOOK):
        for extra in ({}, ENABLED, {**ENABLED, **ENROLL}):
            leaves = managed({**data, **extra}, source=source, include="files")
            assert not [leaf for leaf in leaves if "/match/" in leaf or "/packages/" in leaf]


def test_git_ignores_match_trees_and_keeps_machine_settings(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(ROOT / ".gitignore", repo / ".gitignore")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    def ignored(*parts):
        path = repo.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")
        return subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", "/".join(parts)]).returncode == 0

    for parts in (("private_dot_config", "espanso", "match", "base.yml"),
                  ("private_Library", "Application Support", "espanso", "match", "base.yml"),
                  ("dot_config", "espanso", "match", "base.yml")):
        assert ignored(*parts), parts
    assert ignored("espanso-private", "base.yml")
    for parts in (("private_dot_config", "espanso", "config", "default.yml.tmpl"),
                  ("private_Library", "Application Support", "espanso", "config", "default.yml")):
        assert not ignored(*parts), parts


def test_machine_settings_match_each_keyboard():
    guest = render("private_dot_config/espanso/config/default.yml.tmpl", GUEST)
    assert guest.endswith("toggle_key: OFF\nkeyboard_layout:\n  layout: fi\n")
    for absent in ("variant", "colemak"):
        assert absent not in guest
    hp = render("private_dot_config/espanso/config/default.yml.tmpl", HP)
    assert hp == render("private_dot_config/espanso/config/default.yml.tmpl", MBP)
    assert "layout: us\n  variant: colemak_dh_ortho\n" in hp and "toggle_key: OFF" in hp


def test_mac_config_is_the_byte_identical_stock_file():
    config = ROOT / "private_Library/Application Support/espanso/config/default.yml"
    raw = config.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "cf8f40f250c263655a008b004f2c37d0f937a607bcac2500b888dee64de17a0e"
    assert not raw.endswith(b"\n")
    assert all(not line.strip() or line.startswith(b"#") for line in raw.split(b"\n"))


def test_guest_recipe_is_pinned_native_and_opt_in():
    def names(data):
        return {r["name"] for r in json.loads(render("private_dot_config/omarchy-apps/recipes.json.tmpl", data))["apps"]}

    assert "espanso-wayland" not in names(GUEST)
    assert "espanso-wayland" not in names(profile("omarchy-try", "linux", "amd64", "try-omarchy") | ENABLED)
    entry, = [r for r in json.loads(render("private_dot_config/omarchy-apps/recipes.json.tmpl", GUEST | ENABLED))["apps"]
              if r["name"] == "espanso-wayland"]
    assert entry["command"] == "espanso" and entry["method"] == "aur" and entry["recipe"] == "espanso-wayland"
    pkgbuild = (ROOT / RECIPE / "PKGBUILD").read_text()
    assert f"sha256sums=('{SOURCE_ARCHIVE}')" in pkgbuild
    for phrase in ("pkgver=2.4.1", "arch=(aarch64)", "$url/archive/refs/tags/v$pkgver.tar.gz",
                   "cargo build --frozen --release", "--features wayland",
                   "--manifest-path espanso/Cargo.toml", "makedepends=(cargo)"):
        assert phrase in pkgbuild
    assert "systemd" not in pkgbuild and "install -Dm755" in pkgbuild
    hook = (ROOT / RECIPE / "espanso-wayland.install").read_text()
    assert 'setcap "cap_dac_override+p" /usr/bin/espanso' in hook
    assert "# Espanso recipe: " in render("run_onchange_after_install-omarchy-apps.tmpl", GUEST)
    assert (ROOT / "run_onchange_after_install-omarchy-apps.tmpl").read_text().count(RECIPE) == 1


def test_sync_script_renders_only_for_enrolled_hosts_and_never_applies():
    inert = render("run_after_load-espanso-matches.sh.tmpl", GUEST)
    assert inert.strip() == "exit 0"
    script = render("run_after_load-espanso-matches.sh.tmpl", GUEST | ENABLED | ENROLL)
    subprocess.run(["bash", "-n"], input=script, text=True, check=True)
    assert '--checkout "/srv/dotfiles-private"' in script
    assert '--origin "https://forge.example/tis/dotfiles-private.git"' in script
    for forbidden in ("chezmoi apply", "chezmoi update", "git push", "espanso service", "systemctl"):
        assert forbidden not in script
    for data in (OLD, MACBOOK, profile("omarchy-try", "linux", "amd64", "try-omarchy") | ENABLED | ENROLL):
        assert render("run_after_load-espanso-matches.sh.tmpl", data).strip() == "exit 0"


def test_sync_runs_only_in_an_unqualified_full_apply(tmp_path):
    home = tmp_path / "home"
    fake = home / ".local/bin/espanso-match-sync"
    fake.parent.mkdir(parents=True)
    marker = tmp_path / "marker"
    fake.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{marker}"\n')
    fake.chmod(0o755)
    source = tmp_path / "source"
    source.mkdir()
    (source / "dot_x").write_text("x\n")
    (source / "run_after_load-espanso-matches.sh").write_text(
        render("run_after_load-espanso-matches.sh.tmpl", GUEST | ENABLED | ENROLL))

    def chezmoi_home(*args):
        return subprocess.run(
            ["chezmoi", "-S", str(source), "--config", "/dev/null", "--config-format", "toml",
             "--override-data", json.dumps(GUEST | ENABLED | ENROLL),
             "--persistent-state", str(tmp_path / "state.boltdb"), "--cache", str(tmp_path / "cache"), *args],
            env={**os.environ, "HOME": str(home)}, capture_output=True, text=True, check=True,
        ).stdout

    def runs():
        return marker.read_text().splitlines() if marker.exists() else []

    chezmoi_home("apply")
    assert len(runs()) == 1
    for preview in (("apply", str(home / ".x")), ("diff",), ("status",), ("apply", "--dry-run")):
        chezmoi_home(*preview)
        assert len(runs()) == 1, preview
    chezmoi_home("apply")
    assert len(runs()) == 2


def test_scripts_install_then_load_matches_then_start(tmp_path):
    # The first daemon start must see deployed matches, so the kernel order is a naming contract.
    source = tmp_path / "source"
    source.mkdir()
    (source / "run_onchange_after_install-omarchy-apps.sh").write_text("#!/bin/sh\necho install\n")
    (source / "run_after_load-espanso-matches.sh").write_text("#!/bin/sh\necho load\n")
    (source / "run_onchange_after_start-espanso.sh").write_text("#!/bin/sh\necho start\n")
    output = subprocess.run(
        ["chezmoi", "-S", str(source), "--config", "/dev/null", "--config-format", "toml",
         "--override-data", "{}", "--persistent-state", str(tmp_path / "state.boltdb"),
         "--cache", str(tmp_path / "cache"), "apply"],
        env={**os.environ, "HOME": str(tmp_path / "home")}, capture_output=True, text=True, check=True,
    ).stdout
    assert output.split() == ["install", "load", "start"]


def test_start_script_guards_binary_capability_and_session(tmp_path):
    script = render("run_onchange_after_start-espanso.sh.tmpl", GUEST | ENABLED)
    subprocess.run(["bash", "-n"], input=script, text=True, check=True)
    assert "graphical-session.target" in script and "systemctl --user start espanso.service" in script

    def run(binary, capability, graphical, active, data=GUEST | ENABLED):
        commands = tmp_path / "bin"
        shutil.rmtree(commands, ignore_errors=True)
        commands.mkdir()
        log = tmp_path / "systemd.log"
        binary_path = tmp_path / "espanso"
        binary_path.write_text("#!/bin/sh\n")
        binary_path.chmod(0o755)
        if not binary:
            binary_path.unlink()
        fakes = {
            "systemctl": '#!/bin/sh\necho "$*" >> "' + str(log) + '"\n'
                         'case " $* " in\n'
                         '  *" is-active "*" graphical-session.target ") exit ' + str(0 if graphical else 3) + ' ;;\n'
                         '  *" is-active "*" espanso.service ") exit ' + str(0 if active else 3) + ' ;;\n'
                         'esac\nexit 0\n',
            "getcap": '#!/bin/sh\necho "/usr/bin/espanso ' + ("cap_dac_override+p" if capability else "") + '"\n',
        }
        for name, body in fakes.items():
            path = commands / name
            path.write_text(body)
            path.chmod(0o755)
        home = tmp_path / "home"
        shutil.rmtree(home, ignore_errors=True)
        home.mkdir()
        log.unlink(missing_ok=True)
        result = subprocess.run(
            ["bash"], input=script, text=True, capture_output=True,
            env={"PATH": f"{commands}:/usr/bin:/bin", "HOME": str(home), "ESPANSO_BIN": str(binary_path),
                 "XDG_CACHE_HOME": str(home / ".cache")},
        )
        calls = log.read_text().splitlines() if log.exists() else []
        return result, calls, home

    missing, calls, home = run(binary=False, capability=True, graphical=True, active=False)
    assert missing.returncode == 0 and "missing" in missing.stderr and calls == []
    assert not (home / ".cache/espanso/kvs").exists()

    uncapped, calls, _ = run(binary=True, capability=False, graphical=True, active=False)
    assert uncapped.returncode == 0 and "cap_dac_override" in uncapped.stderr and calls == []

    started, calls, home = run(binary=True, capability=True, graphical=True, active=False)
    assert started.returncode == 0, started.stderr
    assert calls == ["--user daemon-reload", "--user is-active --quiet graphical-session.target",
                     "--user is-active --quiet espanso.service", "--user start espanso.service"]
    for key in ("has_completed_wizard", "has_displayed_welcome"):
        assert (home / ".cache/espanso/kvs" / key).read_text() == "true\n"

    for graphical, active in ((False, False), (True, True)):
        _, calls, _ = run(binary=True, capability=True, graphical=graphical, active=active)
        assert "start" not in " ".join(calls), (graphical, active)


def test_start_script_is_inert_when_disabled_or_off_profile():
    for data in (GUEST, OLD, MAC | ENABLED, profile("omarchy-try", "linux", "amd64", "try-omarchy") | ENABLED):
        assert render("run_onchange_after_start-espanso.sh.tmpl", data).strip() == "exit 0"


def test_enrollment_keys_pass_through_the_chezmoi_config():
    def initial_config(data):
        result = subprocess.run(
            ["chezmoi", "--config", "/dev/null", "--config-format", "toml", "--source", str(ROOT),
             "--override-data", json.dumps(data), "execute-template", "--init",
             "--file", str(ROOT / ".chezmoi.toml.tmpl")],
            capture_output=True, text=True, check=True,
        )
        return tomllib.loads(result.stdout)["data"]

    data = initial_config(GUEST | ENABLED | ENROLL)
    assert data["espanso_enabled"] is True
    assert data["espanso_private_checkout"] == "/srv/dotfiles-private"
    assert data["espanso_private_origin"] == "https://forge.example/tis/dotfiles-private.git"
    assert not [key for key in initial_config(GUEST) if key.startswith("espanso")]


def test_guest_example_config_documents_the_opt_in_without_private_hosts():
    example = (ROOT / "config.omarchy-try.example.toml").read_text()
    assert "# espanso_enabled = true" in example
    assert "espanso_private_checkout" in example and "espanso_private_origin" in example
    assert "tail62e96c" not in example


def test_feature_spec_states_the_contract():
    spec = (ROOT / "docs/specs/host_tool_maintenance/features/espanso.md").read_text()
    for phrase in (
        "Validate the configured origin and disjoint leaf ownership",
        "Never feed generated guest defaults back into private Git",
        "One guest expansion",
        "accTitle: Espanso leaf ownership",
        "accTitle: Enrolled full apply and private match sync",
        "Text Equivalent",
        SOURCE_ARCHIVE,
        "`diverged`",
        "`unowned-collision`",
    ):
        assert phrase in spec
    assert spec.count("```mermaid") == 2
    assert "tail62e96c" not in spec


def test_docs_describe_opt_in_enrollment_and_retire_the_legacy_add():
    readme = (ROOT / "README.md").read_text()
    for phrase in ("espanso_enabled", "espanso_private_checkout", "espanso_private_origin",
                   "espanso-match-sync"):
        assert phrase in readme
    assert "chezmoi-private/espanso.toml add" not in readme
    next_steps = (ROOT / "private_dot_config/omarchy-host/next-steps.md").read_text()
    assert "chezmoi-private/espanso.toml add" not in next_steps
    assert "espanso_enabled" in next_steps
    assert "espanso_enabled" in (ROOT / "docs/OMARCHY_TRY.md").read_text()


@pytest.mark.parametrize("installed,capability,arch,tty,code,installs", [
    (True, True, "x86_64", True, 0, False),
    (True, False, "x86_64", True, 1, False),
    (False, True, "x86_64", True, 0, True),
    (False, True, "x86_64", False, 1, False),
    (True, True, "aarch64", True, 1, False),
])
def test_helper_installs_and_verifies_without_owning_config_or_matches(
        tmp_path, installed, capability, arch, tty, code, installs):
    commands = tmp_path / "bin"
    commands.mkdir()
    home = tmp_path / "home"
    log = tmp_path / "calls.log"
    fakes = {
        "uname": f'#!/bin/sh\necho {arch}\n',
        "espanso": "#!/bin/sh\necho 'espanso 2.4.1'\n",
        "pacman": '#!/bin/sh\n[ "$1" = -Q ] && exit ' + str(0 if installed else 1) + '\necho "pacman $*" >> "' + str(log) + '"\n',
        "omarchy": '#!/bin/sh\necho "omarchy $*" >> "' + str(log) + '"\n',
        "systemctl": '#!/bin/sh\necho "systemctl $*" >> "' + str(log) + '"\n',
        "chezmoi": '#!/bin/sh\necho "chezmoi $*" >> "' + str(log) + '"\n',
        "getcap": '#!/bin/sh\n' + ('echo "/usr/bin/espanso cap_dac_override+p"\n' if capability else 'exit 1\n'),
    }
    test_dir = tmp_path / "run"
    test_dir.mkdir()
    for name, body in fakes.items():
        path = commands / name
        path.write_text(body)
        path.chmod(0o755)
    env = {"PATH": f"{commands}:/usr/bin:/bin", "HOME": str(home),
           "XDG_CONFIG_HOME": str(home / ".config"), "XDG_CACHE_HOME": str(home / ".cache"),
           "XDG_DATA_HOME": str(home / ".local/share")}
    if tty:
        master, slave = pty.openpty()
        try:
            result = subprocess.run(["bash", str(ROOT / "dot_local/bin/executable_omarchy-espanso-setup")],
                                    stdin=slave, capture_output=True, text=True, env=env)
        finally:
            os.close(master)
            os.close(slave)
    else:
        result = subprocess.run(["bash", str(ROOT / "dot_local/bin/executable_omarchy-espanso-setup")],
                                stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env)
    assert result.returncode == code, result.stderr
    calls = log.read_text().splitlines() if log.exists() else []
    assert ("omarchy pkg aur add espanso-wayland-bin" in calls) == installs
    assert not [call for call in calls if call.startswith(("systemctl", "chezmoi"))]
    if installed:
        assert not (home / ".config/espanso").exists()
        assert not (home / ".config/chezmoi-private").exists()
        assert not (home / ".local/share/chezmoi-private").exists()
    if not capability:
        assert "cap_dac_override" in result.stderr


def test_recovery_backup_still_covers_live_espanso_state():
    backup = (ROOT / "dot_local/bin/executable_omarchy-recovery-backup").read_text()
    for path in ('"$HOME/.config/espanso"', '"$HOME/.config/chezmoi-private"', '"$HOME/.local/share/chezmoi-private"'):
        assert path in backup
