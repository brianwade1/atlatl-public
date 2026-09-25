"""S03 portable contracts and narrowly matched K01/K02 reproductions."""

from copy import deepcopy
import json

import pytest

from tests.support.imports import import_server
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.fixture
def geometry(engine_imports):
    return import_server("map")


def test_hex_and_edge_portable_fields(geometry):
    data = geometry.MapData()
    cell = geometry.Hex(0, 0, "urban", data)
    cell.setup = "setup-type-red"
    expected = {
        "x_offset": 0, "y_offset": 0, "x_grid": 2, "y_grid": 2,
        "terrain": "urban", "setup": "setup-type-red",
        "edges": ["edge-1-1-3-1", "edge-3-1-4-2", "edge-4-2-3-3",
                  "edge-3-3-1-3", "edge-1-3-0-2", "edge-0-2-1-1"],
    }
    assert cell.id == "hex-0-0"
    assert cell.portableCopy() == expected
    assert json.loads(json.dumps(cell.portableCopy())) == expected
    edge = cell.edges[0]
    edge.type = "river"
    assert edge.toPortable() == {
        "id": "edge-1-1-3-1", "xa_grid": 1, "ya_grid": 1,
        "xb_grid": 3, "yb_grid": 1, "type": "river",
    }
    portable = cell.portableCopy()
    portable["edges"].clear()
    portable["terrain"] = "water"
    edge_copy = edge.toPortable()
    edge_copy["type"] = "normal"
    assert cell.portableCopy() == expected
    assert edge.type == "river"


def test_generic_loaders_recompute_geometry_and_reuse_forward_edges(geometry):
    data = geometry.MapData()
    edge_input = {"id": "ignored", "xa_grid": 1, "ya_grid": 1,
                  "xb_grid": 3, "yb_grid": 1, "type": "river"}
    cell_input = {"x_offset": 0, "y_offset": 0, "terrain": "rough",
                  "setup": "setup-type-blue", "x_grid": 999, "y_grid": 999,
                  "edges": ["ignored"]}
    before = deepcopy((edge_input, cell_input))
    edge = geometry.edgeFromGenericObject(edge_input, data)
    cell = geometry.hexFromGenericObject(cell_input, data)
    assert (edge_input, cell_input) == before
    assert data.hexIndex["hex-0-0"] is cell
    assert (cell.x_grid, cell.y_grid) == (2, 2)
    assert (cell.terrain, cell.setup) == ("rough", "setup-type-blue")
    assert cell.edges[0] is edge is data.edgeIndex["edge-1-1-3-1"]
    assert geometry.getEdgeFromEndpoints({"x": 1, "y": 1}, {"x": 3, "y": 1}, data) is edge
    assert geometry.getEdgeFromEndpoints({"x": 99, "y": 99}, {"x": 100, "y": 99}, data) is None


@pytest.mark.parametrize("rows,cols", [(0, 0), (1, 1), (2, 3)], ids=["empty", "single", "rectangle"])
def test_json_round_trip(geometry, make_map, rows, cols):
    source = make_map(rows, cols, terrain_overrides={(0, 0): "urban", (1, 0): "marsh"},
                      setup_overrides={(0, 0): "setup-type-blue", (2, 1): "setup-type-red"})
    before = deepcopy(source)
    data = geometry.MapData()
    geometry.fromPortable(source, data)
    portable = data.toPortable()
    assert source == before
    assert set(portable) == {"hexes", "edges", "paths"}
    assert portable["paths"] == []
    fields = ("x_offset", "y_offset", "x_grid", "y_grid", "terrain", "setup")
    assert [{k: h[k] for k in fields} for h in portable["hexes"]] == [
        {k: h[k] for k in fields} for h in source["hexes"]]
    edge_ids = {e["id"] for e in portable["edges"]}
    assert all(len(h["edges"]) == 6 and set(h["edges"]) <= edge_ids for h in portable["hexes"])
    assert json.loads(data.toString()) == portable
    restored = geometry.MapData()
    geometry.fromPortable(json.loads(data.toString()), restored)
    assert restored.toPortable() == portable
    assert restored.getDimensions() == {"width": cols, "height": rows}
    portable["hexes"].clear()
    portable["edges"].clear()
    assert len(data.hexIndex) == rows * cols
    assert data.toPortable() == restored.toPortable()


