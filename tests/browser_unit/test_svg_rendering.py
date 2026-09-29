"""S10 map rendering and factory wiring; controller actions belong to S11/S12."""

import math

import pytest

from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


def test_map_shapes_styles_handlers_markers_and_paths(svg_page):
    r = svg_page.evaluate('''() => {
        GameMap.createHexGrid(2,1); const [a,b]=GameMap.hexes;
        a.terrain='urban'; a.setup='setup-type-blue'; b.terrain='water';
        GameMap.edges[0].type='river'; const path=GameMap.addPath(a,b,'road');
        const s=root(), calls=[];
        MapEditorControl.edgeMouseOver=e=>calls.push(['edge',e.currentTarget.id]);
        SVGMapView.add(param,s,e=>calls.push(['over',e.currentTarget.id]),
            e=>calls.push(['down',e.currentTarget.id]));
        const hex=document.getElementById(a.id), edge=document.getElementById(GameMap.edges[0].id);
        hex.dispatchEvent(new MouseEvent('mouseover')); hex.dispatchEvent(new MouseEvent('mousedown'));
        edge.dispatchEvent(new MouseEvent('mouseover'));
        const pathElem=SVGCreateView.pathIndex[path.id];
        const result={hex:attrs(hex), edge:attrs(edge), path:attrs(pathElem),
            hexbox:box(hex.getBBox()), edgeCount:s.querySelectorAll('[id^="edge-"]').length,
            modelEdges:GameMap.edges.length, calls, pathIndexed:pathElem===document.getElementById(path.id),
            setup:attrs(SVGSetupMarker.setupMarkerIndex[a.id]),
            cities:SVGCityMarker.cityMarkerGroup.children.length};
        SVGUtil.removePath(path); SVGUtil.removePath(path);
        result.removed=!pathElem.isConnected;
        return result;
    }''')
    assert r['hex']['id'] == 'hex-0-0' and r['hex']['fill'] == 'lightgray'
    assert r['hex']['stroke'] == 'transparent'
    assert r['hex']['d'].count('L ') == 6
    assert r['hexbox'] == pytest.approx([10,4+2*math.sqrt(3),8,4*math.sqrt(3)])
    assert r['edge']['stroke'] == 'blue' and r['edge']['stroke-width'] == '0.5'
    assert r['edge']['stroke-linecap'] == 'round' and r['edge']['fill'] == 'transparent'
    assert r['edgeCount'] == r['modelEdges']  # Known duplicate identities are not an ideal-count oracle.
    assert r['path']['id'] == 'path-hex-0-0-hex-0-1'
    nums = r['path']['d'].replace('M','').replace('L','').split()
    assert list(map(float, nums)) == pytest.approx([14,4+4*math.sqrt(3),14,4+8*math.sqrt(3)])
    assert r['path']['stroke'] == 'black' and r['path']['stroke-width'] == '0.2'
    assert r['pathIndexed'] and r['removed']
    assert r['calls'] == [['over','hex-0-0'],['down','hex-0-0'],['edge',r['edge']['id']]]
    assert r['setup']['fill'] == 'blue' and r['cities'] == 2


