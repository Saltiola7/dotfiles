"""Try Omarchy reuses personal settings without taking over guest integration."""
import importlib.machinery
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
DATA = {
    "machine_type": "omarchy-try",
    "name": "Test User",
    "email": "test@example.com",
    "atuin_sync_address": "https://api.atuin.sh",
    "chezmoi": {"os": "linux", "arch": "arm64", "homeDir": "/home/test"},
}
TARGETS = {
    ".bashrc", ".config/hypr/bindings.lua", ".config/hypr/input.lua", ".config/hypr/xdph.conf",
    ".config/kitty/kitty-query.py", ".config/kitty/kitty.conf",
    ".config/kitty/load-snapshot.py", ".config/kitty/mocha.conf",
    ".config/kitty/save-workspace.py", ".config/xdg-terminals.list",
    ".config/omarchy-apps/recipes.json", ".config/omarchy-apps/repository.txt",
    ".config/rustdesk-client/server.json", ".local/bin/omarchy-apps",
    ".local/bin/omarchy-rustdesk-client-setup",
    ".local/bin/try-omarchy-update", ".local/bin/try-omarchy-efi-audit",
    ".local/lib/omarchy-apps/recipes/rustdesk-bin/PKGBUILD",
    ".local/lib/omarchy-apps/recipes/rustdesk-bin/rustdesk-bin.install",
    ".local/state/omarchy/indicators/stay-awake", "apply-omarchy-theme.sh",
    "create-kitty-socket-dir.sh", "install-omarchy-apps",
    "start-omarchy-deskflow.sh",
    "setup-blackarch.sh",
    "setup-tailscale.sh",
    ".config/atuin/config.toml",
    "setup-shell-tooling.sh",
    ".config/deskflow/deskflow.conf", ".config/deskflow/deskflow-core.conf",
    ".config/systemd/user/omarchy-deskflow.service",
    ".config/systemd/user/citrix-ica-watch.service",
    ".config/systemd/user/citrix-ica-watch.path",
    ".local/bin/ica-autolaunch", ".local/share/mime/packages/ica.xml",
    ".config/systemd/user/herdr.service",
    ".config/systemd/user/graphical-session.target.wants/herdr.service",
    ".local/bin/omarchy-herdr-server", ".local/bin/omarchy-herdr-shell",
    ".local/bin/kitty-plain", ".local/share/applications/kitty-plain.desktop",
    ".config/autostart/chatgpt.desktop", ".config/autostart/kitty.desktop",
    "configure-desktop-startup.sh",
    ".local/share/applications/zen.desktop",
    ".local/share/icons/hicolor/16x16/apps/zen-browser.png",
    ".local/share/icons/hicolor/32x32/apps/zen-browser.png",
    ".local/share/icons/hicolor/48x48/apps/zen-browser.png",
    ".local/share/icons/hicolor/64x64/apps/zen-browser.png",
    ".local/share/icons/hicolor/128x128/apps/zen-browser.png",
    ".local/lib/omarchy-apps/recipes/icaclient/PKGBUILD",
    ".local/lib/omarchy-apps/recipes/icaclient/citrix-client.install",
    ".local/lib/omarchy-apps/recipes/icaclient/citrix-configmgr.desktop",
    ".local/lib/omarchy-apps/recipes/icaclient/citrix-conncenter.desktop",
    ".local/lib/omarchy-apps/recipes/icaclient/citrix-wfica.desktop",
    ".local/lib/omarchy-apps/recipes/icaclient/citrix-workspace.desktop",
    ".local/lib/omarchy-apps/recipes/icaclient/ctxcwalogd.service",
    ".local/lib/omarchy-apps/recipes/icaclient/ctxusbd.service",
    ".local/lib/omarchy-apps/recipes/icaclient/wfica.sh",
    ".local/lib/omarchy-apps/recipes/icaclient/wfica_assoc.sh",
}


def chezmoi(*args, data=None, text=None):
    return subprocess.run(
        ["chezmoi", "-S", str(ROOT), "--config", "/dev/null", "--config-format", "toml",
         "--override-data", json.dumps(data or DATA), *args], input=text,
        capture_output=True, text=True, check=True,
    ).stdout


def render(path, data=None):
    return chezmoi("execute-template", data=data, text=(ROOT / path).read_text())


def test_exact_guest_ownership_excludes_hardware_and_ai():
    assert set(chezmoi("managed", "--include", "files,scripts,symlinks").splitlines()) == TARGETS


def test_keyboard_is_finnish_without_replacing_try_devices():
    rendered = render("private_dot_config/hypr/input.lua.tmpl")
    assert 'kb_layout = "fi"' in rendered
    assert 'kb_variant = ""' in rendered
    assert 'resolve_binds_by_sym = true' in rendered
    for forbidden in ('hl.device', 'colemak_dh', 'parallels', 'dofile', 'kb_model'):
        assert forbidden not in rendered


