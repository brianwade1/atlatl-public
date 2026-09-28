"""Protect source before collection and keep generated artifacts test-local."""

import json
import os
import subprocess
import sys

import pytest
from pytest_playwright import pytest_playwright as playwright_plugin

from tests.support.imports import REPO_ROOT, TESTS_DIR, server_imports
from tests.support.isolation import content_manifest, manifest_changes
from tests.support import builders
from tests.support.isolation import isolated_rng, finite_random, preserve_globals


_MANIFEST = pytest.StashKey[dict]()
_GIT_DIFF = pytest.StashKey[bytes]()

# The synchronous driver's loop remains running until playwright.stop().
# Scope the plugin dependency chain per test so pytest-asyncio can run in any
# collection order. Reuse plugin bodies/options/artifact handling unchanged.
for _fixture_name in ("playwright", "browser_type", "launch_browser", "browser",
                      "browser_context_args"):
    globals()[_fixture_name] = pytest.fixture(scope="function")(
        getattr(playwright_plugin, _fixture_name).__wrapped__)


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


@pytest.fixture
def make_map():
    return builders.make_map


@pytest.fixture
def make_unit():
    return builders.make_unit


@pytest.fixture
def unit_world(engine_imports):
    """Load fresh real map/unit objects without serialization or detection draws."""
    from tests.support.imports import import_server

    def build(units=(), *, map_input=None, **map_options):
        geometry = import_server("map")
        module = import_server("unit")
        board = geometry.MapData()
        geometry.fromPortable(
            builders.make_map(**map_options) if map_input is None else map_input, board)
        data = module.UnitData()
        module.fromPortable(units, data, board)
        return module, board, data
    return build


@pytest.fixture
def make_scenario():
    return builders.make_scenario


@pytest.fixture
def make_state():
    return builders.make_state


FIXTURE_FILES = {
    "hex_geometry": "maps/hex_geometry.json",
    "movement_corridors": "scenarios/movement_corridors.json",
    "combat_duel": "scenarios/combat_duel.json",
    "setup_exchange": "scenarios/setup_exchange.json",
    "city_scoring": "scenarios/city_scoring.json",
    "fog_sequence": "observations/fog_sequence.json",
    "rectangular_features": "observations/rectangular_features.json",
    "tiny_episode": "scenarios/tiny_episode.json",
    "hierarchy_units": "scenarios/hierarchy_units.json",
    "protocol_messages": "protocol/protocol_messages.json",
    "replay_sequences": "replay/replay_sequences.json",
}


def _json_fixture(path):
    @pytest.fixture
    def fixture():
        return builders.load_fixture(path)
    return fixture


for _name, _path in FIXTURE_FILES.items():
    globals()[_name] = _json_fixture(_path)


@pytest.fixture
def rng():
    with isolated_rng():
        yield


@pytest.fixture
def detection_draws(engine_imports, monkeypatch):
    from tests.support.imports import import_server

    def install(values):
        monkeypatch.setattr(import_server("unit"), "random", finite_random(values))
    return install


@pytest.fixture
def global_guard():
    """Register additional globals/AI counters before changing them."""
    from contextlib import ExitStack

    with ExitStack() as stack:
        def guard(*attributes):
            stack.enter_context(preserve_globals(*attributes))
        yield guard


@pytest.fixture
def engine_globals(engine_imports, global_guard, monkeypatch):
    from tests.support.imports import import_server

    monkeypatch.setenv("ATLATL_NEURAL", "0")
    modules = {name: import_server(name) for name in (
        "mobility", "combat", "airegistry", "scenario_gen_reg",
        "current_game_access", "messageserver")}
    attributes = [(modules["mobility"], "cost"), (modules["mobility"], "stackingLimit")]
    attributes += [(modules["combat"], name) for name in (
        "range", "sight", "pDetect", "ineffectiveThreshold", "firepower_scaling",
        "firepower", "defensivefp", "terrain_multiplier")]
    attributes += [(modules["airegistry"], "ai_registry"),
                   (modules["scenario_gen_reg"], "scenario_generator_registry"),
                   (modules["current_game_access"], "server"),
                   (modules["messageserver"], "SLEEP_TIME"),
                   (modules["messageserver"].ClientWrapper, "next_id")]
    # These light AI modules are already imported by the registry.
    for name in ("ai.gym_ai_surrogate", "ai.multigym_ai"):
        attributes.append((sys.modules[name], "action_count"))
    # Optional modules stay opt-in. Preserve them if the consumer loaded them.
    for name in ("ai.neural", "ai.azero"):
        if name in sys.modules:
            attributes.append((sys.modules[name], "action_count"))
    server_module = sys.modules.get("server")
    if server_module is not None and getattr(server_module, "__file__", None) == str(REPO_ROOT / "server/server.py"):
        attributes.extend((server_module, name) for name in ("server", "gym_ai"))
    global_guard(*attributes)
    return modules


@pytest.fixture
def model_and_numeric_data(tmp_path):
    import numpy as np

    data = builders.load_fixture("models/numeric.json")
    archive = tmp_path / "tiny.npz"
    try:
        np.savez(archive, matrix=np.array(data["matrix"], dtype=np.float32),
                 results=np.array([[1., 3.], [2., 4.]], dtype=np.float32),
                 timesteps=np.array([10, 20], dtype=np.int64))
        data["archive"] = archive
        data["data_file"] = TESTS_DIR / "fixtures/models/sample.data"
        data["model_source"] = TESTS_DIR / "fixtures/models/tiny_cpu.py"
        yield data
    finally:
        archive.unlink(missing_ok=True)
