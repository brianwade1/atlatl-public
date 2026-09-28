"""Small S05 game factory with controlled detection, using the real engine."""

import pytest

from tests.support.builders import make_scenario
from tests.support.imports import import_server


@pytest.fixture
def game_factory(engine_imports, detection_draws):
    detection_draws([0.25] * 512)

    def build(scenario=None, **options):
        return import_server("game").Game(
            make_scenario(**options) if scenario is None else scenario)
    return build
