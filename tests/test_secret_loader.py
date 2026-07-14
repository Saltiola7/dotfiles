import os
import shlex
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_aws_settings_are_shell_config_not_secrets() -> None:
    secret = (ROOT / "dot_local/bin/executable_secret").read_text()
    profiles = (
        (ROOT / "dot_common_profile.tmpl").read_text(),
        (ROOT / "dot_xonshrc.tmpl").read_text(),
    )
    assert "AWS_PROFILE" not in secret
    assert "AWS_REGION" not in secret
    assert "CLAUDE_CODE_USE_BEDROCK" not in secret
    for profile in profiles:
        assert "BedrockDeveloperAccess-302432775606" in profile
        assert "us-west-2" in profile


def test_secret_fetches_one_item_and_preserves_aws_env(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "op.log"
    executable(bin_dir / "op-session", "#!/bin/bash\nexport OP_ACCOUNT=my\n")
    executable(
        bin_dir / "op",
        f'''#!/bin/bash
printf '%s\n' "$*" >> {shlex.quote(str(log))}
[ "$1 $2" = "item get" ] || exit 2
cat <<'JSON'
{{"fields":[
{{"label":"GEMINI_API_KEY","value":"gemini"}},
{{"label":"GOOGLE_GENERATIVE_AI_API_KEY","value":"google"}},
{{"label":"OPENAI_API_KEY","value":"openai"}},
{{"label":"DATABRICKS_HOST","value":"https://databricks.example"}},
{{"label":"DATABRICKS_TOKEN","value":"db-token"}},
{{"label":"GCP_ENTERPRISE_SEO_TOOLS_CREDENTIAL","value":"{{\\"type\\":\\"service_account\\"}}"}},
{{"label":"GOOGLE_VERTEX_PROJECT","value":"project-a"}},
{{"label":"GOOGLE_VERTEX_LOCATION","value":"us-central1"}},
{{"label":"CLICKHOUSE_HOST","value":"clickhouse"}},
{{"label":"CLICKHOUSE_USER","value":"user"}},
{{"label":"CLICKHOUSE_PORT","value":"9440"}},
{{"label":"CLICKHOUSE_PASSWORD","value":"pass"}},
{{"label":"SEMRUSH_API","value":"semrush"}},
{{"label":"SEMRUSH_ENTERPRISE_API","value":"enterprise"}},
{{"label":"PAGESPEED_API_KEY","value":"pagespeed"}},
{{"label":"GCS_AKAMAI_ACCESS_KEY","value":"access"}},
{{"label":"GCS_AKAMAI_SECRET_KEY","value":"secret"}},
{{"label":"CLOCKIFY_API_KEY","value":"clockify"}},
{{"label":"GITHUB_PERSONAL_ACCESS_TOKEN_CLASSIC","value":"github"}},
{{"label":"ATLASSIAN_API","value":"atlassian"}},
{{"label":"EMAIL","value":"me@example.com"}},
{{"label":"ATLASSIAN_URL","value":"https://example.atlassian.net"}},
{{"label":"GWS_CONTENT_READER_CREDENTIAL","value":"{{\\"type\\":\\"service_account\\"}}"}}
]}}
JSON
''',
    )
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "AWS_PROFILE": "existing-profile",
        "AWS_REGION": "existing-region",
    }
    result = subprocess.run(
        [
            "bash",
            "-lc",
            f'''source {ROOT / "dot_local/bin/executable_secret"}
test "$GEMINI_API_KEY" = gemini
test "$AWS_PROFILE" = existing-profile
test "$AWS_REGION" = existing-region
test -z "${{CLAUDE_CODE_USE_BEDROCK:-}}"
''',
        ],
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [
        "item get ojb5dyao2ahusvjgvgh7gbuxj4 --vault Automation --reveal --format json"
    ]
