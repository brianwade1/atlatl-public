"""Small positions with literal distances, priorities and terrain-cost oracles."""

import importlib
import math
import re
import pytest

from tests.support.ai_contract import prepare, send, apply_reply
from tests.support.builders import make_map, make_scenario, make_state, make_unit
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.core, pytest.mark.unit]
POSTURE = ["pass_agg", "burt_reynolds_lab2", "burtplus"]
SHOOT = POSTURE + ["potential_field", "shootback"]
TACTICAL = ["simpleAssault", "simpleDisengage", "simpleEncircle", "simpleFireCoordination", "simpleMovement"]


@pytest.mark.parametrize("module", POSTURE)
@pytest.mark.parametrize("role,blue,red,expected", [
    ("blue", 100, 50, "attack"), ("red", 100, 50, "defense"),
    ("blue", 50, 100, "defense"), ("red", 50, 100, "attack"),
    ("blue", 50, 50, "attack"), ("red", 50, 50, "attack")])
def test_posture(module, role, blue, red, expected, unit_world):
    _, board, units = unit_world([make_unit(strength=blue), make_unit("B", "red", strength=red, hex="hex-3-2"),
                                make_unit("Dead", "red", strength=1000, ineffective=True, hex=None)])
    ai = importlib.import_module("ai." + module).AI(role)
    ai.unitData = units
    assert ai.getPosture() == expected


@pytest.mark.parametrize("mode,expected", [("pass", "defense"), ("agg", "attack")])
def test_forced_posture(mode, expected, unit_world):
    from ai.pass_agg import AI
    ai = AI("blue", {"mode": mode})
    _, _, ai.unitData = unit_world([])
    assert ai.getPosture() == expected


@pytest.mark.parametrize("module", SHOOT)
def test_shoot_first_single_target(module, engine_imports, game_factory, rng):
    params = make_scenario(units=[make_unit(), make_unit("B", "red", hex="hex-0-1")])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare(module, "blue", params, state)
    reply = send(ai, "observation", observation=game.observation(state, "blue"))
    assert reply["action"] == {"type": "fire", "source": "blue A", "target": "red B"}
    apply_reply(game, state, reply)


def test_burtplus_weakest_target(engine_imports, game_factory):
    params = make_scenario(units=[make_unit(hex="hex-1-1"),
        make_unit("Strong", "red", hex="hex-1-0"), make_unit("Weak", "red", strength=40, hex="hex-2-1")])
    game = game_factory(params)
    ai = prepare("burtplus", "blue", params, game.initial_state())
    assert ai.takeBestAction()["action"]["target"] == "red Weak"


@pytest.mark.parametrize("module", SHOOT + ["random_actor"])
def test_no_eligible_unit_passes(module, engine_imports, game_factory):
    params = make_scenario(units=[make_unit(can_move=False), make_unit("Dead", ineffective=True, hex=None)])
    state = make_state(params["units"])
    ai = prepare(module, "blue", params, state)
    method = ai.takeRandomAction if module in ("random_actor", "shootback") else ai.takeBestAction
    assert method()["action"] == {"type": "pass"}


@pytest.mark.parametrize("module", POSTURE + ["potential_field"])
def test_no_enemy_or_city_distance(module, engine_imports, game_factory):
    params = make_scenario(units=[make_unit()])
    ai = prepare(module, "blue", params, make_state(params["units"]))
    actor = ai.unitData.unitIndex["blue A"]
    assert ai.euclideanDistanceToOpfor(actor, actor.hex) == math.inf
    city = ai.euclideanDistanceToOpforCities if module == "potential_field" else ai.euclideanDistanceToCities
    assert city(actor, actor.hex) == math.inf


def test_field_filters_city_faction(engine_imports):
    params = make_scenario(map_data=make_map(terrain_overrides={(0, 0): "urban", (0, 2): "urban"}))
    state = make_state(params["units"], city_owner={"hex-0-0": "blue", "hex-0-2": "red"})
    ai = prepare("potential_field", "blue", params, state)
    actor = ai.unitData.unitIndex["blue A"]
    assert ai.euclideanDistanceToOpforCities(actor, actor.hex) == 2
    ai.role = "red"
    actor.faction = "red"
    assert ai.euclideanDistanceToOpforCities(actor, actor.hex) == 0


@pytest.mark.parametrize("module", POSTURE + ["potential_field", "pass_agg_setup", "hierarchy_template", "hierarchy"])
@pytest.mark.parametrize("values", [{"a": 0., "b": 2.}, {"a": 1., "b": 1.}, {"a": math.inf, "b": math.inf}])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K35: debug RGB conversion drops hex digits")
def test_debug_colors_are_six_digits(module, values, engine_imports):
    colors = importlib.import_module("ai." + module).AI("blue").colorsFromDists(values)
    assert set(colors) == set(values)
    if all(re.fullmatch(r"#[0-9a-f]{3}", c) for c in colors.values()):
        raise KnownDefect("K35: one digit per channel")
    assert all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in colors.values())


