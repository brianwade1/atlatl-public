"""Setup action legality and fog probability mass on controlled tiny maps."""

import importlib
import math
import re
import pytest

from tests.support.ai_contract import ALIASES, construct, scenario, send, apply_reply, prepare
from tests.support.builders import make_map, make_unit, make_scenario, make_state
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("alias", ALIASES)
@pytest.mark.parametrize("role", ["blue", "red"])
def test_setup_queue_then_pass(alias, role, engine_globals, game_factory, rng):
    params = scenario(setup=True)
    game = game_factory(params)
    state = game.initial_state()
    assert state["status"]["setupMode"]
    if role == "red":
        state = game.transition(state, {"type": "pass"})
    ai = construct(alias, role, params)
    kinds = []
    for _ in range(4):
        reply = send(ai, "observation", observation=game.observation(state, role))
        kinds.append(reply["action"]["type"])
        # Setup exchanges with oneself may be legal no-ops. Validate separately.
        assert game._is_legal_setup(state, reply["action"]), reply
        state = game.transition(state, reply["action"])
        if kinds[-1] == "pass":
            break
    assert kinds[-1] == "pass"
    active = {"pass-agg-setup", "pass-agg-setup-fog", "setup-demo", "simon-says"}
    assert len(kinds) == (2 if alias in active else 1)


@pytest.mark.parametrize("module", ["pass_agg_setup", "pass_agg_setup_fog", "setup_demo"])
@pytest.mark.parametrize("role", ["blue", "red"])
def test_setup_occupied_exchange_and_empty_move(module, role, engine_imports, rng):
    params = make_scenario(make_map(rows=4, cols=1, terrain_overrides={(0, 0): "urban"},
        setup_overrides={(0, 0): "setup-type-" + role, (0, 1): "setup-type-" + role}),
        [make_unit("A", role), make_unit("B", role, hex="hex-0-2"),
         make_unit("Enemy", "red" if role == "blue" else "blue", hex="hex-0-3")])
    state = make_state(params["units"], setup=True, on_move=role, city_owner={"hex-0-0": "neutral"})
    ai = prepare(module, role, params, state)
    if module == "setup_demo":
        queue = ai._setupActions(state["status"]["cityOwner"])
        assert {destination for _, destination in queue} == {"hex-0-0", "hex-0-1"}
        assert ai._hexesToClosestCity(ai.mapData.hexIndex["hex-0-2"], state["status"]["cityOwner"]) == 2
    else:
        queue = ai.getSetupMoves()
        assert queue[0] == {"type": "pass"}
        assert {a["type"] for a in queue[1:]} == {"setup-exchange", "setup-move"}
        assert next(a for a in queue if a["type"] == "setup-exchange")["friendly"] == role + " A"
        assert next(a for a in queue if a["type"] == "setup-move")["destination"] == "hex-0-1"


@pytest.mark.parametrize("module", ["pass_agg_setup", "pass_agg_setup_fog", "setup_demo"])
def test_insufficient_setup_cells_characterization(module, engine_imports):
    params = make_scenario()
    ai = prepare(module, "blue", params, make_state(params["units"], setup=True))
    with pytest.raises(IndexError, match="pop from empty list"):
        ai._setupActions({}) if module == "setup_demo" else ai.getSetupMoves()


def test_setup_demo_new_parameters_rebuild_queue(engine_globals, game_factory):
    params = scenario(setup=True)
    ai = construct("setup-demo", "blue", params)
    ai.action_queue = [("blue Old", "hex-9-9")]
    ai.doSetup = False
    send(ai, "parameters", parameters=params)
    assert ai.action_queue == [] and ai.doSetup
    game = game_factory(params)
    reply = send(ai, "observation", observation=game.observation(game.initial_state(), "blue"))
    assert reply["action"]["mover"] == "blue A/1/HQ"


