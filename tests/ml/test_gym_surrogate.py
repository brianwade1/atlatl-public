"""Surrogate protocol, all discrete offsets, channel layouts and reward copies."""

import importlib
import json
from unittest.mock import Mock
import numpy as np
import pytest
from tests.support.builders import make_map, make_unit, make_scenario, make_state
from tests.support.isolation import KnownDefect
from tests.ml.test_observation_features import expected_channels

pytestmark = [pytest.mark.ml, pytest.mark.unit]


def deliver(ai, kind, payload=None, callback=None):
    msg = {"type": kind}
    if payload is not None:
        msg[kind if kind == "parameters" else "observation"] = payload
    response = ai.process(json.dumps(msg), callback)
    return json.loads(response) if response else None


def ready(ai, scenario, state):
    assert deliver(ai, "parameters", scenario) == {"type": "role-request", "role": ai.role}
    assert deliver(ai, "observation", state) == {"type": "gym-pause"}
    return ai


# Literal destination rings, independent of production offset constants.
RINGS = {
    (2, 2): [(2,1),(3,1),(3,2),(2,3),(1,2),(1,1),(2,0),(3,0),(4,1),(4,2),(4,3),(3,3),(2,4),(1,3),(0,3),(0,2),(0,1),(1,0)],
    (3, 2): [(3,1),(4,2),(4,3),(3,3),(2,3),(2,2),(3,0),(4,1),(5,1),(5,2),(5,3),(4,4),(3,4),(2,4),(1,3),(1,2),(1,1),(2,1)],
    (0, 0): [(0,-1),(1,-1),(1,0),(0,1),(-1,0),(-1,-1),(0,-2),(1,-2),(2,-1),(2,0),(2,1),(1,1),(0,2),(-1,1),(-2,1),(-2,0),(-2,-1),(-1,-2)],
    (1, 0): [(1,-1),(2,0),(2,1),(1,1),(0,1),(0,0),(1,-2),(2,-1),(3,-1),(3,0),(3,1),(2,2),(1,2),(0,2),(-1,1),(-1,0),(-1,-1),(0,-1)],
}


@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("origin", list(RINGS))
@pytest.mark.parametrize("index", range(19))
@pytest.mark.parametrize("target_kind", ["clear", "enemy", "friendly", "water"])
def test_all_discrete_actions(surrogate, role, origin, index, target_kind):
    from game import Game
    x, y = origin
    tx, ty = RINGS[origin][index - 1] if index else (-9, -9)
    valid = 0 <= tx < 7 and 0 <= ty < 6
    destination = f"hex-{tx}-{ty}"
    units = [make_unit(faction=role, hex=f"hex-{x}-{y}")]
    other = "red" if role == "blue" else "blue"
    if valid and target_kind in ("enemy", "friendly"):
        units.append(make_unit("B", other if target_kind == "enemy" else role, hex=destination, can_move=target_kind == "friendly"))
    overrides = {(tx, ty): "water"} if valid and target_kind == "water" else {}
    scenario = make_scenario(make_map(rows=6, cols=7, terrain_overrides=overrides), units)
    state = make_state(units, on_move=role)
    ai = ready(surrogate.AI(role), scenario, state)
    actual = ai.actionMessageDiscrete(index)
    expected = None if valid and target_kind == "friendly" else {"type": "action", "action": {"type": "pass"}}
    if index and valid and index <= 6 and target_kind in ("clear", "enemy"):
        action = ({"type": "move", "mover": f"{role} A", "destination": destination} if target_kind == "clear"
                  else {"type": "fire", "source": f"{role} A", "target": f"{other} B"})
        expected = {"type": "action", "action": action}
    assert actual == expected
    assert ai.attempted_moveD[f"{role} A"] is True
    if actual is not None:
        game = Game(scenario)
        assert actual["action"] in game.legal_actions(state)
        game.transition(state, actual["action"])


