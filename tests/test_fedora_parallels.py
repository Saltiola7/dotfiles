import ast
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[1]
COMMAND = ROOT / "dot_local/bin/executable_fedora-parallels"
VOLUME_UUID = "D4A50898-0879-4A6C-BAE2-4C48D31CC59B"
CONTAINER_UUID = "936D6900-611B-4CA7-9C85-CC3FCD0B90E0"


def run_command(*args, env=None):
    return subprocess.run(
        ["/bin/sh", str(COMMAND), *args], cwd=ROOT,
        env=os.environ | (env or {}), capture_output=True, text=True,
    )


@pytest.fixture
def host(tmp_path):
    ext, volume = tmp_path / "ext", tmp_path / "Parallels"
    # Deliberately not the VM display name; no ISO or CD is present.
    bundle = tmp_path / "GUI Created Server.pvm"
    root_disk = bundle / "original-root.hdd"
    data_disk = volume / "fedora-parallels-data.hdd"
    for path in (ext / "git", root_disk, data_disk):
        path.mkdir(parents=True)
    info = {
        str(ext): {"VolumeUUID": "65AF3638-96BB-4F56-8259-38EA49F3F7DF", "VolumeName": "ext"},
        str(volume): {"VolumeUUID": VOLUME_UUID, "VolumeName": "Parallels"},
    }
    for mount, fields in info.items():
        fields.update(MountPoint=mount, FilesystemType="apfs", Internal=False,
                      Encryption=False, APFSContainerReference="disk42")
    info["/dev/internal"] = {"Internal": True}
    fixture = {
        "info": info,
        "apfs": {"Containers": [{"APFSContainerUUID": CONTAINER_UUID, "CapacityFree": 1234,
            "Volumes": [{"Name": "Parallels", "APFSVolumeUUID": VOLUME_UUID,
                         "CapacityQuota": 214748364800, "Roles": []}]}]},
        "vm": [{
            "Name": "fedora-parallels", "OS": "fedora-core", "Template": "no",
            "State": "running", "Home": str(bundle) + "/",
            "GuestTools": {"state": "installed", "version": "27.0.0-58628"},
            "Startup and Shutdown": {"Autostart": "off", "Startup view": "fullscreen"},
            "Smart Guard": {"enabled": False},
            "Hardware": {
                "cpu": {"type": "arm", "cpus": 6}, "memory": {"size": "12288Mb"},
                "hdd0": {"enabled": True, "image": str(root_disk), "type": "expanded", "size": "65536Mb"},
                "hdd1": {"enabled": True, "image": str(data_disk), "type": "expanded", "size": "163840Mb"},
                "net0": {"enabled": True, "type": "shared"},
            },
            "Host defined sharing": "Off", "Shared Profile": {"enabled": False},
            "Host Shared Folders": {
                "enabled": False,
                "ext": {"enabled": True, "path": str(ext), "mode": "ro"},
                "git": {"enabled": True, "path": str(ext / "git"), "mode": "rw"},
            },
            "Shared Applications": {"Host-to-guest apps sharing": "off", "Guest-to-host apps sharing": "off"},
            "SmartMount": {"enabled": False},
            "Miscellaneous Sharing": {"Shared clipboard mode": "on", "Shared cloud": "off"},
            "Advanced": {"Public SSH keys synchronization": "off", "Share host location": "off"},
        }],
    }
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(fixture))
    log = tmp_path / "calls.jsonl"
    env = {"FIXTURE": str(fixture_path), "CALL_LOG": str(log),
           "FEDORA_PARALLELS_EXT_MOUNT": str(ext), "FEDORA_PARALLELS_VOLUME": str(volume)}

    def tool(name, body):
        path = tmp_path / name
        path.write_text(f"#!{sys.executable}\nimport json, os, plistlib, shlex, sys\n"
                        "from pathlib import Path\n"
                        "data = json.loads(Path(os.environ['FIXTURE']).read_text())\n"
                        "args = sys.argv[1:]\n"
                        f"with open(os.environ['CALL_LOG'], 'a') as log: log.write(json.dumps([{name!r}, *args]) + '\\n')\n"
                        + body)
        path.chmod(0o755)
        env["FEDORA_PARALLELS_" + name.upper()] = str(path)

    tool("diskutil", """
if args[:2] == ['info', '-plist']:
    sys.stdout.buffer.write(plistlib.dumps(data['info'].get(args[2], {})))
elif args == ['apfs', 'list', '-plist', 'disk42']:
    sys.stdout.buffer.write(plistlib.dumps(data['apfs']))
else:
    raise SystemExit('unexpected diskutil mutation or hardcoded device')
""")
    tool("prlctl", """
if args == ['--version']:
    print('prlctl version 27.0.0 (58628)')
elif args == ['list', '--info', 'fedora-parallels', '--json']:
    print(json.dumps(data['vm']))
elif args[:2] == ['set', 'fedora-parallels']:
    pass
elif args[:4] == ['exec', 'fedora-parallels', '/usr/bin/python3', '-c']:
    # Emulate the verified guest-shell quoting boundary, not a direct argv exec.
    forwarded = shlex.split(' '.join(args[2:]))
    assert len(forwarded) == 3
    compile(forwarded[2], '<guest>', 'exec')
    print(data.get('guest_result', 'FEDORA_ADOPTION_VERIFIED'))
else:
    raise SystemExit('unexpected prlctl operation')
""")
    tool("prlsrvctl", "print(json.dumps(dict(status='ACTIVE', edition='pro', cpu_total=32, max_memory=131072)))\n")
    tool("df", """
device = '/dev/external' if args[1].startswith(os.environ['FEDORA_PARALLELS_VOLUME']) else '/dev/internal'
print('Filesystem 512-blocks Used Available Capacity Mounted on')
print(device, '100 1 99 1% /fixture')
""")
    return env, fixture, fixture_path, log


