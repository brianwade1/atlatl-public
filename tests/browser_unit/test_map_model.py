"""S09 public map models, geometry and same-page replacement."""

import pytest

from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


@pytest.mark.parametrize('mode', ['grid', 'portable', 'string'])
def test_geometry_vectors(model_page, hex_geometry, mode):
    result = model_page.evaluate('''({data, mode}) => {
        if (mode === 'grid') GameMap.createHexGrid(3, 4);
        else if (mode === 'portable') GameMap.fromPortable(data.map);
        else GameMap.fromString(JSON.stringify(data.map));
        return {dimensions: GameMap.getDimensions(), setup: GameMap.hasSetupHex(),
            missing: GameMap.hexFromOffsetCoordinates(99,99) === undefined,
            cells: data.oracles.map(o => {
                const h = GameMap.hexIndex[o.id];
                return {id: h.id, center: [h.x_grid,h.y_grid],
                    vertices: h.getPoints().map(p => [p.x,p.y]),
                    neighbors: GameMap.getNeighborHexes(h).map(n => n.id),
                    lookup: GameMap.hexFromOffsetCoordinates(h.x_offset,h.y_offset) === h};
            })};
    }''', {'data': hex_geometry, 'mode': mode})
    assert result == {'dimensions': hex_geometry['dimensions'], 'setup': False,
                      'missing': True, 'cells': [dict(o, lookup=True) for o in hex_geometry['oracles']]}


@pytest.mark.parametrize('rows,cols', [(0, 0), (1, 1), (2, 4)])
def test_grid_dimensions_and_default(model_page, rows, cols):
    assert model_page.evaluate('''([rows,cols]) => {
        GameMap.createHexGrid(rows,cols);
        return [GameMap.hexes.length, GameMap.getDimensions(),
                GameMap.hexes.every(h => h.terrain === 'clear' && h.setup === null)];
    }''', [rows, cols]) == [rows * cols, {'width': cols, 'height': rows}, True]


def test_semantic_round_trip_and_setup(model_page):
    result = model_page.evaluate('''() => {
        GameMap.createHexGrid(1,1);
        const h = GameMap.hexes[0]; h.setTerrain('urban'); h.setup = 'setup-type-blue';
        h.edges[0].type = 'river';
        const source = GameMap.toPortable(), text = GameMap.toString();
        GameMap.fromString(text);
        return {source, target: GameMap.toPortable(), setup: GameMap.hasSetupHex(),
                indexed: GameMap.hexes[0] === GameMap.hexIndex['hex-0-0'],
                edges: GameMap.hexes[0].edges.every(e => GameMap.edgeIndex[e.id] === e)};
    }''')
    assert result['target'] == result['source']
    assert result['source']['hexes'][0]['terrain'] == 'urban'
    assert result['source']['edges'][0]['type'] == 'river'
    assert result['setup'] and result['indexed'] and result['edges']


def test_malformed_json_preserves_state(model_page):
    assert model_page.evaluate('''() => {
        GameMap.createHexGrid(1,1); const h = GameMap.hexes[0];
        try { GameMap.fromString('{'); } catch(e) {
            return [e.name, GameMap.hexes[0] === h];
        }
    }''') == ['SyntaxError', True]


@pytest.mark.parametrize('reverse', [False, True])
def test_path_lifecycle(model_page, reverse):
    result = model_page.evaluate('''reverse => {
        GameMap.createHexGrid(2,1);
        let [a,b] = GameMap.hexes; if (reverse) [a,b] = [b,a];
        const p = GameMap.addPath(a,b,'road');
        const shared = [a.paths.includes(p), b.paths.includes(p),
            GameMap.pathIndex[p.id] === p];
        const portable = p.portableCopy();
        GameMap.fromString(GameMap.toString());
        [a,b] = [GameMap.hexIndex[a.id], GameMap.hexIndex[b.id]];
        const loaded = GameMap.pathIndex[p.id];
        const restored = [loaded.hexA === a, loaded.hexB === b,
            a.paths.includes(loaded), b.paths.includes(loaded)];
        const replacement = GameMap.addPath(a,b,'path');
        const replaced = GameMap.pathIndex[p.id] === replacement && !a.paths.includes(loaded);
        const removed = GameMap.removePath(b,a) === replacement;
        const absent = GameMap.removePath(a,b) === undefined;
        return {shared, portable, restored, replaced, removed, absent,
            slots: [...a.paths,...b.paths], paths: Object.keys(GameMap.pathIndex)};
    }''', reverse)
    a, b = ('hex-0-1', 'hex-0-0') if reverse else ('hex-0-0', 'hex-0-1')
    assert result == dict(shared=[True]*3,
        portable={'id': f'path-{a}-{b}', 'hexA': a, 'hexB': b, 'type': 'road'},
        restored=[True]*4, replaced=True, removed=True, absent=True,
        slots=[None]*12, paths=[])