def test_reload_replaces_hex_and_edge_indexes(geometry, make_map):
    data = geometry.MapData()
    geometry.fromPortable(make_map(3, 4), data)
    old_cell = data.hexIndex["hex-0-0"]
    old_edge = data.edgeIndex["edge-1-1-3-1"]
    small = make_map(1, 1, terrain_overrides={(0, 0): "water"})
    geometry.fromPortable(small, data)
    assert data.toPortable() == small
    assert data.hexIndex["hex-0-0"] is not old_cell
    assert data.edgeIndex["edge-1-1-3-1"] is not old_edge
    assert data.getDimensions() == {"width": 1, "height": 1}


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K01: reverse endpoint lookup misses an existing edge")
def test_reverse_endpoint_lookup(geometry):
    data = geometry.MapData()
    edge = geometry.Edge(1, 1, 3, 1, "river", data)
    actual = geometry.getEdgeFromEndpoints({"x": 3, "y": 1}, {"x": 1, "y": 1}, data)
    if actual is None and list(data.edgeIndex.values()) == [edge]:
        raise KnownDefect("K01: reverse lookup returns None for edge-1-1-3-1")
    assert actual is edge


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K01: adjacent hexes duplicate their shared edge")
def test_adjacent_hexes_share_edge_identity(geometry):
    data = geometry.MapData()
    a = geometry.Hex(0, 0, "clear", data)
    b = geometry.Hex(0, 1, "clear", data)
    if (a.edges[3] is not b.edges[0] and len(data.edgeIndex) == 12
            and a.edges[3].id == "edge-3-3-1-3" and b.edges[0].id == "edge-1-3-3-3"):
        raise KnownDefect("K01: reversed shared edge stored twice; 12 edges instead of 11")
    assert a.edges[3] is b.edges[0]
    assert len(data.edgeIndex) == 11


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K01: Path.portableCopy assigns attributes on a dict")
def test_path_portable_copy(geometry):
    data = geometry.MapData()
    data.createHexGrid(2, 1)
    a, b = list(data.hexes())
    path = geometry.Path(a, b, "road", data)
    assert data.pathIndex[path.id] is path
    assert path.hexA is a and path.hexB is b
    expected = {"id": "path-hex-0-0-hex-0-1", "hexA": "hex-0-0", "hexB": "hex-0-1", "type": "road"}
    try:
        actual = path.portableCopy()
    except AttributeError as exc:
        if str(exc) in (
            "'dict' object has no attribute 'id'",
            "'dict' object has no attribute 'id' and no __dict__ for setting new attributes",
        ):
            raise KnownDefect("K01: Path.portableCopy fails on copy.id") from exc
        raise
    assert actual == expected
    assert json.loads(data.toString())["paths"] == [expected]


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K01: fromPortable ignores paths")
def test_path_loading(geometry, make_map):
    source = make_map(2, 1)
    source["paths"] = [{"id": "path-hex-0-0-hex-0-1", "hexA": "hex-0-0",
                        "hexB": "hex-0-1", "type": "road"}]
    data = geometry.MapData()
    geometry.fromPortable(source, data)
    if data.pathIndex == {} and all(h.paths == [None] * 6 for h in data.hexes()):
        raise KnownDefect("K01: populated portable paths load as empty index and empty hex slots")
    path = data.pathIndex["path-hex-0-0-hex-0-1"]
    assert path.type == "road"
    assert path.hexA is data.hexIndex["hex-0-0"]
    assert path.hexB is data.hexIndex["hex-0-1"]
    assert path.hexA.paths[3] is path.hexB.paths[0] is path


@pytest.mark.parametrize("size", [(1, 1), (0, 0)], ids=["smaller", "empty"])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K02: loading does not invalidate cached dimensions")
def test_reload_refreshes_cached_dimensions(geometry, make_map, size):
    data = geometry.MapData()
    geometry.fromPortable(make_map(3, 4), data)
    assert data.getDimensions() == {"width": 4, "height": 3}
    rows, cols = size
    geometry.fromPortable(make_map(rows, cols), data)
    assert len(data.hexIndex) == rows * cols
    actual = data.getDimensions()
    if actual == {"width": 4, "height": 3}:
        raise KnownDefect("K02: dimensions remain 4x3 after smaller/empty load")
    assert actual == {"width": cols, "height": rows}


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K02: repeated grid creation retains old hexes")
def test_create_grid_replaces_old_hexes(geometry):
    data = geometry.MapData()
    data.createHexGrid(2, 2)
    data.createHexGrid(1, 1)
    if set(data.hexIndex) == {"hex-0-0", "hex-1-0", "hex-0-1", "hex-1-1"} and len(data.edgeIndex) == 6:
        raise KnownDefect("K02: smaller grid retains four hexes but resets edges to six")
    assert list(data.hexIndex) == ["hex-0-0"]
    assert data.getDimensions() == {"width": 1, "height": 1}


@pytest.mark.parametrize("operation", ["load", "grid"])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K02: map replacement retains stale paths")
def test_replacement_clears_paths(geometry, make_map, operation):
    data = geometry.MapData()
    data.createHexGrid(2, 1)
    a, b = list(data.hexes())
    path = geometry.Path(a, b, "road", data)
    if operation == "load":
        geometry.fromPortable(make_map(1, 1), data)
    else:
        data.createHexGrid(1, 1)
    if data.pathIndex == {path.id: path} and path.hexA is a and data.hexIndex[a.id] is not a:
        raise KnownDefect("K02: path index retains a path referencing the replaced hex object")
    assert data.pathIndex == {}
