"""Private Espanso matches reach enrolled hosts through one guarded, one-way sync."""
import fcntl
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SYNC = ROOT / "dot_local/bin/executable_espanso-match-sync"
CHEZMOI = shutil.which("chezmoi")
pytestmark = pytest.mark.skipif(CHEZMOI is None, reason="chezmoi parses candidate YAML")
SECRET = "REPLACEMENT-7f3a9c"
BASE = f"matches:\n  - trigger: ':sample'\n    replace: '{SECRET}'\n"
EMPTY = "matches: []\n"
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_TERMINAL_PROMPT": "0",
}


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
        check=check, capture_output=True, text=True, env={**os.environ, **GIT_ENV},
    )


class World:
    """A private bare origin, an enrolled clone, a live config root and a public source."""

    def __init__(self, root):
        self.root = root
        self.home = root / "home"
        self.home.mkdir()
        self.config_root = self.home / ".config" / "espanso"
        self.match_dir = self.config_root / "match"
        self.state = root / "state"
        self.origin = root / "origin.git"
        self.work = root / "author"
        self.checkout = root / "dotfiles-private"
        self.source = root / "chezmoi-source"
        self.config = root / "chezmoi.toml"
        git(root, "init", "-q", "-b", "main", str(self.work))
        self.write(self.work, {"espanso/match/base.yml": BASE, "README.md": "private\n"})
        self.commit(self.work)
        git(root, "clone", "-q", "--bare", str(self.work), str(self.origin))
        git(self.work, "remote", "add", "origin", str(self.origin))
        git(root, "clone", "-q", str(self.origin), str(self.checkout))
        self.source.mkdir()
        (self.source / "dot_x").write_text("public\n")
        self.config.write_text(
            f'sourceDir = "{self.source}"\n\n[data]\n    machine_type = "omarchy-try"\n'
        )

    @staticmethod
    def write(repo, files):
        for name, text in files.items():
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    @staticmethod
    def commit(repo):
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "candidate")

    def push(self, build=None, remove=()):
        """Publish a new reviewed candidate from the authoring clone."""
        if build:
            build(self.work)
        for name in remove:
            git(self.work, "rm", "-q", "--ignore-unmatch", name)
        self.commit(self.work)
        git(self.work, "push", "-q", "origin", "main")

    def sync(self, origin=None, extra_env=None):
        env = {
            **os.environ, **GIT_ENV,
            "HOME": str(self.home),
            "CHEZMOI_EXECUTABLE": CHEZMOI,
            "CHEZMOI_SOURCE_DIR": str(self.source),
            "CHEZMOI_CONFIG_FILE": str(self.config),
            "CHEZMOI_DEST_DIR": str(self.home),
            **(extra_env or {}),
        }
        return subprocess.run(
            [sys.executable, str(SYNC), "--checkout", str(self.checkout),
             "--origin", origin or str(self.origin),
             "--config-root", str(self.config_root), "--state-dir", str(self.state)],
            capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL,
        )

    def live(self, name="base.yml"):
        return (self.match_dir / name).read_bytes()

    def put(self, name, text):
        self.match_dir.mkdir(parents=True, exist_ok=True)
        (self.match_dir / name).write_text(text)

    def snapshot(self):
        if not self.match_dir.exists():
            return {}
        return {p.name: (p.read_bytes(), p.lstat().st_mtime_ns)
                for p in self.match_dir.iterdir()}

    def head(self, repo):
        return git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def assert_no_values(result):
    output = result.stdout + result.stderr
    assert SECRET not in output and ":sample" not in output, output


def assert_refused(result, reason, *leaves):
    assert result.returncode == 1, result.stderr
    assert f"reason={reason}" in result.stderr
    for leaf in leaves:
        assert leaf in result.stderr
    assert_no_values(result)


def test_clean_fast_forward_deploys_matches_once_without_pushing(world):
    first = world.sync()
    assert first.returncode == 0, first.stderr
    assert "added=1 updated=0 removed=0 unchanged=0" in first.stdout
    assert world.live() == BASE.encode()
    assert (world.match_dir / "base.yml").stat().st_mode & 0o777 == 0o600
    state = json.loads((world.state / "state.json").read_text())
    assert state == {"revision": world.head(world.checkout), "leaves": ["base.yml"]}
    before = world.snapshot()

    repeat = world.sync()
    assert repeat.returncode == 0, repeat.stderr
    assert "added=0 updated=0 removed=0 unchanged=1" in repeat.stdout
    assert world.snapshot() == before

    world.push(lambda w: world.write(w, {"espanso/match/base.yml": BASE + "# revised\n"}))
    updated = world.sync()
    assert updated.returncode == 0, updated.stderr
    assert "added=0 updated=1 removed=0 unchanged=0" in updated.stdout
    assert world.live().endswith(b"# revised\n")
    # One-way: the sync leaves no commit, edit or untracked file in the private checkout.
    assert git(world.checkout, "status", "--porcelain").stdout == ""
    assert world.head(world.checkout) == world.head(world.origin) == world.head(world.work)


