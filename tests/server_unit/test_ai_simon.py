"""Hand-solvable Simon tactics, with recursion confined to bounded children."""

import pytest

from tests.support.ai_contract import prepare, send
from tests.support.builders import make_map, make_scenario, make_state, make_unit
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.core, pytest.mark.unit]


def test_city_distances_and_setup_ranking(engine_imports):
    params = make_scenario(make_map(rows=5, cols=1, terrain_overrides={(0, 1): "urban", (0, 4): "urban"},
        setup_overrides={(0, 0): "setup-type-blue", (0, 2): "setup-type-blue"}),
        [make_unit(), make_unit("B", hex="hex-0-3")])
    state = make_state(params["units"], city_owner={"hex-0-1": "blue", "hex-0-4": "red"})
    ai = prepare("simon_says", "blue", params, state)
    hx = ai.mapData.hexIndex["hex-0-0"]
    cities = state["status"]["cityOwner"]
    assert ai.getHexDistToClosestCity(hx, cities) == 1
    assert ai.getTotalHexDistToCities(hx, cities) == 5
    assert ai.getScoreHexDistToCities(hx, cities) == pytest.approx(1.05)
    dist, city = ai.getHexDistToClosestEnemyCity(hx)
    assert (dist, city.id) == (4, "hex-0-4")
    setup = ai._setupActions(cities)
    assert {unit for unit, _ in setup} == {"blue A", "blue B"}
    assert {hex for _, hex in setup} == {"hex-0-0", "hex-0-2"}


@pytest.mark.parametrize("strength,remaining,expected", [(74, 4, None), (75, 4, "hex-0-1"), (76, 4, "hex-0-1"), (100, 1, None)])
def test_maneuver_strength_and_time_threshold(strength, remaining, expected, engine_imports):
    params = make_scenario(make_map(rows=5, cols=1), [make_unit(strength=strength), make_unit("E", "red", hex="hex-0-3", can_move=False)])
    ai = prepare("simon_says", "blue", params, make_state(params["units"]))
    actor = ai.unitData.unitIndex["blue A"]
    action = ai.getBestUnitManeuverAction(actor, remaining)
    assert action == (None if expected is None else {"type": "move", "mover": "blue A", "destination": expected})
    assert ai.getBestUnitManeuverAction(actor, remaining, {"hex-0-1"}) is None


def test_reset_clears_setup_queue_and_off_turn_assault_flag(engine_imports):
    params = make_scenario()
    state = make_state(params["units"], on_move="red")
    ai = prepare("simon_says", "blue", params, state)
    ai.action_queue = [("blue Old", "hex-9-9")]
    ai.doSetup = False
    ai.hasAssaulted = True
    assert send(ai, "observation", observation=state) is None
    assert not ai.hasAssaulted
    assert send(ai, "reset") is None
    assert ai.action_queue == [] and ai.doSetup
    # The separate K33 test covers best_action_list, which reset does not clear.


@pytest.mark.parametrize("method", ["attack", "counterattack", "assault-fire", "assault-counter", "assault-move", "pending"])
def test_recursive_tactics_finish_and_return_legal_order(method, tmp_path):
    result = run_python(f'''
from copy import deepcopy
import math
from tests.support.imports import server_imports
from tests.support.ai_contract import prepare, apply_reply
from tests.support.builders import make_map, make_scenario, make_state, make_unit
with server_imports():
    from game import Game
    params = make_scenario(make_map(rows=3, cols=1), [make_unit(), make_unit("E", "red", hex="hex-0-1", can_move=False)], max_phases=8)
    game = Game(params)
    state = game.initial_state()
    ai = prepare("simon_says", "blue", params, state)
    method = {method!r}
    if method in ("counterattack", "assault-counter"):
        state = game.transition(state, {{"type": "pass"}})
    before = deepcopy(state)
    group = {{"blue A"}}
    if method == "attack":
        actions, score = ai.getBestBattlegroupAttackActions(game, state, group)
    elif method == "counterattack":
        actions, score = ai.getWorstCaseCounterAttackActions(game, state, group, 100, 0)
    elif method == "assault-fire":
        actions, score = ai.getBestAssaultGroupAttackActions(game, state, group, 0)
    elif method == "assault-counter":
        actions, score = ai.getWorstCaseAttackActionsOnAssaultGroup(game, state, group, 0, 100)
    elif method == "assault-move":
        params["units"][1]["hex"] = "hex-0-2"
        game = Game(params)
        state = game.initial_state()
        before = deepcopy(state)
        ai = prepare("simon_says", "blue", params, state)
        actions, score = ai.getBestAssaultGroupAssaultActions(game, state, group, {{"hex-0-1"}})
    else:
        actions = ai.getPendingUnitsNextActions(game, state)
        score = 0
    assert math.isfinite(score)
    assert state == before
    assert len(actions) <= 2
    if method in ("counterattack", "assault-counter"):
        assert actions == [{{"type": "fire", "source": "red E", "target": "blue A"}}]
    if method == "assault-fire":
        assert actions == [{{"type": "fire", "source": "blue A", "target": "red E"}}]
    if method == "pending":
        assert actions
    for action in reversed(actions):
        state = apply_reply(game, state, {{"type": "action", "action": action}})
    print('bounded tactic verified')
''', cwd=tmp_path, timeout=10)
    assert "bounded tactic verified" in result.stdout


def test_three_unit_pending_plan_applies_in_order(tmp_path):
    result = run_python('''
from copy import deepcopy
from tests.support.imports import server_imports
from tests.support.ai_contract import prepare, apply_reply
from tests.support.builders import make_map, make_scenario, make_unit
with server_imports():
    from game import Game
    params = make_scenario(make_map(rows=3, cols=1), [make_unit(),
        make_unit("B", hex="hex-0-2"), make_unit("E", "red", hex="hex-0-1", can_move=False)], max_phases=8)
    game = Game(params)
    state = game.initial_state()
    before = deepcopy(state)
    ai = prepare("simon_says", "blue", params, state)
    actions = ai.getPendingUnitsNextActions(game, state)
    assert 1 <= len(actions) <= 2
    assert state == before
    for action in reversed(actions):
        state = apply_reply(game, state, {"type": "action", "action": action})
    print('three-unit plan verified')
''', cwd=tmp_path, timeout=10)
    assert "three-unit plan verified" in result.stdout
