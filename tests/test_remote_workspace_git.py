"""F02 native Git/gh fixtures; no provider requests or real credentials.

The minimal source deliberately bypasses the primary-owned profile allowlist.
These tests do not claim full-source profile integration.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
INCLUDES = ("remote-workspace.inc", "remote-workspace-work.inc",
            "remote-workspace-personal.inc", "remote-workspace-conflict.inc")
SOURCES = ("dot_local/bin/executable_remote-workspace-git",
           "run_after_configure-remote-workspace-git.sh.tmpl", *(
               f"private_dot_config/git/private_{name}.tmpl" for name in INCLUDES))
DATA = {"machine_type": "remote-workspace", "name": "Explicit Fixture User",
        "work_email": "work@example.invalid", "personal_email": "personal@example.invalid"}


def run(env, *args, check=True, **kwargs):
    return subprocess.run(args, cwd=env["HOME"], env=env, check=check,
                          text=True, capture_output=True, timeout=30, **kwargs)


@pytest.fixture
def env(tmp_path):
    home = (tmp_path / "home").resolve()
    home.mkdir()
    return {"HOME": str(home), "PATH": os.environ["PATH"],
            "XDG_CONFIG_HOME": str(home / ".config"),
            "GH_CONFIG_DIR": str(home / ".config/gh"),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
            "GIT_CEILING_DIRECTORIES": str(home), "GIT_TERMINAL_PROMPT": "0",
            "USER": "not-the-git-identity", "EMAIL": "os-login@example.invalid",
            "GH_PROMPT_DISABLED": "1", "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9", "ALL_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": ""}


def render(env, name, data=None):
    return run(env, "chezmoi", "--config", "/dev/null", "--config-format", "toml",
               "--override-data", json.dumps(DATA if data is None else data),
               "execute-template", input=(ROOT / f"private_dot_config/git/private_{name}.tmpl").read_text(),
               check=False)


def install(env):
    directory = Path(env["HOME"]) / ".config/git"
    directory.mkdir(parents=True)
    for name in INCLUDES:
        result = render(env, name)
        assert result.returncode == 0, result.stderr
        path = directory / name
        path.write_text(result.stdout)
        path.chmod(0o600)


def update(env, check=True):
    return run(env, sys.executable, str(ROOT / SOURCES[0]), check=check)


@pytest.mark.parametrize("key", ["name", "work_email", "personal_email"])
@pytest.mark.parametrize("value", [None, "", " \t "])
def test_identity_requires_explicit_nonblank_inputs(env, key, value):
    data = DATA | {"email": "must-not-be-a-fallback@example.invalid"}
    if value is None:
        data.pop(key)
    else:
        data[key] = value
    assert render(env, INCLUDES[0], data).returncode != 0


@pytest.mark.parametrize("remotes,expected", [
    (["https://github.com/mgmri-dge/repo.git"], "work"),
    (["git@github.com:Superformula/repo.git"], "work"),
    (["https://github.com/Superformula/repo.git"], "work"),
    (["https://github.com/superformula/repo.git"], "work"),
    (["git@github.com:superformula/repo.git"], "work"),
    (["ssh://git@github.com/Superformula/repo.git"], "work"),
    (["git@github.com:mgmri-dge/repo.git"], "work"),
    (["ssh://git@github.com/superformula/repo.git"], "work"),
    (["ssh://git@github.com:22/mgmri-dge/repo.git"], "work"),
    (["https://github.com/Saltiola7/repo.git"], "personal"),
    (["git@github.com:Saltiola7/repo.git"], "personal"),
    (["ssh://git@github.com/Saltiola7/repo.git"], "personal"),
    (["ssh://git@github.com:22/Saltiola7/repo.git"], "personal"),
    (["https://github.com/saltiola7/repo.git"], "personal"),
    (["https://github.com/unknown/repo.git"], None),
    (["https://github.com/Saltiola7-impostor/repo.git"], None),
    (["https://github.com.evil.invalid/Saltiola7/repo.git"], None),
    ([], None),
    (["git@github.com:mgmri-dge/a", "https://github.com/Superformula/b"], "work"),
    (["https://github.com/Saltiola7/a", "git@github.com:mgmri-dge/b"], None),
    (["ssh://git@github.com/superformula/a", "git@github.com:Saltiola7/b"], None),
    (["https://github.com/mgmri-dge/a", "https://github.com/Saltiola7/b"], None),
    (["git@github.com:Saltiola7/a", "git@github.com:Superformula/b"], None),
])
def test_native_remote_routing_and_conflict_rejection(env, remotes, expected):
    config = Path(env["GIT_CONFIG_GLOBAL"])
    config.write_text("[user]\n name = Legacy Name\n email = legacy@example.invalid\n")
    install(env)
    update(env)
    repo = Path(env["HOME"]) / "repo"
    run(env, "git", "init", "-q", str(repo))
    for index, url in enumerate(remotes):
        run(env, "git", "-C", str(repo), "remote", "add", f"remote{index}", url)
    for variable in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        identity = run(env, "git", "-C", str(repo), "var", variable, check=False)
        if expected:
            assert identity.returncode == 0, identity.stderr
            assert f'{DATA["name"]} <{DATA[expected + "_email"]}>' in identity.stdout
        else:
            assert identity.returncode != 0
    if expected is None:
        for key in ("name", "email"):
            assert run(env, "git", "-C", str(repo), "config", "--get", f"user.{key}").stdout == "\n"
    assert run(env, "git", "-C", str(repo), "config", "--get", "user.useConfigOnly").stdout.strip() == "true"


def test_routing_reacts_to_remote_changes_without_reapply(env):
    install(env)
    update(env)
    run(env, "git", "init", "-q")
    run(env, "git", "remote", "add", "origin", "git@github.com:Saltiola7/project")
    assert run(env, "git", "config", "--get", "user.email").stdout.strip() == DATA["personal_email"]
    run(env, "git", "remote", "set-url", "origin", "https://github.com/mgmri-dge/project")
    assert run(env, "git", "config", "--get", "user.email").stdout.strip() == DATA["work_email"]
    run(env, "git", "remote", "add", "fork", "git@github.com:Saltiola7/project")
    assert run(env, "git", "var", "GIT_AUTHOR_IDENT", check=False).returncode != 0
    run(env, "git", "remote", "remove", "fork")
    assert run(env, "git", "config", "--get", "user.email").stdout.strip() == DATA["work_email"]
    run(env, "git", "remote", "remove", "origin")
    assert run(env, "git", "var", "GIT_AUTHOR_IDENT", check=False).returncode != 0


@pytest.mark.parametrize("unsafe", ["symlink", "writable"])
def test_unsafe_include_directory_is_preserved(env, unsafe):
    install(env)
    directory = Path(env["HOME"]) / ".config/git"
    if unsafe == "symlink":
        retained = directory.with_name("retained")
        directory.rename(retained)
        directory.symlink_to(retained, target_is_directory=True)
    else:
        directory.chmod(0o777)
    before = (directory / INCLUDES[0]).read_bytes()
    assert update(env, check=False).returncode != 0
    assert (directory / INCLUDES[0]).read_bytes() == before
    assert not Path(env["GIT_CONFIG_GLOBAL"]).exists()


def test_nonremote_hook_is_inert(env):
    result = run(env, "chezmoi", "--config", "/dev/null", "--config-format", "toml",
                 "--override-data", json.dumps({"machine_type": "macbook"}), "execute-template",
                 input=(ROOT / SOURCES[1]).read_text())
    # There is deliberately no helper in this isolated home.
    assert run(env, "bash", input=result.stdout).returncode == 0


@pytest.mark.parametrize("target", [".gitconfig", *[f".config/git/{name}" for name in INCLUDES]])
@pytest.mark.parametrize("unsafe", ["symlink", "hardlink", "writable", "malformed"])
def test_unsafe_files_are_preserved(env, target, unsafe):
    install(env)
    config = Path(env["GIT_CONFIG_GLOBAL"])
    config.write_text("[custom]\n preserved = yes\n")
    path = Path(env["HOME"]) / target
    if unsafe == "symlink":
        retained = Path(env["HOME"]) / "retained"
        path.rename(retained)
        path.symlink_to(retained)
    elif unsafe == "hardlink":
        os.link(path, Path(env["HOME"]) / "retained")
    elif unsafe == "writable":
        path.chmod(0o666)
    else:
        path.write_text("not valid [config\n")
    before = {p: p.read_bytes() for p in (config, path)}
    assert update(env, check=False).returncode != 0
    assert all(p.read_bytes() == contents for p, contents in before.items())


def test_native_hasconfig_includes_never_declare_remotes(env):
    install(env)
    path = Path(env["HOME"]) / ".config/git" / INCLUDES[1]
    path.write_text(path.read_text() + '[remote "injected"]\n url = https://github.com/Saltiola7/no\n')
    assert update(env, check=False).returncode != 0
    assert not Path(env["GIT_CONFIG_GLOBAL"]).exists()


def test_repeated_minimal_apply_preserves_native_gh_and_unknown_settings(env, tmp_path):
    assert shutil.which("gh"), "native gh required for F02 fixture"
    hosts = Path(env["GH_CONFIG_DIR"]) / "hosts.yml"
    hosts.parent.mkdir(parents=True)
    hosts.write_text("github.com:\n    user: fixture-owner\n    git_protocol: https\n"
                     "    oauth_token: fixture-not-a-real-token\n    users:\n"
                     "        fixture-owner:\n            oauth_token: fixture-not-a-real-token\n")
    hosts.chmod(0o600)
    config = Path(env["GIT_CONFIG_GLOBAL"])
    config.write_text('[custom "unknown"]\n preserved = yes\n[credential "https://example.invalid"]\n helper = fixture-helper\n')
    config.chmod(0o600)
    run(env, "gh", "auth", "setup-git", "--hostname", "github.com")
    original = config.read_bytes()
    helpers = run(env, "git", "config", "--global", "--get-regexp", r"^credential\.").stdout

    def credential():
        result = run(env, "git", "credential", "fill",
                     input="protocol=https\nhost=github.com\nusername=fixture-owner\n\n")
        assert "password=fixture-not-a-real-token" in result.stdout

    credential()
    source = tmp_path / "source"
    for name in SOURCES:
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    settings = tmp_path / "chezmoi.toml"
    settings.write_text("[data]\n" + "\n".join(f"{key} = {json.dumps(value)}" for key, value in DATA.items()))
    command = ("chezmoi", "-S", str(source), "-D", env["HOME"], "-c", str(settings),
               "--persistent-state", str(tmp_path / "state.boltdb"), "--no-tty", "apply")
    run(env, *command)
    first = config.read_bytes()
    assert first.startswith(original)
    run(env, *command)
    assert config.read_bytes() == first
    assert run(env, "git", "config", "--global", "--get", "custom.unknown.preserved").stdout.strip() == "yes"
    assert run(env, "git", "config", "--global", "--get-regexp", r"^credential\.").stdout == helpers
    assert run(env, "git", "config", "--global", "--get-all", "include.path").stdout.splitlines() == [str(Path(env["HOME"]) / ".config/git" / INCLUDES[0])]
    credential()
