"""S13 module playback, frame scheduling, debug colors and malformed inputs."""
import pytest

from tests.support.playback import (playback_page, messages, initialize, attempt,
    snapshot, assert_observation, fills)
from tests.support.builders import make_map, make_scenario, make_unit, make_state
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


def test_init_observations_and_exhaustion(playback_page):
    p = playback_page
    records = messages()
    initialize(p, records)
    assert p.locator('#orders_echelon').input_value() == 'NA'
    assert len(fills(p)) == 6
    assert fills(p)['hex-1-1'] == 'lightgray'
    assert [u['id'] for u in snapshot(p)] == ['blue A', 'red A']
    for record in records[1:]:
        assert p.evaluate('Playback.next_message()') is True
        assert_observation(p, record['observation']['units'])
        blue = snapshot(p)[0]
        if blue['visible']:
            assert blue['fill'] == ('#c5c5fc' if blue['canMove'] else '#ababe0')
    before = snapshot(p)
    for _ in range(2):
        assert p.evaluate('Playback.next_message()') is False
        assert snapshot(p) == before


def test_frame_pause_resume_step_and_end(playback_page):
    p = playback_page
    initialize(p)
    before = snapshot(p)
    p.evaluate('Playback.play()')
    assert snapshot(p) == before
    assert p.evaluate('framesPending.length') == 0
    p.evaluate('Playback.set_play_mode(true); Playback.play()')
    assert p.evaluate('framesPending.length') == 1
    p.evaluate('advanceFrame()')
    assert_observation(p, messages()[2]['observation']['units'])
    p.evaluate('Playback.set_play_mode(false); advanceFrame()')
    assert p.evaluate('framesPending.length') == 0
    assert p.evaluate('Playback.next_message()') is True
    p.evaluate('Playback.set_play_mode(true); Playback.play(); advanceFrame()')
    assert_observation(p, messages()[-1]['observation']['units'])
    assert p.evaluate('framesPending.length') == 0
    assert p.evaluate('Playback.next_message()') is False


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K30: repeated play starts concurrent frame loops')
def test_repeated_play_has_one_frame_loop(playback_page):
    p = playback_page
    initialize(p)
    p.evaluate('Playback.set_play_mode(true); Playback.play(); Playback.play()')
    pending = p.evaluate('framesPending.length')
    p.evaluate('Playback.set_play_mode(false); advanceFrame(); advanceFrame()')
    assert p.evaluate('framesPending.length') == 0
    if pending == 2:
        assert_observation(p, messages()[2]['observation']['units'])
        raise KnownDefect('K30: two Play calls enqueue two callbacks and consume two observations')
    assert pending == 1
    assert_observation(p, messages()[1]['observation']['units'])


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K31: init retains its message index')
def test_repeated_init_restarts_replay(playback_page):
    p = playback_page
    initialize(p)
    before = snapshot(p)
    result = attempt(p, 'Playback.init()')
    if result == {'name':'TypeError', 'message':"Cannot read properties of undefined (reading 'map')"}:
        assert snapshot(p) == before
        raise KnownDefect('K31: second init treats the first observation as parameters')
    assert result == {}
    assert p.evaluate('Playback.next_message()') is True
    assert_observation(p, messages()[1]['observation']['units'])


def test_second_game_replaces_visible_map_and_characterizes_stale_indexes(playback_page):
    p = playback_page
    second = make_scenario(make_map(rows=2, cols=1), [make_unit(name='New')])
    records = messages()[:2] + [{'type':'parameters','parameters':second},
        {'type':'observation','observation':make_state(second['units'])}]
    initialize(p, records)
    assert p.evaluate('Playback.next_message()') is True
    assert p.evaluate('Playback.next_message()') is True
    assert len(fills(p)) == 2
    assert_observation(p, second['units'])
    assert p.locator('[id="blue A"], [id="red A"], [id^="mark "]').count() == 0
    # Existing K20: replacement clears the visible scene but retains old unit objects.
    assert p.evaluate('Object.keys(Unit.unitIndex).sort()') == ['blue A', 'blue New', 'red A']
    assert p.evaluate('Object.values(Unit.occupancy).flat().map(u=>u.uniqueId).sort()') == ['blue A', 'blue New', 'red A']
    assert p.evaluate('Playback.next_message()') is False


