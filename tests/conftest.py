"""Protect source before collection and keep generated artifacts test-local."""

import json
import os
import subprocess
import sys

import pytest

from tests.support.imports import REPO_ROOT, TESTS_DIR, server_imports
from tests.support.isolation import content_manifest, manifest_changes


_MANIFEST = pytest.StashKey[dict]()
_GIT_DIFF = pytest.StashKey[bytes]()


def protected_git_diff():
    return subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--", "server", "browser", "scenarios"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout


def pytest_configure(config):
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(TESTS_DIR / ".cache/ms-playwright")
    os.environ["COVERAGE_FILE"] = str(TESTS_DIR / ".artifacts/.coverage")
    (TESTS_DIR / ".artifacts").mkdir(exist_ok=True)
    runtime_temp = TESTS_DIR / ".tmp/runtime"
    runtime_temp.mkdir(parents=True, exist_ok=True)
    for name in ("TMP", "TEMP", "TMPDIR"):
        os.environ[name] = str(runtime_temp)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    session.config.stash[_MANIFEST] = content_manifest(REPO_ROOT)
    session.config.stash[_GIT_DIFF] = protected_git_diff()


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    try:
        return (yield)
    finally:
        check_protected_paths(session)


def check_protected_paths(session):
    before = session.config.stash[_MANIFEST]
    after = content_manifest(REPO_ROOT)
    changes = manifest_changes(before, after)
    diff_changed = session.config.stash[_GIT_DIFF] != protected_git_diff()
    report = {"files_checked": len(before), "changes": changes,
              "git_diff_changed": diff_changed}
    (TESTS_DIR / ".artifacts/protected-paths.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8",
    )
    if any(changes.values()) or diff_changed:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_sep("!", "Protected paths changed; no files reverted")
            reporter.write_line(json.dumps(report, indent=2))


@pytest.fixture
def engine_imports():
    with server_imports():
        yield


@pytest.fixture
def http_base_url():
    from tests.support.http_server import serve_test_files

    with serve_test_files() as url:
        yield url
