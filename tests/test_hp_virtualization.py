"""HP virtualization: managed-set isolation and an off-host rehearsal."""
import json
import os
from pathlib import Path
import pty
import re
import shutil
import subprocess
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "dot_local/bin/executable_hp-virtualization-setup"
WRAPPER = ROOT / "run_always_setup-hp-virtualization.sh.tmpl"
IGNORE = ROOT / ".chezmoiignore"
GATE = ('and (eq .machine_type "omarchy") (eq .chezmoi.os "linux") '
        '(eq .chezmoi.arch "amd64") (eq .chezmoi.hostname "omarchy")')
TARGETS = {".local/bin/hp-virtualization-setup", "always_setup-hp-virtualization.sh"}
# The Try Omarchy guest answers to the same hostname as the HP.
OTHERS = [
    ("omarchy-try", "omarchy", "arm64", "linux"),
    ("omarchy", "mbp-omarchy", "amd64", "linux"),
    ("omarchy", "old-omarchy", "amd64", "linux"),
    ("mac-mini", "mac-mini", "arm64", "darwin"),
]
PACKAGES = ["qemu-desktop", "libvirt", "virt-install", "virt-manager", "dnsmasq", "swtpm"]
UFW_RULES = {
    "route allow in on virbr0": "-A ufw-user-forward -i virbr0 -j ACCEPT",
    "route allow out on virbr0": "-A ufw-user-forward -o virbr0 -j ACCEPT",
    "allow in on virbr0": "-A ufw-user-input -i virbr0 -j ACCEPT",
}
FIRST_RUN = [
    "sudo pacman -S --noconfirm --needed " + " ".join(PACKAGES),
    "sudo groupadd --system libvirt",
    "sudo usermod -aG libvirt test",
    "sudo systemctl enable --now libvirtd.service",
    "sudo virsh --connect qemu:///system net-autostart default",
    "sudo virsh --connect qemu:///system net-start default",
    *["sudo ufw " + rule for rule in UFW_RULES],
]

# Every privileged or system-mutating command is a stub that records itself.
STUBS = {
    "hostname": "echo omarchy\n",
    "pacman": '[ "$1" = -Q ] && grep -qx -- "$2" "$STUB_STATE/installed"\n',
    "omarchy": """\
[ "$1 $2" = "pkg add" ] || exit 2
shift 2
echo "sudo pacman -S --noconfirm --needed $*" >>"$STUB_STATE/calls"
printf '%s\\n' "$@" >>"$STUB_STATE/installed"
""",
    "id": """\
if [ "$1" = -un ]; then echo test
elif [ "$1" = -nG ]; then
  if [ $# -eq 1 ]; then tr ' ' '\\n' <"$STUB_STATE/session_groups"
  else tr ' ' '\\n' <"$STUB_STATE/db_groups"; fi
else exit 2
fi
""",
    "getent": '[ "$1 $2" = "group libvirt" ] && grep -qx libvirt "$STUB_STATE/group_db"\n',
    "systemctl": """\
case "$1" in
  is-enabled) [ "$3" = libvirtd.service ] && [ -e "$STUB_STATE/libvirtd_enabled" ] ;;
  is-active) [ -e "$STUB_STATE/active:$3" ] ;;
  enable) touch "$STUB_STATE/libvirtd_enabled" "$STUB_STATE/active:libvirtd.service" ;;
  *) exit 2 ;;
esac
""",
    "virsh": """\
case "$*" in
  *" uri") ;;
  *" net-info default")
    for key in Active Persistent Autostart; do
      lower=$(echo "$key" | tr '[:upper:]' '[:lower:]')
      if [ -e "$STUB_STATE/net_$lower" ]; then echo "$key: yes"; else echo "$key: no"; fi
    done ;;
  *" capabilities")
    echo "<guest><arch name='x86_64'><domain type='qemu'/>"
    if [ -c "$HP_VIRT_KVM_DEVICE" ]; then echo "<domain type='kvm'>"; fi
    echo "</arch></guest>" ;;
  *" net-autostart default") touch "$STUB_STATE/net_autostart" ;;
  *" net-start default") touch "$STUB_STATE/net_active" ;;
  *) exit 2 ;;
esac
""",
    "sudo": """\
echo "sudo $*" >>"$STUB_STATE/calls"
command=$1; shift
case "$command" in
  groupadd) echo libvirt >>"$STUB_STATE/group_db" ;;
  usermod) echo libvirt >>"$STUB_STATE/db_groups" ;;
  systemctl | virsh | ufw | modprobe) exec "$command" "$@" ;;
  *) exit 2 ;;
esac
""",
    "modprobe": """\
[ "$1" = kvm_intel ] && [ -z "${STUB_NO_KVM:-}" ] && ln -s /dev/null "$HP_VIRT_KVM_DEVICE"
exit 0
""",
}
STUBS["ufw"] = 'case "$*" in\n' + "".join(
    f'  "{rule}") echo "{line}" ;;\n' for rule, line in UFW_RULES.items()
) + '  *) exit 2 ;;\nesac >>"$HP_VIRT_UFW_RULES"\n'


