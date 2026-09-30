"""S12 socket callbacks, exact outbound protocol and observation rendering."""
import pytest

from tests.support.live_play import (play_page, scenario, deliver, observe, sent, down, marks)
from tests.support.builders import make_map, make_scenario, make_unit
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


def test_connection_callbacks_and_parameters(play_page):
    p = play_page
    assert p.locator('#status').inner_text() == 'Connected'
    assert p.locator('[id^="hex-"]').count() == 6
    assert p.locator('[id="blue A"]').count() == 1
    for name in ('blue', 'red', 'next-game'):
        assert p.locator('#'+name).is_enabled()
    for name in ('end-move', 'reset'):
        assert p.locator('#'+name).is_disabled()
    p.evaluate("testSockets[0].emit('error',new Event('error'))")
    assert p.locator('#status').inner_text() == 'Connected'
    p.evaluate('testSockets[0].close()')
    assert p.locator('#status').inner_text() == 'Socket closed'


@pytest.mark.parametrize('role', ['blue', 'red'])
def test_roles_waiting_input_terminal(play_page, role):
    p = play_page
    p.locator('#'+role).click()
    assert sent(p) == [{'type':'role-request','role':role,'auto_next_game':False}]
    assert p.locator('#end-move').is_disabled()
    assert p.locator('#reset').is_enabled()
    assert p.locator('#blue').is_disabled() and p.locator('#red').is_disabled()
    observe(p, on_move=role, phase=2, score=50)
    assert p.locator('#end-move').is_enabled()
    assert [p.locator('#'+s).inner_text() for s in ('onmove','phase','score')] == [role,'2','50']
    observe(p, on_move='red' if role=='blue' else 'blue')
    assert p.locator('#end-move').is_disabled()
    observe(p, on_move=role, terminal=True)
    assert p.locator('#onmove').inner_text() == 'terminal'
    assert p.locator('#end-move').is_disabled()


@pytest.mark.parametrize('expression,expected', [
    ("Play.sendMove(GameMap.hexIndex['hex-0-1'])", {'type':'action','action':{'type':'move','mover':'blue A','destination':'hex-0-1'}}),
    ("Play.sendFire(Unit.unitIndex['red A'])", {'type':'action','action':{'type':'fire','source':'blue A','target':'red A'}}),
    ("Play.sendSetupMove(GameMap.hexIndex['hex-0-1'])", {'type':'action','action':{'type':'setup-move','mover':'blue A','destination':'hex-0-1'}}),
    ("Play.sendSetupExchange(Unit.unitIndex['blue B'])", {'type':'action','action':{'type':'setup-exchange','mover':'blue A','friendly':'blue B'}}),
    ('Play.sendReset()', {'type':'reset-request'}),
    ('Play.sendNextGame()', {'type':'next-game-request'}),
    ('Play.endMovePressed()', {'type':'action','action':{'type':'pass'}}),
])
def test_exact_senders(play_page, expression, expected):
    play_page.evaluate("HumanPlayerControl.selectedUnit=Unit.unitIndex['blue A']")
    play_page.evaluate(expression)
    assert sent(play_page) == [expected]


