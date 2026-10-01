"""Explicit S14 registry selection and engine-backed protocol assertions."""

from copy import deepcopy
import importlib
import json

from tests.support.builders import make_map, make_scenario, make_unit


ALIASES = (
    "passive random shootback field pass-agg pass-agg-fp pass-agg-fog "
    "pass-agg-setup pass-agg-setup-fog dijkstra pass-agg-pseudo-q pass-agg-state "
    "stomp-scoring simon-says simple-assault simple-disengage simple-encircle "
    "simple-fire-coordination simple-movement burt-reynolds-lab2 burtplus stomp "
    "stomp-pp pass agg hierarchy-template hierarchy-random-commander "
    "hierarchy-ignore-commander deep-hierarchy setup-demo"
).split()
MCTS = ["mcts1k", "mcts10k", "mctsd"]
CALLBACK = ("gym gymx2 gym12 gym13 gym14 gym16 gym18 multigym multi-ai-rl "
            "multi-ai-rl-ppo").split()
NEURAL = ("neural cnn hex12 hex13 hex14 hex14dqn hex18dqn mando-fun-lab3 "
          "alphazero dlalphabeta state-eval-gpu state-eval-gpu-pp pascal "
          "ibarra-m3 ibarra-lx3").split()


def send(agent, kind, **payload):
    reply = agent.process(json.dumps({"type": kind, **payload}))
    return None if reply is None else json.loads(reply)


def scenario(*, setup=False, adjacent=False):
    board = make_map(rows=3, cols=4, terrain_overrides={(1, 1): "urban"},
                     setup_overrides=({(0, 0): "setup-type-blue",
                                       (0, 1): "setup-type-blue",
                                       (3, 1): "setup-type-red",
                                       (3, 2): "setup-type-red"} if setup else {}))
    return make_scenario(board, [make_unit("A/1/HQ"), make_unit(
        "B/2/HQ", "red", hex="hex-1-0" if adjacent else "hex-3-2")],
        max_phases=4, city_score=5)


def construct(alias, role, parameters):
    registry = importlib.import_module("airegistry").ai_registry
    cls, options = registry[alias]
    options = deepcopy(options)
    if alias in MCTS:
        options.update(max_rollouts=8, debug=False)
    agent = cls(role, options)
    response = send(agent, "parameters", parameters=parameters)
    assert response["type"] == "role-request"
    assert response["role"] == role
    return agent


def apply_reply(game, state, reply):
    assert reply["type"] == "action"
    action = reply["action"]
    if action["type"] != "pass":
        actor_id = action.get("mover", action.get("source"))
        actor = next(u for u in state["units"] if u["faction"] + " " + u["longName"] == actor_id)
        assert actor["faction"] == state["status"]["onMove"], (state, reply)
        if not state["status"]["setupMode"]:
            assert actor["canMove"] and not actor["ineffective"], (state, reply)
    validator = game._is_legal_setup if state["status"]["setupMode"] else game._is_legal_move
    assert validator(state, action), (state, reply)
    before = deepcopy(state)
    successor = game.transition(state, action)
    assert state == before, "AI action application mutated its input"
    assert successor != state, (state, reply)
    return successor


def prepare(module, role, parameters, state, options=None):
    """Real model hydration for focused decision tests, without invoking decisions."""
    agent = importlib.import_module("ai." + module).AI(role, options or {})
    send(agent, "parameters", parameters=parameters)
    import status
    import unit
    agent.unitData = unit.UnitData()
    unit.fromPortable(state["units"], agent.unitData, agent.mapData)
    agent.statusData = status.Status.fromPortable(state["status"], parameters, agent.mapData)
    return agent