@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("module_name", ["ai.gym_ai_surrogate", "ai.multigym_ai"])
def test_protocol_lifecycle_reward_and_restart(ml_registry, module_name, role):
    module = importlib.import_module(module_name)
    scenario = make_scenario()
    state = make_state(scenario["units"], on_move=role)
    ai = module.AI(role, {} if module_name.endswith("surrogate") else {"mode":"training", "subAIs":"[]"})
    callback = Mock()
    assert deliver(ai, "parameters", scenario, callback) == {"type": "role-request", "role": role}
    assert ai.response_fn is None  # reset clears handshake callback
    ai.sendToServer({"probe": 1}); callback.assert_not_called()
    state["status"]["setupMode"] = True
    assert deliver(ai, "observation", state, callback) == {"type": "action", "action": {"type": "pass"}}
    ai.sendToServer({"probe": 2}); callback.assert_called_once_with({"probe": 2})
    state["status"].update(setupMode=False, onMove="red" if role == "blue" else "blue")
    assert deliver(ai, "observation", state) is None
    assert ai.phase == "wait"
    state["status"].update(onMove=role, score=10, phaseCount=2)
    assert deliver(ai, "observation", state) == {"type": "gym-pause"}
    assert ai.phaseCount == 2
    assert ai.action_result()[1:] == (10, False, {"score": 10})
    assert ai.action_result()[1] == 0
    if module_name.endswith("surrogate"):
        ai.actionMessageDiscrete(0)
    else:
        ai.attempted_moveD[f"{role} A"] = True
    assert ai.nextMover() is None
    state["status"].update(isTerminal=True, score=14)
    assert deliver(ai, "observation", state) == {"type": "gym-pause"}
    assert ai.action_result()[1:] == (29, True, {"score": 14})
    assert ai.action_result()[1:] == (0, True, {"score": 14})
    assert deliver(ai, "reset") is None
    assert ai.mapData is ai.unitData is ai.response_fn is None
    assert ai.last_score == ai.accumulated_reward == 0
    state["status"].update(isTerminal=False, score=0)
    ready(ai, scenario, state)
    assert ai.nextMover().faction == role
    assert ai.rewArt.original_strength == 100


def test_reward_accumulates_before_consumption(surrogate):
    scenario = make_scenario(); state = make_state(scenario["units"])
    ai = ready(surrogate.AI("blue"), scenario, state)
    for score in [4, 9, 7, 12]:
        state["status"]["score"] = score
        ai.updateLocalState(state)
    assert ai.action_result()[1:] == (14, False, {"score":12})
    assert ai.action_result()[1] == 0
    ai.reset()
    assert ai.rewArt.original_strength is None


@pytest.mark.parametrize("index,error", [(19, IndexError), (-19, IndexError), (1.5, TypeError), ("1", TypeError)])
def test_invalid_actions_characterization(surrogate, index, error):
    scenario = make_scenario()
    ai = ready(surrogate.AI("blue"), scenario, make_state(scenario["units"]))
    with pytest.raises(error):
        ai.actionMessageDiscrete(index)
    assert ai.attempted_moveD["blue A"] is True


def test_negative_index_and_no_mover_characterization(surrogate):
    scenario = make_scenario()
    ai = ready(surrogate.AI("blue"), scenario, make_state(scenario["units"]))
    assert ai.actionMessageDiscrete(-1) == {"type": "action", "action": {"type": "pass"}}
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'uniqueId'"):
        ai.actionMessageDiscrete(0)


@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("origin", [(2,2), (3,2)])
@pytest.mark.parametrize("index", range(1,19))
def test_all_artillery_fire_offsets(surrogate, role, origin, index):
    from game import Game
    x,y = origin; tx,ty = RINGS[origin][index-1]
    other = "red" if role == "blue" else "blue"
    units = [make_unit(faction=role, unit_type="artillery", hex=f"hex-{x}-{y}"),
             make_unit("target", other, hex=f"hex-{tx}-{ty}", can_move=False)]
    scenario = make_scenario(make_map(rows=6, cols=7), units)
    state = make_state(units, on_move=role)
    ai = ready(surrogate.AI(role), scenario, state)
    expected = {"type":"fire", "source":f"{role} A", "target":f"{other} target"}
    assert ai.actionMessageDiscrete(index) == {"type":"action", "action":expected}
    game = Game(scenario)
    assert expected in game.legal_actions(state)
    game.transition(state, expected)


def test_wait_with_remaining_mover_and_completely_blocked_mover(surrogate):
    units = [make_unit(), make_unit("B", hex="hex-3-2")]
    scenario = make_scenario(units=units)
    ai = ready(surrogate.AI("blue"), scenario, make_state(units))
    assert ai.actionMessageDiscrete(0) is None
    assert ai.nextMover().uniqueId == "blue B"
    assert ai.actionMessageDiscrete(0) == {"type":"action", "action":{"type":"pass"}}
    units = [make_unit()]
    scenario = make_scenario(make_map(rows=1, cols=1), units)
    ai = ready(surrogate.AI("blue"), scenario, make_state(units))
    assert ai.actionMessageDiscrete(18) == {"type":"action", "action":{"type":"pass"}}


