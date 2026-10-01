"""Action conversion, scoring boundaries and finite ordered plans."""

from copy import deepcopy
import math
from unittest.mock import Mock
import pytest

from tests.support.ai_contract import prepare, apply_reply, construct
from tests.support.builders import make_map, make_scenario, make_state, make_unit

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("action", [{"type": "pass"}, {"type": "move", "mover": "blue A", "destination": "hex-0-1"},
    {"type": "fire", "source": "blue A", "target": "red B"}])
def test_action_round_trip(action, unit_world):
    from ai.scoring import _to_object, _to_portable
    _, board, data = unit_world([make_unit(), make_unit("B", "red", hex="hex-1-0")])
    original = deepcopy(action)
    objects = _to_object(action, data, board)
    assert _to_portable(objects) == original
    assert action == original
    if action["type"] == "move":
        assert objects["mover"] is data.unitIndex["blue A"]
        assert objects["destination"] is board.hexIndex["hex-0-1"]


def test_wait_is_per_unit_pass_is_phase(engine_imports, game_factory):
    params = make_scenario(units=[make_unit(), make_unit("B", hex="hex-0-1")])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("pass_agg_scoring", "blue", params, state, {"search": "fixed"})
    actor = ai.all_unmoved_units(state)[0]
    assert ai.all_actions(game, state, actor)[0]["type"] == "wait"
    state["units"][1]["canMove"] = False
    assert ai.all_actions(game, state, actor)[0] == {"type": "pass"}
    state["units"][0]["canMove"] = False
    assert ai.all_unmoved_units(state) == []
    assert ai.best_single_unit_action(game, state) == {"type": "pass"}
    assert ai.best_action_any_unit(game, state) == {"type": "pass"}


@pytest.mark.parametrize("is_q", [False, True])
def test_action_score_q_or_successor_boundary(is_q, engine_imports, game_factory):
    params = make_scenario()
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("pass_agg_scoring", "blue", params, state, {"search": "fixed", "score_is_Q": is_q})
    score = Mock(return_value=17)
    ai.score_fn = score
    boundary = Mock(wraps=game)
    action = {"type": "pass"}
    assert ai.action_score(boundary, state, action) == 17
    if is_q:
        boundary.transition.assert_not_called()
        score.assert_called_once_with(boundary, state, action)
    else:
        boundary.transition.assert_called_once_with(state, action)
        assert score.call_args.args[1] == game.transition(state, action)
        assert score.call_args.args[2] is None
    boundary.reset_mock()
    score.reset_mock()
    wait = {"type": "wait", "mover": ai.unitData.units()[0]}
    assert ai.action_score(boundary, state, wait) == 17
    boundary.transition.assert_not_called()
    assert score.call_args.args[1] is state


@pytest.mark.parametrize("method", ["fixed", "random", "greedy", "full"])
@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("is_q", [False, True])
def test_search_methods_legal_sequences_and_isolated_branches(method, role, is_q, engine_imports, game_factory, rng):
    other = "red" if role == "blue" else "blue"
    params = make_scenario(make_map(rows=3, cols=2), [make_unit("A", role), make_unit("B", role, hex="hex-1-0"),
                                                   make_unit("E", other, hex="hex-0-1", can_move=False)])
    game = game_factory(params)
    state = make_state(params["units"], on_move=role)
    before = deepcopy(state)
    ai = prepare("pass_agg_scoring", role, params, state, {"search": method, "score_is_Q": is_q})
    plans = list(ai._legalActionSequences(game, state))
    assert plans
    for final, sequence in plans:
        replayed = state
        for action in sequence:
            replayed = apply_reply(game, replayed, {"type": "action", "action": action})
        assert replayed == final
    actions = ai.findBestActions(game, state)
    assert state == before
    assert actions
    for action in reversed(actions):
        state = apply_reply(game, state, {"type": "action", "action": action})
    assert before == make_state(params["units"], on_move=role)
    # Distinct yielded branches must not share mutable state.
    untouched = deepcopy(plans[1][0])
    plans[0][0]["status"]["score"] = 9999
    assert plans[1][0] == untouched


@pytest.mark.parametrize("alias", ["pass-agg-fp", "stomp", "stomp-pp"])
@pytest.mark.parametrize("role", ["blue", "red"])
def test_full_and_partial_plans_prefer_unique_fire(alias, role, engine_globals, game_factory):
    other = "red" if role == "blue" else "blue"
    params = make_scenario(make_map(rows=2, cols=1), [make_unit("A", role), make_unit("B", other, hex="hex-0-1", strength=10, can_move=False)])
    game = game_factory(params)
    state = make_state(params["units"], on_move=role)
    ai = construct(alias, role, params)
    if alias == "pass-agg-fp":
        actions = ai.findBestActions(game, state)
    else:
        method = ai.findSingleBestAction if alias == "stomp-pp" else ai.findBestActions
        actions, score = method(game, state)
        assert math.isfinite(score)
    assert actions[-1] == {"type": "fire", "source": role + " A", "target": other + " B"}
    for action in reversed(actions):
        state = apply_reply(game, state, {"type": "action", "action": action})


def test_pseudo_q_fire_wait_and_unknown_action(engine_imports, game_factory):
    params = make_scenario(make_map(rows=3, cols=1), [make_unit(), make_unit("B", "red", hex="hex-0-2")])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("pass_agg_scoring", "blue", params, state, {"search": "fixed"})
    actor = ai.unitData.units()[0]
    assert ai.score_pseudo_q(game, state, {"type": "fire"}) == 10
    assert ai.score_pseudo_q(game, state, {"type": "wait", "mover": actor}) == pytest.approx(1 / 3 + .001)
    with pytest.raises(ValueError, match="Unknown action type: nope"):
        ai.score_pseudo_q(game, state, {"type": "nope"})