def test_legacy_provisioning_refuses_before_accessing_host():
    for command in ("create", "prepare-image"):
        result = run_command(command, env={"FEDORA_PARALLELS_DISKUTIL": "/nonexistent"})
        assert result.returncode != 0
        assert "Parallels GUI" in result.stderr
        assert "required command" not in result.stderr


def test_help_and_unknown_command_are_non_mutating():
    assert run_command("help").returncode == 0
    result = run_command("destroy")
    assert result.returncode != 0
    assert "unknown command" in result.stderr
    script = COMMAND.read_text()
    assert 'cask "parallels"' in (ROOT / "Brewfile").read_text()
    for operation in ("addVolume", "eraseDisk", "deleteVolume", "deleteContainer", "create_vm", "curl"):
        assert operation not in script


@pytest.mark.parametrize("command", ["prepare-storage", "doctor", "status", "verify"])
def test_adopts_gui_vm_with_renamed_bundle_no_iso_and_low_free_space(host, command):
    env, _, _, log = host
    result = run_command(command, env=env)
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert not any(call[:2] == ["prlctl", "set"] for call in calls)
    if command == "verify":
        assert "user/root share probes passed" in result.stdout


@pytest.mark.parametrize("mismatch", ["external_uuid", "volume_uuid", "container_uuid", "quota", "duplicate", "missing"])
def test_storage_mismatch_refuses_without_mutation(host, mismatch):
    env, data, path, log = host
    volume = data["info"][env["FEDORA_PARALLELS_VOLUME"]]
    container = data["apfs"]["Containers"][0]
    if mismatch == "external_uuid":
        data["info"][env["FEDORA_PARALLELS_EXT_MOUNT"]]["VolumeUUID"] = "wrong"
    elif mismatch == "volume_uuid":
        volume["VolumeUUID"] = "wrong"
    elif mismatch == "container_uuid":
        container["APFSContainerUUID"] = "wrong"
    elif mismatch == "quota":
        container["Volumes"][0]["CapacityQuota"] = 1
    elif mismatch == "duplicate":
        container["Volumes"].append(dict(Name="Parallels", APFSVolumeUUID="another"))
    else:
        volume["MountPoint"] = ""
    path.write_text(json.dumps(data))
    assert run_command("prepare-storage", env=env).returncode != 0
    assert all(json.loads(line)[0] == "diskutil" for line in log.read_text().splitlines())


