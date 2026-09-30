"""Unchanged play.html, with either a recording socket or a real endpoint override."""

import pytest

from tests.support.browser_helpers import checked_page
from tests.support.builders import make_map, make_scenario, make_unit, make_state
from tests.support.imports import TESTS_DIR


def scenario():
    return make_scenario(make_map(rows=3, cols=2,
        terrain_overrides={(1, 1): 'urban'},
        setup_overrides={(0, 0): 'setup-type-blue', (0, 1): 'setup-type-blue',
                         (0, 2): 'setup-type-red'}),
        [make_unit(), make_unit(name='B', hex='hex-1-0'),
         make_unit(faction='red', hex='hex-0-2')])


def expose(page):
    page.evaluate('''async () => {
        for (const [file,name] of [['play','Play'],['human-player-control','HumanPlayerControl'],
            ['unit','Unit'],['map','Map'],['svg-unit-symbol','SVGUnitSymbol'],
            ['svg-setup-marker','SVGSetupMarker'],['svg-city-marker','SVGCityMarker']]) {
            window[name === 'Map' ? 'GameMap' : name] = (await import('/browser/'+file+'.js'))[name];
        }
    }''')


def deliver(page, message):
    page.evaluate('(m) => testSockets[0].receive(JSON.stringify(m))', message)


def observe(page, **kwargs):
    units = kwargs.pop('units', scenario()['units'])
    deliver(page, {'type': 'observation', 'observation': make_state(units, **kwargs)})


def sent(page):
    return page.evaluate('testSockets[0].sent.map(s => JSON.parse(s))')


def down(page, element_id):
    page.locator('[id="' + element_id + '"]').dispatch_event('mousedown')


def marks(page):
    return page.locator('[id^="mark "]').count()


@pytest.fixture
def play_page(page, http_base_url):
    page.add_init_script(path=TESTS_DIR / 'browser_support/boundaries.js')
    with checked_page(page):
        page.goto(http_base_url + '/browser/play.html')
        expose(page)
        page.evaluate('testSockets[0].open()')
        deliver(page, {'type': 'parameters', 'parameters': scenario()})
        yield page


def real_page(context, port):
    page = context.new_page()
    page.add_init_script('''(() => {
        const Native = window.WebSocket;
        window.received = [];
        window.WebSocket = class extends Native {
            constructor(url, ...args) {
                super(url === 'ws://localhost:9999' ? 'ws://127.0.0.1:PORT' : url, ...args);
                this.addEventListener('message', e => received.push(JSON.parse(e.data)));
            }
        };
    })();'''.replace('PORT', str(port)))
    return page