@pytest.mark.parametrize("module", TACTICAL)
@pytest.mark.parametrize("unavailable", ["empty", "exhausted", "ineffective"])
def test_tactical_no_actor(module, unavailable, engine_imports, game_factory):
    units = [] if unavailable == "empty" else [make_unit(can_move=False if unavailable == "exhausted" else True,
                                                       ineffective=unavailable == "ineffective")]
    params = make_scenario(units=units)
    state = make_state(units)
    ai = prepare(module, "blue", params, state)
    assert ai.findNewBestAction(game_factory(params), state) == {"type": "pass"}


@pytest.mark.parametrize("strength,kind", [(74, "pass"), (75, "move"), (76, "move")])
def test_assault_threshold(strength, kind, engine_imports, game_factory):
    params = make_scenario(make_map(rows=4, cols=1), [make_unit(strength=strength), make_unit("B", "red", hex="hex-0-2")])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("simpleAssault", "blue", params, state)
    action = ai.findNewBestAction(game, state)
    assert action["type"] == kind
    if kind == "move":
        assert action["destination"] == "hex-0-1"
    apply_reply(game, state, {"type": "action", "action": action})


def test_disengage_unique_safe_escape(engine_imports, game_factory):
    params = make_scenario(make_map(rows=4, cols=1), [make_unit(hex="hex-0-1"), make_unit("B", "red", hex="hex-0-2")])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("simpleDisengage", "blue", params, state)
    assert ai.findNewBestAction(game, state) == {"type": "move", "mover": "blue A", "destination": "hex-0-0"}


def test_encircle_approaches_without_entering_range(engine_imports, game_factory):
    params = make_scenario(make_map(rows=5, cols=1), [make_unit(), make_unit("B", "red", hex="hex-0-4")])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("simpleEncircle", "blue", params, state)
    assert ai.findNewBestAction(game, state) == {"type": "move", "mover": "blue A", "destination": "hex-0-1"}


@pytest.mark.parametrize("role", ["blue", "red"])
def test_coordinated_fire_prioritizes_limited_shooter(role, engine_imports, game_factory):
    other = "red" if role == "blue" else "blue"
    params = make_scenario(make_map(rows=5, cols=1), [
        make_unit("Limited", role), make_unit("Flexible", role, hex="hex-0-2"),
        make_unit("X", other, hex="hex-0-1", can_move=False), make_unit("Y", other, hex="hex-0-3", can_move=False)])
    state = make_state(params["units"], on_move=role)
    game = game_factory(params)
    ai = prepare("simpleFireCoordination", role, params, state)
    action = ai.findNewBestAction(game, state)
    assert action == {"type": "fire", "source": role + " Limited", "target": other + " X"}
    apply_reply(game, state, {"type": "action", "action": action})


@pytest.mark.parametrize("mode,expected", [("Capture", 1), ("DefendCity", 3), ("Offensive", 3), ("DefendUnits", 4), ("Flee", -3), ("unknown", -1)])
def test_movement_remaining_phase_scores(mode, expected, engine_imports):
    params = make_scenario(make_map(rows=5, cols=1, terrain_overrides={(0, 0): "urban", (0, 2): "urban"}),
        [make_unit(), make_unit("Friend", hex="hex-0-1"), make_unit("B", "red", hex="hex-0-2")], max_phases=8)
    state = make_state(params["units"], phase=3, city_owner={"hex-0-0": "blue", "hex-0-2": "red"})
    ai = prepare("simpleMovement", "blue", params, state)
    actor = ai.unitData.unitIndex["blue A"]
    assert ai.getScore(mode, None, state, actor.hex, actor) == expected


@pytest.mark.parametrize("module", ["dijkstra_demo", "stomp", "stomp_scoring"])
def test_directed_terrain_shortest_paths(module, engine_imports):
    params = make_scenario(make_map(rows=4, cols=1, terrain_overrides={(0, 1): "rough", (0, 3): "water"}), [])
    ai = prepare(module, "blue", params, make_state(), {"search": "fixed"})
    ai.runDijkstra()
    matrices = {"armor": ai.dist_matrix} if module == "dijkstra_demo" else ai.paths
    for kind, matrix in matrices.items():
        clear = 100 if kind == "infantry" else 50
        # Directed entry costs on a four-cell chain; entering water is impossible.
        expected = [[0, 100, 100 + clear, math.inf], [clear, 0, clear, math.inf],
                    [100 + clear, 100, 0, math.inf], [100 + 2 * clear, 100 + clear, clear, 0]]
        for i in range(4):
            for j in range(4):
                assert matrix[ai.arrayIndex[f"hex-0-{i}"], ai.arrayIndex[f"hex-0-{j}"]] == expected[i][j]


