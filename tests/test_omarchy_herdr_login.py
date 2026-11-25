"""Linux graphical-login recovery. All panes, identities and clients are disposable."""
import errno
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import pytest


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Try Omarchy guest recovery')

ROOT = Path(__file__).resolve().parents[1]
USER = Path('.config/systemd/user')
LINK = USER / 'graphical-session.target.wants/herdr-pane-reconcile.service'
UNIT = USER / 'herdr-pane-reconcile.service'
DATA = {'machine_type': 'omarchy-try', 'name': 'Guest', 'email': 'guest@example.org',
        'atuin_sync_address': '', 'chezmoi': {'os': 'linux', 'arch': 'arm64'}}


def test_login_entry_upgrades_managed_file_to_relative_symlink(tmp_path):
    home = tmp_path / 'home'
    (home / LINK.parent).mkdir(parents=True)
    state = tmp_path / 'state.db'
    old = tmp_path / 'old'
    src = old / 'private_dot_config/systemd/user'
    (src / LINK.parent.name).mkdir(parents=True)
    (src / UNIT.name).write_text('[Service]\nExecStart=/bin/true\n')
    (src / LINK.parent.name / UNIT.name).symlink_to('../' + UNIT.name)
    def apply(source, *targets):
        result = subprocess.run(['chezmoi', '-c', '/dev/null', '--config-format', 'toml', '-S', source,
                        '-D', home, '--persistent-state', state, '--refresh-externals=never',
                        '--no-tty', '--override-data', json.dumps(DATA), 'apply', '--exclude', 'scripts',
                        *(home / entry for entry in targets)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    apply(old, UNIT, LINK)
    assert (home / LINK).is_file() and not (home / LINK).is_symlink()
    apply(ROOT, LINK)
    assert (home / LINK).is_symlink() and os.readlink(home / LINK) == '../' + UNIT.name
    inode = (home / LINK).lstat().st_ino
    apply(ROOT, LINK)
    assert (home / LINK).lstat().st_ino == inode
    # Ask systemd's offline unit-file reader. It never contacts the user manager.
    unit_dir = tmp_path / 'etc/systemd/user'
    unit_dir.parent.mkdir(parents=True)
    unit_dir.symlink_to('../../home/.config/systemd/user')
    state = subprocess.check_output(['systemctl', '--root', tmp_path, '--global', 'is-enabled', UNIT.name], text=True)
    assert state.strip() == 'enabled'


FAKE_HERDR = '''#!/usr/bin/env python3
import json, os, pathlib, sys
home = pathlib.Path.home()
args = sys.argv[1:]
with (home / 'calls').open('a') as f: f.write(json.dumps(args) + '\\n')
state = json.loads((home / 'native').read_text())
if args[:2] == ['workspace', 'list']: result = {'workspaces': state['workspaces']}
elif args[:2] == ['tab', 'list']: result = {'tabs': state['tabs']}
elif args[:2] == ['pane', 'list']: result = {'panes': state['panes']}
elif args[:2] == ['tab', 'create']:
    ws = args[args.index('--workspace')+1]; label = args[args.index('--label')+1]
    state['tabs'].append({'tab_id':'created', 'workspace_id':ws,'label':label,'pane_count':1})
    state['panes'].append({'pane_id':'new1','tab_id':'created','workspace_id':ws})
    (home/'native').write_text(json.dumps(state)); result = {}
elif args[:2] == ['pane','split']:
    last = next(p for p in state['panes'] if p['pane_id']==args[2]); tab = next(t for t in state['tabs'] if t['tab_id']==last['tab_id'])
    tab['pane_count'] += 1; state['panes'].append({**last,'pane_id':'new2'})
    (home/'native').write_text(json.dumps(state)); result = {}
elif args[:2] == ['pane', 'process-info']:
    pid = int((home / 'root-pid').read_text())
    result = {'process_info': {'pane_id': 'w1:p1', 'shell_pid': pid + state.get('offset', 0)}}
else: result = {}
print(json.dumps({'result': result}))
'''


@pytest.fixture
def guest(tmp_path):
    home = tmp_path
    bin_dir = home / '.local/bin'
    bin_dir.mkdir(parents=True)
    for name in ('herdr-pane-reconcile', 'omarchy-herdr-recovery'):
        source = ROOT / 'dot_local/bin' / ('executable_' + name)
        if source.is_file():
            shutil.copyfile(source, bin_dir / name)
            (bin_dir / name).chmod(0o755)
    (bin_dir / 'herdr').write_text(FAKE_HERDR)
    (bin_dir / 'herdr').chmod(0o755)
    (home / '.local/state/dotfiles').mkdir(parents=True)
    mapping = home / '.local/share/dotfiles/herdr-pane-mapping.json'
    mapping.parent.mkdir(parents=True)
    mapping.write_text(json.dumps({'dotfiles': {'work': [{'sid': 'ses_Example1', 'cwd': str(home)}]}}))
    (home / 'calls').touch()
    (home / 'native').write_text(json.dumps({
        'workspaces': [{'workspace_id': 'w1', 'label': 'dotfiles'}],
        'tabs': [{'tab_id': 'tab1', 'workspace_id': 'w1', 'label': 'work', 'pane_count': 1},
                 {'tab_id': 'anchor', 'workspace_id': 'w1', 'label': 'AI-ROI', 'pane_count': 19}],
        'panes': [{'pane_id': 'w1:p1', 'workspace_id': 'w1', 'tab_id': 'tab1', 'cwd': str(home),
                   'agent': 'opencode', 'agent_status': 'working'}] + [
            {'pane_id': f'w1:q{i}', 'workspace_id': 'w1', 'tab_id': 'anchor'} for i in range(19)]}))
    opencode = home / '.opencode/bin/opencode'
    opencode.parent.mkdir(parents=True)
    opencode.write_text('#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n'
                        'with (Path.home()/"launches").open("a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n')
    opencode.chmod(0o755)
    return home, {'HOME': str(home), 'PATH': f'{bin_dir}:/usr/bin:/bin', 'TERM': 'xterm',
                  'HERDR_ENV': '1', 'HERDR_PANE_ID': 'w1:p1', 'HERDR_SESSION': 'default'}


def test_repeated_login_layout_sends_nothing_to_occupied_panes(guest):
    home, env = guest
    for _ in range(2):
        subprocess.run([home / '.local/bin/herdr-pane-reconcile'], env=env, cwd=home,
                       capture_output=True, check=True, timeout=6)
    calls = [json.loads(line) for line in (home / 'calls').read_text().splitlines()]
    assert calls and all(call[:2] in (['workspace','list'], ['tab','list'], ['pane','list']) for call in calls)
    assert not (home / 'launches').exists()


def run_new_shell(home, env, cwd=None):
    # Use the real managed startup snippet in an interactive Bash PTY. No user rc,
    # Herdr socket, session history, or real OpenCode binary can be reached.
    startup = (ROOT / '.chezmoitemplates/omarchy-herdr-shell-start.sh').read_text()
    rc = home / 'fixture.rc'
    rc.write_text('set -e\nprintf "%s" "$$" > "$HOME/root-pid"\n' + startup + '\n' + startup + '\nexit 0\n')
    pid, master = pty.fork()
    if pid == 0:
        os.chdir(cwd or home)
        os.execve('/bin/bash', ['bash', '--noprofile', '--rcfile', str(rc), '-i'], env)
    deadline = time.monotonic() + 10
    reaped = False
    try:
        while time.monotonic() < deadline:
            child, status = os.waitpid(pid, os.WNOHANG)
            if child == pid:
                reaped = True
                assert os.waitstatus_to_exitcode(status) == 0
                return
            if select.select([master], [], [], 0.05)[0]:
                try: os.read(master, 16384)
                except OSError as e:
                    if e.errno != errno.EIO: raise
        pytest.fail('fresh shell did not return')
    finally:
        os.close(master)
        if not reaped:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)


@pytest.mark.parametrize('case', ['mapped', 'nested', 'other-directory', 'unmapped', 'duplicate-tab', 'named-session',
                                   'native-agent', 'extra-pane', 'invalid-id', 'external-directory', 'client-error'])
def test_only_fresh_owning_shell_starts_exact_mapped_client(guest, case):
    home, env = guest
    native = json.loads((home / 'native').read_text())
    # A fresh shell is not a running agent. An editor/agent never executes Bash startup.
    native['panes'][0].pop('agent')
    native['panes'][0]['agent_status'] = 'unknown'
    if case == 'nested':
        native['offset'] = 1
    if case == 'duplicate-tab':
        native['tabs'].append({**native['tabs'][0], 'tab_id': 'another'})
    if case == 'native-agent':
        native['panes'][0]['agent_session'] = {'kind': 'id', 'value': 'ses_Example1'}
    if case == 'extra-pane':
        native['panes'].append({**native['panes'][0], 'pane_id': 'w1:p2'})
        native['tabs'][0]['pane_count'] = 2
    (home / 'native').write_text(json.dumps(native))
    if case == 'named-session':
        env['HERDR_SESSION'] = 'other'
    mapping = home / '.local/share/dotfiles/herdr-pane-mapping.json'
    if case == 'other-directory':
        (home / 'other').mkdir()
        mapping.write_text(json.dumps({'dotfiles': {'work': [{'sid': 'ses_Example1', 'cwd': str(home / 'other')}]}}))
    if case == 'invalid-id':
        mapping.write_text(json.dumps({'dotfiles': {'work':[{'sid':'not a session','cwd':str(home)}]}}))
    if case == 'external-directory':
        external = home / 'Work/MGM'
        external.mkdir(parents=True)
        mapping.write_text(json.dumps({'dotfiles': {'work':[{'sid':'ses_Example1','cwd':str(external)}]}}))
    if case == 'unmapped':
        mapping.unlink()
    if case == 'client-error':
        binary = home / '.opencode/bin/opencode'
        binary.write_text(binary.read_text() + '\nraise SystemExit(47)\n')
    run_new_shell(home, env, home / 'Work/MGM' if case == 'external-directory' else None)
    launches = home / 'launches'
    assert ([json.loads(s) for s in launches.read_text().splitlines()] if launches.exists() else []) == (
        [['--session', 'ses_Example1']] if case in ('mapped','client-error') else [])


def test_layout_fills_missing_tab_and_pane_once_without_stealing_focus(guest):
    home, env = guest
    mapping = home / '.local/share/dotfiles/herdr-pane-mapping.json'
    mapping.write_text(json.dumps({'dotfiles': {'missing': [{'cwd': str(home)}, {'cwd': str(home)}]}}))
    for _ in range(2):
        subprocess.run([home / '.local/bin/herdr-pane-reconcile'], env=env, cwd=home,
                       capture_output=True, check=True, timeout=6)
    calls = [json.loads(line) for line in (home / 'calls').read_text().splitlines()]
    writes = [call for call in calls if call[1] != 'list']
    assert [call[:2] for call in writes] == [['tab', 'create'], ['pane', 'split']]
    assert all('--no-focus' in call for call in writes)
    assert not (home / 'launches').exists()


def test_only_guest_bash_includes_the_startup_handshake():
    template = (ROOT / 'dot_bashrc.tmpl').read_text()
    hook = (ROOT / '.chezmoitemplates/omarchy-herdr-shell-start.sh').read_text().strip()
    for machine in ('omarchy-try', 'omarchy'):
        command = ['chezmoi', '-S', str(ROOT), '-c', '/dev/null', '--config-format', 'toml',
                   '--override-data', json.dumps({**DATA, 'machine_type':machine})]
        rendered = subprocess.run([*command, 'execute-template'], input=template, text=True,
                                  capture_output=True, check=True).stdout
        subprocess.run(['bash', '-n'], input=rendered, text=True, check=True)
        assert (hook in rendered) == (machine == 'omarchy-try')
        links = subprocess.check_output([*command, 'managed', '--include', 'symlinks'], text=True)
        assert (str(LINK) in links.splitlines()) == (machine == 'omarchy-try')


def test_native_herdr_restores_exact_client_once_per_server_start(guest):
    herdr = shutil.which('herdr')
    if not herdr or subprocess.check_output([herdr, '--version'], text=True).strip() != 'herdr 0.9.5':
        pytest.skip('optional native Herdr 0.9.5 qualification')
    home, _ = guest
    # Both the API and its derived client socket must be inside this short,
    # private directory before any CLI call. Inherit no host XDG / Herdr state.
    with tempfile.TemporaryDirectory(prefix='herdr-login-') as sockets:
        api = Path(sockets) / 'api.sock'
        client = Path(sockets) / 'api-client.sock'
        cfg = home / '.config/herdr/config.toml'
        cfg.parent.mkdir(parents=True)
        cfg.write_text('onboarding = false\n')
        env = {'HOME': str(home), 'SHELL': '/bin/bash', 'TERM': 'xterm-256color',
               'PATH': f"{home}/.local/bin:/usr/bin:/bin", 'XDG_RUNTIME_DIR': sockets,
               'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_DATA_HOME': str(home / '.local/share'),
               'XDG_STATE_HOME': str(home / 'state'), 'XDG_CACHE_HOME': str(home / 'cache'),
               'HERDR_SOCKET_PATH': str(api), 'HERDR_CLIENT_SOCKET_PATH': str(client),
               'HERDR_CONFIG_PATH': str(cfg)}
        fake = home / '.local/bin/herdr'
        fake.unlink()
        fake.symlink_to(herdr)
        (home / '.bashrc').write_text((ROOT / '.chezmoitemplates/omarchy-herdr-shell-start.sh').read_text())
        (home / '.bash_profile').write_text('source "$HOME/.bashrc"\n')
        def start():
            return subprocess.Popen([herdr, 'server'], cwd=home, env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        def stop(server):
            if server.poll() is None:
                server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()

        def command(*args):
            return subprocess.check_output([herdr, *args], cwd=home, env=env, text=True, timeout=4)

        receipt = home / 'launches'
        for generation in (1, 2):
            server = start()
            try:
                until = time.monotonic() + 8
                while True:
                    assert server.poll() is None and time.monotonic() < until, 'isolated Herdr not ready'
                    if api.is_socket() and client.is_socket():
                        try:
                            tabs = json.loads(command('tab', 'list'))['result']['tabs']
                            if generation == 1 or any(t.get('label') == 'work' for t in tabs):
                                break
                        except (subprocess.SubprocessError, ValueError, KeyError):
                            pass  # Retry observations only, never a creation or launch.
                    time.sleep(0.05)
                if generation == 1:
                    command('workspace', 'create', '--label', 'dotfiles', '--cwd', str(home), '--no-focus')
                    subprocess.run([home / '.local/bin/herdr-pane-reconcile'], env=env, cwd=home,
                                   check=True, timeout=8)
                else:
                    # No layout command yet: exercise a retained tab's new Bash on
                    # native server restart, not separately created replacement panes.
                    assert sum(t.get('label') == 'work' for t in tabs) == 1
                until = time.monotonic() + 8
                while time.monotonic() < until:
                    if receipt.exists() and len(receipt.read_text().splitlines()) >= generation:
                        break
                    time.sleep(0.05)
                subprocess.run([home / '.local/bin/herdr-pane-reconcile'], env=env, cwd=home,
                               check=True, timeout=8)
                assert receipt.is_file(), 'fresh native pane did not open its mapped fixture client'
                assert [json.loads(s) for s in receipt.read_text().splitlines()] == [
                    ['--session', 'ses_Example1']] * generation
            finally:
                stop(server)
