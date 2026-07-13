import json
import os
import subprocess
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
    assert bash["dbsctrctl cleanup*"] == "ask"
    for command in (
        "herdr server stop*", "herdr config reset-keys*", "herdr worktree remove*",
        "herdr workspace close*", "herdr pane close*", "herdr tab close*",
        "herdr session stop*", "herdr session delete*",
    ):
        assert bash[command] == "ask"
    assert config["permission"]["dbsctr_status"] == "allow"
    assert config["permission"]["dbsctr_begin"] == "ask"
    assert config["permission"]["dbsctr_audit"] == "allow"
    assert config["agent"]["plan"]["permission"]["dbsctr_begin"] == "deny"
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
    assert "dbsctr_begin: deny" in reviewer

    for name in ("plan-gpt-pro.md", "plan-gpt-pro-max.md"):
        assert "dbsctr_begin: deny" in (OC / "agents" / name).read_text()
    for name in ("build-gpt.md", "build-gpt-pro.md", "build-claude.md"):
        assert "dbsctr_begin: allow" in (OC / "agents" / name).read_text()
    for name in ("builder-openai.md", "builder-bedrock.md"):
        assert "dbsctr_begin: deny" in (OC / "agents" / name).read_text()


def test_dbsctr_tools_and_herdr_config_are_managed():
    tools = (OC / "tools/dbsctr.ts").read_text()
    assert 'export const status = tool({' in tools
    assert 'export const begin = tool({' in tools
    assert 'export const audit = tool({' in tools
    assert "default(false)" in tools
    runtime = (OC / "lib/dbsctr-runtime.ts").read_text()
    assert '["dbsctrctl", "status", "--json"]' in runtime
    assert '["dbsctrctl", "audit", "--commit", commit, "--json"]' in runtime
    assert '"herdr", "agent", "start", "opencode"' in runtime
    herdr = text("private_dot_config/herdr/config.toml")
    assert "pane_history = false" in herdr
    assert 'name = "catppuccin"' in herdr


def test_dbsctr_tool_runtime_preserves_argv_and_opts_in_to_herdr(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    dbsctr_log = tmp_path / "dbsctr.log"
    herdr_log = tmp_path / "herdr.log"
    dbsctr = bin_dir / "dbsctrctl"
    dbsctr.write_text(
        "#!/bin/sh\npwd > \"$DBSCTR_CWD\"\nprintf '<%s>\\n' \"$@\" > \"$DBSCTR_LOG\"\n"
        "[ \"$DBSCTR_MODE\" = fail ] && { printf 'boom\\n' >&2; exit 7; }\n"
        "[ \"$DBSCTR_MODE\" = malformed ] && { printf 'not-json\\n'; exit 0; }\n"
        "printf '{\"cycle_id\":\"x\",\"worktree\":\"/tmp/cycle\"}\\n'\n"
    )
    herdr = bin_dir / "herdr"
    herdr.write_text(
        "#!/bin/sh\nprintf 'CALL\\nCWD:%s\\n' \"$(pwd)\" >> \"$HERDR_LOG\"\n"
        "printf '<%s>\\n' \"$@\" >> \"$HERDR_LOG\"\n"
        "[ \"$HERDR_FAIL\" = 1 ] && { printf 'herdr-boom\\n' >&2; exit 9; }\n"
        "exit 0\n"
    )
    dbsctr.chmod(0o755)
    herdr.chmod(0o755)
    runtime = OC / "lib/dbsctr-runtime.ts"
    script = (
        f'import {{ beginCycle }} from {json.dumps(str(runtime))};'
        'console.log(JSON.stringify(await beginCycle({cycleId:"x;touch nope",context:"ctx",risk:"routine",'
        'deliveryIntent:"local",planPath:"/tmp/plan with spaces"},process.cwd(),'
        'process.argv[1] === "launch",process.env)));'
    )
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "DBSCTR_LOG": str(dbsctr_log),
        "DBSCTR_CWD": str(tmp_path / "dbsctr.cwd"),
        "HERDR_LOG": str(herdr_log),
        "HERDR_ENV": "1",
    }
    no_launch = subprocess.run(["bun", "-e", script], cwd=ROOT, env=env, text=True,
                               capture_output=True, check=True)
    assert json.loads(no_launch.stdout)["herdr"] == "not_launched"
    assert not herdr_log.exists()
    assert (tmp_path / "dbsctr.cwd").read_text().strip() == str(ROOT)
    assert dbsctr_log.read_text().splitlines() == [
        "<begin>", "<--cycle-id>", "<x;touch nope>", "<--context>", "<ctx>",
        "<--risk>", "<routine>", "<--delivery-intent>", "<local>",
        "<--plan>", "</tmp/plan with spaces>",
    ]
    launched = subprocess.run(["bun", "-e", script, "launch"], cwd=ROOT, env=env, text=True,
                              capture_output=True, check=True)
    assert json.loads(launched.stdout)["herdr"] == "launched"
    assert herdr_log.read_text().splitlines() == [
        "CALL", f"CWD:{ROOT}", "<agent>", "<start>", "<opencode>", "<--cwd>",
        "</tmp/cycle>", "<--focus>", "<-->", "<opencode>", "</tmp/cycle>",
    ]

    failed = subprocess.run(["bun", "-e", script], cwd=ROOT,
                            env={**env, "DBSCTR_MODE": "fail"}, text=True, capture_output=True)
    assert failed.returncode != 0 and "boom" in failed.stderr
    malformed = subprocess.run(["bun", "-e", script], cwd=ROOT,
                               env={**env, "DBSCTR_MODE": "malformed"}, text=True, capture_output=True)
    assert malformed.returncode != 0
    herdr_failed = subprocess.run(["bun", "-e", script, "launch"], cwd=ROOT,
                                  env={**env, "HERDR_FAIL": "1"}, text=True,
                                  capture_output=True, check=True)
    assert json.loads(herdr_failed.stdout)["herdr"].startswith("launch_failed:")


def test_dbsctr_begin_asks_before_running_helper(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    helper_log = tmp_path / "helper.log"
    helper = bin_dir / "dbsctrctl"
    helper.write_text("#!/bin/sh\nprintf helper > \"$HELPER_LOG\"\nprintf '{\"worktree\":\"/tmp/cycle\"}\\n'\n")
    helper.chmod(0o755)
    tools = OC / "tools/dbsctr.ts"
    script = f'''import {{ begin }} from {json.dumps(str(tools))};
const context = {{ worktree: process.cwd(), ask: async (input) => {{
  if (process.argv[1] !== "allow") throw new Error(process.argv[1]);
  console.log(JSON.stringify(input));
}} }};
try {{ console.log(await begin.execute({{cycleId:"x",context:"ctx",risk:"routine",deliveryIntent:"local",planPath:"/tmp/plan"}}, context)); }}
catch (error) {{ console.error(error.message); process.exit(1); }}'''
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "HELPER_LOG": str(helper_log)}
    for outcome in ("denied", "cancelled"):
        result = subprocess.run(["bun", "-e", script, outcome], cwd=ROOT, env=env, text=True,
                                capture_output=True)
        assert result.returncode != 0
        assert outcome in result.stderr
        assert not helper_log.exists()

    result = subprocess.run(["bun", "-e", script, "allow"], cwd=ROOT, env=env, text=True,
                            capture_output=True, check=True)
    ask = json.loads(result.stdout.splitlines()[0])
    assert ask["permission"] == "dbsctr_begin"
    assert ask["patterns"] == ["*"]
    assert helper_log.read_text() == "helper"


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
