import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]


def text(path):
    return (ROOT / path).read_text()


def test_lmsh_profile_is_portable_and_excludes_credentials():
    assert '"machine_type" "Machine type (macbook/mac-mini/lmsh)" "macbook"' in text(
        ".chezmoi.toml.tmpl"
    )
    assert "macbook/mac-mini/lmsh" in text(".chezmoi.toml.tmpl")
    assert "atuin_sync_address" in text(".chezmoi.toml.tmpl")
    ignored = text(".chezmoiignore")
    assert '{{ if eq .machine_type "lmsh" }}' in ignored

    bashrc = text("dot_bashrc.tmpl")
    for tool in ("atuin", "zoxide", "starship"):
        assert f"command -v {tool}" in bashrc
    assert '{{ if eq .machine_type "lmsh" -}}' in bashrc
    assert "[ -t 0 ]" in bashrc

    profile = text("dot_common_profile.tmpl")
    assert 'export ATUIN_DATA_DIR="{{ .chezmoi.homeDir }}/.local/share/atuin"' in profile
    assert '{{ if eq .machine_type "lmsh" -}}' in profile
    lmsh, macos = profile.split("{{ else -}}", 1)
    assert "/opt/homebrew" not in lmsh
    assert "ATUIN_DATA_DIR" in lmsh
    assert "/Applications" not in lmsh
    assert "/opt/homebrew" in macos


def test_mac_mini_uses_native_external_cache_paths():
    profile = text("dot_common_profile.tmpl")
    assert '[ -f "/Volumes/ext/state/.dotfiles-ai-state" ]' in profile
    for setting in (
        'LIMA_HOME="/Volumes/ext/state/lima"',
        'COLIMA_HOME="/Volumes/ext/state/colima"',
        'COLIMA_CACHE_HOME="/Volumes/ext/state/cache/colima"',
        'PLAYWRIGHT_BROWSERS_PATH="$DOTFILES_CACHE_ROOT/playwright"',
        'UV_CACHE_DIR="$DOTFILES_CACHE_ROOT/uv"',
        'PRE_COMMIT_HOME="$DOTFILES_CACHE_ROOT/pre-commit"',
        'npm_config_cache="$DOTFILES_CACHE_ROOT/npm"',
        'PULUMI_HOME="/Volumes/ext/state/pulumi"',
        'PREFECT_HOME="/Volumes/ext/state/prefect/seo-data-science"',
        'CODEX_HOME="/Volumes/ext/state/codex/home"',
        'PYCHARM_PROPERTIES="/Volumes/ext/state/jetbrains/PyCharm2026.2/idea.properties"',
    ):
        assert setting in profile
    for variable in (
        "DOTFILES_CACHE_ROOT",
        "PLAYWRIGHT_BROWSERS_PATH",
        "UV_CACHE_DIR",
        "PRE_COMMIT_HOME",
        "npm_config_cache",
        "PULUMI_HOME",
        "PREFECT_HOME",
        "CODEX_HOME",
        "PYCHARM_PROPERTIES",
    ):
        assert f'unset {variable}' in profile


def cache_env_script(sentinel):
    profile = text("dot_common_profile.tmpl")
    return profile.split('{{ if eq .machine_type "mac-mini" -}}', 1)[1].split("{{ end -}}", 1)[0].replace(
        "/Volumes/ext/state/.dotfiles-ai-state", str(sentinel)
    )


def test_external_cache_exports_and_fallback(tmp_path):
    sentinel = tmp_path / "sentinel"
    script = cache_env_script(sentinel)
    managed = {
        "DOTFILES_CACHE_ROOT": "/Volumes/ext/state/cache",
        "PLAYWRIGHT_BROWSERS_PATH": "/Volumes/ext/state/cache/playwright",
        "UV_CACHE_DIR": "/Volumes/ext/state/cache/uv",
        "PRE_COMMIT_HOME": "/Volumes/ext/state/cache/pre-commit",
        "npm_config_cache": "/Volumes/ext/state/cache/npm",
        "PULUMI_HOME": "/Volumes/ext/state/pulumi",
        "PREFECT_HOME": "/Volumes/ext/state/prefect/seo-data-science",
        "CODEX_HOME": "/Volumes/ext/state/codex/home",
        "PYCHARM_PROPERTIES": "/Volumes/ext/state/jetbrains/PyCharm2026.2/idea.properties",
    }

    shells = [shell for shell in ("/bin/bash", "/bin/zsh") if Path(shell).exists()]
    assert shells
    for shell in shells:
        sentinel.touch()
        exported = subprocess.run(
            [shell, "-c", script + "\nenv"], check=True, capture_output=True, text=True
        ).stdout
        for name, value in managed.items():
            assert f"{name}={value}" in exported

        sentinel.unlink()
        inherited = os.environ | managed | {"UV_CACHE_DIR": "/custom/uv"}
        fallback = subprocess.run(
            [shell, "-c", script + "\nenv"], env=inherited, check=True, capture_output=True, text=True
        ).stdout
        assert "UV_CACHE_DIR=/custom/uv" in fallback
        for name in managed.keys() - {"UV_CACHE_DIR"}:
            assert f"{name}=" not in fallback