def test_unreachable_origin_preserves_last_working_matches(world):
    assert world.sync().returncode == 0
    world.push(lambda w: world.write(w, {"espanso/match/base.yml": BASE + "# later\n"}))
    missing = world.root / "missing.git"
    git(world.checkout, "remote", "set-url", "origin", str(missing))
    result = world.sync(origin=str(missing))
    assert_refused(result, "unreachable")
    assert world.live() == BASE.encode()
    assert not (world.state / "preimages").exists()


def test_unknown_origin_is_refused_before_any_change(world):
    result = world.sync(origin="https://forge.example/tis/dotfiles-private.git")
    assert_refused(result, "unknown-origin")
    assert not world.match_dir.exists()


def test_origin_identity_ignores_scheme_user_and_git_suffix(world):
    git(world.checkout, "remote", "set-url", "origin", "ssh://git@forge.example/tis/dotfiles-private.git")
    result = world.sync(
        origin="https://forge.example/tis/dotfiles-private",
        extra_env={"GIT_SSH_COMMAND": "ssh -o BatchMode=yes -o ConnectTimeout=5"},
    )
    assert_refused(result, "unreachable")


def test_dirty_tracked_checkout_is_refused(world):
    (world.checkout / "README.md").write_text("local edit\n")
    result = world.sync()
    assert_refused(result, "dirty-checkout")
    assert (world.checkout / "README.md").read_text() == "local edit\n"
    assert not world.match_dir.exists()


def test_untracked_checkout_files_do_not_block_a_clean_sync(world):
    (world.checkout / "notes.txt").write_text("untracked\n")
    assert world.sync().returncode == 0
    assert (world.checkout / "notes.txt").read_text() == "untracked\n"


def test_divergent_history_is_refused_without_merge_or_reset(world):
    world.write(world.checkout, {"README.md": "local commit\n"})
    world.commit(world.checkout)
    local_head = world.head(world.checkout)
    world.push(lambda w: world.write(w, {"README.md": "remote commit\n"}))
    result = world.sync()
    assert_refused(result, "diverged")
    assert world.head(world.checkout) == local_head
    assert not world.match_dir.exists()


def test_detached_head_and_missing_upstream_are_refused(world):
    git(world.checkout, "checkout", "-q", "--detach", "HEAD")
    assert_refused(world.sync(), "detached-head")
    git(world.checkout, "checkout", "-q", "main")
    git(world.checkout, "branch", "--unset-upstream")
    assert_refused(world.sync(), "no-upstream")
    assert not world.match_dir.exists()


def test_interrupted_operation_and_missing_checkout_are_refused(world, tmp_path):
    marker = world.checkout / ".git" / "MERGE_HEAD"
    marker.write_text("0" * 40 + "\n")
    assert_refused(world.sync(), "in-progress-operation")
    marker.unlink()
    empty = tmp_path / "not-a-repository"
    empty.mkdir()
    result = subprocess.run(
        [sys.executable, str(SYNC), "--checkout", str(empty), "--origin", str(world.origin),
         "--config-root", str(world.config_root), "--state-dir", str(world.state)],
        capture_output=True, text=True,
        env={**os.environ, **GIT_ENV, "HOME": str(world.home), "CHEZMOI_EXECUTABLE": CHEZMOI},
    )
    assert_refused(result, "checkout-unavailable")
    assert not world.match_dir.exists()


def test_local_edit_of_a_deployed_leaf_blocks_the_whole_plan(world):
    world.push(lambda w: world.write(w, {"espanso/match/other.yml": EMPTY}))
    assert world.sync().returncode == 0
    world.put("base.yml", EMPTY + "# mine\n")
    edited = world.live()
    world.push(lambda w: world.write(w, {"espanso/match/other.yml": EMPTY + "# new\n"}))
    result = world.sync()
    assert_refused(result, "local-edit", "base.yml")
    assert world.live() == edited
    assert world.live("other.yml") == EMPTY.encode()


def test_unowned_live_leaf_is_never_replaced(world):
    world.put("base.yml", EMPTY + "# local\n")
    assert_refused(world.sync(), "unowned-collision", "base.yml")
    assert world.live() == (EMPTY + "# local\n").encode()


