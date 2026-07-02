import os
import shlex
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _base_env(tmp_path: Path, bin_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env.pop("HERDR_ENV", None)
    env.pop("OP_SERVICE_ACCOUNT_TOKEN", None)
    env.pop("OP_SESSION", None)
    env.pop("OP_SESSION_my", None)
    env.pop("OP_SESSION_FORCE_MINT", None)
    env.pop("OP_SESSION_KZRNJU45TFHCFMB22WI6VCJVDY", None)
    return env


def test_op_session_validates_cache_once_before_fanout(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    cache_dir = tmp_path / ".cache" / "op"
    bin_dir.mkdir()
    cache_dir.mkdir(parents=True)
    (cache_dir / "session").write_text("cached-token")
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\n' "$*" >> {quoted_log_file}
if [ "$1 $2" = "vault list" ]; then
  exit 0
fi
exit 0
""",
    )

    env = _base_env(tmp_path, bin_dir)

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert log_file.read_text().splitlines() == ["vault list"]


def test_op_session_service_account_token_skips_signin_and_cache(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    cache_dir = tmp_path / ".cache" / "op"
    bin_dir.mkdir()
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\n' "$*" >> {quoted_log_file}
if [ "$1 $2" = "vault list" ]; then
  [ "${{OP_SERVICE_ACCOUNT_TOKEN:-}}" = "service-token" ]
  exit $?
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env["OP_SERVICE_ACCOUNT_TOKEN"] = "service-token"

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert log_file.read_text().splitlines() == ["vault list"]
    assert not (cache_dir / "session").exists()


def test_op_session_invalid_service_account_token_fails_without_signin(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\n' "$*" >> {quoted_log_file}
if [ "$1 $2" = "vault list" ]; then
  exit 1
fi
if [ "$1" = "signin" ]; then
  exit 0
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env["OP_SERVICE_ACCOUNT_TOKEN"] = "bad-token"

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "OP_SERVICE_ACCOUNT_TOKEN is invalid or lacks access" in result.stderr + result.stdout
    assert log_file.read_text().splitlines() == ["vault list"]


def test_op_session_herdr_uses_keychain_service_account_token(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    cache_dir = tmp_path / ".cache" / "op"
    bin_dir.mkdir()
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "security",
        """#!/bin/bash
if [ "$1" = "find-generic-password" ] && [ "$2" = "-s" ] && [ "$3" = "op-service-account-token" ] && [ "$4" = "-a" ] && [ "$5" = "my" ] && [ "$6" = "-w" ]; then
  printf '%s\n' keychain-token
  exit 0
fi
exit 2
""",
    )

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\t%s\n' "$*" "${{OP_SERVICE_ACCOUNT_TOKEN:-}}" >> {quoted_log_file}
if [ "$1 $2" = "vault list" ]; then
  [ "${{OP_SERVICE_ACCOUNT_TOKEN:-}}" = "keychain-token" ]
  exit $?
fi
if [ "$1" = "signin" ]; then
  exit 9
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env["HERDR_ENV"] = "1"

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert log_file.read_text().splitlines() == ["vault list\tkeychain-token"]
    assert not (cache_dir / "session").exists()


def test_op_session_herdr_without_service_token_does_not_signin(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "security",
        "#!/bin/bash\nexit 44\n",
    )

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\n' "$*" >> {quoted_log_file}
if [ "$1" = "signin" ]; then
  exit 9
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env["HERDR_ENV"] = "1"

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Herdr shells require OP_SERVICE_ACCOUNT_TOKEN" in result.stderr + result.stdout
    assert not log_file.exists()


def test_op_session_ssh_without_service_token_does_not_signin(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    cache_dir = tmp_path / ".cache" / "op"
    bin_dir.mkdir()
    cache_dir.mkdir(parents=True)
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\n' "$*" >> {quoted_log_file}
if [ "$1 $2" = "vault list" ]; then
  exit 1
fi
if [ "$1" = "signin" ]; then
  exit 0
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env["SSH_CONNECTION"] = "client server"

    result = subprocess.run(
        [
            "script",
            "-q",
            "/dev/null",
            "bash",
            "-lc",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "SSH shells require OP_SERVICE_ACCOUNT_TOKEN" in result.stderr + result.stdout
    assert not log_file.exists()


def test_op_session_force_mint_clears_stale_lock(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    cache_dir = tmp_path / ".cache" / "op"
    lock_dir = cache_dir / "session.lock"
    bin_dir.mkdir()
    lock_dir.mkdir(parents=True)
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\t%s\n' "$*" "${{OP_SESSION_KZRNJU45TFHCFMB22WI6VCJVDY:-}}" >> {quoted_log_file}
if [ "$1" = "signin" ]; then
  printf '%s\n' fresh-token
  exit 0
fi
if [ "$1 $2" = "vault list" ]; then
  exit 0
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env.pop("SSH_CONNECTION", None)
    env.pop("SSH_TTY", None)
    env["OP_SESSION_FORCE_MINT"] = "1"
    env["OP_SESSION_KZRNJU45TFHCFMB22WI6VCJVDY"] = "stale-token"

    result = subprocess.run(
        [
            "script",
            "-q",
            "/dev/null",
            "bash",
            "-lc",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not lock_dir.exists()
    assert (cache_dir / "session").read_text() == "fresh-token"
    assert log_file.read_text().splitlines() == [
        "signin --account my --force --raw\t",
        "vault list\tfresh-token",
    ]


def test_op_session_stale_env_force_mint_clears_stale_lock(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    cache_dir = tmp_path / ".cache" / "op"
    lock_dir = cache_dir / "session.lock"
    bin_dir.mkdir()
    lock_dir.mkdir(parents=True)
    log_file = tmp_path / "op.log"
    quoted_log_file = shlex.quote(str(log_file))

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\t%s\n' "$*" "${{OP_SESSION_KZRNJU45TFHCFMB22WI6VCJVDY:-}}" >> {quoted_log_file}
if [ "$1 $2" = "vault list" ]; then
  [ "${{OP_SESSION_KZRNJU45TFHCFMB22WI6VCJVDY:-}}" = "fresh-token" ]
  exit $?
fi
if [ "$1" = "signin" ]; then
  printf '%s\n' fresh-token
  exit 0
fi
exit 2
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env.pop("SSH_CONNECTION", None)
    env.pop("SSH_TTY", None)
    env["OP_SESSION_KZRNJU45TFHCFMB22WI6VCJVDY"] = "stale-token"

    result = subprocess.run(
        [
            "script",
            "-q",
            "/dev/null",
            "bash",
            "-lc",
            f"source {ROOT / 'dot_local/bin/executable_op-session'}",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not lock_dir.exists()
    assert (cache_dir / "session").read_text() == "fresh-token"
    assert log_file.read_text().splitlines() == [
        "vault list\tstale-token",
        "signin --account my --force --raw\t",
        "vault list\tfresh-token",
    ]


def test_secret_fetches_single_item_by_uuid_and_projects_once(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    op_log = tmp_path / "op.log"
    quoted_op_log = shlex.quote(str(op_log))

    _write_executable(
        bin_dir / "op-session",
        "#!/bin/bash\nexport OP_ACCOUNT=my\n",
    )

    _write_executable(
        bin_dir / "op",
        f"""#!/bin/bash
printf '%s\n' "$*" >> {quoted_op_log}
if [ "$1" != "item" ] || [ "$2" != "get" ]; then
  exit 2
fi
case "$3" in
  ojb5dyao2ahusvjgvgh7gbuxj4) ;;
  *) exit 3 ;;
