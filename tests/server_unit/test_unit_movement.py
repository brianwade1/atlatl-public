"""S04 movement budgets and geometric fire targets with independent oracles."""

from math import inf

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]


def assert_destinations(actor, board, data, expected):
    for targets in (actor.findMoveTargets(board, data),
                    actor._findMoveTargets(actor.hex, actor.type, board, data)):
        ids = [cell.id for cell in targets]
        assert set(ids) == set(expected)
        assert len(ids) == len(set(ids))
        assert actor.hex.id not in ids
        assert all(cell is board.hexIndex[cell.id] for cell in targets)


@pytest.mark.parametrize("kind,expected", [
    ("infantry", {"hex-0-1"}),
    ("armor", {"hex-0-1", "hex-0-2"}),
    ("mechinf", {"hex-0-1", "hex-0-2"}),
    ("artillery", {"hex-0-1", "hex-0-2"}),
])
def test_clear_corridor(unit_world, make_unit, movement_corridors, kind, expected):
    _, board, data = unit_world([make_unit(unit_type=kind)],
                                map_input=movement_corridors["line"])
    assert_destinations(data.units()[0], board, data, expected)


@pytest.mark.parametrize("kind", ["infantry", "armor", "mechinf", "artillery"])
@pytest.mark.parametrize("terrain", ["rough", "urban", "marsh", "water", "unused"])
def test_terrain_entry_budget(unit_world, make_unit, kind, terrain):
    _, board, data = unit_world([make_unit(unit_type=kind)], rows=4, cols=1,
                                terrain_overrides={(0, 1): terrain})
    impassable = terrain in {"water", "unused"} or (kind == "artillery" and terrain == "marsh")
    assert_destinations(data.units()[0], board, data, [] if impassable else ["hex-0-1"])


def test_clear_then_rough_exceeds_budget(unit_world, make_unit):
    _, board, data = unit_world([make_unit(unit_type="armor")], rows=4, cols=1,
                                terrain_overrides={(0, 2): "rough"})
    assert_destinations(data.units()[0], board, data, ["hex-0-1"])


@pytest.mark.parametrize("faction", ["blue", "red"])
@pytest.mark.parametrize("blocked,expected", [(1, []), (2, ["hex-0-1"])])
def test_occupied_intermediate_and_destination(unit_world, make_unit, faction, blocked, expected):
    _, board, data = unit_world([
        make_unit(unit_type="armor"),
        make_unit(name="block", faction=faction, hex=f"hex-0-{blocked}")], rows=4, cols=1)
    assert_destinations(data.units()[0], board, data, expected)


def test_stacking_capacity_allows_traversal(unit_world, make_unit, monkeypatch):
    _, board, data = unit_world([make_unit(unit_type="armor"),
                                make_unit(name="B", hex="hex-0-1")], rows=4, cols=1)
    monkeypatch.setattr(import_server("mobility"), "stackingLimit", 2)
    assert_destinations(data.units()[0], board, data, ["hex-0-1", "hex-0-2"])


def test_single_hex_has_no_destination(unit_world, make_unit):
    _, board, data = unit_world([make_unit(unit_type="armor")], rows=1, cols=1)
    assert_destinations(data.units()[0], board, data, [])


# Hand-drawn 2-column, 3-row map. Bellman-Ford relaxation deliberately uses
# neither production neighbors nor its FIFO/first-visit movement search.
ADJACENCY = {
    "hex-0-0": ("hex-1-0", "hex-0-1"),
    "hex-1-0": ("hex-0-0", "hex-0-1", "hex-1-1"),
    "hex-0-1": ("hex-0-0", "hex-1-0", "hex-1-1", "hex-0-2"),
    "hex-1-1": ("hex-1-0", "hex-0-1", "hex-0-2", "hex-1-2"),
    "hex-0-2": ("hex-0-1", "hex-1-1", "hex-1-2"),
    "hex-1-2": ("hex-1-1", "hex-0-2"),
}


def shortest_costs(entry_cost, blocked):
    distances = dict.fromkeys(ADJACENCY, inf)
    distances["hex-0-0"] = 0
    for _ in range(len(ADJACENCY) - 1):
        for origin, neighbors in ADJACENCY.items():
            for target in neighbors:
                if target not in blocked:
                    distances[target] = min(distances[target],
                                            distances[origin] + entry_cost[target])
    return distances


@pytest.mark.parametrize("obstacle", ["occupied", "rough", "water"])
def test_alternative_route_against_shortest_paths(unit_world, make_unit,
                                                  movement_corridors, obstacle):
    portable = movement_corridors["alternative"]
    sources = [make_unit(unit_type="armor")]
    blocked = {"hex-0-1"} if obstacle == "occupied" else set()
    costs = dict.fromkeys(ADJACENCY, 50)
    if blocked:
        sources.append(make_unit(name="block", hex="hex-0-1"))
    else:
        for cell in portable["hexes"]:
            if (cell["x_offset"], cell["y_offset"]) == (0, 1):
                cell["terrain"] = obstacle
        costs["hex-0-1"] = 100 if obstacle == "rough" else inf
    distances = shortest_costs(costs, blocked)
    expected = {"hex-1-0", "hex-1-1"}
    if obstacle == "rough":
        expected.add("hex-0-1")
    assert {cell for cell, cost in distances.items() if 0 < cost <= 100} == expected
    _, board, data = unit_world(sources, map_input=portable)
    assert_destinations(data.units()[0], board, data, expected)


@pytest.mark.parametrize("column", [0, 1], ids=["even", "odd"])
@pytest.mark.parametrize("kind,radius", [("infantry", 1), ("armor", 1),
                                        ("mechinf", 1), ("artillery", 2)])
def test_fire_range_and_target_filters(unit_world, make_unit, column, kind, radius):
    sources = [make_unit(unit_type=kind, hex=f"hex-{column}-0", can_move=False),
               make_unit(name="edge", faction="red", hex=f"hex-{column}-{radius}"),
               make_unit(name="outside", faction="red", hex=f"hex-{column}-{radius+1}"),
               make_unit(name="friendly", hex=f"hex-{column}-1"),
               make_unit(name="ineffective", faction="red", hex=f"hex-{column}-1", ineffective=True),
               make_unit(name="unplaced", faction="red", hex=None)]
    _, _, data = unit_world(sources, rows=4, cols=2)
    actor = data.units()[0]
    assert actor.findFireTargets(data) == [data.unitIndex["red edge"]]
    # Detection and canMove are not eligibility filters in this helper.
    assert not actor.canMove
    assert not data.unitIndex["red edge"].detected


@pytest.mark.parametrize("column", [0, 1], ids=["even", "odd"])
@pytest.mark.parametrize("radius,expected", [(1.7, []), (1.75, ["red A"])])
def test_fire_uses_euclidean_distance(unit_world, make_unit, monkeypatch, column, radius, expected):
    _, _, data = unit_world([
        make_unit(hex=f"hex-{column}-0"),
        make_unit(faction="red", hex=f"hex-{column+2}-0")], rows=1, cols=4)
    # Two horizontal columns are sqrt(3) apart in gridDistance, but two hex steps.
    monkeypatch.setitem(import_server("combat").range, "infantry", radius)
    assert [u.uniqueId for u in data.units()[0].findFireTargets(data)] == expected