def test_unowned_leaf_with_identical_content_is_adopted_without_rewrite(world):
    world.put("base.yml", BASE)
    before = world.snapshot()
    adopted = world.sync()
    assert adopted.returncode == 0, adopted.stderr
    assert "added=0 updated=0 removed=0 unchanged=1" in adopted.stdout
    assert world.snapshot() == before
    world.push(lambda w: world.write(w, {"espanso/match/base.yml": BASE + "# v2\n"}))
    assert world.sync().returncode == 0
    assert world.live().endswith(b"# v2\n")


def test_unrelated_local_matches_and_symlinks_are_left_alone(world):
    world.put("mine.yml", EMPTY)
    outside = world.root / "outside.yml"
    outside.write_text(EMPTY)
    world.match_dir.joinpath("link.yml").symlink_to(outside)
    assert world.sync().returncode == 0
    assert world.live("mine.yml") == EMPTY.encode()
    assert (world.match_dir / "link.yml").is_symlink()
    assert outside.read_text() == EMPTY


def test_incoming_name_that_is_a_live_symlink_is_refused(world):
    world.match_dir.mkdir(parents=True)
    target = world.root / "target.yml"
    world.match_dir.joinpath("base.yml").symlink_to(target)
    assert_refused(world.sync(), "non-regular-live-file", "base.yml")
    assert (world.match_dir / "base.yml").is_symlink()
    assert not target.exists()


def test_replaced_leaf_keeps_a_restricted_preimage(world):
    assert world.sync().returncode == 0
    world.push(lambda w: world.write(w, {"espanso/match/base.yml": BASE + "# v2\n"}))
    assert world.sync().returncode == 0
    preimage, = (world.state / "preimages").glob("*/base.yml")
    assert preimage.read_bytes() == BASE.encode()
    assert preimage.stat().st_mode & 0o777 == 0o600
    assert world.state.stat().st_mode & 0o777 == 0o700


def test_upstream_removal_deletes_only_an_unchanged_deployed_leaf(world):
    world.push(lambda w: world.write(w, {"espanso/match/gone.yml": EMPTY}))
    assert world.sync().returncode == 0
    world.push(remove=["espanso/match/gone.yml"])
    removed = world.sync()
    assert removed.returncode == 0, removed.stderr
    assert "removed=1" in removed.stdout
    assert not (world.match_dir / "gone.yml").exists()
    preimage, = (world.state / "preimages").glob("*/gone.yml")
    assert preimage.read_bytes() == EMPTY.encode()


def test_upstream_removal_of_an_edited_leaf_is_a_conflict(world):
    world.push(lambda w: world.write(w, {"espanso/match/gone.yml": EMPTY}))
    assert world.sync().returncode == 0
    world.put("gone.yml", EMPTY + "# keep\n")
    world.push(remove=["espanso/match/gone.yml"])
    result = world.sync()
    assert_refused(result, "local-edit", "gone.yml")
    assert world.live("gone.yml") == (EMPTY + "# keep\n").encode()


def test_invalid_yaml_refuses_the_whole_sync_without_quoting_content(world):
    assert world.sync().returncode == 0
    world.push(lambda w: world.write(w, {
        "espanso/match/base.yml": BASE + "# harmless\n",
        "espanso/match/broken.yml": f"matches:\n  - trigger: ':broken'\n    replace: '{SECRET}\n",
    }))
    result = world.sync()
    assert_refused(result, "invalid-yaml", "broken.yml")
    assert world.live() == BASE.encode()
    assert not (world.match_dir / "broken.yml").exists()


def test_non_mapping_yaml_is_refused(world):
    world.push(lambda w: world.write(w, {"espanso/match/list.yml": "- just\n- a list\n"}))
    assert_refused(world.sync(), "invalid-yaml", "list.yml")


def test_template_syntax_and_empty_documents_are_judged_only_as_yaml(world):
    world.push(lambda w: world.write(w, {
        "espanso/match/curly.yml": "matches: []\n# {{ not a template }}\n",
        "espanso/match/blank.yml": "",
    }))
    result = world.sync()
    assert result.returncode == 0, result.stderr
    assert world.live("curly.yml") == b"matches: []\n# {{ not a template }}\n"
    assert world.live("blank.yml") == b""


def _script(work):
    (work / "espanso/match/evil.sh").write_text("#!/bin/sh\n")


def _nested(work):
    World.write(work, {"espanso/match/nested/x.yml": EMPTY})


def _symlink(work):
    (work / "espanso/match/link.yml").symlink_to("/etc/hostname")


def _executable(work):
    World.write(work, {"espanso/match/exec.yml": EMPTY})
    (work / "espanso/match/exec.yml").chmod(0o755)


def _hidden(work):
    World.write(work, {"espanso/match/.hidden.yml": EMPTY})


def _missing_tree(work):
    git(work, "rm", "-q", "-r", "espanso/match")


