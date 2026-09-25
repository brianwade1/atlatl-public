"""S01 safety/isolation checks; these are not engine behavior coverage."""

import json
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from tests.support.imports import (
    SERVER_DIR, explicit_module, import_server, server_imports,
)
from tests.support.process_helpers import run_python


pytestmark = pytest.mark.core


@pytest.mark.unit
@pytest.mark.parametrize("change", ["added", "changed", "removed"])
def test_protected_manifest_fails_session_without_reverting(tmp_path, monkeypatch, change):
    # Exercise the real hooks against a disposable tree, never the source tree.
    from tests import conftest as hooks

    (tmp_path / "server").mkdir()
    source = tmp_path / "server/existing.py"
    source.write_text("original", encoding="utf-8")
    (tmp_path / "tests/.artifacts").mkdir(parents=True)
    monkeypatch.setattr(hooks, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(hooks, "TESTS_DIR", tmp_path / "tests")
    monkeypatch.setattr(hooks, "protected_git_diff", lambda: b"existing user diff")
    config = SimpleNamespace(stash=pytest.Stash(), pluginmanager=SimpleNamespace(
        get_plugin=lambda name: None))
    session = SimpleNamespace(config=config, exitstatus=pytest.ExitCode.OK)
    hooks.pytest_sessionstart(session)
    target = source
    if change == "added":
        target = tmp_path / "server/untracked.pyc"
        target.write_text("new", encoding="utf-8")
    elif change == "changed":
        target.write_text("changed", encoding="utf-8")
    else:
        target.unlink()
    hooks.check_protected_paths(session)
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    report = json.loads((tmp_path / "tests/.artifacts/protected-paths.json").read_text())
    assert report["changes"][change] == [target.relative_to(tmp_path).as_posix()]
    if change == "removed":
        assert not target.exists()
    else:
        assert target.read_text() == ("new" if change == "added" else "changed")


@pytest.mark.unit
def test_flat_engine_import_checks_provenance_and_restores_state():
    old_path = sys.path[:]
    old_module = sys.modules.get("game")
    with server_imports():
        assert Path(import_server("game").__file__).resolve() == SERVER_DIR / "game.py"
    assert sys.path == old_path
    assert sys.modules.get("game") is old_module


@pytest.mark.unit
@pytest.mark.parametrize("fails", [False, True], ids=["normal", "import-error"])
def test_explicit_import_restores_colliding_module(tmp_path, monkeypatch, fails):
    source = tmp_path / "Game.py"
    source.write_text("raise RuntimeError('import failed')" if fails else "value = 42",
                      encoding="utf-8")
    original = SimpleNamespace(value="original")
    monkeypatch.setitem(sys.modules, "Game", original)
    if fails:
        with pytest.raises(RuntimeError, match="import failed"):
            with explicit_module("Game", source):
                pytest.fail("Import should fail before yielding")
    else:
        with explicit_module("Game", source) as module:
            assert module.value == 42
            assert sys.modules["Game"] is module
    assert sys.modules["Game"] is original


@pytest.mark.integration
def test_subprocess_uses_test_local_working_directory_and_no_bytecode(tmp_path):
    result = run_python(
        "import json, os, sys; from pathlib import Path; "
        "print(json.dumps([str(Path.cwd()), sys.dont_write_bytecode, "
        "os.environ['PYTHONDONTWRITEBYTECODE']]))", cwd=tmp_path,
    )
    cwd, disabled, inherited = json.loads(result.stdout)
    assert Path(cwd) == tmp_path
    assert disabled is True
    assert inherited == "1"


@pytest.mark.integration
def test_http_serves_javascript_and_limits_routes(http_base_url):
    with urlopen(f"{http_base_url}/browser/combat.js", timeout=5) as response:
        assert response.headers.get_content_type() == "text/javascript"
        assert b"export var Combat" in response.read()
    for path in ("/pyproject.toml", "/server/game.py", "/browser/../server/game.py",
                 "/browser/%2e%2e/server/game.py"):
        with pytest.raises(HTTPError) as caught:
            urlopen(http_base_url + path, timeout=5)
        assert caught.value.code == 404
        caught.value.close()
