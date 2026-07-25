from pathlib import Path


ROOT = Path(__file__).parents[1]


def text(path):
    return (ROOT / path).read_text()


def test_lmsh_profile_is_portable_and_excludes_credentials():
    assert "macbook/mac-mini/lmsh" in text(".chezmoi.toml.tmpl")
    assert "atuin_sync_address" in text(".chezmoi.toml.tmpl")
    ignored = text(".chezmoiignore")
    assert '{{ if eq .machine_type "lmsh" }}' in ignored
    for path in (".ssh/", ".config/gh/", ".databrickscfg", "Library/", ".config/sketchybar/"):
        assert path in ignored

    bashrc = text("dot_bashrc.tmpl")
    for tool in ("atuin", "zoxide", "starship"):
        assert f"command -v {tool}" in bashrc
    assert '{{ if eq .machine_type "lmsh" -}}' in bashrc
    assert "[ -t 0 ]" in bashrc

    profile = text("dot_common_profile.tmpl")
    assert '{{ if eq .machine_type "lmsh" -}}' in profile
    lmsh, macos = profile.split("{{ else -}}", 1)
    assert "/opt/homebrew" not in lmsh
    assert "/Applications" not in lmsh
    assert "/opt/homebrew" in macos


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
