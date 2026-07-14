from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_herdr_server_runs_in_aqua_without_secrets() -> None:
    plist = (ROOT / "private_Library/LaunchAgents/com.tis.herdr-server.plist.tmpl").read_text()
    loader = (ROOT / "run_onchange_load-herdr-launchagent.sh.tmpl").read_text()

    assert "<key>LimitLoadToSessionType</key>\n    <string>Aqua</string>" in plist
    assert "<key>KeepAlive</key>" in plist
    assert "<key>LANG</key>\n        <string>en_US.UTF-8</string>" in plist
    assert "OP_SERVICE_ACCOUNT_TOKEN" not in plist + loader
    assert "launchctl bootstrap" in loader
    assert "herdr server stop" not in loader
    assert "unmanaged server owns the socket" in loader
