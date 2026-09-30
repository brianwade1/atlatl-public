"""S12 native WebSockets and unchanged play.html against an owned real server."""
from contextlib import ExitStack

import pytest
from playwright.sync_api import expect

from tests.support.browser_helpers import checked_page
from tests.support.builders import load_fixture, make_map, make_scenario, make_unit
from tests.support.episode_assertions import expected_messages
from tests.support.integration_server import running_server, read_report
from tests.support.live_play import real_page, down

pytestmark = [pytest.mark.browser, pytest.mark.integration, pytest.mark.protocol]


def open_players(stack, browser, url, port, roles):
    pages = {}
    for role in roles:
        context = stack.enter_context(browser.new_context())
        page = real_page(context, port)
        stack.enter_context(checked_page(page))
        page.goto(url + '/browser/play.html')
        expect(page.locator('#'+role)).to_be_enabled()
        page.locator('#'+role).click()
        pages[role] = page
    return pages


def phase(page, count, on_move):
    expect(page.locator('#phase')).to_have_text(str(count))
    expect(page.locator('#onmove')).to_have_text(on_move)


def action(page, target):
    expect(page.locator('#end-move')).to_be_enabled()
    down(page, 'blue A')
    down(page, target)


@pytest.mark.parametrize('function_red', [False, True])
def test_scripted_episode_both_browsers_or_function_ai(browser, http_base_url, tmp_path, function_red):
    with running_server(tmp_path, socket=True, functions=['red'] if function_red else []) as child:
        port = child.ready()['port']
        with ExitStack() as stack:
            pages = open_players(stack, browser, http_base_url, port,
                                 ['blue'] if function_red else ['blue','red'])
            blue = pages['blue']
            phase(blue, 0, 'blue')
            action(blue, 'mark hex-0-1')
            if not function_red:
                phase(pages['red'], 1, 'red')
                pages['red'].locator('#end-move').click()
            phase(blue, 2, 'blue')
            action(blue, 'mark red A')
            if not function_red:
                phase(pages['red'], 3, 'red')
                pages['red'].locator('#end-move').click()
            for page in pages.values():
                phase(page, 4, 'terminal')
                expect(page.locator('#score')).to_have_text('50')
                expect(page.locator('#end-move')).to_be_disabled()
                assert page.evaluate('received') == expected_messages()
            child.wait()
            report = read_report(tmp_path)
            assert report['state'] == expected_messages()[-1]['observation']
            assert report['reps_done'] == 1


def test_setup_reset_next_game_and_terminal(browser, http_base_url, tmp_path):
    scenario = load_fixture('scenarios/tiny_episode.json')['scenario']
    scenario['map']['hexes'][0]['setup'] = 'setup-type-blue'
    scenario['map']['hexes'][1]['setup'] = 'setup-type-blue'
    scenario['map']['hexes'][2]['setup'] = 'setup-type-red'
    with running_server(tmp_path, socket=True, scenario=scenario) as child:
        with ExitStack() as stack:
            pages = open_players(stack, browser, http_base_url, child.ready()['port'], ['blue','red'])
            b, r = pages['blue'], pages['red']
            phase(b, 'setup', 'blue')
            down(b, 'blue A')
            down(b, 'hex-0-1')
            b.wait_for_function("received.at(-1).observation?.units[0].hex === 'hex-0-1'")
            b.locator('#end-move').click()
            phase(r, 'setup', 'red')
            r.locator('#end-move').click()
            phase(b, 0, 'blue')
            b.locator('#reset').click()
            b.wait_for_function("received.at(-1).type === 'reset'")
            for p in (b,r):
                phase(p, 'setup', 'blue')
                expect(p.locator('#blue')).to_be_disabled()
                assert p.evaluate("received.filter(m=>m.type==='observation').at(-1).observation.units[0].hex") == 'hex-0-0'
            b.locator('#next-game').click()
            for p in (b,r):
                expect(p.locator('#blue')).to_be_enabled()
                expect(p.locator('#phase')).to_have_text('None')
                assert p.evaluate("received.filter(m=>m.type==='parameters').length") == 2
            # Swap human roles to prove new role assignment, not an ordinary reset.
            b.locator('#red').click()
            r.locator('#blue').click()
            phase(r, 'setup', 'blue')
            r.locator('#end-move').click()
            phase(b, 'setup', 'red')
            b.locator('#end-move').click()
            phase(r, 0, 'blue')
            action(r, 'mark hex-0-1')
            phase(b, 1, 'red')
            b.locator('#end-move').click()
            phase(r, 2, 'blue')
            action(r, 'mark red A')
            phase(b, 3, 'red')
            b.locator('#end-move').click()
            for p in (b,r):
                phase(p, 4, 'terminal')
                expect(p.locator('#score')).to_have_text('50')
            child.wait()
            assert read_report(tmp_path)['state'] == expected_messages()[-1]['observation']