def test_mac_mini_gui_state_paths_are_scoped_and_native():
    ignored = text(".chezmoiignore")
    mac_mini = ignored.split('{{ if ne .machine_type "mac-mini" }}', 1)[1].split("{{ end }}", 1)[0]
    assert "Library/LaunchAgents/dev.dotfiles.runtime-state.plist" in mac_mini
    assert ".local/bin/configure-runtime-state" in mac_mini
    assert "Library/LaunchAgents/dev.dotfiles.colima-atuin.plist" in mac_mini
    assert ".local/bin/start-colima-atuin" in mac_mini
    runtime_state = text("dot_local/bin/executable_configure-runtime-state")
    assert "/Volumes/ext/state/.dotfiles-ai-state" in runtime_state
    assert "codex_home=/Volumes/ext/state/codex/home" in runtime_state
    assert "pycharm_properties=/Volumes/ext/state/jetbrains/PyCharm2026.2/idea.properties" in runtime_state
    for variable in ("CODEX_HOME", "PYCHARM_PROPERTIES"):
        assert f"/bin/launchctl setenv {variable}" in runtime_state
        assert f"/bin/launchctl unsetenv {variable}" in runtime_state
    launch_agent = text("private_Library/LaunchAgents/dev.dotfiles.runtime-state.plist.tmpl")
    assert "<key>WatchPaths</key>" in launch_agent
    assert "<key>StartInterval</key>" in launch_agent


def test_colima_atuin_service_requires_external_state(tmp_path):
    state = tmp_path / "state"
    sentinel = state / ".dotfiles-ai-state"
    lima = state / "lima"
    colima = state / "colima"
    cache = state / "cache/colima"
    fake = tmp_path / "colima"
    fake_mount = tmp_path / "mount"
    output = tmp_path / "output"
    fake.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$LIMA_HOME|$COLIMA_HOME|$COLIMA_CACHE_HOME|$*\" >\"$OUTPUT\"\n"
    )
    fake.chmod(0o755)
    fake_mount.write_text("#!/bin/sh\nprintf '/dev/test on %s (apfs, local)\\n' \"$MOUNT_ROOT\"\n")
    fake_mount.chmod(0o755)
    script = (
        text("dot_local/bin/executable_start-colima-atuin")
        .replace("/Volumes/ext/state", str(state))
        .replace("/opt/homebrew/bin/colima", str(fake))
        .replace("/sbin/mount", str(fake_mount))
    )
    assert 'PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"' in script

    env = os.environ | {"OUTPUT": str(output), "MOUNT_ROOT": str(tmp_path)}
    subprocess.run(["/bin/sh", "-c", script], env=env, check=True)
    assert not output.exists()

    for path in (lima, colima, cache):
        path.mkdir(parents=True, exist_ok=True)
    sentinel.touch()
    subprocess.run(["/bin/sh", "-c", script], env=env, check=True)
    assert output.read_text().strip() == f"{lima}|{colima}|{cache}|start -f"

    output.unlink()
    assert subprocess.run(
        ["/bin/sh", "-c", script], env=env | {"MOUNT_ROOT": "/wrong"}
    ).returncode != 0
    assert not output.exists()

    plist = text("private_Library/LaunchAgents/dev.dotfiles.colima-atuin.plist.tmpl")
    assert "executable_start-colima-atuin" not in plist
    assert "/.local/bin/start-colima-atuin" in plist
    assert "<key>RunAtLoad</key>" in plist
    assert "<key>StartInterval</key>" in plist

    bootstrap = text("run_onchange_after_bootstrap-colima-atuin.sh.tmpl")
    assert '{{ if ne .machine_type "mac-mini" -}}' in bootstrap
    assert "launchctl bootout" in bootstrap
    assert "launchctl bootstrap" in bootstrap