@pytest.mark.parametrize("module", ["stomp", "stomp_scoring"])
def test_stomp_score_symmetry_and_empty(module, engine_imports):
    params = make_scenario(make_map(rows=3, cols=1), [make_unit(), make_unit("B", "red", hex="hex-0-2")])
    state = make_state(params["units"])
    ai = prepare(module, "blue", params, state, {"search": "fixed"})
    ai.runDijkstra()
    assert ai.getScore(state) == pytest.approx(0)
    state["units"][1]["currentStrength"] = 40
    assert math.isfinite(ai.getScore(state)) and ai.getScore(state) > 0
    assert ai.getScore(make_state()) == 0


@pytest.mark.parametrize("kind", ["move", "fire"])
def test_random_actor_chooses_only_available_options(kind, engine_imports, game_factory, monkeypatch):
    import ai.random_actor as module
    params = make_scenario(units=[make_unit(), make_unit("B", "red", hex="hex-0-1", can_move=False)])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare("random_actor", "blue", params, state)
    monkeypatch.setattr(module.random, "randint", lambda low, high: low if kind == "move" else high)
    monkeypatch.setattr(module.random, "choice", lambda options: options[-1])
    reply = ai.takeRandomAction()
    assert reply["action"]["type"] == kind
    apply_reply(game, state, reply)


def test_shootback_no_target_and_passive_always_pass(engine_globals, game_factory):
    from tests.support.ai_contract import construct
    game = game_factory()
    state = game.initial_state()
    for alias in ["shootback", "passive"]:
        ai = construct(alias, "blue", game.parameters())
        assert send(ai, "observation", observation=game.observation(state, "blue"))["action"] == {"type": "pass"}


@pytest.mark.parametrize("mode,expected", [("Capture", "hex-0-1"), ("DefendCity", "hex-0-1"), ("Offensive", "hex-0-1")])
def test_movement_chooses_safe_destination(mode, expected, engine_imports, game_factory):
    params = make_scenario(make_map(rows=5, cols=1, terrain_overrides={(0, 2): "urban"}),
        [make_unit(), make_unit("E", "red", hex="hex-0-4", can_move=False)])
    game = game_factory(params)
    state = game.initial_state()
    state["status"]["cityOwner"]["hex-0-2"] = "blue" if mode == "DefendCity" else "red"
    ai = prepare("simpleMovement", "blue", params, state, {"mode": mode})
    action = ai.findNewBestAction(game, state)
    assert action == {"type": "move", "mover": "blue A", "destination": expected}
    # A one-cell corridor with an adjacent enemy offers no safe destination.
    ai.unitData.unitIndex["red E"].setHex(ai.mapData.hexIndex["hex-0-2"], ai.unitData)
    assert ai.findNewBestAction(game, state) == {"type": "pass"}


@pytest.mark.parametrize("module", ["burt_reynolds_lab2", "burtplus"])
def test_burt_friend_distance_includes_self_characterization(module, engine_imports):
    params = make_scenario(make_map(rows=4, cols=1), [make_unit(), make_unit("B", hex="hex-0-3")])
    ai = prepare(module, "blue", params, make_state(params["units"]))
    actor = ai.unitData.units()[0]
    assert ai.euclideanDistanceToFriend(actor, actor.hex) == 0
    assert ai.euclideanDistanceToFriend(actor, ai.mapData.hexIndex["hex-0-1"]) == 1


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K35: mixed infinite color distances produce NaN")
def test_mixed_infinite_debug_distances(engine_imports):
    from ai.pass_agg import AI
    try:
        colors = AI("blue").colorsFromDists({"a": 0., "b": math.inf})
    except ValueError as exc:
        if str(exc) == "cannot convert float NaN to integer":
            raise KnownDefect("K35: infinity minus infinity color hue") from exc
        raise
    assert all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in colors.values())


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K35: Dijkstra debug colors drop RGB digits")
def test_dijkstra_debug_colors(engine_imports):
    params = make_scenario(make_map(rows=3, cols=1, terrain_overrides={(0, 2): "water"}), [])
    ai = prepare("dijkstra_demo", "blue", params, make_state())
    colors = ai.colorsFromDistTo(ai.mapData.hexIndex["hex-0-0"])
    assert set(colors) == {"hex-0-0", "hex-0-1", "hex-0-2"}
    if set(colors.values()) == {"#f88"}:
        raise KnownDefect("K35: unreachable distances produce three-digit red")
    assert all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in colors.values())


@pytest.mark.parametrize("module", TACTICAL[:-1])
def test_tactical_no_enemy_passes(module, engine_imports, game_factory):
    params = make_scenario(units=[make_unit()])
    game = game_factory(params)
    state = game.initial_state()
    ai = prepare(module, "blue", params, state)
    assert ai.findNewBestAction(game, state) == {"type": "pass"}