esac
cat <<'JSON'
{{"id":"vjsfewbg2dzuatpwfmkqws5hle","title":"Shell Secrets","fields":[
{{"label":"GEMINI_API_KEY","value":"gemini"}},
{{"label":"GOOGLE_GENERATIVE_AI_API_KEY","value":"google"}},
{{"label":"OPENAI_API_KEY","value":"openai"}},
{{"label":"DATABRICKS_HOST","value":"https://databricks.example"}},
{{"label":"DATABRICKS_TOKEN","value":"db-token"}},
{{"label":"AWS_PROFILE","value":"bedrock"}},
{{"label":"AWS_REGION","value":"us-west-2"}},
{{"label":"GCP_ENTERPRISE_SEO_TOOLS_CREDENTIAL","value":"{{\\\"type\\\":\\\"service_account\\\"}}"}},
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
{{"label":"GWS_CONTENT_READER_CREDENTIAL","value":"{{\\\"type\\\":\\\"service_account\\\"}}"}}
]}}
JSON
""",
    )

    env = _base_env(tmp_path, bin_dir)
    env["SECRET_PROFILE"] = "1"

    command = f"""
source {ROOT / 'dot_local/bin/executable_secret'}
test "$GEMINI_API_KEY" = gemini
test "$GOOGLE_APPLICATION_CREDENTIALS" = "$HOME/.cache/gcp/enterprise-seo-tools-sa.json"
test "$GWS_CONTENT_READER_CREDENTIALS" = "$HOME/.cache/gcp/gws-content-reader-key.json"
test "$(cat "$GOOGLE_APPLICATION_CREDENTIALS")" = '{{"type":"service_account"}}'
test "$(cat /tmp/sketchybar_clockify/api_key)" = clockify
"""
    result = subprocess.run(
        ["bash", "-lc", command],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    op_calls = op_log.read_text().splitlines()
    assert op_calls == ["item get ojb5dyao2ahusvjgvgh7gbuxj4 --vault Automation --reveal --format json"]
    assert all("--reveal --format json" in call for call in op_calls)
