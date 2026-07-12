import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OC = ROOT / "private_dot_config/opencode"


def text(path: str) -> str:
    return (ROOT / path).read_text()


def test_provider_and_primary_contracts():
    config = json.loads((OC / "opencode.json.tmpl").read_text())
    assert config["$schema"] == "https://opencode.ai/config.json"
    assert config["default_agent"] == "plan"
    assert config["agent"]["build"]["disable"] is True
    assert config["agent"]["plan"]["permission"]["edit"] == "deny"
    assert config["agent"]["plan"]["permission"]["bash"] == "ask"
    assert "amazon-bedrock" in config["provider"]
    assert "lmstudio" in config["provider"]
    assert "headroom" not in config["provider"]
    assert "headroom-lmstudio" not in config["provider"]
    assert any(
        p == {"effect": "deny", "action": "provider.use", "resource": "anthropic"}
        for p in config["experimental"]["policies"]
    )


def test_commands_inherit_current_agent():
    for name in ("dbsctr", "discovery", "qa"):
        assert "\nagent:" not in (OC / f"commands/{name}.md").read_text()


def test_provider_affine_task_permissions():
    expected = {
        "build-gpt.md": ("explore-openai", "scout-openai", "builder-openai"),
        "build-gpt-pro.md": ("explore-openai", "scout-openai", "builder-openai"),
        "build-claude.md": ("explore-bedrock", "scout-bedrock", "builder-bedrock"),
    }
    for name, allowed in expected.items():
        body = (OC / "agents" / name).read_text()
        assert '"*": deny' in body
        for agent in allowed:
            assert f"{agent}: allow" in body


def test_builder_boundaries():
    for name in ("builder-openai.md", "builder-bedrock.md"):
        body = (OC / "agents" / name).read_text()
        assert "external_directory: deny" in body
        assert "task: deny" in body
        for command in ("git *", "gh *", "chezmoi apply*", "dvc push*", "npm publish*"):
            assert f'"{command}": deny' in body


def test_dbsctr_safe_git_permissions_and_reviewer():
    config = json.loads((OC / "opencode.json.tmpl").read_text())
    bash = config["permission"]["bash"]
    assert bash["dbsctrctl gate-commit*"] == "allow"
    assert bash["dbsctrctl final-push*"] == "allow"
    assert bash["dbsctrctl approve-exception*"] == "ask"
    assert bash["dbsctrctl record-dvc-push*"] == "ask"
    for command in (
        "git push --force*", "git push -f*", "git *push*--force*", "git push *+*",
        "git commit --no-verify*", "git commit -n*", "git *commit*--no-verify*",
    ):
        assert bash[command] == "deny"

    reviewer = (OC / "agents/reviewer-openai.md").read_text()
    assert "mode: subagent" in reviewer
    assert "model: openai/gpt-5.6-sol" in reviewer
    assert "edit: deny" in reviewer
    assert "task: deny" in reviewer


def test_removed_managed_integrations_are_absent():
    removed = (
        "dot_local/bin/executable_claude-personal",
        "dot_local/bin/executable_opencode-personal",
        "private_Library/LaunchAgents/ai.headroom.proxy.bedrock.plist",
        "private_Library/LaunchAgents/ai.headroom.proxy.lmstudio.plist",
        "docs/specs/opencode-personal.md",
        "docs/adr/ADR-001-omo-removal.md",
    )
    assert not [path for path in removed if (ROOT / path).exists()]
    assert not list((ROOT / "private_dot_config/meridian").glob("*"))


def test_skill_install_is_opencode_only_and_curated():
    installer = text("run_onchange_install-skills.sh.tmpl")
    assert "--all" not in installer
    assert "--agent opencode" in installer
    assert "marimo-team/marimo-pair --skill marimo-pair" in installer
    for removed in ("cavecrew", "caveman-stats", "caveman-compress", " compress"):
        assert removed not in installer


def test_graphify_is_preserved_without_project_plugin():
    assert "graphify install --platform opencode" in text(
        "run_onchange_install-graphify.sh.tmpl"
    )
    assert not (ROOT / ".opencode/opencode.json").exists()
    assert not (ROOT / ".opencode/plugins/graphify.js").exists()
    assert ".opencode/plugins/graphify.js" not in text(".gitignore")
    assert ".opencode/opencode.json" not in text(".gitignore")