def chezmoi(machine_type, hostname, arch, os_name, *args, text=None):
    data = {
        "machine_type": machine_type,
        "name": "Test User",
        "email": "test@example.com",
        "atuin_sync_address": "https://api.atuin.sh",
        "blackarch_enabled": False,
        "chezmoi": {
            "os": os_name, "arch": arch, "hostname": hostname,
            "homeDir": "/home/test", "username": "test",
        },
    }
    return subprocess.run(
        ["chezmoi", "-S", str(ROOT), "--config", "/dev/null", "--config-format", "toml",
         "--override-data", json.dumps(data), *args],
        input=text, capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture
def rig(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "group_db").write_text("kvm\nwheel\n")
    (state / "db_groups").write_text("wheel\n")
    (state / "session_groups").write_text("wheel\n")
    (state / "net_persistent").touch()
    (state / "active:ufw.service").touch()
    stubs = tmp_path / "bin"
    stubs.mkdir()
    for name, body in STUBS.items():
        path = stubs / name
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    product = inputs / "product"
    product.write_text("HP ENVY Laptop 13-ah0xxx\n")
    cpuinfo = inputs / "cpuinfo"
    cpuinfo.write_text("processor\t: 0\nflags\t\t: fpu sse\n")
    env = {
        **os.environ,
        "PATH": f"{stubs}:{os.environ['PATH']}",
        "STUB_STATE": str(state),
        "HP_VIRT_PRODUCT_FILE": str(product),
        "HP_VIRT_CPUINFO_FILE": str(cpuinfo),
        "HP_VIRT_KVM_DEVICE": "/dev/null",
        "HP_VIRT_UFW_RULES": str(inputs / "user.rules"),
    }

    def run(tty=True, **override):
        merged = {**env, **override}
        if not tty:
            return subprocess.run([str(HELPER)], stdin=subprocess.DEVNULL, capture_output=True,
                                  text=True, env=merged, timeout=30)
        master, slave = pty.openpty()
        try:
            return subprocess.run([str(HELPER)], stdin=slave, capture_output=True,
                                  text=True, env=merged, timeout=30)
        finally:
            os.close(master)
            os.close(slave)

    def calls():
        log = state / "calls"
        return log.read_text().splitlines() if log.exists() else []

    def converged():
        (state / "installed").write_text("\n".join(PACKAGES) + "\n")
        (state / "libvirtd_enabled").touch()
        (state / "active:libvirtd.service").touch()
        (state / "net_autostart").touch()
        (state / "net_active").touch()
        (state / "db_groups").write_text("wheel libvirt\n")
        (state / "session_groups").write_text("wheel libvirt\n")
        (inputs / "user.rules").write_text("".join(line + "\n" for line in UFW_RULES.values()))
        cpuinfo.write_text("processor\t: 0\nflags\t\t: fpu vmx ept\n")

    return SimpleNamespace(state=state, inputs=inputs, product=product, run=run,
                           calls=calls, converged=converged)


def test_stack_is_managed_only_on_the_hp():
    managed = set(chezmoi("omarchy", "omarchy", "amd64", "linux",
                          "managed", "--include", "files,scripts").splitlines())
    assert TARGETS <= managed
    for profile in OTHERS:
        managed = set(chezmoi(*profile, "managed", "--include", "files,scripts").splitlines())
        assert not TARGETS & managed, profile


def test_wrapper_shares_the_ignore_gate_and_needs_a_terminal(tmp_path):
    assert GATE in IGNORE.read_text()
    assert GATE in WRAPPER.read_text()
    rendered = chezmoi("omarchy", "omarchy", "amd64", "linux",
                       "execute-template", text=WRAPPER.read_text())
    assert 'exec "$HOME/.local/bin/hp-virtualization-setup"' in rendered
    assert "[[ -t 0 ]]" in rendered
    script = tmp_path / "wrapper.sh"
    script.write_text(rendered)
    bash = shutil.which("bash")
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    pending = subprocess.run([bash, str(script)], stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, env={**os.environ, "PATH": str(empty)})
    assert pending.returncode == 0 and "Privileged setup pending" in pending.stderr
    (empty / "virsh").write_text("#!/bin/sh\nexit 2\n")
    (empty / "virsh").chmod(0o755)
    quiet = subprocess.run([bash, str(script)], stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, env={**os.environ, "PATH": str(empty)})
    assert quiet.returncode == 0 and quiet.stderr == ""
    for profile in OTHERS:
        rendered = chezmoi(*profile, "execute-template", text=WRAPPER.read_text())
        assert rendered.strip() == "#!/usr/bin/env bash\nexit 0", profile


def test_helper_keeps_firmware_firewall_defaults_and_reboots_manual():
    subprocess.run(["bash", "-n", str(HELPER)], check=True)
    script = HELPER.read_text()
    assert '== omarchy && $(<"$HP_VIRT_PRODUCT_FILE")' in script
    assert "HP ENVY Laptop 13-ah0xxx" in script
    assert "packages=(" + " ".join(PACKAGES) + ")" in script
    assert 'omarchy pkg add "${missing[@]}"' in script
    assert "usermod -aG libvirt" in script
    assert "systemctl enable --now libvirtd.service" in script
    assert re.findall(r"^ +sudo ufw (.+)$", script, re.M) == list(UFW_RULES)
    reboot_lines = [line for line in script.splitlines() if "reboot" in line]
    assert all(line.lstrip().startswith(("#", "note ")) for line in reboot_lines)
    assert any("systemctl reboot --firmware-setup" in line for line in reboot_lines)
    for forbidden in ("pacman -Sy", "ufw disable", "ufw default", "ufw --force", "pkill",
                      "mkfs", "wipefs", "virsh destroy", "virsh undefine"):
        assert forbidden not in script


def test_rehearsal_installs_then_reports_the_pending_firmware_step(rig):
    first = rig.run()
    assert first.returncode == 0, first.stderr
    assert (rig.state / "installed").read_text().split() == PACKAGES
    assert rig.calls() == FIRST_RUN
    assert "VT-x is still disabled in firmware" in first.stdout
    assert "sudo systemctl reboot --firmware-setup" in first.stdout
    second = rig.run()
    assert second.returncode == 0, second.stderr
    assert rig.calls() == FIRST_RUN


def test_rehearsal_confirms_kvm_once_firmware_exposes_vmx(rig):
    rig.converged()
    ready = rig.run()
    assert ready.returncode == 0, ready.stderr
    assert "Ready:" in ready.stdout
    assert rig.calls() == []

    (rig.state / "session_groups").write_text("wheel\n")
    stale = rig.run()
    assert stale.returncode == 0, stale.stderr
    assert "Log out and back in" in stale.stdout
    assert rig.calls() == []

    (rig.state / "session_groups").write_text("wheel libvirt\n")
    absent = rig.run(HP_VIRT_KVM_DEVICE=str(rig.inputs / "kvm"))
    assert absent.returncode == 0, absent.stderr
    assert "Ready:" in absent.stdout
    assert rig.calls() == ["sudo modprobe kvm_intel"]


def test_rehearsal_fails_when_libvirt_cannot_offer_kvm(rig):
    rig.converged()
    result = rig.run(HP_VIRT_KVM_DEVICE=str(rig.inputs / "kvm"), STUB_NO_KVM="1")
    assert result.returncode == 1
    assert "does not report KVM" in result.stderr
    assert rig.calls() == ["sudo modprobe kvm_intel"]


def test_rehearsal_leaves_the_firewall_alone_when_ufw_is_inactive(rig):
    (rig.state / "active:ufw.service").unlink()
    result = rig.run()
    assert result.returncode == 0, result.stderr
    assert not [call for call in rig.calls() if " ufw " in call]


def test_rehearsal_refuses_when_the_default_network_definition_is_absent(rig):
    (rig.state / "net_persistent").unlink()
    result = rig.run()
    assert result.returncode == 1
    assert "default network definition is missing" in result.stderr


def test_rehearsal_touches_nothing_on_a_foreign_host_or_without_a_terminal(rig):
    rig.product.write_text("ThinkPad\n")
    foreign = rig.run()
    assert foreign.returncode == 1 and "Only for the HP" in foreign.stderr
    rig.product.write_text("HP ENVY Laptop 13-ah0xxx\n")
    quiet = rig.run(tty=False)
    assert quiet.returncode == 1 and "Run hp-virtualization-setup in a terminal" in quiet.stderr
    assert rig.calls() == []
