"""S18-A/B: real engine compositions with bounded, reproducible inputs."""

from copy import deepcopy
import random

import pytest

pytestmark = [pytest.mark.core, pytest.mark.integration]


def identity(unit):
    return unit["faction"] + " " + unit["longName"]


def assert_occupancy(state, board, unit_world):
    _, _, rebuilt = unit_world(state["units"], map_input=board)
    expected = {}
    for unit in state["units"]:
        if unit["ineffective"]:
            assert unit["hex"] is None
        if unit["hex"] is not None:
            expected.setdefault(unit["hex"], []).append(identity(unit))
    actual = {hex_id: sorted(u.uniqueId for u in units)
              for hex_id, units in rebuilt.occupancy.items() if units}
    assert actual == {key: sorted(value) for key, value in expected.items()}
    assert all(len(value) == 1 for value in actual.values())


@pytest.mark.parametrize("seed", [7, 23, 91])
@pytest.mark.parametrize("rows,cols", [(3, 4), (4, 3)])
def test_seeded_legal_sequences_preserve_state_and_phase_invariants(
        game_factory, make_map, make_unit, unit_world, seed, rows, cols):
    board = make_map(rows=rows, cols=cols,
                     terrain_overrides={(1, 1): "urban", (2, 1): "rough"})
    game = game_factory(map_data=board, max_phases=6, city_score=12, units=[
        make_unit("A", hex="hex-0-0"),
        make_unit("B", unit_type="artillery", hex="hex-0-1"),
        make_unit("A", "red", "armor", hex="hex-1-0", can_move=False),
        make_unit("B", "red", "mechinf", hex=f"hex-{cols-1}-{rows-1}", can_move=False),
    ])
    chooser = random.Random(seed)
    state = game.initial_state()
    parameters_before = deepcopy(game.parameters())
    history = []
    for step in range(24):  # Four actors and six phases cannot require >24 actions.
        if game.is_terminal(state):
            break
        before = deepcopy(state)
        actions = game.legal_actions(state)
        assert state == before
        assert len(actions) == len({tuple(sorted(a.items())) for a in actions})
        assert actions.count({"type": "pass"}) == 1
        by_id = {identity(u): u for u in state["units"]}
        for action in actions:
            actor = action.get("mover", action.get("source"))
            if actor:
                assert by_id[actor]["canMove"] and not by_id[actor]["ineffective"]
                assert by_id[actor]["faction"] == state["status"]["onMove"]
        action = chooser.choice(actions)
        result = game.transition(state, action)
        history.append(action)
        assert state == before, (seed, step, history)
        assert game.parameters() == parameters_before
        assert_occupancy(result, board, unit_world)
        actor = action.get("mover", action.get("source"))
        spent = {identity(u) for u in before["units"]
                 if u["canMove"] and not u["ineffective"]}
        if actor:
            spent.remove(actor)
        advanced = action["type"] == "pass" or not spent
        assert result["status"]["phaseCount"] == before["status"]["phaseCount"] + int(advanced)
        expected_role = ({"blue": "red", "red": "blue"}[before["status"]["onMove"]]
                         if advanced else before["status"]["onMove"])
        assert result["status"]["onMove"] == expected_role
        assert result["status"]["isTerminal"] == (result["status"]["phaseCount"] == 6)
        if not advanced and actor:
            assert all(identity(u) != actor or not u["canMove"] for u in result["units"])
            assert all(a.get("mover", a.get("source")) != actor
                       for a in game.legal_actions(result))
        state = result
    assert game.is_terminal(state), (seed, history)


@pytest.mark.parametrize("attacking,scores", [
    ("blue", [60, 60, 72, -48, -48, -60, -72, -72, -84]),
    ("red", [-120, -120, -132, -72, -72, -60, -48, -48, -36]),
])
def test_destroy_capture_recapture_and_terminal_city_scoring(
        game_factory, make_map, make_unit, unit_world, attacking, scores):
    defending = "red" if attacking == "blue" else "blue"
    board = make_map(rows=3, cols=4, terrain_overrides={(1, 0): "urban"})
    game = game_factory(map_data=board, city_score=12, max_phases=4, units=[
        make_unit("shooter", attacking, hex="hex-0-0"),
        make_unit("capturer", attacking, strength=60, hex="hex-1-1"),
        make_unit("reserve", attacking, hex="hex-0-2"),
        make_unit("defender", defending, strength=60, hex="hex-1-0"),
        make_unit("shooter", defending, hex="hex-2-0"),
        make_unit("capturer", defending, hex="hex-2-1"),
        make_unit("reserve", defending, hex="hex-3-2"),
    ])
    state = game.initial_state()
    state["status"]["onMove"] = attacking
    for unit in state["units"]:
        unit["canMove"] = unit["faction"] == attacking
    # Infantry against urban infantry does 100 * 1 * .5 * .5 = 25.
    # A 60-strength victim falls to 35, is removed, and credits 60 total loss.
    # Blue losses cost twice red losses; each owned-city phase contributes +/-12.
    steps = [
        ({"type": "fire", "source": attacking + " shooter", "target": defending + " defender"}, defending, 0),
        ({"type": "move", "mover": attacking + " capturer", "destination": "hex-1-0"}, defending, 0),
        ({"type": "pass"}, attacking, 1),
        ({"type": "fire", "source": defending + " shooter", "target": attacking + " capturer"}, attacking, 1),
        ({"type": "move", "mover": defending + " capturer", "destination": "hex-1-0"}, attacking, 1),
        ({"type": "pass"}, defending, 2),
        ({"type": "pass"}, defending, 3),
        ({"type": "move", "mover": defending + " capturer", "destination": "hex-1-1"}, defending, 3),
        ({"type": "pass"}, defending, 4),
    ]
    for index, ((action, owner, phase), score) in enumerate(zip(steps, scores, strict=True)):
        before = deepcopy(state)
        assert action in game.legal_actions(state)
        result = game.transition(state, action)
        assert state == before
        assert result["status"]["cityOwner"] == {"hex-1-0": owner}
        assert result["status"]["score"] == score
        assert result["status"]["phaseCount"] == phase
        assert result["status"]["isTerminal"] == (index == len(steps) - 1)
        assert result["status"]["onMove"] == (attacking if phase % 2 == 0 else defending)
        assert_occupancy(result, board, unit_world)
        by_id = {identity(u): u for u in result["units"]}
        if index == 0:
            assert by_id[defending + " defender"]["currentStrength"] == 35
            assert by_id[defending + " defender"]["ineffective"]
            assert not by_id[attacking + " shooter"]["canMove"]
        if index == 3:
            assert by_id[attacking + " capturer"]["currentStrength"] == 35
            assert by_id[attacking + " capturer"]["ineffective"]
            assert not by_id[defending + " shooter"]["canMove"]
        if index >= 7:
            assert all(u["hex"] != "hex-1-0" for u in result["units"])
        state = result