@pytest.mark.parametrize("state", ["running", "suspended", "stopped"])
def test_profile_changes_only_a_stopped_vm(host, state):
    env, data, path, log = host
    data["vm"][0]["State"] = state
    path.write_text(json.dumps(data))
    result = run_command("profile", "heavy", env=env)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    mutations = [call for call in calls if call[:2] == ["prlctl", "set"]]
    if state == "stopped":
        assert result.returncode == 0, result.stderr
        assert mutations == [["prlctl", "set", "fedora-parallels", "--cpus", "8", "--memsize", "20480"]]
    else:
        assert result.returncode != 0 and "must be stopped" in result.stderr
        assert not mutations


@pytest.mark.parametrize("mismatch", ["root_external", "root_symlink", "share_rw", "extra_share", "cpu", "tools"])
def test_topology_mismatch_blocks_guest_access_and_mutation(host, mismatch):
    env, data, path, log = host
    vm = data["vm"][0]
    if mismatch == "root_external":
        data["info"]["/dev/internal"]["Internal"] = False
    elif mismatch == "root_symlink":
        link = Path(vm["Home"]) / "linked.hdd"
        link.symlink_to(vm["Hardware"]["hdd0"]["image"], target_is_directory=True)
        vm["Hardware"]["hdd0"]["image"] = str(link)
    elif mismatch == "share_rw":
        vm["Host Shared Folders"]["ext"]["mode"] = "rw"
    elif mismatch == "extra_share":
        vm["Host Shared Folders"]["home"] = dict(enabled=True, path="/Users/tis", mode="rw")
    elif mismatch == "tools":
        vm["GuestTools"]["state"] = "not_installed"
    else:
        vm["Hardware"]["cpu"]["cpus"] = 7
    path.write_text(json.dumps(data))
    assert run_command("verify", env=env).returncode != 0
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert not any(call[:2] in (["prlctl", "exec"], ["prlctl", "set"]) for call in calls)


@pytest.mark.parametrize("output", ["", "READ_ONLY_BOUNDARY_FAILED", "FEDORA_ADOPTION_VERIFIED\nextra"])
def test_silent_or_ambiguous_guest_transport_is_not_success(host, output):
    env, data, path, _ = host
    data["guest_result"] = output
    path.write_text(json.dumps(data))
    result = run_command("verify", env=env)
    assert result.returncode != 0
    assert "ambiguous output" in result.stderr


def test_share_probe_uses_exclusive_files_and_detects_root_write_without_leaking(tmp_path):
    guest = COMMAND.read_text().split("    guest_code='\n", 1)[1].split("\n'\n", 1)[0]
    tree = ast.parse(guest)
    probe = next(ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign) and node.targets[0].id == "probe_code")
    sentinel = tmp_path / ".fedora-share-probe-existing"
    sentinel.write_text("preserve me")
    for mode in ("write", "deny"):
        result = subprocess.run([sys.executable, "-c", probe, str(os.getuid()), str(tmp_path), mode],
                                capture_output=True, text=True)
        assert (result.returncode == 0) == (mode == "write")
        if mode == "deny":
            assert "READ_ONLY_BOUNDARY_FAILED" in result.stderr
        assert list(tmp_path.iterdir()) == [sentinel]
        assert sentinel.read_text() == "preserve me"


