"""Synthetic recovery contracts; these do not qualify native Neovim/parsers."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from tests.test_remote_workspace_nvim import editor_module


@pytest.fixture
def model_install(tmp_path, monkeypatch):
    """Filesystem/transition model: never executes Git, Neovim or a compiler."""
    core = editor_module()
    home = tmp_path / 'home'
    config = home / '.config/nvim'
    config.mkdir(parents=True)
    lock = config / 'lazy-lock.json'
    revision = 'a' * 40
    names = ('lazy.nvim', 'fixture.nvim')
    lock.write_text(json.dumps({n: {'commit': revision, 'branch': 'main'} for n in names}))
    (config / 'init.lua').write_text('-- synthetic owner\n')
    script = home / '.config/remote-workspace/restore-nvim.lua'
    script.parent.mkdir()
    script.write_text('-- synthetic restore\n')
    monkeypatch.setattr(core, 'OWNER_SHA256', core.owner_digest(config, script))
    state = home / '.local/state/remote-workspace'
    data = home / '.local/share/nvim'
    calls = []
    control = {}
    def clone(plugin):
        (plugin / '.git').mkdir(parents=True)
        (plugin / '.git/HEAD').write_text(revision)
        (plugin / 'doc').mkdir()
        (plugin / 'doc/help.txt').write_bytes(b'fixture help')
    def run(*args, env, **kwargs):
        if args[0] == 'git':
            plugin = Path(args[args.index('-C') + 1])
            if 'rev-parse' in args:
                return (plugin / '.git/HEAD').read_text()
            if 'status' in args:
                return '?? doc/tags' if (plugin / 'doc/tags').exists() else ''
            if 'ls-tree' in args:
                import hashlib
                blob = hashlib.sha1(b'blob 12\0fixture help').hexdigest()
                return f'100644 blob {blob}\tdoc/help.txt\0'
            pytest.fail('unmodelled read-only Git predicate')
        assert args[0] == str(home / '.local/bin/nvim')
        staged = env.get('REMOTE_WORKSPACE_LAZY_ROOT')
        root = Path(staged) if staged else data / 'lazy'
        site = Path(env['XDG_DATA_HOME']) / 'nvim/site'
        stage = 'restore' if '-l' in args else 'second' if root != data / 'lazy' else 'normal'
        calls.append((stage, site, env))
        if stage == 'restore':
            for name in names:
                if not (root / name).exists():
                    clone(root / name)
            (root / 'fixture.nvim/doc/tags').write_text('generated')
            (site / 'parser').mkdir(parents=True)
            for lang in ('bash', 'python', 'lua', 'vim', 'vimdoc', 'json', 'yaml', 'toml',
                         'markdown', 'sql', 'markdown_inline'):
                (site / 'parser' / (lang + '.so')).write_bytes(b'model, not a parser')
        if 'callback' in control:
            control['callback'](stage, root, site)
        if control.get('fail') == stage:
            raise core.EditorSetupFailure(1, '')
        return '' if control.get('silent') == stage else 'remote owner AstroNvim ten parsers verified'
    monkeypatch.setattr(core, 'run', run)
    monkeypatch.setattr(core, 'bootstrap', lambda lazy, *args: clone(lazy))
    monkeypatch.setattr(core.shutil, 'which', lambda *a, **kw: '/synthetic/tool')
    def apply():
        # main owns and revalidates the actual advisory lock.
        monkeypatch.setattr(core.Path, 'home', staticmethod(lambda: home))
        monkeypatch.setattr(core.sys, 'argv', ['remote-workspace-nvim'])
        core.main()
    return core, home, data, state, calls, control, clone, apply


@pytest.mark.parametrize('change', ['unknown', 'commit', 'hidden-untracked', 'hidden-tracked', 'empty-dir', 'late'])
def test_model_no_unverified_normal_preimage(model_install, monkeypatch, change):
    core, home, data, state, calls, control, clone, apply = model_install
    plugin = data / 'lazy/fixture.nvim'
    clone(plugin)
    if change == 'unknown':
        clone(data / 'lazy/unlocked')
    elif change == 'commit':
        (plugin / '.git/HEAD').write_text('b' * 40)
    elif change == 'hidden-untracked':
        (plugin / '.owner-note').write_text('status omitted this')
    elif change == 'hidden-tracked':
        (plugin / 'doc/help.txt').write_text('status omitted this')
    elif change == 'empty-dir':
        (plugin / 'untracked-empty-dir').mkdir()
    else:
        original = core.precheck
        def changed(*args, **kwargs):
            original(*args, **kwargs)
            (plugin / 'doc/help.txt').write_text('after clean check')
        monkeypatch.setattr(core, 'precheck', changed)
    with pytest.raises(ValueError):
        apply()
    assert not calls
    assert plugin.is_dir() and not (state / 'editor-ready.json').exists()


def test_model_retry_preserves_first_preimage_through_second_clean_check(model_install, monkeypatch):
    core, home, data, state, calls, control, clone, apply = model_install
    clone(data / 'lazy/fixture.nvim')
    control['fail'] = 'restore'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    first = state / 'editor-attempts/attempt-0001'
    sealed = core.inventory(first)
    control.clear()
    calls.clear()
    original = core.precheck
    def changed(*args, **kwargs):
        original(*args, **kwargs)
        (data / 'lazy/fixture.nvim/doc/help.txt').write_bytes(b'late owner edit')
    monkeypatch.setattr(core, 'precheck', changed)
    with pytest.raises(ValueError):
        apply()
    assert not calls and core.inventory(first) == sealed
    assert (data / 'lazy/fixture.nvim/doc/help.txt').read_bytes() == b'late owner edit'


@pytest.mark.parametrize('when', ['before', 'during', 'retry'])
def test_model_known_owner_config_required(model_install, when):
    core, home, data, state, calls, control, clone, apply = model_install
    init = home / '.config/nvim/init.lua'
    if when == 'retry':
        control['fail'] = 'restore'
        with pytest.raises(core.EditorSetupFailure):
            apply()
        calls.clear()
        control.clear()
    if when == 'during':
        control['callback'] = lambda *_: init.write_text('-- changed during restore')
    else:
        init.write_text('-- unreviewed')
    with pytest.raises(ValueError):
        apply()
    assert len(calls) == (1 if when == 'during' else 0)
    assert not (state / 'editor-ready.json').exists()


@pytest.mark.parametrize('dest', ['site/parser/lua.so', 'mason/owner', 'unrelated'])
def test_model_refuses_unproven_data_destination_before_native(model_install, dest):
    core, home, data, state, calls, control, clone, apply = model_install
    owner = data / dest
    owner.parent.mkdir(parents=True)
    owner.write_bytes(b'owner')
    before = core.inventory(data)
    with pytest.raises(ValueError):
        apply()
    assert not calls and core.inventory(data) == before


@pytest.mark.parametrize('when', ['restore', 'second', 'normal'])
def test_model_zero_exit_without_parser_proof_never_selects_failed_generation(model_install, when):
    core, home, data, state, calls, control, clone, apply = model_install
    clone(data / 'lazy/fixture.nvim')
    before = core.inventory(data)
    control['silent'] = when
    with pytest.raises(core.EditorSetupFailure):
        apply()
    assert core.inventory(data) == before
    assert not (state / 'editor-ready.json').exists()


@pytest.mark.parametrize('mutation', ['unknown-plugin', 'edit-after-check'])
def test_model_candidate_proof_binds_exact_generation(model_install, monkeypatch, mutation):
    core, home, data, state, calls, control, clone, apply = model_install
    if mutation == 'unknown-plugin':
        control['callback'] = lambda stage, root, _: clone(root / 'surprise') if stage == 'restore' else None
    else:
        original = core.check_plugins
        def changed(root, *args, **kwargs):
            result = original(root, *args, **kwargs)
            if not kwargs.get('fresh') and root != data / 'lazy':
                (root / 'fixture.nvim/doc/help.txt').write_bytes(b'after check')
            return result
        monkeypatch.setattr(core, 'check_plugins', changed)
    with pytest.raises(ValueError):
        apply()
    assert not (data / 'lazy').exists() and not (state / 'editor-ready.json').exists()


@pytest.mark.parametrize('change', ['journal', 'lock', 'previous', 'retained', 'ready-race', 'setup-lock'])
def test_model_publication_revalidates_all_evidence(model_install, change):
    core, home, data, state, calls, control, clone, apply = model_install
    clone(data / 'lazy/fixture.nvim')
    control['fail'] = 'restore'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    control.clear()
    target = state / 'editor-ready.json'
    def change_while_testing(stage, *_):
        if stage != 'normal':
            return
        latest = state / 'editor-attempts/attempt-0002'
        if change == 'journal':
            (latest / 'record.json').write_text('{}')
        elif change == 'lock':
            lock = home / '.config/nvim/lazy-lock.json'
            lock.write_bytes(lock.read_bytes() + b'\n')
        elif change == 'previous':
            (latest / 'previous/owner').write_text('keep')
        elif change == 'retained':
            (state / 'editor-attempts/attempt-0001/candidate/owner').write_text('keep')
        elif change == 'setup-lock':
            held = state / 'editor-setup.lock'
            held.rename(state / 'original-lock')
            held.touch(mode=0o600)
        else:
            target.touch(mode=0o600)
            target.write_bytes(b'owner')
    control['callback'] = change_while_testing
    with pytest.raises((ValueError, OSError)):
        apply()
    assert target.read_bytes() == b'owner' if change == 'ready-race' else not target.exists()


def test_model_staged_xdg_and_manifest_never_claim_unrelated_files(model_install):
    core, home, data, state, calls, control, clone, apply = model_install
    keep = []
    for prefix in ('.cache/nvim', '.local/state/nvim', '.local/share/another-app'):
        path = home / prefix / 'owner'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'keep')
        keep.append(path)
    apply()
    assert calls[0][1] != data / 'site' and calls[-1][1] == data / 'site'
    for _, _, env in calls:
        assert Path(env['XDG_CACHE_HOME']) != home / '.cache'
        assert Path(env['XDG_STATE_HOME']) != home / '.local/state'
    assert len({env['XDG_CACHE_HOME'] for _, _, env in calls}) == 3
    assert len({env['XDG_STATE_HOME'] for _, _, env in calls}) == 3
    saved = json.loads((state / 'editor-ready.json').read_bytes())
    assert all(path.read_bytes() == b'keep' and str(path.relative_to(home)) not in saved['files'] for path in keep)
    assert (data / 'site/parser/markdown_inline.so').is_file()


@pytest.mark.parametrize('change', ['fields', 'parsers', 'files', 'journal'])
def test_model_reapply_rejects_incomplete_readiness_before_native(model_install, change):
    core, home, data, state, calls, control, clone, apply = model_install
    apply()
    path = state / 'editor-ready.json'
    saved = json.loads(path.read_bytes())
    if change == 'fields':
        del saved['files']
    elif change == 'parsers':
        saved['required_parsers'] = ['lua']
    elif change == 'files':
        saved['files'].remove('.local/share/nvim/site/parser/sql.so')
    else:
        (state / 'editor-attempts/attempt-0001/record.json').write_text('{}')
    path.write_text(json.dumps(saved))
    calls.clear()
    with pytest.raises(ValueError):
        apply()
    assert not calls


def test_model_final_startup_that_changes_selected_tree_preserves_ambiguity(model_install):
    core, home, data, state, calls, control, clone, apply = model_install
    clone(data / 'lazy/fixture.nvim')
    original = core.inventory(data)
    def edit(stage, root, site):
        if stage == 'normal':
            (root / 'fixture.nvim/doc/help.txt').write_text('concurrent owner work')
    control.update(fail='normal', callback=edit)
    with pytest.raises(ValueError):
        apply()
    gen = state / 'editor-attempts/attempt-0001'
    # Normal startup gates the marked data on a separate *successful final*
    # state. Do not roll back a concurrently edited directory by shape.
    assert json.loads((data / '.remote-workspace-generation').read_bytes()) == {'generation': gen.name}
    assert core.read_attempt(gen / 'record.json')['state'] != 'accepted'
    assert not (state / 'editor-ready.json').exists()
    assert core.inventory(gen / 'previous') == original
    assert (data / 'lazy/fixture.nvim/doc/help.txt').read_text() == 'concurrent owner work'
    calls.clear()
    with pytest.raises(ValueError):
        apply()
    assert not calls


@pytest.mark.parametrize('change', ['record', 'retained', 'lock', 'normal'])
def test_model_last_publication_boundary(model_install, monkeypatch, change):
    core, home, data, state, calls, control, clone, apply = model_install
    control['fail'] = 'restore'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    control.clear()
    publish = core.publish
    def fault(path, doc, **kwargs):
        if path.name == 'editor-ready.json':
            if change == 'record':
                (state / 'editor-attempts/attempt-0002/record.json').write_text('{}')
            elif change == 'retained':
                (state / 'editor-attempts/attempt-0001/candidate/nvim/owner').write_text('keep')
            elif change == 'lock':
                (home / '.config/nvim/lazy-lock.json').write_text('{}')
            else:
                (data / 'lazy/fixture.nvim/doc/help.txt').write_text('owner')
        publish(path, doc, **kwargs)
    monkeypatch.setattr(core, 'publish', fault)
    with pytest.raises(ValueError):
        apply()
    assert not (state / 'editor-ready.json').exists()


def test_model_prior_complete_readiness_is_verify_only(model_install):
    core, home, data, state, calls, control, clone, apply = model_install
    for name in ('lazy.nvim', 'fixture.nvim'):
        clone(data / 'lazy' / name)
    parser = data / 'site/parser'
    parser.mkdir(parents=True)
    for name in (*core.PARSERS, 'markdown_inline'):
        (parser / (name + '.so')).write_bytes(b'fixture')
    state.mkdir(mode=0o700, parents=True)
    lock = home / '.config/nvim/lazy-lock.json'
    target = state / 'editor-ready.json'
    doc = dict(lock_sha256=core.hashlib.sha256(lock.read_bytes()).hexdigest(), generated_tags={},
               files=core.file_manifest(home, data, core.inventory(data)), required_parsers=core.PARSERS)
    core.publish(target, doc)
    before = core.inventory(data)
    ready = target.stat()
    apply()
    assert [stage for stage, *_ in calls] == ['normal']
    assert target.stat().st_ino == ready.st_ino and target.stat().st_mtime_ns == ready.st_mtime_ns
    assert core.inventory(data) == before and not (state / 'editor-attempts').exists()


@pytest.mark.parametrize('boundary', ['withdrawing', 'deselected', 'restored', 'withdrawn', 'accepted'])
def test_model_interrupted_final_check_reconciles_only_exact_layout(model_install, monkeypatch, boundary):
    core, home, data, state, calls, control, clone, apply = model_install
    clone(data / 'lazy/fixture.nvim')
    original = core.inventory(data)
    if boundary != 'accepted':
        control['fail'] = 'normal'
    write, rename = core.write_attempt, core.move_no_replace
    def after_write(gen, rec):
        write(gen, rec)
        if rec['state'] == boundary:
            raise RuntimeError('synthetic interruption')
    def after_rename(path, destination):
        result = rename(path, destination)
        if ((boundary == 'deselected' and path == data and destination.parent.name == 'candidate')
                or boundary == 'restored' and path.name == 'previous' and destination == data):
            raise RuntimeError('synthetic interruption')
        return result
    with monkeypatch.context() as fault:
        fault.setattr(core, 'write_attempt', after_write)
        fault.setattr(core, 'move_no_replace', after_rename)
        with pytest.raises(RuntimeError):
            apply()
    assert not (state / 'editor-ready.json').exists()
    control.clear()
    calls.clear()
    apply()
    gen = state / 'editor-attempts/attempt-0001'
    assert [stage for stage, *_ in calls] == ['normal']
    assert core.inventory(gen / 'previous') == original
    assert core.read_attempt(gen / 'record.json')['state'] == 'accepted'


def test_model_missing_parser_file_cannot_be_promoted_on_exit_marker(model_install):
    core, home, data, state, calls, control, clone, apply = model_install
    def no_parser(stage, root, site):
        if stage == 'restore':
            (site / 'parser/sql.so').unlink()
    control['callback'] = no_parser
    with pytest.raises(core.EditorSetupFailure):
        apply()
    assert not data.exists() and not (state / 'editor-ready.json').exists()
    assert [stage for stage, *_ in calls] == ['restore']
    assert core.read_attempt(state / 'editor-attempts/attempt-0001/record.json')['state'] == 'failed_sealed'


def test_inventory_preserves_identity_and_detects_all_changes(tmp_path):
    core = editor_module()
    root = tmp_path / 'candidate'
    root.mkdir(mode=0o700)
    file = root / 'tags'
    file.write_bytes(b'generated')
    before = core.inventory(root)
    assert before == core.inventory(root)
    file.write_bytes(b'owner edit')
    assert before != core.inventory(root)
    file.unlink()
    assert before != core.inventory(root)
    file.write_bytes(b'generated')
    (root / 'extra').write_bytes(b'owner work')
    assert before != core.inventory(root)


@pytest.mark.parametrize('unsafe', ['symlink', 'hardlink', 'bound'])
def test_inventory_refuses_unsafe_objects(tmp_path, monkeypatch, unsafe):
    core = editor_module()
    root = tmp_path / 'candidate'
    root.mkdir(mode=0o700)
    (root / 'file').write_bytes(b'content')
    if unsafe == 'symlink':
        (root / 'link').symlink_to(root / 'file')
    elif unsafe == 'hardlink':
        os.link(root / 'file', root / 'link')
    else:
        monkeypatch.setattr(core, 'MAX_ENTRIES', 0)
    with pytest.raises(ValueError):
        core.inventory(root)


@pytest.mark.parametrize('bound', ['MAX_FILE_BYTES', 'MAX_TOTAL_BYTES'])
def test_inventory_byte_limits_are_enforced(tmp_path, monkeypatch, bound):
    core = editor_module()
    root = tmp_path / 'candidate'
    root.mkdir(mode=0o700)
    (root / 'file').write_bytes(b'bounded content')
    monkeypatch.setattr(core, bound, 1)
    with pytest.raises(ValueError):
        core.inventory(root)


def test_nonregular_owner_lock_never_blocks_a_guard(tmp_path):
    core = editor_module()
    lock = tmp_path / 'owner-lock'
    os.mkfifo(lock, 0o600)
    with pytest.raises(ValueError):
        core.private_read(lock, private=False)


def test_journal_duplicate_json_and_unsafe_file_refuse(tmp_path):
    core = editor_module()
    path = tmp_path / 'record.json'
    path.write_text('{"version":1,"version":1}')
    path.chmod(0o600)
    with pytest.raises(ValueError):
        core.read_attempt(path)
    path.write_text('{}')
    path.chmod(0o644)
    with pytest.raises(ValueError):
        core.read_attempt(path)


def attempt(core, tmp_path, original=True):
    normal = tmp_path / 'normal'
    generation = tmp_path / 'attempt-0001'
    generation.mkdir(mode=0o700)
    candidate = generation / 'candidate/nvim'
    candidate.mkdir(mode=0o700, parents=True)
    (candidate / 'new').write_bytes(b'verified')
    if original:
        normal.mkdir(mode=0o700)
        (normal / 'old').write_bytes(b'untouched')
    record = dict(version=2, state='promoting', owner_sha256=core.OWNER_SHA256, lock_sha256='a' * 64,
                  normal=core.inventory(normal), candidate=core.inventory(candidate), generated_tags={})
    core.write_attempt(generation, record)
    return normal, generation, record


@pytest.mark.parametrize('original,layout', [(True, 'before'), (True, 'archived'),
    (True, 'selected'), (False, 'before'), (False, 'selected')])
def test_promotion_recovers_only_exact_layouts(tmp_path, original, layout):
    core = editor_module()
    normal, generation, record = attempt(core, tmp_path, original)
    if layout in {'archived', 'selected'} and original:
        normal.rename(generation / 'previous')
    if layout == 'selected':
        (generation / 'candidate/nvim').rename(normal)
    core.promote(generation, record, normal, lambda: None)
    assert core.inventory(normal) == record['candidate']
    assert not (generation / 'candidate/nvim').exists()
    assert core.inventory(generation / 'previous') == record['normal']
    assert core.read_attempt(generation / 'record.json')['state'] == 'promoted'


@pytest.mark.parametrize('change', ['normal', 'candidate', 'archive'])
def test_promotion_never_overwrites_user_work(tmp_path, change):
    core = editor_module()
    normal, generation, record = attempt(core, tmp_path)
    root = {'normal': normal, 'candidate': generation / 'candidate/nvim',
            'archive': generation / 'previous'}[change]
    root.mkdir(exist_ok=True)
    (root / 'owner').write_bytes(b'keep')
    with pytest.raises(ValueError):
        core.promote(generation, record, normal, lambda: None)
    assert (root / 'owner').read_bytes() == b'keep'
    assert (normal / 'old').read_bytes() == b'untouched'


def test_setup_lock_excludes_another_installer(tmp_path):
    core = editor_module()
    state = tmp_path / 'state'
    with core.setup_lock(state):
        with pytest.raises(ValueError):
            with core.setup_lock(state):
                pytest.fail('lock must exclude the second installer')


@pytest.fixture
def installation(tmp_path, monkeypatch):
    """Real isolated Git trees; only native editor/compiler behavior is mocked."""
    core = editor_module()
    home = tmp_path / 'home'
    home.mkdir(mode=0o700)
    source = tmp_path / 'source'
    source.mkdir()
    git_env = dict(os.environ, HOME=str(home), GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
    def git(*args):
        return subprocess.check_output(['git', *map(str, args)], env=git_env, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    git('init', '-q', source)
    (source / 'doc').mkdir()
    (source / 'doc/help.txt').write_bytes(b'fixture help')
    git('-C', source, 'add', '.')
    git('-C', source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
    sha = git('-C', source, 'rev-parse', 'HEAD')
    config = home / '.config/nvim'
    config.mkdir(parents=True)
    pins = {name: dict(commit=sha, branch='main') for name in ('lazy.nvim', 'fixture.nvim')}
    lock = config / 'lazy-lock.json'
    lock.write_text(json.dumps(pins))
    (config / 'init.lua').write_text('-- fixture')
    script = home / '.config/remote-workspace/restore-nvim.lua'
    script.parent.mkdir()
    script.write_text('-- fixture')
    monkeypatch.setattr(core, 'OWNER_SHA256', core.owner_digest(config, script))
    state = home / '.local/state/remote-workspace'
    normal = home / '.local/share/nvim/lazy'
    calls = []
    control = {'failure': None}
    def clone(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        git('clone', '-q', '--no-hardlinks', source, path)
    monkeypatch.setattr(core, 'bootstrap', lambda lazy, *args: clone(lazy))
    original_run = core.run
    def run(*args, env, **kwargs):
        if args[0] != str(home / '.local/bin/nvim'):
            return original_run(*args, env=env, **kwargs)
        candidate = env.get('REMOTE_WORKSPACE_LAZY_ROOT')
        root = core.Path(candidate) if candidate else normal
        stage = 'restore' if '-l' in args else 'second' if candidate else 'normal'
        calls.append((stage, root, dict(env)))
        assert not (state / 'editor-ready.json').exists() or stage in {'restore', 'normal'}
        if stage == 'restore':
            for name in pins:
                if not (root / name).exists():
                    clone(root / name)
            (root / 'fixture.nvim/doc/tags').write_bytes(b'generated tags')
            parser = root.parent / 'site/parser'
            parser.mkdir(parents=True)
            for name in (*core.PARSERS, 'markdown_inline'):
                (parser / (name + '.so')).write_bytes(b'model, not a parser')
        failure = control['failure']
        if failure == stage or failure in {'tags', 'parser'} and stage == 'restore':
            control['failure'] = None
            raise core.EditorSetupFailure(1, 'remote editor stage parser-build')
        if failure == 'abrupt':
            raise RuntimeError('synthetic abrupt death')
        callback = control.get('callback')
        if callback:
            callback(stage)
        return core.PROOF
    monkeypatch.setattr(core, 'run', run)
    monkeypatch.setattr(core.shutil, 'which', lambda *args, **kw: '/synthetic/tool')
    def apply():
        with core.setup_lock(state) as guard:
            core.setup(home, guard)
    return core, home, state, normal, lock, calls, control, apply, git, source


@pytest.mark.parametrize('failure', ['tags', 'parser', 'second'])
def test_future_failure_is_sealed_and_retry_uses_fresh_generation(installation, failure):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    # An existing clean root must remain byte/object-identical until promotion.
    normal.mkdir(parents=True)
    git('clone', '-q', '--no-hardlinks', source, normal / 'fixture.nvim')
    original = core.inventory(normal)
    control['failure'] = failure
    with pytest.raises(core.EditorSetupFailure):
        apply()
    generation = state / 'editor-attempts/attempt-0001'
    saved = core.read_attempt(generation / 'record.json')
    assert saved['state'] == 'failed_sealed'
    failed = core.inventory(generation / 'candidate')
    assert core.inventory(normal) == original
    assert not (state / 'editor-ready.json').exists()
    apply()
    assert core.inventory(generation / 'candidate') == failed
    assert core.inventory(state / 'editor-attempts/attempt-0002/previous/lazy') == original
    assert (state / 'editor-ready.json').exists()
    assert calls[-1][0] == 'normal' and 'REMOTE_WORKSPACE_LAZY_ROOT' not in calls[-1][2]
    roots = {root for stage, root, env in calls if stage == 'restore'}
    assert len(roots) == 2 and normal not in roots
    before = core.inventory(normal)
    apply()
    assert core.inventory(normal) == before
    assert len(list((state / 'editor-attempts').iterdir())) == 2


@pytest.mark.parametrize('change', ['edit', 'delete', 'extra', 'lock', 'normal'])
def test_post_seal_tampering_refuses_before_native(installation, change):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    control['failure'] = 'parser'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    candidate = state / 'editor-attempts/attempt-0001/candidate/nvim/lazy'
    tags = candidate / 'fixture.nvim/doc/tags'
    if change == 'edit':
        tags.write_bytes(b'owner edit')
    elif change == 'delete':
        tags.unlink()
    elif change == 'extra':
        (candidate / 'owner').write_bytes(b'keep')
    elif change == 'lock':
        lock.write_bytes(lock.read_bytes() + b'\n')
    else:
        normal.mkdir(parents=True)
        (normal / 'owner').write_bytes(b'keep')
    before = core.inventory(candidate)
    count = len(calls)
    with pytest.raises(ValueError):
        apply()
    assert len(calls) == count
    assert core.inventory(candidate) == before
    assert not (state / 'editor-ready.json').exists()


def test_abrupt_running_attempt_is_not_guessed_or_sealed(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    control['failure'] = 'abrupt'
    with pytest.raises(RuntimeError):
        apply()
    record = state / 'editor-attempts/attempt-0001/record.json'
    assert core.read_attempt(record)['state'] == 'running'
    count = len(calls)
    with pytest.raises(ValueError):
        apply()
    assert len(calls) == count


def test_failed_final_normal_startup_resumes_only_exact_withdrawn_state(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    control['failure'] = 'normal'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    record = state / 'editor-attempts/attempt-0001/record.json'
    assert core.read_attempt(record)['state'] == 'withdrawn'
    assert not normal.parent.exists()
    assert not (state / 'editor-ready.json').exists()
    apply()
    assert [stage for stage, root, env in calls] == ['restore', 'second', 'normal', 'normal']
    assert (state / 'editor-ready.json').exists()


def test_genuine_deletion_in_promisor_clone_never_authorizes_repair(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    normal.mkdir(parents=True)
    plugin = normal / 'fixture.nvim'
    git('-c', 'protocol.file.allow=always', 'clone', '-q', '--filter=blob:none', source.as_uri(), plugin)
    sha = git('-C', plugin, 'rev-parse', 'HEAD')
    assert git('-C', plugin, 'config', 'remote.origin.promisor') == 'true'
    assert git('-C', plugin, 'diff', '--cached', '--name-only', sha) == ''
    reflog = git('-C', plugin, 'reflog', '--format=%gs')
    assert len(reflog.splitlines()) == 1 and reflog.startswith('clone:')
    (plugin / 'doc/help.txt').unlink()  # Actual user action, not interrupted checkout.
    before = core.inventory(normal)
    with pytest.raises(ValueError, match='plugin contains local work'):
        apply()
    assert not calls
    assert core.inventory(normal) == before
    assert not (plugin / 'doc/help.txt').exists()


@pytest.mark.parametrize('change', ['symlink', 'hardlink', 'mode', 'duplicate', 'schema', 'size'])
def test_unsafe_sealed_journal_refuses_without_native(installation, change):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    control['failure'] = 'parser'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    path = state / 'editor-attempts/attempt-0001/record.json'
    if change == 'symlink':
        path.rename(home / 'retained-record')
        path.symlink_to(home / 'retained-record')
    elif change == 'hardlink':
        os.link(path, home / 'retained-record')
    elif change == 'mode':
        path.chmod(0o644)
    elif change == 'duplicate':
        path.write_bytes(b'{"version":1,"version":1}')
    elif change == 'schema':
        record = core.read_attempt(path)
        record['arbitrary_path'] = '/not-allowed'
        path.write_text(json.dumps(record))
    else:
        path.write_bytes(b' ' * (core.MAX_MANIFEST_BYTES + 1))
    count = len(calls)
    with pytest.raises((OSError, ValueError)):
        apply()
    assert len(calls) == count
    assert not (state / 'editor-ready.json').exists()


def test_changed_normal_before_promotion_stays_untouched(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    def edit(stage):
        if stage == 'second':
            normal.mkdir(parents=True)
            (normal / 'owner').write_bytes(b'concurrent work')
    control['callback'] = edit
    with pytest.raises(ValueError):
        apply()
    assert (normal / 'owner').read_bytes() == b'concurrent work'
    assert (state / 'editor-attempts/attempt-0001/candidate').is_dir()
    assert not (state / 'editor-ready.json').exists()


def test_withdrawn_user_edit_is_not_blessed_on_resume(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    control['failure'] = 'normal'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    file = state / 'editor-attempts/attempt-0001/candidate/nvim/lazy/fixture.nvim/doc/help.txt'
    file.write_bytes(b'owner edit after failure')
    count = len(calls)
    with pytest.raises(ValueError):
        apply()
    assert len(calls) == count
    assert file.read_bytes() == b'owner edit after failure'
    assert not (state / 'editor-ready.json').exists()


def test_retention_exhaustion_never_removes_failed_tree(installation, monkeypatch):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    control['failure'] = 'parser'
    with pytest.raises(core.EditorSetupFailure):
        apply()
    candidate = state / 'editor-attempts/attempt-0001/candidate'
    before = core.inventory(candidate)
    monkeypatch.setattr(core, 'MAX_ATTEMPTS', 1)
    count = len(calls)
    with pytest.raises(ValueError):
        apply()
    assert len(calls) == count and core.inventory(candidate) == before


def test_promotion_rechecks_after_guard_before_rename(tmp_path):
    core = editor_module()
    normal, generation, record = attempt(core, tmp_path)
    calls = 0
    def guard():
        nonlocal calls
        calls += 1
        if calls == 2:
            (normal / 'owner').write_bytes(b'concurrent work')
    with pytest.raises(ValueError):
        core.promote(generation, record, normal, guard)
    assert (normal / 'owner').read_bytes() == b'concurrent work'
    assert not (generation / 'previous').exists()


def test_rechecks_source_after_inventorying_other_large_roots(tmp_path, monkeypatch):
    core = editor_module()
    normal, generation, record = attempt(core, tmp_path)
    inventory = core.inventory
    def interleave(path, **kwargs):
        result = inventory(path, **kwargs)
        if path == generation / 'candidate/nvim' and normal.exists():
            (normal / 'old').write_bytes(b'changed during candidate inventory')
        return result
    monkeypatch.setattr(core, 'inventory', interleave)
    with pytest.raises(ValueError):
        core.promote(generation, record, normal, lambda: None)
    assert (normal / 'old').read_bytes() == b'changed during candidate inventory'
    assert not (generation / 'previous').exists()


def test_rename_does_not_replace_an_empty_directory_that_appeared(tmp_path):
    core = editor_module()
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'work').write_bytes(b'keep')
    destination = tmp_path / 'owner directory'
    destination.mkdir()
    original = core.inventory(destination)
    with pytest.raises(FileExistsError):
        core.move_no_replace(source, destination)
    assert core.inventory(destination) == original
    assert (source / 'work').read_bytes() == b'keep'


def test_cross_device_promotion_refuses_without_copy(tmp_path, monkeypatch):
    core = editor_module()
    normal, generation, record = attempt(core, tmp_path)
    original_stat = core.Path.stat
    def changed_device(path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if path == normal.parent:
            from types import SimpleNamespace
            return SimpleNamespace(st_dev=result.st_dev + 1)
        return result
    monkeypatch.setattr(core.Path, 'stat', changed_device)
    with pytest.raises(ValueError):
        core.promote(generation, record, normal, lambda: None)
    assert (normal / 'old').read_bytes() == b'untouched'
    assert (generation / 'candidate/nvim/new').read_bytes() == b'verified'


def test_native_group_cleanup_is_required_before_failure_is_classified(tmp_path, monkeypatch):
    core = editor_module()
    signals = []
    group = {'alive': True}
    class Process:
        pid = 12345
        def wait(self, timeout=None):
            return 1
        def poll(self):
            return 1
    def popen(*args, **kwargs):
        assert kwargs['start_new_session'] and kwargs['close_fds']
        return Process()
    def killpg(pid, sig):
        assert pid == Process.pid
        if not group['alive']:
            raise ProcessLookupError
        if sig:
            signals.append(sig)
            group['alive'] = False
    monkeypatch.setattr(core.subprocess, 'Popen', popen)
    monkeypatch.setattr(core.os, 'killpg', killpg)
    with pytest.raises(core.EditorSetupFailure):
        core.run('synthetic-editor', env={'HOME': str(tmp_path)})
    assert signals == [core.signal.SIGTERM] and not group['alive']
    def unknown_group(pid, sig):
        raise PermissionError
    monkeypatch.setattr(core.os, 'killpg', unknown_group)
    with pytest.raises(PermissionError):
        core.run('synthetic-editor', env={'HOME': str(tmp_path)})


def test_helper_controlled_root_selection_does_not_change_default_config():
    root = __import__('pathlib').Path(__file__).parents[1]
    restore = (root / 'private_dot_config/remote-workspace/restore-nvim.lua').read_text()
    lazy = (root / 'private_dot_config/nvim/lua/lazy_setup.lua').read_text()
    assert restore.index('root == vim.env.REMOTE_WORKSPACE_LAZY_ROOT') < restore.index('dofile(config')
    assert 'root = vim.g.' not in lazy
    assert lazy.index('vim.opt.loadplugins = false') < lazy.index('require("lazy").setup')
    assert 'record.state == "accepted"' in lazy


@pytest.mark.parametrize('boundary', ['verified', 'promoting', 'archived', 'selected'])
def test_apply_recovers_each_durable_promotion_boundary(installation, monkeypatch, boundary):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    normal.mkdir(parents=True)
    git('clone', '-q', '--no-hardlinks', source, normal / 'fixture.nvim')
    before = core.inventory(normal)
    original_write = core.write_attempt
    original_rename = core.move_no_replace
    def write(generation, record):
        original_write(generation, record)
        if record['state'] == boundary:
            raise RuntimeError('synthetic crash after durable journal')
    def rename(path, destination):
        result = original_rename(path, destination)
        if (boundary == 'archived' and path == normal.parent
                or boundary == 'selected' and path.parent.name == 'candidate'):
            raise RuntimeError('synthetic crash after rename')
        return result
    with monkeypatch.context() as fault:
        fault.setattr(core, 'write_attempt', write)
        fault.setattr(core, 'move_no_replace', rename)
        with pytest.raises(RuntimeError):
            apply()
    assert not (state / 'editor-ready.json').exists()
    count = len(calls)
    apply()
    assert [stage for stage, root, env in calls[count:]] == ['normal']
    assert core.inventory(state / 'editor-attempts/attempt-0001/previous/lazy') == before
    assert (state / 'editor-ready.json').exists()


def test_external_root_environment_cannot_select_normal_preparation(installation, monkeypatch):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    monkeypatch.setenv('REMOTE_WORKSPACE_LAZY_ROOT', str(normal))
    monkeypatch.setenv('LAZY', str(normal / 'lazy.nvim'))
    apply()
    assert calls[0][1] != normal
    assert 'REMOTE_WORKSPACE_LAZY_ROOT' not in calls[-1][2]


def test_ready_reapply_does_not_recreate_a_user_removed_plugin(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    apply()
    plugin = normal / 'lazy.nvim'
    plugin.rename(home / 'retained-owner-plugin')
    count = len(calls)
    with pytest.raises(ValueError):
        apply()
    assert len(calls) == count and not plugin.exists()
    assert (home / 'retained-owner-plugin/doc/help.txt').read_bytes() == b'fixture help'


def test_unknown_cleanup_failure_leaves_running_not_sealed(installation):
    core, home, state, normal, lock, calls, control, apply, git, source = installation
    def cleanup_unknown(stage):
        if stage == 'restore':
            raise PermissionError('synthetic unknown cleanup')
    control['callback'] = cleanup_unknown
    with pytest.raises(PermissionError):
        apply()
    assert core.read_attempt(state / 'editor-attempts/attempt-0001/record.json')['state'] == 'running'
    assert not (state / 'editor-ready.json').exists()


def test_owned_group_timeout_waits_for_kill_before_classified_failure(tmp_path, monkeypatch):
    core = editor_module()
    group = {'alive': True}
    signals = []
    class Process:
        pid = 54321
        def wait(self, timeout=None):
            if timeout is not None:
                raise core.subprocess.TimeoutExpired('synthetic-editor', timeout)
            return -9
        def poll(self):
            return None
    def killpg(pid, sig):
        assert pid == Process.pid
        if not group['alive']:
            raise ProcessLookupError
        if sig:
            signals.append(sig)
        if sig == core.signal.SIGKILL:
            group['alive'] = False
    clock = iter(range(100))
    monkeypatch.setattr(core.subprocess, 'Popen', lambda *args, **kwargs: Process())
    monkeypatch.setattr(core.os, 'killpg', killpg)
    monkeypatch.setattr(core.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(core.time, 'sleep', lambda seconds: None)
    with pytest.raises(core.EditorSetupFailure):
        core.run('synthetic-editor', env={'HOME': str(tmp_path)}, timeout=1)
    assert signals == [core.signal.SIGTERM, core.signal.SIGKILL]
    assert not group['alive']
