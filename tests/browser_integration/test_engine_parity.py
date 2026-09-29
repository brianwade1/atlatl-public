"""Both real implementations must satisfy independently specified JSON oracles."""

import math

import pytest

from tests.support.builders import load_fixture
from tests.support.imports import import_server
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.integration]
CONTRACT = load_fixture('browser_contract.json')


def contract_cases(group):
    return [dict(case, map=CONTRACT['maps'][case['map']])
            for case in CONTRACT[group]]


def test_geometry_and_rule_contract(model_page, engine_imports):
    contract = load_fixture('browser_contract.json')
    geometry = import_server('map')
    board = geometry.MapData()
    geometry.fromPortable(contract['geometry']['map'], board)
    actual = model_page.evaluate('''c => {
        GameMap.fromPortable(c.geometry.map);
        return {dimensions: GameMap.getDimensions(),
            cells: c.geometry.oracles.map(o => {
                const h = GameMap.hexIndex[o.id];
                return {id:h.id,center:[h.x_grid,h.y_grid],
                    vertices:h.getPoints().map(p => [p.x,p.y]),
                    neighbors:GameMap.getNeighborHexes(h).map(n => n.id)};
            }), distances: c.distances.map(([args]) => GameMap.gridDistance(...args)),
            cost: JSON.parse(JSON.stringify(Mobility.cost, (k,v) => v === Infinity ? 'impassable' : v)),
            stackingLimit: Mobility.stackingLimit, range: Combat.range};
    }''', contract)
    assert actual['dimensions'] == board.getDimensions() == contract['geometry']['dimensions']
    assert actual['cells'] == contract['geometry']['oracles']
    for oracle in contract['geometry']['oracles']:
        h = board.hexIndex[oracle['id']]
        assert [h.x_grid, h.y_grid] == oracle['center']
        assert [[p['x'],p['y']] for p in h.getPoints(board)] == oracle['vertices']
        assert sorted(n.id for n in geometry.getNeighborHexes(h, board)) == sorted(oracle['neighbors'])
    for value, (args, expected) in zip(actual['distances'], contract['distances'], strict=True):
        assert value == pytest.approx(expected)
        assert geometry.gridDistance(*args) == pytest.approx(expected)
    mobility = import_server('mobility')
    costs = {kind: {terrain: 'impassable' if math.isinf(cost) else cost
                    for terrain,cost in row.items()} for kind,row in mobility.cost.items()}
    assert actual['cost'] == costs == contract['cost']
    assert actual['range'] == import_server('combat').range == contract['range']
    assert actual['stackingLimit'] == mobility.stackingLimit == contract['stackingLimit']


@pytest.mark.parametrize('case', contract_cases('movement'), ids=lambda case: case['id'])
def test_move_target_contract(model_page, unit_world, monkeypatch, case):
    _, board, units = unit_world(case['units'], map_input=case['map'])
    monkeypatch.setattr(import_server('mobility'), 'stackingLimit', case.get('stackingLimit', 1))
    expected = sorted(case['expected'])
    assert sorted(h.id for h in units.units()[0].findMoveTargets(board, units)) == expected
    actual = model_page.evaluate('''c => {
        GameMap.fromPortable(c.map); Unit.fromPortable2(c.units);
        for (let i=0;i<c.units.length;i++) Unit.units[i].partialObsUpdate(c.units[i]);
        Mobility.stackingLimit = c.stackingLimit ?? 1;
        const u = Unit.units[0];
        return u.findMoveTargets().map(h => h.id).sort();
    }''', case)
    assert actual == expected


@pytest.mark.parametrize('case', contract_cases('fire'), ids=lambda case: case['id'])
def test_fire_target_contract(model_page, unit_world, case):
    _, _, units = unit_world(case['units'], map_input=case['map'])
    expected = sorted(case['expected'])
    assert sorted(u.uniqueId for u in units.units()[0].findFireTargets(units)) == expected
    actual = model_page.evaluate('''c => {
        GameMap.fromPortable(c.map); Unit.fromPortable2(c.units);
        for (let i=0;i<c.units.length;i++) {
            const obs = c.units[i];
            Unit.units[i].partialObsUpdate({...obs, hex:obs.hex ?? 'fog'});
        }
        return Unit.units[0].findFireTargets().map(u => u.uniqueId).sort();
    }''', case)
    assert actual == expected


def test_semantic_map_unit_serialization(model_page, unit_world, make_map, make_unit):
    source = make_map(rows=1, cols=1, terrain_overrides={(0,0):'urban'},
                      setup_overrides={(0,0):'setup-type-blue'})
    records = [make_unit(strength=71, can_move=True)]
    _, board, units = unit_world(records, map_input=source)
    actual = model_page.evaluate('''({map,units}) => {
        GameMap.fromPortable(map); Unit.fromPortable2(units);
        Unit.units[0].partialObsUpdate(units[0]);
        return {hex:GameMap.toPortable().hexes[0], unit:Unit.toPortable()[0]};
    }''', {'map': source, 'units': records})
    h = board.hexIndex['hex-0-0']
    for field in ['x_offset','y_offset','x_grid','y_grid','terrain','setup']:
        assert actual['hex'][field] == getattr(h, field) == source['hexes'][0][field]
    python_unit = units.units()[0].portableCopy()
    for field in ['type','longName','faction','currentStrength','hex','canMove','ineffective']:
        assert actual['unit'][field] == python_unit[field] == records[0][field]
    assert actual['unit']['uniqueId'] == units.units()[0].uniqueId == 'blue A'
    assert 'echelon' not in python_unit
    assert actual['unit']['echelon'] == 'regiment'


def test_combat_difference_audit_characterization(model_page, engine_imports):
    browser = model_page.evaluate('Combat.firepower')
    server = import_server('combat').firepower
    assert sorted(set(server) - set(browser)) == ['infantry']
    assert not (set(browser) - set(server))
    differences = {f'{a}/{t}': [value,server[a][t]]
        for a,row in browser.items() for t,value in row.items() if value != server[a][t]}
    assert differences == {
        'mechinf/infantry':[1,0.75], 'mechinf/armor':[0.5,0.75],
        'armor/mechinf':[1,0.75], 'armor/armor':[0.5,1],
        'armor/artillery':[1.5,1], 'artillery/mechinf':[1,0.75]}
    # This is an explicit compatibility inventory, not a full-parity requirement.

@pytest.mark.parametrize('vector', [
    pytest.param(v, marks=pytest.mark.xfail(strict=True, raises=KnownDefect,
        reason='K21: negative odd browser columns use signed remainder'))
    if v['offset'][0] in (-1, -3) else v
    for v in CONTRACT['coordinates']
], ids=lambda v: str(v['offset']))
def test_coordinate_conversion_contract(model_page, engine_imports, vector):
    geometry = import_server('map')
    assert list(geometry.offsetToGridCenters(*vector['offset'])) == vector['center']
    actual = model_page.evaluate('''v => {
        const [x,y] = v.offset;
        GameMap.fromPortable({hexes:[{x_offset:x,y_offset:y,terrain:'clear',
            setup:null,edges:[]}],edges:[],paths:[]});
        const h = GameMap.hexFromOffsetCoordinates(x,y);
        return [h.x_grid,h.y_grid];
    }''', vector)
    wrong = {(-1,0): [-1,1], (-3,2): [-7,5]}
    if actual == wrong.get(tuple(vector['offset'])):
        raise KnownDefect('K21: negative odd column center is two grid units too high')
    assert actual == vector['center']
