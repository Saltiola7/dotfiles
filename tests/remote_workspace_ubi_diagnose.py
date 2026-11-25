"""Summarize a failed disposable apply. Diagnostics never authorize retry."""
import os
from pathlib import Path
import re
import shutil
import stat
import sys


TAIL_LIMIT = 65536
PREFIX = 'remote owner editor setup failed: '
PREFLIGHT = {
    'unsupported editor setup operation', 'unsafe editor lock', 'invalid lazy revision',
    'editor compiler prerequisite missing', 'unsafe editor directory', 'unsafe lazy directory',
    'installed lazy identity differs from lock', 'unsafe plugin link',
    'plugin contains local work; refusing restore', 'managed editor lock changed during restore',
    'unsafe editor state directory', 'unsafe editor readiness manifest',
    'editor recovery requires operator review', 'unclassified preparation failure',
}
STAGES = {'owner-init', 'plugin-restore', 'plugin-verify', 'parser-build', 'parser-verify', 'native-command'}
INVARIANTS = {
    'locked plugin absent', 'locked plugin restore/build failed', 'locked plugin identity mismatch',
    'parser installation failed', 'required compiled parser absent', 'required parser cannot load',
    'headless editor reported an error', 'output suppressed',
}
HOOKS = {
    'configure-remote-workspace-git.sh': 'git-include',
    'install-01-remote-workspace-tools.sh': 'tools',
    'install-remote-workspace-yazi.sh': 'yazi', 'install-yazi-flavor.sh': 'flavor',
    'zz-remote-workspace-nvim.sh': 'editor',
}
MILESTONES = {
    'remote Git include ready': 'git-include', 'remote overlay tools verified': 'tools',
    **{'remote editor preparation ' + name: name for name in
       ('inputs', 'lazy-bootstrap', 'headless-restore', 'second-startup')},
}
# Public fixed target labels only. Existence is a location hint, not evidence of
# successful native execution. Don't walk plugins, print paths, or inspect auth.
TARGETS = {
    'owner-lock': '.config/nvim/lazy-lock.json', 'restore-lua': '.config/remote-workspace/restore-nvim.lua',
    'git-helper': '.local/bin/remote-workspace-git', 'tool-helper': '.local/bin/remote-workspace-tools',
    'editor-helper': '.local/bin/remote-workspace-nvim', 'yazi': '.local/bin/yazi',
    'ya': '.local/bin/ya', 'fd': '.local/bin/fd', 'fzf': '.local/bin/fzf', '7zz': '.local/bin/7zz',
    'zoxide': '.local/bin/zoxide', 'direnv': '.local/bin/direnv', 'rg': '.local/bin/rg',
    'nvim': '.local/bin/nvim', 'tree-sitter': '.local/libexec/remote-workspace/tree-sitter',
    'tool-receipt': '.local/state/remote-workspace/installed-tools.json',
    'setup-lock': '.local/state/remote-workspace/editor-setup.lock',
    'first-record': '.local/state/remote-workspace/editor-attempts/attempt-0001/record.json',
}


def summary(log: Path, home: Path, fixture: Path) -> str:
    hook = progress = stage = cause = 'unreported'
    with log.open('rb') as stream:
        size = stream.seek(0, os.SEEK_END)
        stream.seek(max(0, size - TAIL_LIMIT))
        data = stream.read(TAIL_LIMIT)
        if size > TAIL_LIMIT:
            data = data.partition(b'\n')[2]  # never attribute a truncated line
    for line in data.decode(errors='replace').splitlines():
        line = re.sub(r'\x1b\[[0-9;]{0,32}m', '', line)  # SGR for diagnosis only
        if line in MILESTONES:
            progress = MILESTONES[line]
        match = re.fullmatch(r'chezmoi: ([a-z0-9.-]+): exit status [0-9]{1,3}', line)
        if match and match[1] in HOOKS:
            hook = HOOKS[match[1]]
        if line.startswith(PREFIX):
            detail = line[len(PREFIX):]
            stage, cause = 'unreported', 'unreported'
            if detail in PREFLIGHT:
                stage, cause = 'preflight', detail
            else:
                native = re.fullmatch(r'editor exit [1-9][0-9]{0,2}; stage ([a-z-]+); (.+)', detail)
                if native and native[1] in STAGES and native[2] in INVARIANTS:
                    stage, cause = native[1], native[2]
        elif line == 'remote overlay tool installation failed; prior generations retained':
            cause = 'tool installation failed'
        elif line == 'remote Git include refused; existing configuration retained':
            cause = 'Git include refused'

    state = home / '.local/state/remote-workspace'
    private = state.is_dir() and not state.is_symlink() and stat.S_IMODE(state.stat().st_mode) == 0o700
    path = os.pathsep.join((str(home / '.local/libexec/remote-workspace'), str(home / '.local/bin'), os.defpath))
    unavailable = ','.join(tool for tool in ('gcc', 'g++', 'make', 'tree-sitter') if not shutil.which(tool, path=path))
    selected = all(shutil.which(tool, path=path) == str(home / '.local/bin' / tool)
                   and (home / '.local/bin' / tool).is_symlink()
                   and (home / '.local/bin' / tool).readlink() == fixture / tool
                   for tool in ('cc', 'c++', 'gcc', 'g++'))
    missing = ','.join(label for label, relative in TARGETS.items() if not (home / relative).is_file())
    return (f'first apply: hook={hook}; last-marker={progress}; stage={stage}; cause={cause}; '
            f'state={"0700" if private else "absent-or-not-private"}; '
            f'compiler={"fixture" if selected else "not-selected"}; unavailable={unavailable or "none"}; '
            f'missing={missing or "none"}')


if __name__ == '__main__':
    try:
        print(summary(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
    except (OSError, ValueError):
        sys.exit('first apply: diagnostic unavailable')
