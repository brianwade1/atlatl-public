"""S13 real writer JavaScript executed by unchanged playback.html over HTTP."""
import pytest

from tests.support.browser_helpers import checked_page
from tests.support.builders import load_fixture, make_map
from tests.support.episode_assertions import expected_messages, read_replay
from tests.support.integration_server import running_server, read_report
from tests.support.playback import (FRAMES, load_page, script, messages, snapshot,
    assert_observation, fills, attempt)
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.integration]


@pytest.mark.parametrize('role', ['blue','red'])
@pytest.mark.parametrize('fog', [False, True])
def test_generated_replay_to_terminal(page, http_base_url, tmp_path, role, fog):
    config = {}
    if fog:
        scenario = load_fixture('scenarios/tiny_episode.json')['scenario']
        scenario['map'] = make_map(rows=7, cols=1)
        scenario['map']['fogOfWar'] = True
        scenario['units'][1]['hex'] = 'hex-0-6'
        config = {'scenario':scenario, 'actions':[{'type':'pass'}]*4}
    with running_server(tmp_path, functions=['blue','red'], reps=2, **config) as child:
        child.wait()
    report = read_report(tmp_path)
    path = tmp_path / (role+'.js')
    records = read_replay(path)
    assert records == report['transcripts'][role]
    if not fog:
        assert records == expected_messages()*2
    with checked_page(page):
        load_page(page, http_base_url, path.read_text(encoding='utf-8'))
        for record in records:
            if record['type'] == 'parameters':
                continue
            page.locator('#step').click()
            assert_observation(page, record['observation']['units'])
        before = snapshot(page)
        assert page.evaluate('Playback.next_message()') is False
        page.locator('#step').click()
        assert snapshot(page) == before
        assert records[-1]['observation']['status'] == report['state']['status']
        for observed, terminal in zip(records[-1]['observation']['units'], report['state']['units']):
            expected = dict(terminal)
            if fog and expected['faction'] != role:
                expected['hex'] = 'fog'
            assert observed == expected


def test_page_controls_and_debug(page, http_base_url):
    page.add_init_script(FRAMES)
    records = messages()
    records[1]['debug'] = {'colors':{'hex-0-0':'cyan'}}
    with checked_page(page):
        load_page(page, http_base_url, script(records))
        page.locator('#play').click()
        assert page.evaluate('framesPending.length') == 1
        page.locator('#false_color').click()
        assert fills(page)['hex-0-0'] == 'cyan'
        page.locator('#stop').click()
        before = snapshot(page)
        page.evaluate('advanceFrame()')
        assert snapshot(page) == before
        assert page.evaluate('framesPending.length') == 0
        page.locator('#step').click()
        assert_observation(page, records[2]['observation']['units'])
        assert set(fills(page).values()) == {'white'}
        page.locator('#terrain_color').click()
        assert fills(page)['hex-1-1'] == 'lightgray'
        for level in [0,1,2,0]:
            page.locator('#orders_color').click()
            assert page.locator('#orders_echelon').input_value() == str(level)
        page.locator('#play').click()
        page.evaluate('advanceFrame(); advanceFrame()')
        assert page.evaluate('framesPending.length') == 0
        assert_observation(page, records[-1]['observation']['units'])


def test_generated_action_log_compatibility_gap(page, http_base_url, tmp_path):
    with running_server(tmp_path, functions=['blue','red'], log_actions=True) as child:
        child.wait()
    read_report(tmp_path)
    path = tmp_path / 'blue.js'
    assert read_replay(path)[2]['type'] == 'action'
    with checked_page(page):
        load_page(page, http_base_url, path.read_text(encoding='utf-8'))
        page.locator('#step').click()
        before = snapshot(page)
        result = attempt(page, 'Playback.next_message()')
        assert result == {'name':'TypeError','message':"Cannot read properties of undefined (reading 'type')"}
        assert snapshot(page) == before


def test_native_animation_plays_to_completion(page, http_base_url):
    records = messages()
    records[-1]['observation']['units'][0]['currentStrength'] = 91
    with checked_page(page):
        load_page(page, http_base_url, script(records))
        page.locator('#play').click()
        page.wait_for_function("Unit.units[0].currentStrength === 91")
        assert page.evaluate('Playback.next_message()') is False
        assert_observation(page, records[-1]['observation']['units'])


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K30: repeated Play clicks enqueue duplicate loops')
def test_repeated_play_button(page, http_base_url):
    page.add_init_script(FRAMES)
    with checked_page(page):
        load_page(page, http_base_url, script(messages()))
        page.locator('#play').click(click_count=2)
        pending = page.evaluate('framesPending.length')
        page.locator('#stop').click()
        page.evaluate('advanceFrame(); advanceFrame()')
        assert page.evaluate('framesPending.length') == 0
        if pending == 2:
            assert_observation(page, messages()[2]['observation']['units'])
            raise KnownDefect('K30: two native clicks consume two entries and enqueue two callbacks')
        assert pending == 1


@pytest.mark.parametrize('name', [
    pytest.param("O'Brien", marks=pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K09: unescaped apostrophe')),
    pytest.param(r'A\B', marks=pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K09: lost JSON backslash')),
    'λ隊'])
def test_generated_name_executes_in_browser(page, http_base_url, tmp_path, name):
    scenario = load_fixture('scenarios/tiny_episode.json')['scenario']
    scenario['units'][0]['longName'] = name
    with running_server(tmp_path, functions=['blue','red'], scenario=scenario,
                        actions=[{'type':'pass'}]*4) as child:
        child.wait()
    read_report(tmp_path)
    content = (tmp_path/'blue.js').read_text(encoding='utf-8')
    # Collect exact startup errors, then feed them to the ordinary page guard.
    # All console/network errors still fail; no blanket suppression of page errors.
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    with checked_page(page, expected_page_errors=errors):
        load_page(page, http_base_url, content)
        if name == "O'Brien" and errors == ["Unexpected identifier 'Brien'", 'replayData is not defined']:
            assert page.locator('[id^="hex-"]').count() == 0
            raise KnownDefect('K09: emitted JavaScript does not parse')
        if name == r'A\B' and len(errors) == 1 and errors[0].startswith('Bad escaped character in JSON at position '):
            wire = page.evaluate('replayData[0]')
            position = wire.index('A'+chr(92)+'B') + 2
            assert errors == [f'Bad escaped character in JSON at position {position} (line 1 column {position+1})']
            assert page.locator('[id^="hex-"]').count() == 0
            raise KnownDefect('K09: JavaScript consumes the JSON escape layer')
        assert errors == []
        for _ in range(5):
            page.locator('#step').click()
        assert_observation(page, read_replay(tmp_path/'blue.js')[-1]['observation']['units'])
        assert snapshot(page)[0]['id'] == 'blue '+name


def test_checked_in_replay_bounded_smoke(page, http_base_url):
    with checked_page(page):
        page.goto(http_base_url+'/browser/playback.html')
        from tests.support.playback import expose
        expose(page)
        assert page.evaluate('replayData.length') > 3
        for _ in range(3):
            assert page.evaluate('Playback.next_message()') is True
        assert any(u['visible'] for u in snapshot(page))
