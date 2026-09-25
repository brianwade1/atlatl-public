"""Original baseline assertions, migrated without extending launcher coverage."""

from pathlib import Path

import pytest

from tests.support.imports import REPO_ROOT, SERVER_DIR, assert_origin, import_server


pytestmark = [pytest.mark.core, pytest.mark.integration,
              pytest.mark.usefixtures("engine_imports")]


def test_launcher_preserves_bare_filenames_and_generator_names():
    import main

    assert_origin(main, REPO_ROOT / "main.py")
    assert main._scenario_arg_for_server("test4.scn") == "test4.scn"
    assert main._scenario_arg_for_server("city-inf-5") == "city-inf-5"


def test_launcher_makes_explicit_relative_path_absolute(monkeypatch):
    import main

    assert_origin(main, REPO_ROOT / "main.py")
    monkeypatch.chdir(REPO_ROOT)
    resolved = main._scenario_arg_for_server(
        "scenarios/Lydian_Republic/game/defense_of_the_lydian_republic.scn"
    )
    assert Path(resolved) == (
        REPO_ROOT / "scenarios/Lydian_Republic/game/defense_of_the_lydian_republic.scn"
    )


def test_bare_filename_uses_default_scenario_directory():
    scenario = import_server("scenario")
    assert scenario.resolve_scenario_path("test4.scn") == SERVER_DIR / "scenarios/test4.scn"


@pytest.mark.parametrize("alias,hex_count,unit_count", [
    pytest.param("lydian-republic", 280, 21, id="lydian-republic"),
    pytest.param("ordan-basin", 144, 26, id="ordan-basin"),
])
def test_packaged_aliases_load_expected_scenarios(alias, hex_count, unit_count):
    registry = import_server("scenario_gen_reg").scenario_generator_registry
    factory, kwargs = registry[alias]
    scenario_data = factory(**kwargs)()
    assert len(scenario_data["map"]["hexes"]) == hex_count
    assert len(scenario_data["units"]) == unit_count
