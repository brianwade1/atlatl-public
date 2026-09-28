"""S05 public accessors, initial state and observer reference behavior."""

from copy import deepcopy

import pytest

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("setup", [False, True])
def test_initial_state_and_public_accessors(game_factory, make_map, make_unit, make_scenario, setup):
    board = make_map(terrain_overrides={(0, 0): "urban", (3, 2): "urban", (1, 1): "urban"},
        setup_overrides={(0, 0): "setup-type-blue"} if setup else None)
    scenario = make_scenario(board, [make_unit(can_move=False),
        make_unit(faction="red", hex="hex-3-2", can_move=False)])
    before = deepcopy(scenario)
    game = game_factory(scenario)
    first, second = game.initial_state(), game.initial_state()
    assert first == second
    assert first["units"] == [dict(before["units"][0], canMove=True), before["units"][1]]
    assert first["status"] == {"cityOwner": {"hex-0-0": "blue", "hex-3-2": "red", "hex-1-1": "neutral"},
        "score": 0, "phaseCount": 0, "isTerminal": False, "onMove": "blue", "setupMode": setup}
    assert game.players() == ["blue", "red"]
    assert game.max_player() == game.on_move(first) == "blue"
    assert game.score(first) == 0 and not game.is_terminal(first)
    first["units"][0]["currentStrength"] = 1
    first["status"]["cityOwner"].clear()
    assert game.initial_state() == second
    assert scenario == before
    second["status"].update(score=-12.5, isTerminal=True, onMove="red")
    assert game.score(second) == -12.5 and game.is_terminal(second)
    assert game.on_move(second) == "red"


def test_parameters_shared_reference_characterization(game_factory, make_scenario):
    scenario = make_scenario()
    game = game_factory(scenario)
    assert game.parameters() is scenario
    game.parameters()["units"][0]["currentStrength"] = 67
    assert scenario["units"][0]["currentStrength"] == 67
    assert game.initial_state()["units"][0]["currentStrength"] == 67


@pytest.mark.parametrize("fog", [False, True], ids=["clear", "fog"])
@pytest.mark.parametrize("player", ["blue", "red"])
@pytest.mark.parametrize("near", [False, True], ids=["outside-sight", "detected"])
def test_observation_both_players_and_fog_modes(game_factory, make_map, make_unit, fog, player, near):
    board = make_map()
    board["fogOfWar"] = fog
    game = game_factory(map_data=board, units=[make_unit(),
        make_unit(faction="red", hex="hex-1-0" if near else "hex-3-2", can_move=False)])
    state = game.initial_state()
    before = deepcopy(state)
    observed = game.observation(state, player)
    expected = deepcopy(state)
    for unit in expected["units"]:
        unit["detected"] = near
        if fog and not near and unit["faction"] != player:
            unit["hex"] = "fog"
    assert observed == expected  # Hidden enemies keep every other field.
    assert state == before  # Detection runs on freshly loaded unit objects.
    assert observed["units"] is not state["units"]
    observed["units"][0]["currentStrength"] = 1
    assert state == before
    assert observed["status"] is state["status"]
    observed["status"]["score"] = 9
    assert state["status"]["score"] == 9


def test_observation_missing_fog_flag_and_repeated_detection(game_factory, make_unit, monkeypatch, detection_draws):
    from tests.support.imports import import_server

    game = game_factory(units=[make_unit(), make_unit(faction="red", hex="hex-1-0", can_move=False)])
    monkeypatch.setattr(import_server("combat"), "pDetect", 0.5)
    state = game.initial_state()
    before = deepcopy(state)
    detection_draws([0.9, 0.9, 0.1, 0.1])
    missed = game.observation(state, "blue")
    seen = game.observation(state, "blue")
    assert [u["detected"] for u in missed["units"]] == [False, False]
    assert [u["detected"] for u in seen["units"]] == [True, True]
    assert [u["hex"] for u in missed["units"]] == ["hex-0-0", "hex-1-0"]
    assert state == before