def test_guest_workspace_bindings_do_not_capture_hp_at_macro():
    bindings = render("private_dot_config/hypr/bindings.lua.tmpl")
    assert 'for workspace = 1, 8 do' in bindings
    assert 'follow = false' in bindings
    assert 'SUPER + CTRL + SHIFT + ALT + ' in bindings
    assert 'SUPER + SPACE' in bindings
    assert 'pending_at' not in bindings
    assert 'wtype' not in bindings
    hp = render("private_dot_config/hypr/bindings.lua.tmpl", {**DATA, 'machine_type': 'omarchy'})
    assert 'pending_at' in hp
    assert 'for workspace = 1, 7 do' in hp
    assert 'kb_variant = "colemak_dh_ortho,' in render("private_dot_config/hypr/input.lua.tmpl", {**DATA, 'machine_type': 'omarchy'})
    assert 'natural_scroll = true' in render("private_dot_config/hypr/input.lua.tmpl", {**DATA, 'machine_type': 'omarchy'})
    assert 'natural_scroll = true' in render("private_dot_config/hypr/input.lua.tmpl", {**DATA, 'machine_type': 'omarchy'})


def test_recipes_select_native_architecture_and_essentials_only():
    # icaclient and zen are arm64-only recipes (x86_64 sources unverified/unpinned).
    expected_apps = {'arm64': {'pycharm', 'rustdesk-bin', 'icaclient', 'zen'},
                     'amd64': {'pycharm', 'rustdesk-bin'}}
    for arch, native, suffix in [('arm64', 'aarch64', '-aarch64'), ('amd64', 'x86_64', '')]:
        data = {**DATA, 'chezmoi': {**DATA['chezmoi'], 'arch': arch}}
        profile = json.loads(render("private_dot_config/omarchy-apps/recipes.json.tmpl", data))
        assert profile['architecture'] == native
        assert {r['name'] for r in profile['apps']} == expected_apps[arch]
        pycharm = next(r for r in profile['apps'] if r['name'] == 'pycharm')
        assert f'pycharm-2026.2.3{suffix}.tar.gz' in pycharm['url']
    packages = (ROOT / 'private_dot_config/omarchy-apps/repository.txt').read_text().splitlines()
    assert {p for p in packages if p and not p.startswith('#')} == {'python', 'curl', 'git', 'podman', 'deskflow'}


def test_apply_hook_renders_as_a_script_only_for_try():
    path = 'run_onchange_after_install-omarchy-apps.tmpl'
    script = render(path)
    assert script.startswith('#!/bin/bash\n')
    subprocess.run(['bash', '-n'], input=script, text=True, check=True)
    assert not render(path, {**DATA, 'machine_type': 'omarchy'}).strip()
    assert 'omarchy theme set catppuccin' in render('run_onchange_after_apply-omarchy-theme.sh.tmpl')
    routing = render('dot_local/bin/executable_omarchy-rustdesk-client-setup.tmpl')
    assert 'omarchy pkg aur add' not in routing
    assert 'omarchy-apps --install' in routing
    subprocess.run(['bash', '-n'], input=routing, text=True, check=True)


def load_installer():
    loader = importlib.machinery.SourceFileLoader('omarchy_try_apps', str(ROOT / 'dot_local/bin/executable_omarchy-apps'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_current_guest_installer_does_not_require_legacy_kernel_holds(monkeypatch):
    module = load_installer()
    calls = []
    monkeypatch.setattr(module, 'run', lambda command, **kwargs: calls.append(command))
    monkeypatch.setattr(module.platform, 'machine', lambda: 'aarch64')
    module.install_repository(['podman'])
    assert calls == [['sudo', 'pacman', '-Syu', '--needed', 'podman']]


def test_release_checksum_failure_preserves_existing_command(tmp_path, monkeypatch):
    module = load_installer()
    monkeypatch.setattr(module, 'LIB', tmp_path / 'bundles')
    monkeypatch.setattr(module, 'BIN', tmp_path / 'bin')
    (tmp_path / 'bin').mkdir()
    existing = tmp_path / 'bin' / 'pycharm'
    existing.write_text('existing application')

    def bad_download(recipe, directory):
        archive = directory / 'release.download'
        archive.write_bytes(b'not the expected release')
        module.verify_digest(archive, recipe['sha256'])
        return archive

    monkeypatch.setattr(module, 'download', bad_download)
    with pytest.raises(ValueError, match='checksum mismatch'):
        module.install_release({'name': 'pycharm', 'command': 'pycharm', 'version': 'test', 'sha256': '0' * 64})
    assert existing.read_text() == 'existing application'
    assert not list((tmp_path / 'bundles').iterdir())


def test_native_share_picker_is_scoped_to_try_guest():
    picker = ROOT / "private_dot_config/hypr/xdph.conf"
    assert "custom_picker_binary = /usr/bin/hyprland-share-picker" in picker.read_text()
    for machine, os_name in [("omarchy", "linux"), ("mac-mini", "darwin")]:
        data = {**DATA, "machine_type": machine, "chezmoi": {**DATA["chezmoi"], "os": os_name}}
        assert ".config/hypr/xdph.conf" not in chezmoi("managed", "--include", "files", data=data).splitlines()

# CI trigger 202611-17: path-filtered test workflow must report on branch updates.

# CI trigger 202611-17b: re-run after 92 merge.

# CI trigger 20261117c

# CI nudge

# CI nudge

# CI nudge

# CI nudge

# CI trigger 20261118: path-filtered test run for blackarch fixes.

# CI trigger 20261118b: post-99 merge.

# CI trigger 20261118c.

# CI trigger 20261118d: omarchy-common herdr.

# CI trigger 20261118f.

# CI trigger 20261118h.

# CI trigger 20261118i.

# CI trigger 20261118j.

# CI trigger 20261118k.

# CI trigger 20261118l.