def test_real_fog_disappearance_reappearance(browser, http_base_url, tmp_path):
    scenario = make_scenario(make_map(rows=5, cols=1),
        [make_unit(hex='hex-0-1'), make_unit(faction='red', hex='hex-0-4', can_move=False)],
        max_phases=6)
    scenario['map']['fogOfWar'] = True
    with running_server(tmp_path, socket=True, scenario=scenario) as child:
        with ExitStack() as stack:
            pages = open_players(stack, browser, http_base_url, child.ready()['port'], ['blue','red'])
            b, r = pages['blue'], pages['red']
            phase(b, 0, 'blue')
            expect(b.locator('[id="red A"]')).to_have_count(0)
            expect(r.locator('[id="blue A"]')).to_have_count(0)
            for index, destination in enumerate(('hex-0-2','hex-0-1','hex-0-2')):
                action(b, 'mark '+destination)
                phase(r, 2*index+1, 'red')
                visible = 0 if index == 1 else 1
                expect(b.locator('[id="red A"]')).to_have_count(visible)
                expect(r.locator('[id="blue A"]')).to_have_count(visible)
                r.locator('#end-move').click()
                phase(b, 2*index+2, 'terminal' if index==2 else 'blue')
            child.wait()
            state = read_report(tmp_path)['state']
            assert state['status']['score'] == 0
            assert state['status']['isTerminal']
            assert state['units'][0]['hex'] == 'hex-0-2'


@pytest.mark.parametrize('control', ['reset', 'next-game'])
def test_terminal_controls_start_another_game(browser, http_base_url, tmp_path, control):
    scenario = load_fixture('scenarios/tiny_episode.json')['scenario']
    scenario['score']['maxPhases'] = 1
    with running_server(tmp_path, socket=True, scenario=scenario, reps=2) as child:
        with ExitStack() as stack:
            pages = open_players(stack, browser, http_base_url, child.ready()['port'], ['blue','red'])
            b, r = pages['blue'], pages['red']
            phase(b, 0, 'blue')
            b.locator('#end-move').click()
            for p in (b,r):
                phase(p, 1, 'terminal')
                expect(p.locator('#end-move')).to_be_disabled()
            b.locator('#'+control).click()
            if control == 'next-game':
                for p in (b,r):
                    expect(p.locator('#blue')).to_be_enabled()
                    expect(p.locator('#phase')).to_have_text('None')
                b.locator('#blue').click()
                r.locator('#red').click()
            else:
                b.wait_for_function("received.at(-1).type === 'reset'")
                expect(b.locator('#blue')).to_be_disabled()
            phase(b, 0, 'blue')
            b.locator('#end-move').click()
            for p in (b,r):
                phase(p, 1, 'terminal')
                expect(p.locator('#score')).to_have_text('0')
                assert p.evaluate("received.filter(m=>m.type==='parameters').length") == (2 if control=='next-game' else 1)
            child.wait()
            assert read_report(tmp_path)['reps_done'] == 2
