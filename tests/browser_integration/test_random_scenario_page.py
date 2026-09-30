"""S11 deterministic random page generation and same-page regeneration."""
import pytest

from tests.support.creation_pages import creation_page, oob, prompt_load, copy_json, assert_fitted
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def fixed_draws(page):
    # Finite nonzero sequence avoids Box-Muller rejection and gives east cities.
    page.evaluate('''() => {let remaining=2000; window.drawCount=0;
        Math.random=()=>{if(!remaining--) throw Error('Random sequence exhausted');
            window.drawCount++; return 0.25;};}''')


@pytest.mark.parametrize('rows,cols', [(10,10),(8,12)])
def test_generate_export_and_regenerate(page, http_base_url, rows, cols):
    with creation_page(page, http_base_url, 'random-scenario'):
        prompt_load(page, 'loadOob', oob())
        page.locator('#rows').fill(str(rows))
        page.locator('#cols').fill(str(cols))
        fixed_draws(page)
        for generation in range(2):
            page.locator('#generate').click()
            data = copy_json(page)
            assert set(data) == {'map','units'}  # page deliberately has no scoring controls
            hexes = data['map']['hexes']
            assert len(hexes) == rows*cols
            assert {h['terrain'] for h in hexes} <= {'clear','rough','marsh','water','urban'}
            cities = [h for h in hexes if h['terrain'] == 'urban']
            assert [(h['x_offset'],h['y_offset']) for h in cities] == [(6+(cols-6)//4,rows//4)]
            assert len({u['hex'] for u in data['units']}) == 2
            index = {f"hex-{h['x_offset']}-{h['y_offset']}":h for h in hexes}
            for unit in data['units']:
                h = index[unit['hex']]
                assert h['setup'] == 'setup-type-' + unit['faction']
                assert h['terrain'] != 'water'
                assert unit['homeOrgId'] == 'HQ' and unit['taskOrgId'] == 'TF'
            assert sum(h['setup']=='setup-type-blue' for h in hexes) >= 1
            assert sum(h['setup']=='setup-type-red' for h in hexes) >= 1
            assert all(h['x_offset'] <= 2 for h in hexes if h['setup']=='setup-type-blue')
            assert all(h['x_offset'] >= cols-3 for h in hexes if h['setup']=='setup-type-red')
            assert_fitted(page)
        assert page.evaluate('window.drawCount') > rows*cols


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K25: random geography assumes at least seven columns')
def test_small_dimensions(page, http_base_url):
    with creation_page(page, http_base_url, 'random-scenario',
                       defect_error=('K25', "Cannot read properties of undefined (reading 'setTerrain')")):
        prompt_load(page, 'loadOob', oob())
        page.locator('#rows').fill('3')
        page.locator('#cols').fill('3')
        fixed_draws(page)
        page.locator('#generate').click()
        assert page.evaluate('GameMap.hexes.length') == 9
    assert page.evaluate('Unit.units.every(u=>u.hex!==null)')


def test_cancel_oob_preserves_loaded_units(page, http_base_url):
    with creation_page(page, http_base_url, 'random-scenario'):
        prompt_load(page, 'loadOob', oob())
        prompt_load(page, 'loadOob', None)
        assert page.evaluate('Unit.units.map(u=>u.uniqueId)') == ['blue Alpha','red Bravo']


def test_repeated_oob_then_generate_characterization(page, http_base_url):
    with creation_page(page, http_base_url, 'random-scenario'):
        prompt_load(page, 'loadOob', oob())
        replacement = oob()[:1]
        replacement[0].update(uniqueId='blue New', longName='New')
        prompt_load(page, 'loadOob', replacement)
        fixed_draws(page)
        page.locator('#generate').click()
        data = copy_json(page)
        assert [u['uniqueId'] for u in data['units']] == ['blue New']
        # K20: discarded unplaced OOB records survive in the index, not occupancy.
        assert page.evaluate('Object.keys(Unit.unitIndex)') == ['blue Alpha','red Bravo','blue New']
        assert page.evaluate('Object.values(Unit.occupancy).flat().length') == 1


def test_empty_oob_can_generate_map(page, http_base_url):
    with creation_page(page, http_base_url, 'random-scenario'):
        prompt_load(page, 'loadOob', [])
        fixed_draws(page)
        page.locator('#generate').click()
        data = copy_json(page)
        assert data['units'] == [] and len(data['map']['hexes']) == 100
        assert_fitted(page)


def test_malformed_oob_characterization(page, http_base_url):
    with creation_page(page, http_base_url, 'random-scenario',
                       expected_errors=['Expected property name or \'}\' in JSON at position 1 (line 1 column 2)']):
        prompt_load(page, 'loadOob', oob())
        page.evaluate("window.promptInputs.push('{')")
        page.locator('#loadOob').click()
        assert page.evaluate('Unit.units.map(u=>u.uniqueId)') == ['blue Alpha','red Bravo']
