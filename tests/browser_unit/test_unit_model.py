"""S09 browser units: model state is real; rendering is a recorded boundary."""

import pytest

from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]

RICH = dict(type='armor', echelon='battalion', name='7', longName='Alpha',
            uniqueId='custom-7', faction='blue', currentStrength=73,
            fullStrength=120, homeOrgId='HQ', taskOrgId='Task',
            hex='hex-0-0', canMove=True, ineffective=True)


def test_constructor_registration_sethex_remove_init(model_page):
    result = model_page.evaluate('''p => {
        GameMap.createHexGrid(2,1);
        const u = new Unit.Unit(p), [a,b] = GameMap.hexes;
        const initial = [Unit.units.length, Unit.unitIndex[p.uniqueId] === u,
                         u.hex, u.canMove, u.ineffective];
        Unit.units.push(u); u.setHex(a); u.setHex(a); u.setHex(b);
        const moved = [Unit.occupancy[a.id].length, Unit.occupancy[b.id].length,
                       Unit.occupancy[b.id][0] === u];
        const portable = Unit.toPortable();
        u.remove(); u.remove();
        const removed = [u.hex, Unit.occupancy[b.id].length,
                         Unit.unitIndex[p.uniqueId] === u, Unit.units.length];
        Unit.init();
        return {initial, moved, portable, removed,
            reset: [Unit.units, Unit.unitIndex, Unit.occupancy]};
    }''', RICH)
    assert result == dict(initial=[0, True, None, False, False],
        moved=[0, 1, True], portable=[dict(RICH, hex='hex-0-1', canMove=False, ineffective=False)],
        removed=[None, 0, True, 1], reset=[[], {}, {}])


@pytest.mark.parametrize('loader', ['fromPortable', 'fromPortable2'])
def test_loader_format_characterization(model_page, loader):
    actual = model_page.evaluate('''({p,loader}) => {
        GameMap.createHexGrid(1,1); Unit[loader]([p], () => {});
        return {portable: Unit.toPortable(), calls: symbolCalls,
            indexed: Unit.unitIndex[Unit.units[0].uniqueId] === Unit.units[0],
            occupied: Unit.occupancy['hex-0-0'][0] === Unit.units[0]};
    }''', {'p': RICH, 'loader': loader})
    expected = dict(RICH, canMove=False, ineffective=False)
    if loader == 'fromPortable2':
        expected.update(echelon='regiment', name='1', uniqueId='blue Alpha',
                        fullStrength=100, homeOrgId=None, taskOrgId=None)
    assert actual == dict(portable=[expected], indexed=True, occupied=True,
        calls=[dict(id=expected['uniqueId'], hex='hex-0-0', handler='function')])


@pytest.mark.parametrize('setup', [False, True])
def test_placeunits_faction_and_no_setup(model_page, setup):
    assert model_page.evaluate('''setup => {
        GameMap.createHexGrid(3,1);
        if (setup) {
            GameMap.hexes[1].setup = 'setup-type-red';
            GameMap.hexes[2].setup = 'setup-type-blue';
        }
        Unit.fromPortable2([{type:'infantry',longName:'B',faction:'blue'},
                            {type:'armor',longName:'R',faction:'red'}]);
        Unit.placeUnits();
        return [Unit.units.map(u => u.hex.id), Object.values(Unit.occupancy).map(v => v.length),
                symbolCalls.length];
    }''', setup) == [['hex-0-2', 'hex-0-1'] if setup else ['hex-0-0', 'hex-0-1'], [1, 1], 0]


@pytest.mark.parametrize('setup', [False, True])
def test_placeunit_exhaustion(model_page, setup):
    assert model_page.evaluate('''setup => {
        GameMap.createHexGrid(1,1); GameMap.hexes[0].setup = 'setup-type-blue';
        const a = new Unit.Unit({uniqueId:'a',faction:'blue'});
        const b = new Unit.Unit({uniqueId:'b',faction:'blue'});
        a.placeUnit(setup);
        try { b.placeUnit(setup); } catch(e) {
            return [String(e), b.hex, Unit.occupancy['hex-0-0'].length];
        }
    }''', setup) == ['No available setup hex for unit', None, 1]


