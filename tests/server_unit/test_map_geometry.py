"""S03 geometry oracles use explicit coordinates, not engine-derived answers."""

import math

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.fixture
def geometry(engine_imports):
    return import_server("map")


@pytest.mark.parametrize("offset,center,cube", [
    ((0, 0), (2, 2), (0, 0, 0)),
    ((1, 0), (5, 3), (1, 0, -1)),
    ((2, 1), (8, 4), (2, 0, -2)),
    ((3, -2), (11, -1), (3, -3, 0)),
    ((-1, 0), (-1, 3), (-1, 1, 0)),
    ((-2, -1), (-4, 0), (-2, 0, 2)),
    ((-3, 2), (-7, 7), (-3, 4, -1)),
], ids=["origin", "positive-odd", "positive-even", "negative-row",
        "negative-odd", "negative-even", "negative-three"])
def test_coordinate_conversions(geometry, offset, center, cube):
    assert geometry.offsetToGridCenters(*offset) == center
    actual = geometry.offsetToCube(*offset)
    assert actual == cube
    assert sum(actual) == 0
    assert geometry.cubeToOffset(*cube) == offset
    assert geometry.cubeToOffset(*actual) == offset
    assert geometry.offsetToCube(*geometry.cubeToOffset(*cube)) == cube


@pytest.mark.parametrize("column,neighbors", [
    (1, ["hex-1-0", "hex-2-1", "hex-2-2", "hex-1-2", "hex-0-2", "hex-0-1"]),
    (2, ["hex-2-0", "hex-3-0", "hex-3-1", "hex-2-2", "hex-1-1", "hex-1-0"]),
], ids=["odd", "even"])
@pytest.mark.parametrize("direction", range(6), ids=["N", "NE", "SE", "S", "SW", "NW"])
def test_neighbors_and_reciprocal_directions(geometry, column, neighbors, direction):
    data = geometry.MapData()
    data.createHexGrid(3, 4)
    cell = data.hexIndex[f"hex-{column}-1"]
    neighbor = geometry.getNeighborHex(cell, data, direction)
    assert neighbor is data.hexIndex[neighbors[direction]]
    assert geometry.directionFrom(cell, neighbor) == direction
    assert geometry.directionFrom(neighbor, cell) == (direction + 3) % 6
    assert geometry.getNeighborHex(neighbor, data, (direction + 3) % 6) is cell
    assert [h.id for h in geometry.getNeighborHexes(cell, data)] == neighbors
    assert geometry.hexDistance(cell.x_offset, cell.y_offset,
                                neighbor.x_offset, neighbor.y_offset) == 1
    assert geometry.gridDistance(cell.x_grid, cell.y_grid,
                                 neighbor.x_grid, neighbor.y_grid) == pytest.approx(1)


@pytest.mark.parametrize("cell_id,neighbors", [
    ("hex-0-0", [None, None, "hex-1-0", "hex-0-1", None, None]),
    ("hex-1-0", [None, "hex-2-0", "hex-2-1", "hex-1-1", "hex-0-1", "hex-0-0"]),
    ("hex-2-0", [None, None, "hex-3-0", "hex-2-1", "hex-1-0", None]),
    ("hex-3-2", ["hex-3-1", None, None, None, None, "hex-2-2"]),
], ids=["even-corner", "odd-top", "even-top", "odd-corner"])
def test_boundaries(geometry, cell_id, neighbors):
    data = geometry.MapData()
    data.createHexGrid(3, 4)
    cell = data.hexIndex[cell_id]
    actual = [geometry.getNeighborHex(cell, data, d) for d in range(6)]
    assert [h.id if h else None for h in actual] == neighbors
    assert [h.id for h in geometry.getNeighborHexes(cell, data)] == [n for n in neighbors if n]
    assert geometry.directionFrom(cell, cell) is None
    assert geometry.directionFrom(data.hexIndex["hex-0-0"], data.hexIndex["hex-3-2"]) is None


@pytest.mark.parametrize("a,b,grid_a,grid_b,hex_distance,euclidean", [
    ((0, 0), (0, 0), (2, 2), (2, 2), 0, 0),
    ((0, 0), (1, 0), (2, 2), (5, 3), 1, 1),
    ((0, 0), (0, 2), (2, 2), (2, 6), 2, 2),
    ((0, 0), (2, 0), (2, 2), (8, 2), 2, math.sqrt(3)),
    ((-1, 0), (1, 0), (-1, 3), (5, 3), 2, math.sqrt(3)),
], ids=["identity", "adjacent", "straight-two", "bent-two", "negative-to-positive"])
def test_distinct_distance_definitions(geometry, a, b, grid_a, grid_b, hex_distance, euclidean):
    assert geometry.hexDistance(*a, *b) == hex_distance
    assert geometry.hexDistance(*b, *a) == hex_distance
    assert geometry.gridDistance(*grid_a, *grid_b) == pytest.approx(euclidean)
    assert geometry.gridDistance(*grid_b, *grid_a) == pytest.approx(euclidean)


@pytest.mark.parametrize("index", [0, 1, 2], ids=["corner", "odd", "even"])
def test_ordered_vertices(geometry, hex_geometry, index):
    oracle = hex_geometry["oracles"][index]
    data = geometry.MapData()
    data.createHexGrid(3, 4)
    cell = data.hexIndex[oracle["id"]]
    assert [[p["x"], p["y"]] for p in cell.getPoints(data)] == oracle["vertices"]


@pytest.mark.parametrize("rows,cols", [(0, 0), (1, 1), (2, 4)], ids=["empty", "single", "rectangle"])
def test_grid_creation_and_queries(geometry, rows, cols):
    data = geometry.MapData()
    assert list(data.hexes()) == list(data.edges()) == []
    data.createHexGrid(rows, cols)
    assert list(data.hexIndex) == [f"hex-{c}-{r}" for r in range(rows) for c in range(cols)]
    assert list(data.hexes()) == list(data.hexIndex.values())
    assert list(data.edges()) == list(data.edgeIndex.values())
    assert data.getDimensions() == {"width": cols, "height": rows}
    assert data.getCityHexes() == []
    assert not data.hasSetupHexes()
    assert data.getSetupHexes("blue") == []
    for cell in data.hexes():
        assert cell.terrain == "clear" and cell.setup is None
        assert cell.paths == [None] * 6
        assert len(cell.edges) == 6
        assert all(data.edgeIndex[e.id] is e for e in cell.edges)


def test_city_and_faction_filters(geometry):
    data = geometry.MapData()
    data.createHexGrid(2, 3)
    cells = list(data.hexes())
    for cell, terrain in zip(cells, ["clear", "water", "rough", "unused", "marsh", "urban"]):
        cell.terrain = terrain
    cells[0].setup = "setup-type-blue"
    cells[1].setup = "setup-type-red"
    cells[2].setup = "setup-type-blue"
    assert data.getCityHexes() == [cells[5]]
    assert data.hasSetupHexes()
    assert data.getSetupHexes("blue") == [cells[0], cells[2]]
    assert data.getSetupHexes("red") == [cells[1]]
    assert data.getSetupHexes("unknown") == []
