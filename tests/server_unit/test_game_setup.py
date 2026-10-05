"""S05 setup contracts and explicit validation-gap characterizations."""

from copy import deepcopy

import pytest

pytestmark = pytest.mark.core


@pytest.fixture
def setup_game(game_factory, make_map, make_unit):
    board = make_map(rows=1, cols=5,
        terrain_overrides={(1, 0): "urban"},
        setup_overrides={(0, 0): "setup-type-blue", (1, 0): "setup-type-blue",
                         (2, 0): "setup-type-blue", (3, 0): "setup-type-red",
                         (4, 0): "setup-type-red"})
    return game_factory(map_data=board, city_score=12, max_phases=2, units=[
        make_unit(), make_unit("B", hex="hex-2-0"),
        make_unit(faction="red", hex="hex-4-0", can_move=False)])


@pytest.mark.unit
def test_both_setup_moves_exchange_and_passes(setup_game):
    game = setup_game
    initial = game.initial_state()
    before = deepcopy(initial)
    move = {"type": "setup-move", "mover": "blue A", "destination": "hex-1-0"}
    assert game.legal_actions(initial) == [{"type": "pass"}]
    assert game._is_legal_setup(initial, move)
    moved = game.transition(initial, move)
    assert initial == before
    assert moved["units"][0]["hex"] == "hex-1-0"
    assert moved["units"][0]["canMove"]
    assert moved["status"] == initial["status"]
    exchange = {"type": "setup-exchange", "mover": "blue A", "friendly": "blue B"}
    assert game._is_legal_setup(moved, exchange)
    swapped = game.transition(moved, exchange)
    assert [u["hex"] for u in swapped["units"]] == ["hex-2-0", "hex-1-0", "hex-4-0"]
    red = game.transition(swapped, {"type": "pass"})
    assert red["status"] == dict(initial["status"], onMove="red")
    assert [u["canMove"] for u in red["units"]] == [False, False, True]
    red_move = {"type": "setup-move", "mover": "red A", "destination": "hex-3-0"}
    assert game._is_legal_setup(red, red_move)
    placed = game.transition(red, red_move)
    assert placed["units"][2]["hex"] == "hex-3-0"
    blue = game.transition(placed, {"type": "pass"})
    assert blue["status"] == dict(initial["status"], setupMode=False)
    assert [u["canMove"] for u in blue["units"]] == [True, True, False]


@pytest.mark.integration
def test_scripted_setup_to_terminal_exact_states(setup_game):
    game = setup_game
    state = game.initial_state()
    # Units stay outside sight until the blue setup move. Detection is controlled.
    expected_units = deepcopy(state["units"])
    state = game.transition(state, {"type": "setup-move", "mover": "blue A", "destination": "hex-1-0"})
    expected_units[0]["hex"] = "hex-1-0"
    expected_units[1]["detected"] = True
    expected_units[2]["detected"] = True
    assert state == {"units": expected_units, "status": {
        "cityOwner": {"hex-1-0": "neutral"}, "score": 0, "phaseCount": 0,
        "isTerminal": False, "onMove": "blue", "setupMode": True}}
    for on_move, setup, phase, score, terminal, flags, owner in [
        ("red", True, 0, 0, False, [False, False, True], "neutral"),
        ("blue", False, 0, 0, False, [True, True, False], "neutral"),
        ("red", False, 1, 12, False, [False, False, True], "blue"),
        ("blue", False, 2, 24, True, [False, False, True], "blue"),
    ]:
        state = game.transition(state, {"type": "pass"})
        for unit, flag in zip(expected_units, flags):
            unit["canMove"] = flag
        assert state == {"units": expected_units, "status": {
            "cityOwner": {"hex-1-0": owner}, "score": score, "phaseCount": phase,
            "isTerminal": terminal, "onMove": on_move, "setupMode": setup}}
    assert game.is_terminal(state)
    assert game.score(state) == 24


@pytest.mark.parametrize("action", [
    {"type": "setup-move", "mover": "red A", "destination": "hex-3-0"},
    {"type": "setup-move", "mover": "blue A", "destination": "hex-3-0"},
    {"type": "setup-exchange", "mover": "blue A", "friendly": "red A"},
    {"type": "move", "mover": "blue A", "destination": "hex-1-0"},
], ids=["wrong-faction", "wrong-zone", "exchange-wrong-zone", "ordinary-move"])
@pytest.mark.unit
def test_rejected_setup_preserves_input(setup_game, action):
    state = setup_game.initial_state()
    before = deepcopy(state)
    assert not setup_game._is_legal_setup(state, action)
    with pytest.raises(Exception, match="^Action is not legal in this state$"):
        setup_game.transition(state, action)
    assert state == before


@pytest.mark.parametrize("gap", ["occupied", "enemy-exchange", "ineffective"])
@pytest.mark.unit
def test_setup_validation_gaps_characterization(setup_game, gap):
    state = setup_game.initial_state()
    action = {"type": "setup-move", "mover": "blue A", "destination": "hex-2-0"}
    if gap == "enemy-exchange":
        state["units"][2]["hex"] = "hex-1-0"  # Enemy inside blue's zone.
        action = {"type": "setup-exchange", "mover": "blue A", "friendly": "red A"}
    elif gap == "ineffective":
        state["units"][0].update(ineffective=True, hex=None, canMove=False)
        action["destination"] = "hex-1-0"
    before = deepcopy(state)
    assert setup_game._is_legal_setup(state, action)
    result = setup_game.transition(state, action)
    assert state == before
    if gap == "occupied":
        assert [u["hex"] for u in result["units"][:2]] == ["hex-2-0", "hex-2-0"]
    elif gap == "enemy-exchange":
        assert [result["units"][i]["hex"] for i in (0, 2)] == ["hex-1-0", "hex-0-0"]
    else:
        assert result["units"][0] == dict(before["units"][0], hex="hex-1-0")
    assert result["status"] == before["status"]


@pytest.mark.unit
@pytest.mark.parametrize("action,key", [
    ({"type": "setup-move", "mover": "unknown", "destination": "hex-1-0"}, "unknown"),
    ({"type": "setup-move", "mover": "blue A", "destination": "unknown"}, "unknown"),
    ({"type": "setup-exchange", "mover": "blue A", "friendly": "unknown"}, "unknown"),
    ({"type": "setup-move", "mover": "blue A"}, "destination"),
    ({"type": "setup-exchange", "mover": "blue A"}, "friendly"),
], ids=["unknown-mover", "unknown-hex", "unknown-exchange", "missing-destination", "missing-friendly"])
def test_setup_malformed_fields_characterization(setup_game, action, key):
    state = setup_game.initial_state()
    before = deepcopy(state)
    with pytest.raises(KeyError) as caught:
        setup_game.transition(state, action)
    assert caught.value.args == (key,)
    assert state == before


@pytest.mark.unit
def test_unknown_setup_action_with_valid_mover_is_rejected(setup_game):
    state = setup_game.initial_state()
    before = deepcopy(state)
    action = {"type": "unsupported-setup-action", "mover": "blue A"}
    assert not setup_game._is_legal_setup(state, action)
    with pytest.raises(Exception, match="^Action is not legal in this state$"):
        setup_game.transition(state, action)
    assert state == before
