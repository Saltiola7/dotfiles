import os
import shlex
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_op_session_reuses_cache_without_vault_list(tmp_path: Path) -> None:
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
  exit 99
fi
exit 0
""",
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "-lc", f"source {ROOT / 'dot_local/bin/executable_op-session'}"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not log_file.exists()


def test_secret_fetches_by_uuid_and_projects_once(tmp_path: Path) -> None:
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
  iy4hpb3vrg5m64egml5u6ia5gm) title='Gemini API Key'; fields='{{"label":"credential","value":"gemini"}}' ;;
  cbbfbjqstup4lzoz6luz26p3zu) title='Google AI API Key'; fields='{{"label":"credential","value":"google"}}' ;;
  6r7muwfkjvnu5tyc6zq2rbfylu) title='OpenAI API Key'; fields='{{"label":"credential","value":"openai"}}' ;;
  tlsgtbyhjewrb5mqqqlj3gw2l4) title='Databricks'; fields='{{"label":"host","value":"https://databricks.example"}},{{"label":"credential","value":"db-token"}}' ;;
  mfw5uv5ny7abo3fidbl45mbace) title='AWS Bedrock'; fields='{{"label":"profile","value":"bedrock"}},{{"label":"region","value":"us-west-2"}}' ;;
  sav55lbw2vitunujceeyqc6xtq) title='GCP Service Account - Enterprise SEO Tools'; fields='{{"label":"credential","value":"{{\\"type\\":\\"service_account\\"}}"}},{{"label":"project","value":"project-a"}},{{"label":"location","value":"us-central1"}}' ;;
  fwveplt7hyhdyl626h42xutd7u) title='ClickHouse MGM Cloud'; fields='{{"label":"host","value":"clickhouse"}},{{"label":"user","value":"user"}},{{"label":"port","value":"9440"}},{{"label":"password","value":"pass"}}' ;;
  a5i4sdfl2lb2rs5blzuya6tlwi) title='SEMRUSH API'; fields='{{"label":"credential","value":"semrush"}},{{"label":"enterprise","value":"enterprise"}}' ;;
  pr5j4ymhdj5yyl4tyzh7ixd2ki) title='PageSpeed API'; fields='{{"label":"credential","value":"pagespeed"}}' ;;
  fztzpzl6mddi3nzpkstglbqiyy) title='Akamai GCS HMAC'; fields='{{"label":"access_key","value":"access"}},{{"label":"secret_key","value":"secret"}}' ;;
  gi6qx3jixvkuaa74ecrs4pai5a) title='Clockify API Key'; fields='{{"label":"credential","value":"clockify"}}' ;;
  2k3c3l4nrue7twkngkobbgsrba) title='GitHub PAT Classic'; fields='{{"label":"credential","value":"github"}}' ;;
  be7yg6k63qcw2v74jrj557xdnq) title='Atlassian API Token'; fields='{{"label":"credential","value":"atlassian"}},{{"label":"email","value":"me@example.com"}},{{"label":"url","value":"https://example.atlassian.net"}}' ;;
  fce3pdktu67cqnei7nrfn5omb4) title='GCP Service Account - GWS Content Reader'; fields='{{"label":"credential","value":"{{\\"type\\":\\"service_account\\"}}"}}' ;;
  *) exit 3 ;;
esac
printf '{{"id":"%s","title":"%s","fields":[%s]}}\n' "$3" "$title" "$fields"
""",
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["SECRET_PROFILE"] = "1"

    command = f"""
source {ROOT / 'dot_local/bin/executable_secret'}
test "$GEMINI_API_KEY" = gemini
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
    assert len(op_calls) == 14
    assert all("--reveal --format json" in call for call in op_calls)
    assert all("Gemini API Key" not in call for call in op_calls)
