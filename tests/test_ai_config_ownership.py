from pathlib import Path
import json


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


def test_dual_source_apply_slice_is_ready_and_bounded() -> None:
    manifest = json.loads((
        ROOT / "docs/initiatives/dual-source-chezmoi-apply/MANIFEST.json"
    ).read_text())
    slices = {item["id"]: item for item in manifest["slices"]}
    bridge = slices["dual-source-apply-bridge"]
    assert bridge["state"] == "ready"
    assert bridge["execution_owner"] == "build"
    assert bridge["context"] == "shell_auth_startup"
    assert len(manifest["contexts"]) == 2

    spec = (ROOT / "docs/specs/shell_auth_startup/features/dual-source-chezmoi-apply.md").read_text()
    for phrase in (
        "run_after_apply-dotfiles-ai.sh.tmpl",
        "git -C <secondary> pull --ff-only",
        "DOTFILES_AI_CHAINED_APPLY=1",
        "--include=files,symlinks,scripts",
        "Failure is visible",
        "no shared file, symlink, or run-script target",
    ):
        assert phrase in spec

    plan = json.loads((
        ROOT / "docs/specs/shell_auth_startup/DUAL-SOURCE-APPLY.plan.json"
    ).read_text())
    assert plan["profile"] == "docs/specs/shell_auth_startup/README.md"
    assert plan["gates"]["release"]["applicability"] == "not_applicable"
