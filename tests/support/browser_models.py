"""S09 model harness: real modules, with only symbol rendering recorded."""

import pytest

from tests.support.browser_helpers import checked_page
from tests.support.imports import TESTS_DIR


@pytest.fixture
def model_page(page, http_base_url):
    page.add_init_script(path=TESTS_DIR / "browser_support/boundaries.js")
    with checked_page(page):
        page.goto(f"{http_base_url}/tests/browser_support/harness.html")
        page.evaluate('''async () => {
            for (const [file, name] of [['map','Map'], ['unit','Unit'],
                ['mobility','Mobility'], ['combat','Combat'],
                ['terrain','Terrain'], ['style','Style']]) {
                window[name === 'Map' ? 'GameMap' : name] = (await import(`/browser/${file}.js`))[name];
            }
            const {SVGUnitSymbol} = await import('/browser/svg-unit-symbol.js');
            window.symbolCalls = [];
            SVGUnitSymbol.create = (unit, handler) => {
                symbolCalls.push({id: unit.uniqueId, hex: unit.hex.id,
                                  handler: typeof handler});
            };
        }''')
        yield page