@pytest.mark.parametrize('debug', [None, {}, {'colors':{}}, {'colors':{'hex-0-0':'magenta'}}])
def test_false_colors_and_debug_clearing(playback_page, debug):
    p = playback_page
    records = messages()
    if debug is not None:
        records[1]['debug'] = debug
    initialize(p, records)
    p.evaluate('Playback.next_message(); Playback.false_color()')
    expected = {key:'white' for key in fills(p)}
    if debug and debug.get('colors'):
        expected['hex-0-0'] = 'magenta'
    assert fills(p) == expected
    assert p.locator('#orders_echelon').input_value() == 'NA'
    p.evaluate('Playback.next_message()')
    assert set(fills(p).values()) == {'white'}
    p.evaluate('Playback.terrain_color()')
    assert fills(p)['hex-1-1'] == 'lightgray'


@pytest.mark.parametrize('debug', [None, {}, {'echelons':[]}])
def test_orders_missing_levels_cycle(playback_page, debug):
    p = playback_page
    records = messages()
    records[1]['debug'] = debug
    initialize(p, records)
    p.evaluate('Playback.next_message()')
    for level in [0, 1, 2, 0]:
        p.evaluate('Playback.orders_color()')
        assert p.locator('#orders_echelon').input_value() == str(level)
        assert set(fills(p).values()) == {'white'}
    p.evaluate('Playback.terrain_color()')
    assert p.locator('#orders_echelon').input_value() == 'NA'
    p.evaluate('Playback.false_color()')
    assert p.locator('#orders_echelon').input_value() == 'NA'


def test_orders_missing_level_then_observation_without_debug(playback_page):
    p = playback_page
    records = messages()
    records[1]['debug'] = {'echelons':[[{'hex':'hex-0-0','color':'orange'}]]}
    initialize(p, records)
    # Select level 1 before debug arrives: it is absent even in this nonempty list.
    p.evaluate('Playback.orders_color(); Playback.orders_color()')
    assert p.locator('#orders_echelon').input_value() == '1'
    for _ in range(2):
        assert p.evaluate('Playback.next_message()') is True
        assert set(fills(p).values()) == {'white'}
        assert p.locator('#orders_echelon').input_value() == '1'


@pytest.mark.parametrize('level', [[], [{'hex':'hex-0-0','color':'orange'}]])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K32: echelonColorData is undeclared')
def test_orders_present_level(playback_page, level):
    p = playback_page
    records = messages()
    records[1]['debug'] = {'echelons':[level]}
    initialize(p, records)
    p.evaluate('Playback.next_message()')
    result = attempt(p, 'Playback.orders_color()')
    assert p.locator('#orders_echelon').input_value() == '0'
    if result == {'name':'ReferenceError','message':'echelonColorData is not defined'}:
        assert fills(p)['hex-1-1'] == 'lightgray'
        raise KnownDefect('K32: even an empty present level executes the undeclared assignment')
    assert result == {}
    assert fills(p)['hex-0-0'] == ('orange' if level else 'white')
    p.evaluate('Playback.orders_color()')  # Missing level 1.
    assert set(fills(p).values()) == {'white'}


@pytest.mark.parametrize('kind', ['empty','malformed-init','malformed-next','parameters-only',
    'dangling-parameters','unknown','action'])
def test_unsupported_input_characterization(playback_page, kind):
    p = playback_page
    records = messages()[:1]
    if kind == 'empty':
        records = []
    elif kind == 'malformed-init':
        records = ['not json']
    elif kind == 'malformed-next':
        records += ['not json']
    elif kind == 'dangling-parameters':
        records += records[:1]
    elif kind in ('unknown', 'action'):
        records += [{'type':kind, 'action':{'type':'pass'}}]
    if kind in ('empty','malformed-init'):
        from tests.support.playback import script
        p.evaluate(script(records))
        result = attempt(p, 'Playback.init()')
    else:
        initialize(p, records)
        result = attempt(p, 'Playback.next_message()')
    if kind == 'parameters-only':
        assert result == {'value':False}
    elif kind in ('unknown','action'):
        assert result == {'name':'TypeError','message':"Cannot read properties of undefined (reading 'type')"}
        assert attempt(p, 'Playback.next_message()') == result  # Index did not advance.
    else:
        assert result['name'] == 'SyntaxError'
        assert ('not json' if 'malformed' in kind else 'undefined') in result['message']
