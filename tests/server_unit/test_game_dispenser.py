"""S06 dispenser identity and current-game singleton access."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests.support.builders import make_scenario
from tests.support.imports import import_server


pytestmark = [pytest.mark.core, pytest.mark.usefixtures("engine_imports")]


@pytest.mark.integration
def test_scenario_dispenser_constructs_new_games_for_each_call():
    first, second = make_scenario(max_phases=3), make_scenario(max_phases=5)
    generator = Mock(side_effect=[first, second, first])
    dispenser = import_server("game_dispenser").ScenarioGeneratorGameDispenser(generator)
    games = [dispenser.get_next_game() for _ in range(3)]
    assert generator.call_count == 3
    assert all(isinstance(game, import_server("game").Game) for game in games)
    assert len({id(game) for game in games}) == 3
    assert len({id(game.mapData) for game in games}) == 3
    assert [game.parameters()["score"]["maxPhases"] for game in games] == [3,5,3]
    assert games[0].parameters() is first
    assert games[1].parameters() is second
    assert games[2].parameters() is first


@pytest.mark.unit
def test_constant_dispenser_returns_exact_supplied_object():
    supplied = object()
    dispenser = import_server("game_dispenser").ConstantGameDispenser(supplied)
    assert dispenser.get_next_game() is supplied
    assert dispenser.get_next_game() is supplied


@pytest.mark.unit
def test_generator_failure_propagates():
    error = ValueError("test generator exhausted")
    dispenser = import_server("game_dispenser").ScenarioGeneratorGameDispenser(
        Mock(side_effect=error))
    with pytest.raises(ValueError, match="test generator exhausted") as exc:
        dispenser.get_next_game()
    assert exc.value is error


@pytest.mark.unit
def test_current_game_access_tracks_server_and_game_replacement(global_guard):
    access = import_server("current_game_access")
    global_guard((access, "server"))
    first, second = object(), object()
    server = SimpleNamespace(game=first)
    access.set_gameserver(server)
    assert access.get_current_game() is first
    server.game = second
    assert access.get_current_game() is second
    access.set_gameserver(SimpleNamespace(game=first))
    assert access.get_current_game() is first


@pytest.mark.unit
def test_current_game_without_server_characterization(global_guard):
    access = import_server("current_game_access")
    global_guard((access, "server"))
    access.set_gameserver(None)
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'game'"):
        access.get_current_game()
