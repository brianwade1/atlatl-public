"""S10 real unit symbols: public create switch, observations and selection."""

import json

import pytest

from tests.support.imports import REPO_ROOT
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]

# Expected icon element, nested paths, nested ellipses, and icon text. Small,
# literal structural oracles distinguish the families without path-data snapshots.
SYMBOLS = [
    ('infantry','path',0,0,''), ('light','path',0,0,''), ('armor','ellipse',0,0,''),
    ('mechinf','g',1,1,''), ('heavy','g',1,1,''), ('artillery','ellipse',0,0,''),
    ('hq','text',0,0,'HQ'), ('tisr','text',0,0,'HQ'), ('usmc','g',2,0,''),
    ('himars','g',2,1,''), ('df26','g',2,1,''), ('fighter','g',1,0,'F'),
    ('bomber','g',1,0,'B'), ('p8','g',1,0,'B'), ('atkhelo','path',0,0,''),
    ('accarrier','g',4,0,''), ('clf','g',4,0,''), ('destroyer','g',3,0,'DD'),
    ('ddg','g',3,0,'DD'), ('corvette','g',3,0,'FS'), ('msc','g',3,0,'FS'),
    ('frigate','g',3,0,'FF'), ('cruiser','g',3,0,'CG'), ('sub','g',4,0,''),
    ('ssk','g',4,0,''), ('ssn','g',4,0,''), ('amphibship','g',4,0,''), ('aa','path',0,0,''),
]


@pytest.mark.parametrize('kind,tag,paths,ellipses,text', SYMBOLS, ids=[s[0] for s in SYMBOLS])
def test_supported_symbol_types(svg_page, kind, tag, paths, ellipses, text):
    r = svg_page.evaluate('''type => {
        drawMap(1,1); const u=makeUnit({type}), s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId];
        const icon=s.whole.firstElementChild.children[1], bb=s.whole.getBBox();
        s.whole.dispatchEvent(new MouseEvent('mousedown'));
        return {icon:[icon.tagName,icon.querySelectorAll('path').length,icon.querySelectorAll('ellipse').length,icon.textContent],
            id:s.whole.id,fill:s.background.getAttribute('fill'),strength:s.strength.nodeValue,
            label:[...s.whole.children].filter(e=>e.tagName==='text').map(e=>e.textContent),
            pointer:s.whole.getAttribute('pointer-events'),click:unitClick,
            geometry:[bb.width>0,bb.height>0,Number.isFinite(bb.x),Number.isFinite(bb.y)]};
    }''', kind)
    assert r == dict(icon=[tag,paths,ellipses,text], id='blue Alpha', fill='#c5c5fc',
                     strength='73', label=['Alpha','73'], pointer='all', click='blue Alpha',
                     geometry=[True]*4)


@pytest.mark.parametrize('echelon,count', [('regiment',3),('battalion',2),('squadron',2),('unknown',0)])
def test_echelon_and_unknown_characterization(svg_page, echelon, count):
    r = svg_page.evaluate('''echelon => {
        drawMap(1,1); const u=makeUnit({echelon});
        const s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole;
        return {bars:[...s.children].slice(1).reduce((n,e)=>n+e.querySelectorAll('rect').length,0),
            labels:[...s.querySelectorAll('text')].map(e=>e.textContent)};
    }''', echelon)
    assert r == dict(bars=count, labels=['Alpha','73'])


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: company references out-of-scope strokeWidth')
def test_company_symbol_creation(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1);
        try {const u=makeUnit({echelon:'company'});
            const s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole;
            return {bar:s.children[1].tagName,strength:SVGUnitSymbol.unitSymbolIndex[u.uniqueId].strength.nodeValue};}
        catch(e) {return {name:e.name,message:e.message};}
    }''')
    if r == dict(name='ReferenceError', message='strokeWidth is not defined'):
        raise KnownDefect('K13: companyEchelon cannot access strokeWidth')
    assert r == dict(bar='rect', strength='73')


def test_unknown_type_renders_background_labels_without_icon(svg_page):
    assert svg_page.evaluate('''() => {
        drawMap(1,1); const u=makeUnit({type:'unknown'}), s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId];
        return [s.whole.firstElementChild.children.length,s.background.tagName,
            [...s.whole.querySelectorAll('text')].map(e=>e.textContent)];
    }''') == [1,'rect',['Alpha','73']]


def test_sample_oob_compatibility_smoke(svg_page):
    # Read-only production sample; small fixtures above remain the main oracle.
    units = json.loads((REPO_ROOT / 'browser/sample-oobs/oob-all-symbols.json').read_text(encoding='utf-8'))
    r = svg_page.evaluate('''units => {
        drawMap(1,1);
        return units.map(p=>{
            const u=makeUnit(p), s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId];
            return [s.whole.id,s.whole.isConnected,s.strength.nodeValue,s.whole.getBBox().width>0];
        });
    }''', units)
    assert r == [[u['uniqueId'],True,str(u['currentStrength']),True] for u in units]


def test_move_observation_strength_dimming_removal_and_reappearance(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(2,1); const u=makeUnit(), id=u.uniqueId, s=SVGUnitSymbol.unitSymbolIndex[id];
        u.setHex(GameMap.hexes[1]); SVGUnitSymbol.moveSymbolToHex(id,u.hex);
        const m=s.whole.transform.baseVal.consolidate().matrix;
        const moved=[m.a,m.d,m.e,m.f], hb=box(document.getElementById(u.hex.id).getBBox());
        u.currentStrength=42; u.canMove=false; SVGUnitSymbol.partialObsUpdate(id,{ineffective:false});
        const dim=[s.strength.nodeValue,s.background.getAttribute('fill')];
        u.canMove=true; SVGUnitSymbol.partialObsUpdate(id,{ineffective:false});
        const normal=s.background.getAttribute('fill');
        SVGUnitSymbol.partialObsUpdate(id,{ineffective:true}); const dead=!s.whole.isConnected;
        SVGUnitSymbol.partialObsUpdate(id,{ineffective:false}); const alive=s.whole.isConnected;
        u.remove(); SVGUnitSymbol.partialObsUpdate(id,{ineffective:false}); const fog=!s.whole.isConnected;
        u.setHex(GameMap.hexes[0]); SVGUnitSymbol.partialObsUpdate(id,{ineffective:false});
        return {moved,hb,dim,normal,dead,alive,fog,returned:s.whole.isConnected,
            same:SVGUnitSymbol.unitSymbolIndex[id].whole===s.whole,count:document.querySelectorAll('[id="blue Alpha"]').length};
    }''')
    x,y,w,h = r.pop('hb')
    moved = r.pop('moved')
    assert moved == pytest.approx([.6,.6,x+w/2,y+h/2])
    assert r == dict(dim=['42','#ababe0'],normal='#c5c5fc',dead=True,alive=True,fog=True,returned=True,same=True,count=1)


