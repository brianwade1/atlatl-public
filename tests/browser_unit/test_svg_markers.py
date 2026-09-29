"""S10 setup/city/action markers, including repeated-map lifecycle probes."""

import math

import pytest

from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


def test_setup_add_replace_remove_visibility_and_model(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(2,1); const [a,b]=GameMap.hexes;
        SVGSetupMarker.addMarker(a,'setup-type-blue');
        const old=SVGSetupMarker.setupMarkerIndex[a.id], first=attrs(old);
        SVGSetupMarker.addMarker(a,'setup-type-red');
        const replaced=[old.isConnected,SVGSetupMarker.setupMarkerGroup.children.length,
            SVGSetupMarker.setupMarkerIndex[a.id].getAttribute('fill'),a.setup];
        SVGSetupMarker.setAllVisible(false); const hidden=SVGSetupMarker.setupMarkerGroup.getAttribute('visibility');
        SVGSetupMarker.setAllVisible(true); const visible=SVGSetupMarker.setupMarkerGroup.getAttribute('visibility');
        SVGSetupMarker.removeMarker(a); SVGSetupMarker.removeMarker(a);
        const removed=[a.setup,Object.keys(SVGSetupMarker.setupMarkerIndex)];
        SVGSetupMarker.addMarker(a,'setup-type-blue'); SVGSetupMarker.addMarker(b,'setup-type-red');
        SVGSetupMarker.removeAllMarkers(); SVGSetupMarker.removeAllMarkers();
        return {first,replaced,hidden,visible,removed,
            all:[a.setup,b.setup,Object.keys(SVGSetupMarker.setupMarkerIndex),SVGSetupMarker.setupMarkerGroup.children.length]};
    }''')
    first = r.pop('first')
    assert [float(first[k]) for k in ('x','y','width','height')] == pytest.approx([13.75,3.75+4*math.sqrt(3),.5,.5])
    assert first['fill']=='blue' and first['pointer-events']=='none'
    assert r == dict(replaced=[False,1,'red','setup-type-red'], hidden='hidden', visible='visible',
                     removed=[None,[]], all=[None,None,[],0])


def test_city_neutral_and_independent_faction_visibility(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1); const h=GameMap.hexes[0]; SVGCityMarker.addMarkers(h);
        const pair=SVGCityMarker.cityMarkerIndex[h.id], read=()=>['blue','red'].map(k=>pair[k].getAttribute('visibility'));
        const neutral=read(), a=attrs(pair.blue), b=attrs(pair.red);
        SVGCityMarker.setVisible(true,h,'blue'); const blue=read();
        SVGCityMarker.setVisible(true,h,'red'); const both=read();
        SVGCityMarker.setVisible(false,h,'blue'); const red=read();
        SVGCityMarker.setVisible(false,h,'red');
        return {neutral,blue,both,red,none:read(),a,b};
    }''')
    assert [r[k] for k in ('neutral','blue','both','red','none')] == [
        ['hidden','hidden'], ['visible','hidden'], ['visible','visible'], ['hidden','visible'], ['hidden','hidden']]
    for key,color in [('a','#ababe0'),('b','#e0abab')]:
        assert r[key]['fill']==color and r[key]['r']=='0.5' and r[key]['pointer-events']=='none'
        assert [float(r[key][k]) for k in ('cx','cy')] == pytest.approx([14,4+4*math.sqrt(3)])


