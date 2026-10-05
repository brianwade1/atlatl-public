"""S15 imports remain opt-in; missing ML dependencies fail explicitly."""

import pytest
from tests.support.imports import import_server


@pytest.fixture
def ml_registry(engine_imports, monkeypatch):
    monkeypatch.setenv("ATLATL_NEURAL", "0")
    return import_server("airegistry")


@pytest.fixture
def obsmod(engine_imports):
    return import_server("observation")


@pytest.fixture
def rectangular_game(engine_imports, rectangular_features):
    return import_server("game").Game(rectangular_features["scenario"]), rectangular_features["state"]


@pytest.fixture
def surrogate(engine_imports):
    import ai.gym_ai_surrogate as module
    return module