@pytest.mark.parametrize("name,n", [("AI",3),("AIx2",3),("AITwelve",12),("AI13",13),("AI14",14),("AI16",16),("AI17",17),("AI18",18)])
@pytest.mark.parametrize("role", ["blue", "red"])
def test_variant_channel_contracts(surrogate, rectangular_game, rectangular_features, name, n, role):
    game, state = rectangular_game
    state["status"].update(onMove=role, cityOwner={"hex-1-1": "blue", "hex-2-1": "red"})
    ai = ready(getattr(surrogate, name)(role, {}), rectangular_features["scenario"], state)
    base = expected_channels(game, state)
    mover = np.zeros((3, 4)); mover[(2, 0) if role == "blue" else (0, 3)] = 1
    legal = np.zeros((3, 4))
    # Six-neighbor ring clipped at the two corners; water/unused block entry.
    for x, y in ([(0,1),(1,1),(1,2)] if role == "blue" else [(2,0),(2,1),(3,1)]):
        h = game.mapData.hexIndex[f"hex-{x}-{y}"]
        if h.terrain not in ("water", "unused"):
            legal[y,x] = 1
    short = [mover, legal, *base[1:7], *base[7:11]]
    full = [mover, base[0], legal, *base[1:7], *base[7:11]]
    phase = np.full((3,4), .9**2)
    remaining = np.full((3,4), .9)  # maxPhases=4, phase=2
    layouts = {"AI": [mover, *base[1:3]], "AIx2": [mover, *base[1:3]],
               "AITwelve": short, "AI13": short+[phase], "AI14": full+[phase],
               "AI16": full+[*base[13:15], remaining], "AI17": full+[*base[13:15], remaining, base[16]],
               "AI18": [mover, *base[:15], phase, base[16]]}
    expected = np.stack(layouts[name])
    if name == "AIx2":
        doubled = np.zeros((3,7,4))
        for x in range(4):
            doubled[:, x%2:6+x%2:2, x] = expected[:,:,x]
        expected = doubled
    assert ai.getNFeatures() == n
    np.testing.assert_allclose(ai.observation(), expected)
    ai.attempted_moveD[f"{role} A"] = True
    assert not ai.observation()[0].any()


@pytest.mark.parametrize("module_name", ["ai.gym_ai_surrogate", "ai.multigym_ai"])
@pytest.mark.parametrize("role", ["blue", "red"])
def test_reward_copies(ml_registry, unit_world, module_name, role):
    module = importlib.import_module(module_name)
    reward = module.NoNegativesRewArt(role)
    assert reward.engineeredReward(12) == 12
    assert reward.engineeredReward(-3) == reward.engineeredReward(-9) == 0
    assert reward.engineeredReward(12) == 10
    assert reward.negative_rewards == 2
    assert module.NoNegativesRewArt(role).negative_rewards == 0
    _, _, data = unit_world([make_unit(faction=role), make_unit("dead", role, ineffective=True),
                             make_unit(faction="red" if role == "blue" else "blue", hex="hex-3-2")])
    reward = module.BoronRewArt(role)
    assert reward.engineeredReward(20, data) == 20
    data.unitIndex[f"{role} A"].currentStrength = 40
    assert reward.engineeredReward(20, data) == 8
    assert reward.engineeredReward(-5, data) == 0
    assert reward.engineeredReward(-5, data, True) == 10
    assert module.BoronRewArt(role).original_strength is None


@pytest.mark.parametrize("module_name", ["ai.gym_ai_surrogate", "ai.multigym_ai"])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K43: Boron divides by zero starting strength")
def test_zero_initial_strength(ml_registry, unit_world, module_name):
    module = importlib.import_module(module_name)
    _, _, data = unit_world([])
    reward = module.BoronRewArt("blue")
    try:
        result = reward.engineeredReward(0, data, True)
    except ZeroDivisionError as exc:
        if str(exc) == "division by zero" and reward.original_strength == 0:
            raise KnownDefect("K43: no surviving initial strength") from exc
        raise
    assert np.isfinite(result)


@pytest.mark.parametrize("module_name", ["ai.gym_ai_surrogate", "ai.multigym_ai"])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K44: red reward uses blue score sign")
def test_red_reward_sign(ml_registry, module_name):
    module = importlib.import_module(module_name)
    ai = module.AI("red", {} if module_name.endswith("surrogate") else {"mode":"training", "subAIs":"[]"})
    scenario = make_scenario()
    state = make_state(scenario["units"], on_move="red")
    ready(ai, scenario, state)
    state["status"]["score"] = -10
    ai.updateLocalState(state)
    if ai.accumulated_reward == 0 and ai.last_score == -10:
        raise KnownDefect("K44: red improvement clipped as blue loss")
    assert ai.accumulated_reward == 10