def test_observations_fog_kills_markers_brightness_reset(play_page):
    p = play_page
    p.locator('#blue').click()
    observe(p, setup=True, city_owner={'hex-1-1':'blue'})
    assert p.locator('#phase').inner_text() == 'setup'
    assert p.evaluate("SVGSetupMarker.setupMarkerGroup.getAttribute('visibility')") == 'visible'
    down(p, 'blue A')
    assert marks(p) == 1
    units = scenario()['units']
    units[0]['canMove'] = False
    units[2]['hex'] = 'fog'
    observe(p, units=units, phase=1, city_owner={'hex-1-1':'red'})
    assert marks(p) == 0
    assert p.locator('[id="red A"]').count() == 0
    assert p.evaluate("SVGUnitSymbol.unitSymbolIndex['blue A'].background.getAttribute('fill')") == '#ababe0'
    assert p.evaluate("SVGSetupMarker.setupMarkerGroup.getAttribute('visibility')") == 'hidden'
    assert p.evaluate("['blue','red'].map(k=>SVGCityMarker.cityMarkerIndex['hex-1-1'][k].getAttribute('visibility'))") == ['hidden','visible']
    observe(p, city_owner={'hex-1-1':'neutral'})
    assert p.evaluate("['blue','red'].map(k=>SVGCityMarker.cityMarkerIndex['hex-1-1'][k].getAttribute('visibility'))") == ['hidden','hidden']
    assert p.locator('[id="red A"]').count() == 1
    assert p.evaluate("SVGUnitSymbol.unitSymbolIndex['blue A'].background.getAttribute('fill')") == '#c5c5fc'
    units[2].update(hex='hex-0-2', ineffective=True, currentStrength=0)
    observe(p, units=units, score=100)
    assert p.locator('[id="red A"]').count() == 0
    deliver(p, {'type':'reset'})  # Dedicated handler is currently a no-op.
    assert p.locator('#score').inner_text() == '100'
    observe(p, setup=True)
    assert p.locator('#score').inner_text() == '0'
    assert p.locator('[id="red A"]').count() == 1


@pytest.mark.parametrize('wire,expected', [('not json','SyntaxError'), ('{"type":"mystery"}','Unknown message type: mystery')])
def test_bad_messages_throw_through_assigned_callback(play_page, wire, expected):
    result = play_page.evaluate('''wire => {try {testSockets[0].receive(wire); return null;}
        catch(e) {return e.name || String(e);}}''', wire)
    assert result == expected


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K26: newPhase reads phaseCount at wrong nesting level')
def test_phase_lookup(play_page):
    # Spy delegates unchanged behavior; duplicate brightness resets identify newPhase.
    play_page.evaluate('''() => {window.calls=0; const original=SVGUnitSymbol.setAllUnitBrightness;
        SVGUnitSymbol.setAllUnitBrightness=(...a)=>{calls++; return original(...a);};}''')
    observe(play_page, phase=0)
    assert play_page.evaluate('calls') == 2
    observe(play_page, phase=1)
    assert play_page.locator('#phase').inner_text() == '1'
    calls = play_page.evaluate('calls')
    if calls == 3:
        raise KnownDefect('K26: nested phase change misses newPhase')
    assert calls == 4


def test_next_parameters_replace_map(play_page):
    p = play_page
    replacement = make_scenario(make_map(rows=1, cols=1), [make_unit(name='New')])
    deliver(p, {'type':'parameters','parameters':replacement})
    assert p.locator('[id="blue A"]').count() == 0
    assert p.locator('[id="blue New"]').count() == 1
    assert p.locator('#blue').is_enabled()
    assert p.evaluate('Object.keys(Unit.unitIndex)') == ['blue New']
    count = p.locator('[id^="hex-"]').count()
    assert count == 1


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K29: next parameters retain controller selection mode')
def test_next_parameters_allow_fresh_selection(play_page):
    p = play_page
    p.locator('#blue').click()
    observe(p)
    down(p, 'blue A')
    assert marks(p) > 0
    replacement = make_scenario(make_map(rows=2, cols=1), [make_unit(name='New')])
    deliver(p, {'type':'parameters','parameters':replacement})
    assert marks(p) == 0
    assert p.locator('[id="blue A"]').count() == 0
    p.locator('#blue').click()
    observe(p, units=replacement['units'])
    down(p, 'blue New')
    selected = p.evaluate('HumanPlayerControl.selectedUnit?.uniqueId')
    if selected == 'blue A' and marks(p) == 0:
        raise KnownDefect('K29: controller retains old-game unit and ignores new selection')
    assert selected == 'blue New' and marks(p) > 0