@pytest.mark.parametrize('kind', ['setup','city'])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: init retains detached marker indexes')
def test_new_map_drops_detached_marker_references(svg_page, kind):
    r = svg_page.evaluate('''kind => {
        drawMap(2,1); const h=GameMap.hexes[1];
        if(kind==='setup') SVGSetupMarker.addMarker(h,'setup-type-blue');
        else SVGCityMarker.addMarkers(h);
        drawMap(1,1);
        if(kind==='setup') SVGSetupMarker.removeAllMarkers();
        const index=kind==='setup'?SVGSetupMarker.setupMarkerIndex:SVGCityMarker.cityMarkerIndex;
        return {keys:Object.keys(index), connected:Object.values(index).map(v=>(v.blue||v).isConnected)};
    }''', kind)
    if r == dict(keys=['hex-0-1'], connected=[False]):
        raise KnownDefect(f'K13: {kind} index retains detached old-map marker')
    assert r == dict(keys=[], connected=[])


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: repeated city markers orphan visible circles')
def test_city_replacement_removes_previous_pair(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1); const h=GameMap.hexes[0]; SVGCityMarker.addMarkers(h);
        const old=SVGCityMarker.cityMarkerIndex[h.id]; SVGCityMarker.setVisible(true,h,'blue');
        SVGCityMarker.addMarkers(h); SVGCityMarker.setVisible(false,h,'blue');
        return [SVGCityMarker.cityMarkerGroup.children.length,old.blue.isConnected,old.blue.getAttribute('visibility')];
    }''')
    if r == [4,True,'visible']:
        raise KnownDefect('K13: old visible city circle survives replacement')
    assert r[:2] == [2,False]


def test_action_marker_geometry_callback_clear_and_redraw(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(); const u=makeUnit(), calls=[];
        HumanPlayerControl.markerMouseDown=e=>calls.push(e.currentTarget.id);
        const ub=box(SVGUtil.getTransformedBBox(SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole));
        const h=GameMap.hexes[1], hb=box(document.getElementById(h.id).getBBox());
        SVGGui.markHex(h,'green','move-target'); const marker=document.getElementById('move-target');
        marker.dispatchEvent(new MouseEvent('mousedown')); const markerAttrs=attrs(marker);
        SVGGui.clearMarks(); SVGGui.clearMarks(); const removed=!marker.isConnected;
        SVGGui.markHex(h,'blue','again'); const redrawn=!!document.getElementById('again');
        SVGGui.clearMarks(); return {ub,hb,marker:markerAttrs,calls,removed,redrawn,cleared:!document.getElementById('again')};
    }''')
    _, _, w, h = r['ub']
    x, y, hw, hh = r['hb']
    assert [float(r['marker'][k]) for k in ('x','y','width','height')] == pytest.approx(
        [x+hw/2-w*.55,y+hh/2-h/2-w*.05,w*1.1,h+w*.1], abs=1e-5)
    assert r['marker']['id']=='move-target' and r['marker']['stroke']=='green' and r['marker']['fill']=='transparent'
    assert r['calls']==['move-target'] and r['removed'] and r['redrawn'] and r['cleared']


@pytest.mark.parametrize('state', ['empty','ineffective','hidden'])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: action marking requires a live visible unit')
def test_marking_without_live_visible_units(svg_page, state):
    r = svg_page.evaluate('''state => {
        drawMap(1,1);
        if(state!=='empty') {const u=makeUnit(); if(state==='hidden') u.hex=null; else u.ineffective=true;}
        try {SVGGui.markHex(GameMap.hexes[0],'red','target'); return {ok:!!document.getElementById('target')};}
        catch(e) {return {name:e.name,message:e.message};}
    }''', state)
    if r == dict(name='TypeError', message="Cannot read properties of null (reading 'transform')"):
        raise KnownDefect(f'K13: {state} marking dereferences null')
    assert r == dict(ok=True)


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: action marker dimensions remain cached after resizing/map redraw')
def test_marker_dimensions_follow_unit_size_after_new_map(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1); makeUnit(); SVGGui.markHex(GameMap.hexes[0],'red','first');
        const old=box(document.getElementById('first').getBBox()); SVGGui.clearMarks();
        drawMap(1,1); Unit.init(); const u=makeUnit();
        SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole.setAttribute('transform','scale(1.2)');
        SVGGui.markHex(GameMap.hexes[0],'red','next');
        return [old.slice(2),box(document.getElementById('next').getBBox()).slice(2)];
    }''')
    if r[0] == pytest.approx(r[1]) and r[0][0] == pytest.approx(3.102, abs=1e-5):
        raise KnownDefect('K13: marker retains original 0.6-scale width/height')
    assert r[1] == pytest.approx([2*v for v in r[0]], abs=1e-5)