@pytest.mark.parametrize("module", ["pass_agg_fog", "pass_agg_setup_fog"])
def test_fog_mass_moves_culls_and_normalizes(module, unit_world, monkeypatch):
    import combat
    monkeypatch.setitem(combat.sight, "infantry", 0)
    _, board, units = unit_world([make_unit(), make_unit("B", "red", hex="hex-0-3")], rows=4, cols=1)
    distribution = importlib.import_module("ai." + module).OpforDistrib(.1, board, units, "blue")
    assert distribution.distr == {"hex-0-0": 0., "hex-0-1": 0., "hex-0-2": 0., "hex-0-3": 1.}
    distribution.move(units)
    assert distribution.distr == pytest.approx({"hex-0-0": 0., "hex-0-1": 0., "hex-0-2": .1, "hex-0-3": .9})
    assert sum(distribution.distr.values()) == pytest.approx(1)
    monkeypatch.setitem(combat.sight, "infantry", 2)
    distribution.cull(units)
    assert distribution.sum == pytest.approx(.9)
    assert distribution.getNormalizedDist() == {"hex-0-0": 0., "hex-0-1": 0., "hex-0-2": 0., "hex-0-3": 1.}
    monkeypatch.setitem(combat.sight, "infantry", 10)
    distribution.cull(units)
    assert distribution.sum == 0
    assert set(distribution.getNormalizedDist().values()) == {0}


def test_uniform_enemy_setup_support(unit_world, monkeypatch):
    from ai.pass_agg_setup_fog import OpforDistrib
    import combat
    monkeypatch.setitem(combat.sight, "infantry", 0)
    _, board, units = unit_world([make_unit(), make_unit("B", "red", hex="hex-0-3")], rows=4, cols=1,
        setup_overrides={(0, 2): "setup-type-red", (0, 3): "setup-type-red"})
    dist = OpforDistrib(.1, board, units, "blue")
    dist.set_uniform_dist(board)
    assert dist.getNormalizedDist() == {"hex-0-0": 0., "hex-0-1": 0., "hex-0-2": .5, "hex-0-3": .5}


@pytest.mark.parametrize("module", ["pass_agg_fog", "pass_agg_setup_fog"])
def test_no_enemy_prototype_characterization(module, unit_world):
    _, board, units = unit_world([make_unit()])
    with pytest.raises(AttributeError, match="has no attribute 'opforUnitProto'"):
        importlib.import_module("ai." + module).OpforDistrib(.1, board, units, "blue")


@pytest.mark.parametrize("module", ["pass_agg_fog", "pass_agg_setup_fog"])
@pytest.mark.parametrize("values", [{"a": 0., "b": 1.}, {"a": 1., "b": 1.}, {"a": math.inf, "b": 1.}])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K35: debug RGB conversion drops hex digits")
def test_fog_colors(module, values, engine_imports):
    colors = importlib.import_module("ai." + module).colorsFromDict(values)
    if all(re.fullmatch(r"#[0-9a-f]{3}", color) for color in colors.values()):
        raise KnownDefect("K35: one digit per channel")
    assert all(re.fullmatch(r"#[0-9a-f]{6}", color) for color in colors.values())


@pytest.mark.parametrize("alias", ["pass-agg-fog", "pass-agg-setup-fog"])
def test_fog_parameters_replace_distribution(alias, engine_globals, monkeypatch):
    import combat
    monkeypatch.setitem(combat.sight, "infantry", 0)
    ai = construct(alias, "blue", scenario())
    old = ai.opforDistrib
    ai.lastPhase = 99
    params = make_scenario(make_map(rows=4, cols=1), [make_unit(), make_unit("New", "red", hex="hex-0-3")])
    send(ai, "reset")
    send(ai, "parameters", parameters=params)
    assert ai.opforDistrib is not old
    assert ai.lastPhase == 0
    assert ai.opforDistrib.distr == {"hex-0-0": 0., "hex-0-1": 0., "hex-0-2": 0., "hex-0-3": 1.}


@pytest.mark.parametrize("alias", ["pass-agg-fog", "pass-agg-setup-fog"])
def test_hidden_enemy_observation_legal_action(alias, engine_globals, monkeypatch, game_factory):
    import combat
    monkeypatch.setitem(combat.sight, "infantry", 0)
    params = scenario()
    params["map"]["fogOfWar"] = True
    game = game_factory(params)
    state = game.initial_state()
    obs = game.observation(state, "blue")
    assert obs["units"][1]["hex"] == "fog"
    ai = construct(alias, "blue", params)
    reply = send(ai, "observation", observation=obs)
    apply_reply(game, state, reply)