def test_partial_observation_movement_fog_reappearance_removal(model_page):
    actual = model_page.evaluate('''p => {
        GameMap.createHexGrid(2,1); Unit.fromPortable2([p]); const u = Unit.units[0];
        const snapshots = [];
        for (const [hex, strength, canMove, ineffective] of [
            ['hex-0-1',80,true,false], ['fog',70,false,false],
            ['hex-0-0',60,true,false], ['hex-0-0',60,true,false],
            ['hex-0-0',40,false,true]]) {
            u.partialObsUpdate({hex,currentStrength:strength,canMove,ineffective});
            snapshots.push([u.hex?.id ?? null, u.currentStrength,u.canMove,u.ineffective,
                GameMap.hexes.map(h => (Unit.occupancy[h.id] ?? []).map(x => x.uniqueId))]);
        }
        return snapshots;
    }''', dict(RICH, ineffective=False))
    assert actual == [
        ['hex-0-1',80,True,False,[[],['blue Alpha']]],
        [None,70,False,False,[[],[]]],
        ['hex-0-0',60,True,False,[['blue Alpha'],[]]],
        ['hex-0-0',60,True,False,[['blue Alpha'],[]]],
        [None,40,False,True,[[],[]]],
    ]


@pytest.mark.parametrize('loader', ['fromPortable', 'fromPortable2'])
def test_unplaced_load_and_serialization_characterization(model_page, loader):
    # Browser editor export expects placed units; the engine permits null hexes.
    assert model_page.evaluate('''({p,loader}) => {
        Unit[loader]([{...p,hex:null}]);
        try { Unit.toPortable(); } catch(e) {
            return [e.name,e.message,Unit.units[0].hex,symbolCalls.length];
        }
    }''', {'p': RICH, 'loader': loader}) == [
        'TypeError', "Cannot read properties of null (reading 'id')", None, 0]


@pytest.mark.parametrize('loader', ['fromPortable', 'fromPortable2'])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K20: unit reload retains index and occupancy')
def test_repeated_load_replaces_indexes(model_page, loader):
    actual = model_page.evaluate('''({p,loader}) => {
        GameMap.createHexGrid(2,1); Unit[loader]([p]); const old = Unit.units[0];
        Unit[loader]([{...p,uniqueId:'new',longName:'New',hex:'hex-0-1'}]);
        return [Unit.units.length, Object.keys(Unit.unitIndex).sort(),
            Unit.occupancy['hex-0-0'].map(u => u.uniqueId),
            Unit.occupancy['hex-0-1'].map(u => u.uniqueId),
            Unit.unitIndex[old.uniqueId] === old];
    }''', {'p': RICH, 'loader': loader})
    old, new = ('custom-7', 'new') if loader == 'fromPortable' else ('blue Alpha', 'blue New')
    if actual == [1, sorted([old, new]), [old], [new], True]:
        raise KnownDefect('K20: old units remain indexed and block old hexes')
    assert actual == [1, [new], [], [new], False]


@pytest.mark.parametrize('loader', ['fromPortable', 'fromPortable2'])
def test_same_id_reload_duplicates_occupancy_characterization(model_page, loader):
    assert model_page.evaluate('''({p,loader}) => {
        GameMap.createHexGrid(1,1); Unit[loader]([p]); const old = Unit.units[0];
        Unit[loader]([p]); const current = Unit.units[0];
        return [Unit.units.length,Object.keys(Unit.unitIndex).length,
            Unit.unitIndex[current.uniqueId] === current,
            Unit.occupancy['hex-0-0'][0] === old,
            Unit.occupancy['hex-0-0'][1] === current];
    }''', {'p': RICH, 'loader': loader}) == [1, 1, True, True, True]

@pytest.mark.parametrize('loader', ['fromPortable','fromPortable2'])
def test_fog_is_observation_not_loader_input_characterization(model_page, loader):
    assert model_page.evaluate('''({p,loader}) => {
        GameMap.createHexGrid(1,1);
        try { Unit[loader]([{...p,hex:'fog'}]); } catch(e) {
            return [e.name,e.message,symbolCalls.length];
        }
    }''', {'p': RICH,'loader':loader}) == [
        'TypeError', "Cannot read properties of undefined (reading 'id')", 0]