@pytest.mark.parametrize("build", [_script, _nested, _symlink, _executable, _hidden, _missing_tree])
def test_out_of_scope_private_entries_fail_the_whole_sync(world, build):
    world.push(build)
    assert_refused(world.sync(), "invalid-scope")
    assert not world.match_dir.exists()


def test_oversized_candidate_is_refused(world):
    world.push(lambda w: world.write(w, {"espanso/match/big.yml": EMPTY + "#" + "x" * (1024 * 1024) + "\n"}))
    assert_refused(world.sync(), "invalid-scope", "big.yml")


def test_private_paths_outside_the_match_tree_are_never_deployed(world):
    world.push(lambda w: World.write(w, {
        "espanso/config/default.yml": "toggle_key: OFF\n",
        "espanso/run-after.sh": "#!/bin/sh\n",
        "espanso/match.yaml": "matches: []\n",
    }))
    result = world.sync()
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in world.match_dir.iterdir()) == ["base.yml"]
    assert sorted(p.name for p in world.config_root.iterdir()) == ["match"]


def test_public_ownership_of_a_match_leaf_is_refused(world):
    World.write(world.source, {"private_dot_config/espanso/match/base.yml": EMPTY})
    assert_refused(world.sync(), "public-overlap")
    assert not world.match_dir.exists()


def test_missing_chezmoi_is_a_reported_gap(world):
    result = world.sync(extra_env={"CHEZMOI_EXECUTABLE": str(world.root / "missing-chezmoi")})
    assert_refused(result, "chezmoi-unavailable")
    assert not world.match_dir.exists()


def test_a_match_path_that_is_not_a_directory_is_refused(world):
    world.config_root.mkdir(parents=True)
    world.config_root.joinpath("match").write_text("not a directory\n")
    result = world.sync()
    assert_refused(result, "non-regular-live-file", "match")
    assert world.config_root.joinpath("match").read_text() == "not a directory\n"


def test_an_enclosing_git_context_cannot_retarget_the_checkout(world, tmp_path):
    foreign = world.sync(extra_env={
        "GIT_DIR": str(world.origin), "GIT_WORK_TREE": str(tmp_path),
        "GIT_INDEX_FILE": str(tmp_path / "foreign-index"),
    })
    assert foreign.returncode == 0, foreign.stderr
    assert world.live() == BASE.encode()
    assert world.head(world.origin) == world.head(world.work)


def test_concurrent_sync_is_refused(world):
    world.state.mkdir(parents=True)
    with (world.state / "lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            result = world.sync()
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    assert_refused(result, "busy")
    assert not world.match_dir.exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_unwritable_match_directory_fails_without_partial_replacement(world):
    assert world.sync().returncode == 0
    world.push(lambda w: world.write(w, {"espanso/match/base.yml": BASE + "# v2\n",
                                         "espanso/match/other.yml": EMPTY}))
    world.match_dir.chmod(0o500)
    try:
        result = world.sync()
    finally:
        world.match_dir.chmod(0o700)
    assert_refused(result, "write-failed")
    assert world.live() == BASE.encode()
    assert not (world.match_dir / "other.yml").exists()


def load_sync():
    loader = importlib.machinery.SourceFileLoader("espanso_match_sync", str(SYNC))
    module = importlib.util.spec_from_loader(loader.name, loader)
    loaded = importlib.util.module_from_spec(module)
    loader.exec_module(loaded)
    return loaded


def test_partial_write_failure_restores_every_preimage(tmp_path, monkeypatch):
    module = load_sync()
    match_dir, state = tmp_path / "match", tmp_path / "state"
    match_dir.mkdir()
    state.mkdir()
    for name, content in {"a.yml": b"old a\n", "b.yml": b"old b\n", "mine.yml": b"local\n"}.items():
        (match_dir / name).write_bytes(content)
    real_replace, replaced = os.replace, []

    def flaky_replace(source, target):
        replaced.append(Path(target).name)
        if len(replaced) == 2:
            raise OSError("simulated failure")
        real_replace(source, target)

    monkeypatch.setattr(module.os, "replace", flaky_replace)
    with pytest.raises(module.Refused) as refused:
        module.apply_plan(match_dir, {"a.yml": b"new a\n", "c.yml": b"new c\n"}, ["b.yml"], state)
    assert refused.value.reason == "write-failed"
    # Replaced and removed leaves return, the added leaf disappears, nothing staged is left behind.
    assert sorted(p.name for p in match_dir.iterdir()) == ["a.yml", "b.yml", "mine.yml"]
    assert (match_dir / "a.yml").read_bytes() == b"old a\n"
    assert (match_dir / "b.yml").read_bytes() == b"old b\n"
    preimage, = (state / "preimages").iterdir()
    assert sorted(p.name for p in preimage.iterdir()) == ["a.yml", "b.yml"]