def test_gui_state_controller_tracks_sentinel_without_overwriting_custom_values(tmp_path):
    sentinel = tmp_path / "sentinel"
    state = tmp_path / "launchctl-state"
    state.mkdir()
    launchctl = tmp_path / "launchctl"
    launchctl.write_text(
        """#!/bin/sh
case "$1" in
    setenv) printf '%s' "$3" > "$LAUNCHCTL_STATE/$2" ;;
    getenv) cat "$LAUNCHCTL_STATE/$2" 2>/dev/null ;;
    unsetenv) rm -f "$LAUNCHCTL_STATE/$2" ;;
esac
"""
    )
    launchctl.chmod(0o755)
    script = (
        text("dot_local/bin/executable_configure-runtime-state")
        .replace("/Volumes/ext/state/.dotfiles-ai-state", str(sentinel))
        .replace("/bin/launchctl", str(launchctl))
    )
    env = os.environ | {"LAUNCHCTL_STATE": str(state)}

    sentinel.touch()
    subprocess.run(["/bin/sh", "-c", script], env=env, check=True)
    assert (state / "CODEX_HOME").read_text() == "/Volumes/ext/state/codex/home"
    assert (state / "PYCHARM_PROPERTIES").read_text() == (
        "/Volumes/ext/state/jetbrains/PyCharm2026.2/idea.properties"
    )

    sentinel.unlink()
    subprocess.run(["/bin/sh", "-c", script], env=env, check=True)
    assert not list(state.iterdir())

    for variable in ("CODEX_HOME", "PYCHARM_PROPERTIES"):
        (state / variable).write_text("/custom")
    subprocess.run(["/bin/sh", "-c", script], env=env, check=True)
    assert {path.read_text() for path in state.iterdir()} == {"/custom"}


def test_lmsh_targets_are_deny_by_default():
    ignored = text(".chezmoiignore")
    lmsh = ignored.split('{{ if eq .machine_type "lmsh" }}', 1)[1].split("{{ end }}", 1)[0]
    rules = {line.strip() for line in lmsh.splitlines() if line.strip()}
    assert rules == {
        "*",
        ".config/*",
        ".config/atuin/*",
        "!.bash_profile",
        "!.bashrc",
        "!.common_profile",
        "!.config/",
        "!.config/atuin/",
        "!.config/atuin/config.toml",
        "!.config/starship.toml",
        "!install-lmsh-terminal.sh",
    }


def test_lmsh_installer_pins_terminal_binaries():
    installer = text("run_onchange_install-lmsh-terminal.sh.tmpl")
    assert '{{ if ne .machine_type "lmsh" -}}' in installer
    assert "atuin-aarch64-unknown-linux-gnu.tar.gz" in installer
    assert "9412210a9cdd6d0ff7635693e940096d82b368628326d334d27a8ca0ba173b0f" in installer
    assert "zoxide-0.9.8-aarch64-unknown-linux-musl.tar.gz" in installer
    assert "078cc9cc8cedb6c45edb84c0f5bad53518c610859c73bdb3009a52b89652c103" in installer
    assert "starship-aarch64-unknown-linux-musl.tar.gz" in installer
    assert "dc30189378d2f2e287384e8a692d3f95ad1df64cf0e8c36aa9201516028aed6b" in installer


def test_atuin_client_uses_private_bounded_sync():
    config = text("private_dot_config/atuin/private_config.toml.tmpl")
    assert "sync_address = {{ .atuin_sync_address | quote }}" in config
    for path in (
        ".chezmoi.toml.tmpl",
        "private_dot_config/atuin/private_config.toml.tmpl",
        "docs/ATUIN.md",
        "docs/specs/shell_auth_startup/README.md",
    ):
        assert "tail62e96c" not in text(path)
    assert "auto_sync = true" in config
    assert 'sync_frequency = "10m"' in config
    assert "network_connect_timeout = 2" in config
    assert "network_timeout = 5" in config
    assert "secrets_filter = true" in config
    for command in ("atuin key", "gh auth token", "op read"):
        assert command in config
    assert "records = true" in config
    assert "enabled = false" in config


def test_atuin_server_is_pinned_private_and_closed_by_default():
    compose = text("private_dot_config/atuin-server/compose.yaml")
    assert "ghcr.io/atuinsh/atuin:18.17.1" in compose
    assert '127.0.0.1:8888:8888' in compose
    assert "sqlite:///config/atuin.db" in compose
    assert "ATUIN_OPEN_REGISTRATION: ${ATUIN_OPEN_REGISTRATION:-false}" in compose
    assert "restart: unless-stopped" in compose
    assert "atuin-data:/config" in compose
    assert "${HOME}" not in compose
    assert "latest" not in compose

    brewfile = text("Brewfile")
    assert 'brew "atuin"' in brewfile
    assert 'brew "atuin", restart_service:' not in brewfile
