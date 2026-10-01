"""Weighted geometry, faction aggregation and hierarchy debug contracts."""

from copy import deepcopy
import json
import math
import re
import pytest

from tests.support.builders import make_unit
from tests.support.ai_contract import scenario, construct, send, apply_reply
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.core, pytest.mark.unit]


def test_center_of_mass_uses_strength_and_ignores_ineffective(unit_world):
    import abstract_state as module
    _, _, data = unit_world([make_unit(strength=25), make_unit("B", strength=75, hex="hex-2-2"),
                             make_unit("Dead", strength=999, ineffective=True, hex=None)])
    assert module.getCM(data.units()) == pytest.approx((4.5, 3 * math.sqrt(3)))
    assert module.getCM([]) is None
    for unit in data.units():
        unit.currentStrength = 0
    assert module.getCM(data.units()) is None
    for unit in data.units():
        unit.currentStrength, unit.ineffective = 100, True
    assert module.getCM(data.units()) is None


@pytest.mark.parametrize("col,row", [(0, 0), (1, 0), (2, 2), (3, 1)])
@pytest.mark.parametrize("dx,dy", [(0, 0), (.1, .1), (-.1, -.1)])
def test_containing_hex_centers_and_offsets(col, row, dx, dy, engine_imports):
    import abstract_state
    assert abstract_state.getContainingHex((3 * col + dx, (2 * row + col % 2) * math.sqrt(3) + dy)) == (col, row)


def test_containing_hex_across_horizontal_boundary(engine_imports):
    import abstract_state
    boundary = math.sqrt(3)
    assert abstract_state.getContainingHex((0, boundary - 1e-6)) == (0, 0)
    assert abstract_state.getContainingHex((0, boundary + 1e-6)) == (0, 1)
    assert abstract_state.getContainingHex((0, boundary)) == (0, 0)


@pytest.mark.parametrize("role", ["blue", "red"])
def test_grouping_aggregation_and_nonmutation(role, unit_world):
    import abstract_state as module
    other = "red" if role == "blue" else "blue"
    _, board, data = unit_world([make_unit("A/1/HQ", role, strength=25),
        make_unit("B/1/HQ", role, strength=75, hex="hex-0-2"),
        make_unit("C/2/HQ", role, ineffective=True, hex=None),
        make_unit("Enemy", other, hex="hex-3-2")])
    before = [deepcopy(u.portableCopy()) for u in data.units()]
    assert set(module.subUnits(data, role)) == {"1/HQ", "2/HQ"}
    abstract = module.abstractUnitData(data, board, role)
    assert set(abstract.unitIndex) == {role + " 1/HQ", other + " Enemy"}
    aggregate = abstract.unitIndex[role + " 1/HQ"]
    assert aggregate.currentStrength == 100
    assert aggregate.hex.id == "hex-0-1"
    assert aggregate.canMove and not aggregate.ineffective
    assert abstract.unitIndex[other + " Enemy"].portableCopy() == before[3]
    assert abstract.unitIndex[other + " Enemy"] is not data.unitIndex[other + " Enemy"]
    assert [u.portableCopy() for u in data.units()] == before


def test_aggregate_clamps_external_center(unit_world):
    import abstract_state
    _, board, data = unit_world([make_unit("A/1")])
    # An out-of-map geometric center exercises clamping without replacing getCM.
    from types import SimpleNamespace
    data.units()[0].hex = SimpleNamespace(x_offset=100, y_offset=-10)
    result = abstract_state.abstractUnitData(data, board, "blue")
    assert result.units()[0].hex.id == "hex-3-0"


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K37: containing hex chooses wrong odd-column boundary row")
def test_containing_hex_odd_column_right_boundary(engine_imports):
    import abstract_state
    result = abstract_state.getContainingHex((4.5, 3 * math.sqrt(3)))
    if result == (1, 0):
        raise KnownDefect("K37: returned non-containing hex one row above")
    assert result == (1, 1)


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K36: createScenario reads undefined abstate")
def test_create_scenario_uses_argument(unit_world):
    import abstract_state
    _, _, data = unit_world([make_unit()])
    params = scenario()
    try:
        result = abstract_state.createScenario(data, params)
    except NameError as exc:
        if str(exc) == "name 'abstate' is not defined":
            raise KnownDefect("K36: demo-only global") from exc
        raise
    assert json.loads(result)["units"] == data.toPortable()


