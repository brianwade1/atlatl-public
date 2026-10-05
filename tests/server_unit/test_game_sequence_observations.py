"""S18-D: observation calls and JSON round trips during real actions."""

from copy import deepcopy
import json

import pytest

pytestmark = [pytest.mark.core, pytest.mark.integration]


@pytest.mark.parametrize("fog", [False, True], ids=["clear", "fog"])
@pytest.mark.parametrize("role", ["blue", "red"])
def test_observing_both_roles_and_roundtripping_preserves_deterministic_sequence(
        game_factory, make_map, make_unit, role, fog):
    enemy = "red" if role == "blue" else "blue"
    board = make_map(rows=3, cols=3, terrain_overrides={(1, 0): "urban"})
    board["fogOfWar"] = fog
    game = game_factory(map_data=board, max_phases=4, city_score=12, units=[
        make_unit("shooter", role, hex="hex-0-0"),
        make_unit("mover", role, hex="hex-0-2"),
        make_unit("target", enemy, strength=60, hex="hex-1-0"),
        make_unit("reserve", enemy, hex="hex-2-2"),
    ])
    direct = game.initial_state()
    direct["status"]["onMove"] = role
    for unit in direct["units"]:
        unit["canMove"] = unit["faction"] == role
    observed = deepcopy(direct)
    actions = [
        {"type": "fire", "source": role + " shooter", "target": enemy + " target"},
        {"type": "move", "mover": role + " mover", "destination": "hex-1-2"},
        {"type": "pass"}, {"type": "pass"}, {"type": "pass"},
    ]
    for action in actions:
        before = deepcopy(observed)
        # pDetect=1 and the finite draws supplied by game_factory make detection
        # deterministic. This does not claim observation getters are pure under
        # arbitrary probabilities; their RNG/alias behavior has separate tests.
        for observer in ("blue", "red"):
            observation = game.observation(observed, observer)
            assert observation["status"] is observed["status"]  # Existing alias contract.
            encoded = json.loads(json.dumps(observation))
            assert encoded == observation
            encoded["status"]["score"] = 123456
            assert observed == before
        observed = json.loads(json.dumps(observed))
        assert observed == before
        assert game.legal_actions(observed) == game.legal_actions(direct)
        assert action in game.legal_actions(direct)
        direct_before = deepcopy(direct)
        observed_before = deepcopy(observed)
        direct_result = game.transition(direct, action)
        observed_result = game.transition(observed, action)
        assert direct == direct_before
        assert observed == observed_before
        assert observed_result == direct_result
        direct, observed = direct_result, observed_result
    assert game.is_terminal(direct)
    assert direct["status"]["phaseCount"] == 4
