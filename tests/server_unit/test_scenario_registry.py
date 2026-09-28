"""S06 registry structure and small representative generator consumers."""

from copy import deepcopy
import inspect

import pytest

from tests.support.imports import import_server


pytestmark = [pytest.mark.core, pytest.mark.usefixtures("engine_imports", "rng")]


@pytest.mark.unit
def test_registry_entry_structure_and_supported_options():
    registry = import_server("scenario_gen_reg").scenario_generator_registry
    assert {"lydian-republic", "ordan-basin", "clear-inf-5", "hierarchy-inf-10",
            "invasion", "invasion-fog"} <= registry.keys()
    for name, entry in registry.items():
        assert isinstance(name, str) and name
        assert isinstance(entry, tuple) and len(entry) == 2
        factory, options = entry
        assert callable(factory)
        assert isinstance(options, dict)
        inspect.signature(factory).bind(**options)


@pytest.mark.integration
@pytest.mark.parametrize("alias,count", [("clear-inf-5",25), ("hierarchy-inf-10",100),
                                         ("invasion",192)])
def test_representative_registry_generators(alias, count):
    factory, options = import_server("scenario_gen_reg").scenario_generator_registry[alias]
    before = deepcopy(options)
    value = factory(**options, scenarioSeed=17)()
    assert options == before
    assert len(value["map"]["hexes"]) == count
    assert {u["faction"] for u in value["units"]} == {"blue", "red"}
    game = import_server("game").Game(value)
    assert len(game.initial_state()["units"]) == len(value["units"])


@pytest.mark.integration
@pytest.mark.parametrize("alias", ["lydian-republic", "ordan-basin"])
def test_packaged_factory_accepts_unused_generator_options(alias):
    registry = import_server("scenario_gen_reg")
    factory, options = registry.scenario_generator_registry[alias]
    assert factory is registry.packaged_scenario_factory
    expected = factory(**options)()
    actual = factory(**options, scenarioSeed=1729, scenarioCycle=2, balance=True)()
    assert actual == expected
    assert actual is not expected
