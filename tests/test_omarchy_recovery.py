import json
import os
import pty
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("encryption_fails", [False, True])
def test_recovery_restarts_services_and_never_keeps_failed_archive(tmp_path, encryption_fails):
    commands = tmp_path / "bin"
    commands.mkdir()
    log = tmp_path / "services"
    scripts = {
        "sudo": '#!/bin/bash\ncase "$1" in -v) exit 0;; test) exit 0;; esac\nexec "$@"\n',
        "systemctl": '#!/bin/bash\nprintf "%s\\n" "$*" >> "$SERVICE_LOG"\nexit 0\n',
        "tar": '#!/bin/bash\nprintf "private runtime state"\n',
        "chezmoi": '''#!/usr/bin/env python3
import json,os,sys
if sys.argv[1] == 'dump-config':
    print(json.dumps({'age': {'recipient': 'age1test'}}))
else:
    data=sys.stdin.buffer.read()
    output=sys.argv[sys.argv.index('--output')+1]
    open(output,'wb').write(b'age-encryption.org/v1\\n'+data)
    sys.exit(int(os.environ['ENCRYPT_FAIL']))
''',
    }
    for name, body in scripts.items():
        path = commands / name
        path.write_text(body)
        path.chmod(0o755)
    output = tmp_path / "backup/state.tar.gz.age"
    master, slave = pty.openpty()
    try:
        result = subprocess.run(
            ["bash", str(ROOT / "dot_local/bin/executable_omarchy-recovery-backup"), str(output)],
            stdin=slave, capture_output=True, text=True,
            env={**os.environ, "PATH": f"{commands}:{os.environ['PATH']}",
                 "HOME": str(tmp_path), "SERVICE_LOG": str(log),
                 "ENCRYPT_FAIL": str(int(encryption_fails))},
        )
    finally:
        os.close(master)
        os.close(slave)
    assert bool(result.returncode) == encryption_fails, result.stderr
    calls = log.read_text().splitlines()
    assert any(line.startswith("stop ") for line in calls)
    assert calls[-1].startswith("start ")
    assert not Path(f"{output}.partial").exists()
    assert output.exists() != encryption_fails
    if output.exists():
        assert output.stat().st_mode & 0o777 == 0o600
