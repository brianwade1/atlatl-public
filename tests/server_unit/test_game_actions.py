"""S05 ordinary actions, validation, phase timing and branch isolation."""

from copy import deepcopy

import pytest

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.fixture
def action_game(game_factory, make_map, make_unit):
    return game_factory(map_data=make_map(rows=4, cols=4), units=[
        make_unit(), make_unit("B", hex="hex-0-3"),
        make_unit("spent", hex="hex-3-3", can_move=False),
        make_unit("dead", hex=None, ineffective=True, can_move=False),
        make_unit(faction="red", hex="hex-1-0", can_move=False)])


def test_legal_actions_filter_availability_and_exhaustion(action_game):
    state = action_game.initial_state()
    state["units"][2]["canMove"] = False
    actions = action_game.legal_actions(state)
    assert actions.count({"type": "pass"}) == 1
    assert {a.get("mover", a.get("source")) for a in actions[1:]} == {"blue A", "blue B"}
    assert {"type": "move", "mover": "blue A", "destination": "hex-0-1"} in actions
    assert {"type": "fire", "source": "blue A", "target": "red A"} in actions
    assert len(actions) == len({tuple(sorted(a.items())) for a in actions})
    state = action_game.transition(state, {"type": "move", "mover": "blue A", "destination": "hex-0-1"})
    assert all(a.get("mover", a.get("source")) != "blue A" for a in action_game.legal_actions(state))


def test_move_last_actor_advances_and_pass_ends_early(game_factory, make_unit):
    game = game_factory(units=[make_unit(), make_unit("B", hex="hex-0-2")])
    original = game.initial_state()
    before = deepcopy(original)
    moved = game.transition(original, {"type": "move", "mover": "blue A", "destination": "hex-1-0"})
    assert moved["units"] == [dict(before["units"][0], hex="hex-1-0", canMove=False), before["units"][1]]
    assert moved["status"] == before["status"]
    last = game.transition(moved, {"type": "move", "mover": "blue B", "destination": "hex-1-2"})
    assert last["units"] == [moved["units"][0], dict(before["units"][1], hex="hex-1-2", canMove=False)]
    assert last["status"] == dict(before["status"], phaseCount=1, onMove="red")
    passed = game.transition(original, {"type": "pass"})
    assert passed["units"] == [dict(u, canMove=False) for u in original["units"]]
    assert passed["status"] == last["status"]
    assert original == before


def test_city_capture_waits_for_phase_boundary(game_factory, make_map, make_unit):
    game = game_factory(map_data=make_map(terrain_overrides={(1, 0): "urban"}), city_score=8,
                        units=[make_unit(), make_unit("B", hex="hex-0-2")])
    state = game.transition(game.initial_state(),
                            {"type": "move", "mover": "blue A", "destination": "hex-1-0"})
    assert state["status"]["cityOwner"] == {"hex-1-0": "neutral"}
    assert game.score(state) == 0
    result = game.transition(state, {"type": "move", "mover": "blue B", "destination": "hex-1-2"})
    assert result["status"]["cityOwner"] == {"hex-1-0": "blue"}
    assert result["status"]["phaseCount"] == 1
    assert game.score(result) == 8


@pytest.mark.parametrize("action", [
    {"type": "move", "mover": "blue A", "destination": "hex-3-3"},
    {"type": "move", "mover": "blue A", "destination": "hex-1-0"},
    {"type": "move", "mover": "red A", "destination": "hex-2-0"},
    {"type": "move", "mover": "unknown", "destination": "hex-0-1"},
    {"type": "move", "mover": "blue A", "destination": "unknown"},
    {"type": "fire", "source": "blue B", "target": "red A"},
    {"type": "fire", "source": "blue A", "target": "blue B"},
    {"type": "fire", "source": "blue A", "target": "unknown"},
    {"type": "exchange", "mover": "blue A", "target": "blue B"},
], ids=["distant", "occupied", "wrong-faction", "unknown-mover", "unknown-hex",
        "out-of-range-fire", "friendly-fire", "unknown-target", "exchange"])
def test_invalid_actions_rejected_without_mutation(action_game, action):
    state = action_game.initial_state()
    before = deepcopy(state)
    assert not action_game._is_legal_move(state, action)
    with pytest.raises(Exception, match="is not legal in this state"):
        action_game.transition(state, action)
    assert state == before


@pytest.mark.parametrize("action,key", [({}, "type"), ({"type": "move"}, "mover"),
    ({"type": "move", "mover": "blue A"}, "destination"),
    ({"type": "fire"}, "source"), ({"type": "fire", "source": "blue A"}, "target")])
def test_malformed_fields_characterization(action_game, action, key):
    state = action_game.initial_state()
    before = deepcopy(state)
    with pytest.raises(KeyError) as caught:
        action_game.transition(state, action)
    assert caught.value.args == (key,)
    assert state == before


def test_none_rejected_and_extra_fields_ignored(action_game):
    state = action_game.initial_state()
    before = deepcopy(state)
    with pytest.raises(Exception, match="^action is None$"):
        action_game.transition(state, None)
    assert state == before
    assert action_game.transition(state, {"type": "pass", "extra": 17}) == action_game.transition(state, {"type": "pass"})


def test_terminal_transition_characterization(game_factory):
    game = game_factory(max_phases=1)
    terminal = game.transition(game.initial_state(), {"type": "pass"})
    before = deepcopy(terminal)
    assert game.is_terminal(terminal)
    assert {"type": "pass"} in game.legal_actions(terminal)
    result = game.transition(terminal, {"type": "pass"})
    assert terminal == before
    assert result["status"] == dict(before["status"], phaseCount=2, onMove="blue")


def test_off_faction_flag_characterization(game_factory):
    game = game_factory()
    state = game.initial_state()
    state["units"][1]["canMove"] = True
    assert any(a.get("mover") == "red A" for a in game.legal_actions(state))


def test_successor_branches_are_independent(game_factory, make_scenario, make_unit):
    scenario = make_scenario(units=[make_unit(), make_unit("B", hex="hex-0-2")])
    scenario_before = deepcopy(scenario)
    game = game_factory(scenario)
    state = game.initial_state()
    before = deepcopy(state)
    left = game.transition(state, {"type": "move", "mover": "blue A", "destination": "hex-1-0"})
    left_before = deepcopy(left)
    right = game.transition(state, {"type": "move", "mover": "blue A", "destination": "hex-0-1"})
    assert left == left_before
    right["units"][1]["currentStrength"] = 1
    right["status"]["cityOwner"]["sentinel"] = "red"
    assert left == left_before
    assert state == before
    assert scenario == scenario_before
