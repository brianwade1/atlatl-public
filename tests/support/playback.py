"""Replay inputs over HTTP; original viewer/model/rendering code stays intact."""
import json

import pytest

from tests.support.builders import make_map, make_scenario, make_unit, make_state


FRAMES = """window.framesPending=[];
window.requestAnimationFrame=callback => {framesPending.push(callback); return framesPending.length;};
window.advanceFrame=() => {const callback=framesPending.shift(); if(callback) callback(0);};"""


def messages():
    scenario = make_scenario(make_map(rows=3, cols=2, terrain_overrides={(1, 1): 'urban'}),
        [make_unit(), make_unit(faction='red', hex='hex-0-2')])
    result = [{'type': 'parameters', 'parameters': scenario}]
    for units in [scenario['units'],
        [make_unit(hex='hex-0-1', strength=60, can_move=False),
         make_unit(faction='red', hex='fog')],
        [make_unit(hex='hex-0-1', strength=0, ineffective=True),
         make_unit(faction='red', hex='hex-0-2', strength=75)],
        scenario['units']]:
        result.append({'type': 'observation', 'observation': make_state(units)})
    return result


def script(records):
    return 'replayData = ' + json.dumps([json.dumps(m) if not isinstance(m, str) else m for m in records]) + ';'


def expose(page):
    page.evaluate('''async () => {
        for (const [file,name] of [['playback','Playback'],['map','Map'],
            ['unit','Unit'],['svg-unit-symbol','SVGUnitSymbol']])
            window[name==='Map'?'GameMap':name]=(await import('/browser/'+file+'.js'))[name];
    }''')


def load_page(page, base_url, content):
    page.route('**/browser/replay.js', lambda route: route.fulfill(
        status=200, content_type='text/javascript', body=content))
    page.goto(base_url + '/browser/playback.html')
    expose(page)


@pytest.fixture
def playback_page(module_page):
    module_page.evaluate(FRAMES)
    module_page.evaluate("document.body.insertAdjacentHTML('beforeend','<input id=orders_echelon>')")
    expose(module_page)
    return module_page


def initialize(page, records=None):
    page.evaluate(script(messages() if records is None else records))
    page.evaluate('Playback.init()')


def attempt(page, expression):
    return page.evaluate('''expression => {try {return {value:eval(expression)};}
        catch(e) {return {name:e.name,message:e.message};}}''', expression)


def snapshot(page):
    return page.evaluate('''() => Unit.units.map(u => {
        const s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId];
        return {id:u.uniqueId,hex:u.hex?.id??null,strength:u.currentStrength,
            canMove:u.canMove,ineffective:u.ineffective,visible:s.whole.isConnected,
            text:s.strength.nodeValue,fill:s.background.getAttribute('fill'),
            transform:s.whole.getAttribute('transform')};
    })''')


def assert_observation(page, units):
    actual = snapshot(page)
    assert len(actual) == len(units)
    for rendered, unit in zip(actual, units):
        visible = not unit['ineffective'] and unit['hex'] != 'fog'
        assert rendered['id'] == unit['faction'] + ' ' + unit['longName']
        assert rendered['hex'] == (unit['hex'] if visible else None)
        assert rendered['strength'] == unit['currentStrength']
        assert rendered['canMove'] == unit['canMove']
        assert rendered['ineffective'] == unit['ineffective']
        assert rendered['visible'] == visible
        if visible:
            assert rendered['text'] == format(unit['currentStrength'], 'g')
            center = page.locator('[id="'+unit['hex']+'"]').evaluate(
                '(e)=>{const b=e.getBBox(); return [b.x+b.width/2,b.y+b.height/2];}')
            transform = rendered['transform'].split(')')[0].removeprefix('translate(')
            assert list(map(float, transform.split())) == pytest.approx(center)


def fills(page):
    return page.locator('[id^="hex-"]').evaluate_all('(es)=>Object.fromEntries(es.map(e=>[e.id,e.getAttribute("fill")]))')