def test_nonadjacent_path_characterization(model_page):
    # Unsupported input is accepted with a named "null" array property.
    assert model_page.evaluate('''() => {
        GameMap.createHexGrid(3,1); const [a,,b] = GameMap.hexes;
        const p = GameMap.addPath(a,b,'road');
        const result = [a.paths.null === p, b.paths[3] === p,
            a.paths.filter(Boolean).length, Object.keys(GameMap.pathIndex).length];
        GameMap.removePath(a,b);
        return [...result, a.paths.null === p, b.paths.every(x => x === null),
            Object.keys(GameMap.pathIndex).length];
    }''') == [True, True, 0, 1, True, True, 0]


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K01: reversed shared edges duplicated')
def test_adjacent_hexes_share_reversed_edge(model_page):
    actual = model_page.evaluate('''() => {
        GameMap.createHexGrid(2,1); const [a,b] = GameMap.hexes;
        return [GameMap.edges.length, a.edges[3] === b.edges[0],
                a.edges[3].id, b.edges[0].id];
    }''')
    if actual == [12, False, 'edge-3-3-1-3', 'edge-1-3-3-3']:
        raise KnownDefect('K01: opposite directed edges represent one boundary')
    assert actual[:2] == [11, True]


@pytest.mark.parametrize('empty', [False, True])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K02: browser load retains hex index')
def test_load_replaces_hexes_and_dimensions(model_page, make_map, empty):
    small = make_map(rows=0 if empty else 1, cols=0 if empty else 1)
    actual = model_page.evaluate('''small => {
        GameMap.createHexGrid(3,4); const old = GameMap.hexIndex['hex-3-2'];
        GameMap.getDimensions(); GameMap.fromPortable(small);
        return [GameMap.hexes.length, Object.keys(GameMap.hexIndex).length,
            GameMap.getDimensions(), GameMap.hexIndex['hex-3-2'] === old];
    }''', small)
    count = 0 if empty else 1
    if actual == [count, 12, {'width': 4, 'height': 3}, True]:
        raise KnownDefect('K02: stale hexes retain dimensions after load')
    assert actual == [count, count, {'width': count, 'height': count}, False]


@pytest.mark.parametrize('operation', ['load', 'grid'])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K02: browser replacement retains paths')
def test_replacement_clears_paths(model_page, make_map, operation):
    actual = model_page.evaluate('''({small,operation}) => {
        GameMap.createHexGrid(2,1); const [a,b] = GameMap.hexes;
        const p = GameMap.addPath(a,b,'road'); const oldEdge = a.edges[0];
        if (operation === 'load') GameMap.fromPortable(small); else GameMap.createHexGrid(1,1);
        return [Object.keys(GameMap.pathIndex), GameMap.pathIndex[p.id]?.hexA === a,
            GameMap.hexIndex[a.id] === a, GameMap.edgeIndex[oldEdge.id] === oldEdge,
            GameMap.hexes[0].paths.every(p => p === null)];
    }''', {'small': make_map(rows=1, cols=1), 'operation': operation})
    if actual == [['path-hex-0-0-hex-0-1'], True, False, False, True]:
        raise KnownDefect('K02: path retains detached old endpoint objects')
    assert actual == [[], False, False, False, True]


def test_grid_replaces_hex_and_edge_indexes(model_page):
    assert model_page.evaluate('''() => {
        GameMap.createHexGrid(3,4); const old = GameMap.hexes[0]; const edge = old.edges[0];
        GameMap.createHexGrid(1,1);
        return [Object.keys(GameMap.hexIndex), GameMap.getDimensions(), GameMap.edges.length,
            GameMap.hexes[0] === old, GameMap.edgeIndex[edge.id] === edge];
    }''') == [['hex-0-0'], {'width': 1, 'height': 1}, 6, False, False]

@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K01: reversed path replacement retains original index')
def test_reversed_path_replacement_has_single_identity(model_page):
    actual = model_page.evaluate('''() => {
        GameMap.createHexGrid(2,1); const [a,b] = GameMap.hexes;
        const old = GameMap.addPath(a,b,'road');
        const next = GameMap.addPath(b,a,'path');
        const snapshot = [Object.keys(GameMap.pathIndex).sort(),
            a.paths[3] === next, b.paths[0] === next];
        GameMap.removePath(a,b);
        return [...snapshot, Object.keys(GameMap.pathIndex),
            a.paths[3] === next, b.paths[0] === next];
    }''')
    if actual == [['path-hex-0-0-hex-0-1','path-hex-0-1-hex-0-0'], True, True, [], True, True]:
        raise KnownDefect('K01: removal finds old path and leaves replacement in endpoint slots')
    assert actual == [['path-hex-0-1-hex-0-0'], True, True, [], False, False]


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K01: loaded shared edge loses river type on reversed side')
def test_load_preserves_shared_edge_reference_and_type(model_page, make_map):
    source = make_map(rows=2, cols=1)
    shared_id = source['hexes'][0]['edges'][3]
    next(e for e in source['edges'] if e['id'] == shared_id)['type'] = 'river'
    actual = model_page.evaluate('''source => {
        GameMap.fromPortable(source); const [a,b] = GameMap.hexes;
        return [a.edges[3] === b.edges[0], a.edges[3].type, b.edges[0].type,
                GameMap.edges.length];
    }''', source)
    if actual == [False,'river','normal',12]:
        raise KnownDefect('K01: loader ignores the portable shared-edge ID on reversed side')
    assert actual == [True,'river','river',11]