@pytest.mark.parametrize("module", ["hierarchy", "hierarchy_template"])
def test_boss_and_crowding(module, unit_world):
    import importlib
    _, board, data = unit_world([make_unit("A/1/HQ"), make_unit("B/2/HQ", hex="hex-0-1"),
                                make_unit("Enemy", "red", hex="hex-0-2")])
    ai = importlib.import_module("ai." + module).AI("blue")
    actor = data.units()[0]
    assert ai.bossId(actor) == "blue 1/HQ"
    actor.longName = "HQ"
    assert ai.bossId(actor) == (None if module == "hierarchy" else "blue HQ")
    ai.abstractUnitData = data
    if module == "hierarchy":
        assert ai.crowdingPenalty(actor, actor.hex, 0, data) == 0
        assert ai.crowdingPenalty(actor, actor.hex, 1, data) == 100
        assert ai.crowdingPenalty(actor, actor.hex, 2, data) == 200
        assert ai.euclideanDistanceToCommandHex(actor, actor.hex, data) == 0
    else:
        assert ai.crowdingPenalty(actor, actor.hex) == 200


@pytest.mark.parametrize("alias", ["hierarchy-template", "hierarchy-random-commander", "hierarchy-ignore-commander", "deep-hierarchy"])
def test_hierarchy_real_echelons_and_debug(alias, engine_globals, game_factory, rng):
    params = scenario()
    game = game_factory(params)
    state = game.initial_state()
    ai = construct(alias, "blue", params)
    reply = send(ai, "observation", observation=game.observation(state, "blue"))
    apply_reply(game, state, reply)
    if alias == "deep-hierarchy":
        assert ai.nAbstractEchelons == 2
        assert [set(d.unitIndex) & {"blue HQ", "blue 1/HQ"} for d in ai.abstractUnitData] == [{"blue HQ"}, {"blue 1/HQ"}]
        echelons = reply["debug"]["echelons"]
        assert len(echelons) == 2
        for echelon in echelons:
            assert len(echelon) == 2
            for record in echelon:
                assert set(record) == {"id", "hex", "color"}
                assert record["hex"] in ai.mapData.hexIndex
                assert re.fullmatch(r"#[0-9a-f]{6}", record["color"])
    else:
        assert "blue 1/HQ" in ai.abstractUnitData.unitIndex
        for color in reply.get("debug", {}).get("colors", {}).values():
            assert re.fullmatch(r"#[0-9a-f]{6}", color)
    assert json.loads(json.dumps(reply)) == reply


@pytest.mark.parametrize("module", ["hierarchy", "hierarchy_template"])
def test_command_distance_and_parent_center(module, unit_world):
    import abstract_state
    import importlib
    _, board, data = unit_world([make_unit("A/1/HQ"), make_unit("B/1/HQ", hex="hex-0-2")])
    parents = abstract_state.abstractUnitData(data, board, "blue")
    ai = importlib.import_module("ai." + module).AI("blue")
    actor = data.unitIndex["blue A/1/HQ"]
    assert parents.unitIndex["blue 1/HQ"].hex.id == "hex-0-1"
    if module == "hierarchy":
        assert ai.euclideanDistanceToCommandHex(actor, actor.hex, parents) == 1
        ai.unitData, ai.abstractUnitData = data, [parents]
        assert ai.getUnitData(0) is data
        assert ai.getUnitData(1) is parents
        assert ai.getNAbstractEchelons(data) == 2
        assert ai.getCMs([parents]) == [{"1/HQ": board.hexIndex["hex-0-1"]}]
    else:
        ai.abstractUnitData = parents
        assert ai.euclideanDistanceToCommandHex(actor, actor.hex) == 1


def test_aggregate_strength_includes_ineffective_member_characterization(unit_world):
    import abstract_state
    _, board, data = unit_world([make_unit("A/1", strength=25),
                                make_unit("B/1", strength=10, ineffective=True, hex=None)])
    result = abstract_state.abstractUnitData(data, board, "blue").units()[0]
    assert result.currentStrength == 35
    assert result.hex.id == "hex-0-0"