def test_brightness_methods_respect_factions(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1); const a=makeUnit(), b=makeUnit({uniqueId:'red Bravo',faction:'red'});
        const read=()=>[a,b].map(u=>SVGUnitSymbol.unitSymbolIndex[u.uniqueId].background.getAttribute('fill'));
        const normal=read(); SVGUnitSymbol.setBrightness(a.uniqueId,'bright'); const single=read();
        SVGUnitSymbol.setFactionBrightness('red','dim'); const faction=read();
        SVGUnitSymbol.setAllUnitBrightness('dim'); return [normal,single,faction,read()];
    }''')
    assert r == [['#c5c5fc','#fcc5c5'],['#d4d4ff','#fcc5c5'],['#d4d4ff','#e0abab'],['#ababe0','#e0abab']]


def test_selection_geometry_and_balanced_cycles(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1); const u=makeUnit(), s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole;
        const before=SVGCreateView.svg.children.length, bb=box(SVGUtil.getTransformedBBox(s));
        SVGUnitSymbol.markSelected(s); const marker=SVGCreateView.svg.lastChild;
        const a=attrs(marker); SVGUnitSymbol.unmarkSelected(); SVGUnitSymbol.unmarkSelected();
        SVGUnitSymbol.markSelected(s); SVGUnitSymbol.unmarkSelected();
        return {bb,a,detached:!marker.isConnected,delta:SVGCreateView.svg.children.length-before};
    }''')
    x,y,w,h = r['bb']
    assert [float(r['a'][k]) for k in ('x','y','width','height')] == pytest.approx([x-w*.05,y-w*.05,w*1.1,h+w*.1], abs=1e-5)
    assert r['a']['stroke']=='red' and r['a']['fill']=='transparent' and r['detached'] and r['delta']==0


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: repeated selection leaves the first rectangle attached')
def test_repeated_selection_does_not_leave_orphan(svg_page):
    r = svg_page.evaluate('''() => {
        drawMap(1,1); const u=makeUnit(), s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole;
        const before=SVGCreateView.svg.children.length;
        SVGUnitSymbol.markSelected(s); const first=SVGCreateView.svg.lastChild;
        SVGUnitSymbol.markSelected(s); SVGUnitSymbol.unmarkSelected();
        return [SVGCreateView.svg.children.length-before,first.isConnected];
    }''')
    if r == [1,True]:
        raise KnownDefect('K13: first selection rectangle survives clear')
    assert r == [0,False]


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K13: unselect before select dereferences null')
def test_unselect_without_prior_selection(svg_page):
    r = svg_page.evaluate('''() => {
        root(); try {SVGUnitSymbol.unmarkSelected(); return null;}
        catch(e) {return {name:e.name,message:e.message};}
    }''')
    if r == dict(name='TypeError',message="Cannot read properties of null (reading 'remove')"):
        raise KnownDefect('K13: initial unselect dereferences null')
    assert r is None
