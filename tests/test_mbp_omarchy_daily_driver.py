

def test_omarchy_remote_access_script_gates_and_idempotent():
    script = (ROOT / "run_onchange_after_install-omarchy-remote-access.sh.tmpl").read_text()
    assert 'eq .machine_type "omarchy"' in script
    assert "[[ -t 0 ]]" in script
    assert "rustdesk-bin" in script
