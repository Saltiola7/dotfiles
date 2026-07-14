from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_ai_configuration_is_not_owned_by_personal_source() -> None:
    absent = (
        "dot_agents/skills/dbsctr",
        "dot_agents/skills/discovery",
        "dot_agents/skills/qa",
        "dot_local/bin/executable_dbsctrctl",
        "dot_local/bin/executable_op-session",
        "private_dot_config/opencode",
        "private_dot_config/herdr",
        "private_Library/LaunchAgents/com.tis.herdr-server.plist.tmpl",
        "run_onchange_load-herdr-launchagent.sh.tmpl",
    )
    assert not [path for path in absent if (ROOT / path).exists()]

    removals = (ROOT / ".chezmoiremove").read_text()
    for target in (
        ".config/opencode",
        ".config/herdr",
        ".agents/skills/dbsctr",
        ".agents/skills/discovery",
        ".agents/skills/qa",
        ".local/bin/dbsctrctl",
        ".local/bin/op-session",
        "Library/LaunchAgents/com.tis.herdr-server.plist",
        "Library/LaunchAgents/dev.dotfiles-ai.herdr-server.plist",
    ):
        assert target not in removals


def test_secret_loader_keeps_external_op_session_interface() -> None:
    secret = (ROOT / "dot_local/bin/executable_secret").read_text()
    assert '__OP_SESSION_SCRIPT="$__SECRET_BIN_DIR/op-session"' in secret
    assert '. "$__OP_SESSION_SCRIPT"' in secret