def test_fedora_starter_scope_excludes_host_and_ai_targets(tmp_path):
    config = tmp_path / "chezmoi.toml"
    config.write_text('[data]\nmachine_type = "fedora-workstation"\n')
    result = subprocess.run(
        ["chezmoi", "--config", str(config), "--source", str(ROOT), "managed", "--include", "files"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert set(result.stdout.splitlines()) == {
        ".config/sway/config.d/95-fedora-personal.conf",
        ".config/waybar/config.jsonc",
        ".config/waybar/style.css",
        ".config/kitty/catppuccin-mocha.conf",
        ".config/fedora-workstation/dnf-packages.txt",
    }


@pytest.mark.parametrize("machine_type", ["macbook", "mac-mini", "lmsh"])
def test_fedora_starter_does_not_add_targets_to_existing_profiles(tmp_path, machine_type):
    config = tmp_path / "chezmoi.toml"
    config.write_text(f'[data]\nmachine_type = "{machine_type}"\n')
    result = subprocess.run(
        ["chezmoi", "--config", str(config), "--source", str(ROOT), "managed", "--include", "files"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert not any(path.startswith((".config/sway/", ".config/waybar/", ".config/fedora-workstation/",
                                     ".config/kitty/catppuccin-mocha.conf"))
                   for path in result.stdout.splitlines())


def test_out_of_band_guest_state_is_reconciled():
    sway = (ROOT / "private_dot_config/sway/config.d/95-fedora-personal.conf").read_text()
    assert "output * bg #1e1e2e solid_color" in sway
    assert "bindsym Mod4+comma layout toggle all" in sway
    assert "client.focused $ctp_lavender $ctp_base $ctp_text $ctp_rosewater $ctp_lavender" in sway
    waybar = json.loads((ROOT / "private_dot_config/waybar/config.jsonc").read_text())
    assert waybar["position"] == "top"
    style = (ROOT / "private_dot_config/waybar/style.css").read_text()
    assert 'font-family: "JetBrainsMono Nerd Font"' in style
    assert "background: #1e1e2e;" in style
    assert "color: #cdd6f4;" in style
    theme = (ROOT / "private_dot_config/kitty/catppuccin-mocha.conf").read_text()
    assert "background              #1E1E2E" in theme
    # The live guest kitty.conf stays a stand-in; the personal profile owns the
    # final template, and macOS kitty.conf keeps its existing mocha.conf include.
    assert (ROOT / "private_dot_config/kitty/kitty.conf").read_text().startswith("include mocha.conf\n")
    for path in ROOT.rglob("*bar-mocha*"):
        raise AssertionError(f"retired bar-mocha artifact reappeared: {path}")


@pytest.mark.parametrize("machine_type", ["macbook", "mac-mini", "lmsh"])
def test_fedora_starter_does_not_add_targets_to_existing_profiles(tmp_path, machine_type):
    config = tmp_path / "chezmoi.toml"
    config.write_text(f'[data]\nmachine_type = "{machine_type}"\n')
    result = subprocess.run(
        ["chezmoi", "--config", str(config), "--source", str(ROOT), "managed", "--include", "files"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert not any(path.startswith((".config/sway/", ".config/fedora-workstation/"))
                   for path in result.stdout.splitlines())


def test_sway_colemak_bindings_remove_conflicting_logout_and_layout():
    config = (ROOT / "private_dot_config/sway/config.d/95-fedora-personal.conf").read_text()
    assert config.index("unbindsym Mod4+Shift+e") < config.index("bindsym Mod4+Shift+e move down")
    assert config.index("unbindsym Mod4+e") < config.index("bindsym Mod4+e focus down")
    for key, direction in zip("neio", ("left", "down", "up", "right")):
        assert f"bindsym Mod4+{key} focus {direction}" in config
        assert f"bindsym Mod4+Shift+{key} move {direction}" in config
    assert "bindsym Mod4+Return exec kitty" in config