def test_debug_colors_partial_and_terrain_restoration(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(2,1); GameMap.hexes[1].terrain='rough';
        const colors=()=>GameMap.hexes.map(h=>document.getElementById(h.id).getAttribute('fill'));
        SVGMapView.set_colors({'hex-0-0':'pink','hex-0-1':'cyan'}); const full=colors();
        SVGMapView.set_colors({'hex-0-1':'green',missing:'red'}); const partial=colors();
        SVGMapView.terrain_color(); return [full,partial,colors()];
    }''')
    assert r == [['pink','cyan'],['white','green'],['white','wheat']]


@pytest.mark.parametrize('factory,controller,root_events', [
    ('createMapEditorView','MapEditorControl',['mousedown','mouseup']),
    ('createUnitPlacementView','UnitPlacementControl',['mousedown']),
    ('createPlayView','HumanPlayerControl',['mousedown']),
])
def test_factory_replaces_root_and_wires_events(svg_page, factory, controller, root_events):
    r = svg_page.evaluate('''({factory,controller,rootEvents}) => {
        GameMap.createHexGrid(1,1); const calls=[];
        for(const name of ['MapEditorControl','UnitPlacementControl','HumanPlayerControl'])
            for(const method of ['hexMouseOverHandler','hexMouseDownHandler','svgMouseDownHandler','svgMouseUpHandler'])
                window[name][method]=e=>calls.push([name,method,e.currentTarget.id]);
        SVGCreateView[factory](param); const old=SVGCreateView.svg;
        SVGCreateView[factory](param); const s=SVGCreateView.svg;
        const hex=document.getElementById('hex-0-0');
        hex.dispatchEvent(new MouseEvent('mouseover'));
        hex.dispatchEvent(new MouseEvent('mousedown'));
        for(const type of rootEvents) s.dispatchEvent(new MouseEvent(type));
        return {calls, old:old.isConnected, count:document.querySelectorAll('#mysvg').length,
            rootMatches:s===document.getElementById('mysvg'),
            palette:!!s.querySelector('#setup-type-erase')};
    }''', dict(factory=factory, controller=controller, rootEvents=root_events))
    root_controller = 'MapEditorControl' if factory == 'createMapEditorView' else 'UnitPlacementControl'
    expected = [[controller,'hexMouseOverHandler','hex-0-0'], [controller,'hexMouseDownHandler','hex-0-0']]
    expected += [[root_controller, 'svgMouseDownHandler' if e == 'mousedown' else 'svgMouseUpHandler','mysvg'] for e in root_events]
    assert r == dict(calls=expected, old=False, count=1, rootMatches=True, palette=factory=='createMapEditorView')


def test_palette_items_styles_order_and_callback_wiring(svg_page):
    r = svg_page.evaluate('''() => {
        const calls=[];
        for(const kind of ['Setup','Fill','Edge','Path'])
            MapEditorControl[`palette${kind}MouseDown`]=e=>calls.push([kind,e.currentTarget.id]);
        const s=root(); MapEditorPalette.add(param,s);
        const items=[...s.querySelectorAll('[id]')];
        for(const item of items) item.dispatchEvent(new MouseEvent('mousedown'));
        return {labels:[...s.querySelectorAll('text')].map(e=>e.textContent),
            items:items.map(e=>({id:e.id, pointer:e.style.pointerEvents,
                paint:attrs(e.tagName==='g'?e.firstElementChild:e)})),calls};
    }''')
    ids = ['setup-type-erase','setup-type-blue','setup-type-red']
    ids += ['fill-type-'+v for v in ['clear','water','marsh','rough','urban','unused']]
    ids += ['edge-type-normal','edge-type-stream','edge-type-river','path-type-erase','edge-type-road','edge-type-path']
    assert r['labels'] == ['Setup','Fills','Edges','Paths']
    assert [i['id'] for i in r['items']] == ids  # K10 current path IDs; desired contract below.
    assert all(i['pointer']=='all' for i in r['items'])
    assert [i['paint']['fill'] for i in r['items'][3:9]] == ['white','powderblue','palegreen','wheat','lightgray','gray']
    assert [i['paint']['stroke'] for i in r['items'][9:12]] == ['black','blue','blue']
    assert r['calls'] == [[kind,id_] for kind,id_ in zip(['Setup']*3+['Fill']*6+['Edge']*3+['Path']*3,ids)]


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K10: rendered path palette uses edge IDs')
def test_palette_path_identifiers(svg_page):
    r = svg_page.evaluate('''() => {
        MapEditorPalette.add(param,root());
        return [...SVGCreateView.svg.querySelectorAll('[id]')].map(e=>e.id).slice(-2);
    }''')
    if r == ['edge-type-road','edge-type-path']:
        raise KnownDefect('K10: rendered road/path use edge IDs')
    assert r == ['path-type-road','path-type-path']
