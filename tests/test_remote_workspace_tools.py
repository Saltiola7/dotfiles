import hashlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest

ROOT = Path(__file__).parents[1]


def installer():
    path = ROOT / 'dot_local/bin/executable_remote-workspace-tools'
    loader = importlib.machinery.SourceFileLoader('remote_tools', str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def archive(member='fixture/tool', payload=b'fixture binary'):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as stream:
        item = tarfile.TarInfo(member)
        item.size = len(payload)
        item.mode = 0o755
        stream.addfile(item, io.BytesIO(payload))
    return output.getvalue()


def test_reviewed_tools_have_exact_urls_and_sha256():
    pins = json.loads((ROOT / 'private_dot_config/remote-workspace/private_tools.json').read_text())
    assert set(pins) == {'zoxide', 'direnv', 'rg', 'nvim', 'tree-sitter'}
    assert pins['nvim']['version'] == '0.12.6'
    assert pins['tree-sitter']['version'] == '0.26.1'
    for pin in pins.values():
        assert len(pin['sha256']) == 64
        assert '/releases/download/' in pin['url']
        assert '/latest/' not in pin['url']


def test_tool_generation_is_verified_and_reapply_does_not_download(tmp_path, monkeypatch):
    core = installer()
    home = tmp_path / 'home'
    home.mkdir()
    raw = archive()
    pin = {'version': '1.0', 'url': 'https://github.com/example/tool/releases/download/v1/tool.tar.gz',
           'sha256': hashlib.sha256(raw).hexdigest(), 'format': 'tar.gz', 'member': 'fixture/tool'}
    calls = []
    def fetch(url):
        calls.append(url)
        return raw
    monkeypatch.setattr(core, 'download', fetch)
    first = core.install_tool(home, 'zoxide', pin)
    assert (home / '.local/bin/zoxide').read_bytes() == b'fixture binary'
    assert core.install_tool(home, 'zoxide', pin) == first
    assert len(calls) == 1


@pytest.mark.parametrize('fault', ['checksum', 'traversal'])
def test_invalid_artifact_preserves_existing_binary(tmp_path, monkeypatch, fault):
    core = installer()
    home = tmp_path / 'home'
    binary = home / '.local/bin/zoxide'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b'retained')
    raw = archive('../escape' if fault == 'traversal' else 'fixture/tool')
    pin = {'version': '1.0', 'url': 'https://github.com/example/tool/releases/download/v1/tool.tar.gz',
           'sha256': '0' * 64 if fault == 'checksum' else hashlib.sha256(raw).hexdigest(),
           'format': 'tar.gz', 'member': 'fixture/tool'}
    monkeypatch.setattr(core, 'download', lambda _: raw)
    with pytest.raises((ValueError, tarfile.TarError)):
        core.install_tool(home, 'zoxide', pin)
    assert binary.read_bytes() == b'retained'
    assert not (home / '.local/share/remote-workspace/tools/escape').exists()


def test_successful_download_does_not_replace_unowned_owner_binary(tmp_path, monkeypatch):
    core = installer()
    home = tmp_path / 'home'
    binary = home / '.local/bin/zoxide'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b'owner-managed binary')
    raw = archive()
    pin = {'version': '1.0', 'url': 'https://github.com/example/tool/releases/download/v1/tool.tar.gz',
           'sha256': hashlib.sha256(raw).hexdigest(), 'format': 'tar.gz', 'member': 'fixture/tool'}
    monkeypatch.setattr(core, 'download', lambda _: raw)
    with pytest.raises(ValueError):
        core.install_tool(home, 'zoxide', pin)
    assert binary.read_bytes() == b'owner-managed binary'
