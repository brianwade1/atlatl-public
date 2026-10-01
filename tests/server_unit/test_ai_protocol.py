"""Registry protocol contracts; actions are checked against the real engine."""

from copy import deepcopy
import ast
import pytest

from tests.support.ai_contract import ALIASES, CALLBACK, MCTS, NEURAL, construct, send, scenario, apply_reply
from tests.support.imports import SERVER_DIR
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.core, pytest.mark.unit]


def test_registry_matrix_is_complete(engine_globals):
    registry = engine_globals["airegistry"].ai_registry
    assert set(registry) == set(ALIASES + CALLBACK + MCTS)
    tree = ast.parse((SERVER_DIR / "airegistry.py").read_text())
    optional = {node.targets[0].slice.value for node in ast.walk(tree)
                if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript)
                and isinstance(node.targets[0].value, ast.Name)
                and node.targets[0].value.id == "ai_registry"}
    assert optional == set(NEURAL)


@pytest.mark.parametrize("alias", ALIASES + MCTS)
@pytest.mark.parametrize("role", ["blue", "red"])
def test_parameters_off_turn_terminal_and_replacement(alias, role, engine_globals, game_factory):
    params = scenario()
    agent = construct(alias, role, params)
    game = game_factory(params)
    obs = game.observation(game.initial_state(), role)
    obs["status"]["onMove"] = "red" if role == "blue" else "blue"
    assert send(agent, "observation", observation=obs) is None
    obs["status"].update(onMove=role, isTerminal=True)
    assert send(agent, "observation", observation=obs) is None
    assert send(agent, "reset") is None
    new = scenario()
    new["units"][0]["longName"] = "New/1/HQ"
    reply = send(agent, "parameters", parameters=new)
    assert reply["role"] == role
    if getattr(agent, "unitData", None) is not None:
        assert "blue New/1/HQ" in agent.unitData.unitIndex
        assert "blue A/1/HQ" not in agent.unitData.unitIndex


@pytest.mark.parametrize("alias", ALIASES)
@pytest.mark.parametrize("role", ["blue", "red"])
def test_on_turn_action_applies(alias, role, engine_globals, game_factory, rng):
    params = scenario(adjacent=True)
    game = game_factory(params)
    state = game.initial_state()
    if role == "red":
        state = game.transition(state, {"type": "pass"})
    agent = construct(alias, role, params)
    reply = send(agent, "observation", observation=game.observation(state, role))
    apply_reply(game, state, reply)


def test_base_hook_and_lifo_queue(engine_imports, game_factory):
    from ai.base import AI
    class Planned(AI):
        def scenario_available(self):
            self.hooked = self.game.parameters()
        def findBestActions(self, game, state):
            self.calls = getattr(self, "calls", 0) + 1
            return [{"type": "pass"}, {"type": "move", "mover": "blue A/1/HQ", "destination": "hex-0-1"}]
    params = scenario()
    agent = Planned("blue")
    send(agent, "parameters", parameters=params)
    assert agent.hooked == params
    game = game_factory(params)
    obs = game.observation(game.initial_state(), "blue")
    assert send(agent, "observation", observation=obs)["action"]["type"] == "move"
    assert send(agent, "observation", observation=obs)["action"] == {"type": "pass"}
    assert agent.calls == 1


@pytest.mark.parametrize("alias,attribute", [
    ("pass-agg-fp", "best_action_list"), ("pass-agg-state", "best_action_list"),
    ("stomp", "best_action_list"), ("simon-says", "best_action_list"), ("pass-agg-setup", "setup_moves"),
    ("pass-agg-setup-fog", "setup_moves"), ("mcts1k", "actionQueue")])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K33: new parameters retain queued actions")
def test_new_parameters_clear_pending_plan(alias, attribute, engine_globals):
    agent = construct(alias, "blue", scenario())
    stale = [{"type": "move", "mover": "blue Old", "destination": "hex-0-1"}]
    setattr(agent, attribute, deepcopy(stale))
    send(agent, "reset")
    send(agent, "parameters", parameters=scenario())
    actual = getattr(agent, attribute)
    if actual == stale:
        raise KnownDefect("K33: exact stale queue survived reset and parameters")
    assert actual == []
