import os
import shlex
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_aws_and_service_account_settings_are_retired() -> None:
    secret = (ROOT / "dot_local/bin/executable_secret").read_text()
    profiles = (
        (ROOT / "dot_common_profile.tmpl").read_text(),
        (ROOT / "dot_xonshrc.tmpl").read_text(),
    )
    assert "AWS_PROFILE" not in secret
    assert "AWS_REGION" not in secret
    assert "CLAUDE_CODE_USE_BEDROCK" not in secret
    for profile in profiles:
        assert "ClientAccess-000000000000" not in profile
        assert "awslogin" not in profile
        assert "__cleanup_gcp_cache" not in profile
        assert "sa-dev-admin" not in profile


def test_secret_is_a_pure_env_loader_without_credential_files(tmp_path: Path) -> None:
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
{{"title":"Shell Secrets","fields":[
{{"label":"GEMINI_API_KEY","value":"gemini"}},
{{"label":"GOOGLE_GENERATIVE_AI_API_KEY","value":"google"}},
{{"label":"OPENAI_API_KEY","value":"openai"}},
{{"label":"DATABRICKS_HOST","value":"https://databricks.example"}},
{{"label":"DATABRICKS_TOKEN","value":"db-token"}},
{{"label":"GOOGLE_VERTEX_PROJECT","value":"project-a"}},
{{"label":"GOOGLE_VERTEX_LOCATION","value":"us-central1"}},
{{"label":"CLICKHOUSE_HOST","value":"clickhouse"}},
{{"label":"CLICKHOUSE_USER","value":"user"}},
{{"label":"CLICKHOUSE_PORT","value":"9440"}},
{{"label":"CLICKHOUSE_PASSWORD","value":"pass"}},
{{"label":"SEMRUSH_API","value":"semrush"}},
{{"label":"SEMRUSH_ENTERPRISE_API","value":"enterprise"}},
{{"label":"PAGESPEED_API_KEY","value":"pagespeed"}},
{{"label":"CLOCKIFY_API_KEY","value":"clockify"}},
{{"label":"GITHUB_PERSONAL_ACCESS_TOKEN_CLASSIC","value":"github"}},
{{"label":"ATLASSIAN_API","value":"atlassian"}},
{{"label":"EMAIL","value":"me@example.com"}},
{{"label":"ATLASSIAN_URL","value":"https://example.atlassian.net"}}
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
    command = f'''set -e
trap 'touch "$HOME/original-exit-trap-ran"' EXIT
source {ROOT / "dot_local/bin/executable_secret"}
test "$GEMINI_API_KEY" = gemini
test "$OPENAI_API_KEY" = openai
test "$GOOGLE_VERTEX_PROJECT" = project-a
test "$AWS_PROFILE" = existing-profile
test "$AWS_REGION" = existing-region
test -z "${{CLAUDE_CODE_USE_BEDROCK:-}}"
test -z "${{GOOGLE_APPLICATION_CREDENTIALS:-}}"
test -z "${{GWS_CONTENT_READER_CREDENTIALS:-}}"
test -z "${{CLOUDSDK_ACTIVE_CONFIG_NAME:-}}"
test ! -d "$HOME/.cache/gcp"
source {ROOT / "dot_local/bin/executable_secret"}
'''
    result = subprocess.run(
        ["bash", "-lc", command],
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Secrets already loaded." in result.stdout
    assert (tmp_path / "original-exit-trap-ran").is_file()
    assert log.read_text().splitlines() == [
        "item get ojb5dyao2ahusvjgvgh7gbuxj4 --vault Automation --reveal --format json"
    ]
    other_shell = subprocess.run(
        ["bash", "-lc", command],
        env=env,
        text=True,
        capture_output=True,
    )
    assert other_shell.returncode == 0, other_shell.stderr
    assert (tmp_path / "original-exit-trap-ran").is_file()
    assert stat.S_IMODE((Path("/tmp/sketchybar_clockify/api_key")).stat().st_mode) == 0o600
    assert log.read_text().splitlines() == [
        "item get ojb5dyao2ahusvjgvgh7gbuxj4 --vault Automation --reveal --format json"
    ] * 2
