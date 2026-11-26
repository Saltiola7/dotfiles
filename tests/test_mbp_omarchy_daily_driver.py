import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_borg_backup_targets_mini_with_keepalive_and_guarded_prune():
    script = (ROOT / "dot_local/bin/executable_mbp-omarchy-borg-backup").read_text()
    assert "tis@mac-mini" in script
    assert "ServerAliveInterval=15" in script and "ServerAliveCountMax=4" in script
    assert "--glob-archives" in script and "mbp-omarchy-*" in script
    assert "/home/tis" in script


def test_systemd_units_schedule_nightly_backup():
    service = (ROOT / "private_dot_config/systemd/user/mbp-omarchy-borg-backup.service").read_text()
    timer = (ROOT / "private_dot_config/systemd/user/mbp-omarchy-borg-backup.timer").read_text()
    assert "%h/.local/bin/mbp-omarchy-borg-backup" in service
    assert "OnCalendar=*-*-* 04:00:00" in timer
    assert "Persistent=true" in timer


def test_ignore_gates_mbp_omarchy_targets_to_the_laptop():
    ignore = (ROOT / ".chezmoiignore").read_text()
    assert 'hasPrefix "mbp-omarchy" .chezmoi.hostname' in ignore
    for target in (
        ".local/bin/mbp-omarchy-borg-backup",
        ".config/systemd/user/mbp-omarchy-borg-backup.service",
        ".config/systemd/user/mbp-omarchy-borg-backup.timer",
    ):
        assert target in ignore


def test_asahi_hardware_script_guards_and_applies_idempotently():
    script = (ROOT / "run_always_mbp-asahi-hardware.sh.tmpl").read_text()
    assert 'hasPrefix "mbp-omarchy" .chezmoi.hostname' in script
    assert "[[ -t 0 ]]" in script  # sudo needs a terminal; stay silent otherwise
    assert "90-mbp-backlight.rules" in script
    assert "90-kbd-backlight-off.rules" in script
    assert "usermod -aG video" in script
    assert "tiny-dfr" in script


def test_omarchy_remote_access_script_gates_and_is_idempotent():
    script = (ROOT / "run_always_install-omarchy-remote-access.sh.tmpl").read_text()
    assert 'eq .machine_type "omarchy"' in script
    assert "[[ -t 0 ]]" in script
    assert "rustdesk-bin" in script


def test_input_template_maps_both_builtin_keyboard_transports():
    tmpl = (ROOT / "private_dot_config/hypr/input.lua.tmpl").read_text()
    assert '"at-translated-set-2-keyboard"' in tmpl  # x86 (HP)
    assert '"apple-spi-keyboard"' in tmpl  # M1 Apple Silicon


def test_fcitx5_autostart_suppressed_on_mbp():
    ignore = (ROOT / ".chezmoiignore").read_text()
    desktop = (ROOT / "private_dot_config/autostart/org.fcitx.Fcitx5.desktop").read_text()
    assert "org.fcitx.Fcitx5.desktop" in ignore
    assert "Hidden=true" in desktop  # fcitx5 feeds apps its own fi/QWERTY layout


def test_mbp_brightness_keys_target_internal_display_with_osd():
    tmpl = (ROOT / "private_dot_config/hypr/bindings.lua.tmpl").read_text()
    assert 'hasPrefix "mbp-omarchy" .chezmoi.hostname' in tmpl
    for key, step in (("Up", "+5%"), ("Down", "5%-")):
        assert f'"XF86MonBrightness{key}", "Brightness {key.lower()}", "omarchy-brightness-display --monitor eDP-1 {step}"' in tmpl


def test_fcitx5_dbus_activation_masked():
    mask = ROOT / "symlink_.config/systemd/user/org.fcitx.FcitX5.service"
    assert mask.read_text().strip() == "/dev/null"
    assert "org.fcitx.FcitX5.service" in (ROOT / ".chezmoiignore").read_text()


def test_waynergy_package_builds_on_apple_silicon():
    pkgbuild = (ROOT / "private_dot_config/omarchy-host/waynergy-package/PKGBUILD").read_text()
    assert "aarch64" in pkgbuild


def test_uwsm_env_clears_ime_and_is_gated():
    env = (ROOT / "private_dot_config/uwsm/env").read_text()
    assert "QT_IM_MODULE=" in env and "GTK_IM_MODULE=" in env
    assert ".config/uwsm/env" in (ROOT / ".chezmoiignore").read_text()


def test_fcitx5_disable_enforced_on_every_apply():
    script = (ROOT / "run_always_disable-fcitx5-mbp.sh.tmpl").read_text()
    assert "omarchy-fcitx5.service" in script
    assert "disable --now" in script


def test_waynergy_install_converges_via_apply():
    script = (ROOT / "run_always_install-waynergy.sh.tmpl").read_text()
    assert 'eq .machine_type "omarchy"' in script
    assert 'waynergy_enabled' in script  # per-host opt-out; default keeps existing hosts
    assert "[[ -t 0 ]]" in script
    assert "omarchy-waynergy-install" in script
    assert "enable --now omarchy-waynergy.service" in script


def test_waynergy_targets_opt_out_per_omarchy_host():
    # Default-on keeps mbp-omarchy and hp-omarchy unchanged; a host sets
    # waynergy_enabled = false (old-omarchy) to stop deploying the client.
    ignore = (ROOT / ".chezmoiignore").read_text()
    assert '$waynergyEnabled = .waynergy_enabled' in ignore
    assert "{{ if $waynergyEnabled }}!.config/systemd/user/omarchy-waynergy.service{{ end }}" in ignore
    assert "{{ if $waynergyEnabled }}!.config/omarchy-host/waynergy-package/" in ignore
    assert "{{ else }}.config/omarchy-host/waynergy-package/{{ end }}" in ignore
    assert "{{ if $waynergyEnabled }}!always_install-waynergy.sh{{ end }}" in ignore
    config_tmpl = (ROOT / ".chezmoi.toml.tmpl").read_text()
    assert "waynergy_enabled" in config_tmpl


def test_omarchy_allowlist_actually_reincludes_mbp_targets():
    # The omarchy profile ignores * and re-includes explicitly; anything
    # missing here silently never deploys on the host.
    ignore = (ROOT / ".chezmoiignore").read_text()
    for entry in (
        "!always_install-waynergy.sh",
        "!always_install-omarchy-remote-access.sh",
        "!always_mbp-asahi-hardware.sh",
        "!always_disable-fcitx5-mbp.sh",
        "!.config/uwsm/env",
        "!.local/bin/mbp-omarchy-borg-backup",
        "!.config/systemd/user/mbp-omarchy-borg-backup.service",
        "!.config/systemd/user/mbp-omarchy-borg-backup.timer",
        "!.config/systemd/user/org.fcitx.FcitX5.service",
        "!.config/autostart/org.fcitx.Fcitx5.desktop",
    ):
        assert entry in ignore, f"allowlist missing {entry}"
