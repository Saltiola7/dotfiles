import hashlib
import io
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "run_onchange_after_bootstrap-gcloud.sh.tmpl"
DIGEST = "0f580f1323d0465b11d1d7c506e701c27729e9c5ea0e1d0f855a4dc3e665db89"


def executable(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + text)
    path.chmod(0o755)


@pytest.mark.parametrize("scenario", [
    "install", "newer", "unsupported", "checksum", "missing-python",
    "unhealthy", "installer-failure", "concurrent",
])
def test_bootstrap_boundaries(tmp_path, scenario):
    assert SCRIPT.exists(), "managed standalone SDK bootstrap is missing"
    home = tmp_path / "home with spaces"
    home.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ["env", "mktemp", "mkdir", "shasum", "tar", "gzip", "mv", "rm", "dirname", "cat"]:
        (tools / name).symlink_to(shutil.which(name))
    executable(tools / "uname", 'case "$1" in -s) echo Darwin;; *) echo ' +
               ("x86_64" if scenario == "unsupported" else "arm64") + ';; esac\n')
    if scenario != "missing-python":
        (tools / "python3.12").symlink_to(shutil.which("python3"))
    sdk = home / "google-cloud-sdk"
    if scenario == "newer":
        executable(sdk / "bin/gcloud", 'echo "Google Cloud SDK 999.0.0"\n')
        (sdk / "extra-component").write_text("preserve")
    elif scenario == "unhealthy":
        sdk.mkdir()
        (sdk / "keep").write_text("user work")

    archive = tmp_path / "sdk.tar.gz"
    install = 'test -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" || exit 40\n'
    install += 'test -z "${CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE:-}" || exit 41\n'
    install += 'case "$*" in *--install-python=false*) ;; *) exit 42;; esac\n'
    if scenario == "installer-failure":
        install += 'exit 43\n'
    if scenario == "concurrent":
        install += f'mkdir -p "{sdk}"\necho preserve > "{sdk}/concurrent"\n'
    with tarfile.open(archive, "w:gz") as tar:
        for name, body in [("install.sh", install), ("bin/gcloud", 'echo "Google Cloud SDK 588.0.0"\n')]:
            data = ("#!/bin/sh\n" + body).encode()
            info = tarfile.TarInfo("google-cloud-sdk/" + name)
            info.size = len(data)
            info.mode = 0o755
            tar.addfile(info, io.BytesIO(data))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    executable(tools / "curl", f'echo called >> "{tmp_path}/downloads"\n'
               'while [ "$1" != "--output" ]; do shift; done\n'
               f'cat "{archive}" > "$2"\n')
    script = tmp_path / "bootstrap.sh"
    script.write_text(SCRIPT.read_text().replace(DIGEST, "0" * 64 if scenario == "checksum" else digest))
    env = {"HOME": str(home), "PATH": str(tools), "TMPDIR": str(tmp_path),
           "GOOGLE_APPLICATION_CREDENTIALS": "must-not-reach-installer",
           "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE": "must-not-reach-installer"}
    run = lambda: subprocess.run(["/bin/sh", str(script)], env=env, capture_output=True, text=True)
    result = run()
    if scenario in {"install", "newer", "unsupported"}:
        assert result.returncode == 0, result.stderr
        assert run().returncode == 0
        if scenario == "install":
            assert (sdk / "bin/gcloud").is_file()
            assert (tmp_path / "downloads").read_text().splitlines() == ["called"]
        else:
            assert not (tmp_path / "downloads").exists()
        if scenario == "newer":
            assert (sdk / "extra-component").read_text() == "preserve"
    else:
        assert result.returncode != 0
        if scenario == "unhealthy":
            assert (sdk / "keep").read_text() == "user work"
        elif scenario == "concurrent":
            assert (sdk / "concurrent").read_text().strip() == "preserve"
            assert not (sdk / "google-cloud-sdk").exists()
        else:
            assert not sdk.exists()
    assert not (home / ".config/gcloud").exists()
