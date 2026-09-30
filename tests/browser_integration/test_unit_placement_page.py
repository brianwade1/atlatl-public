"""S11 placement page workflows and exported scenario engine acceptance."""
import json

import pytest

from tests.support.creation_pages import (creation_page, creation_map, oob, scenario,
    prompt_load, copy_json, event, assert_fitted, hex_content)
from tests.support.imports import import_server, REPO_ROOT
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def test_map_oob_edit_export_and_engine_roundtrip(page, http_base_url, tmp_path, engine_imports, rng):
    with creation_page(page, http_base_url, 'unit-placement'):
        prompt_load(page, 'loadMap', creation_map())
        prompt_load(page, 'loadOob', oob())
        assert_fitted(page)
        assert [u['hex'] for u in copy_json(page)['units']] == ['hex-0-0','hex-2-1']
        full_view = page.locator('#mysvg').get_attribute('viewBox')
        page.locator('[id="blue Alpha"]').click(modifiers=['Shift'])
        # This tiny fitted map is already smaller than the zoom target.
        assert page.locator('#mysvg').get_attribute('viewBox') == full_view
        page.locator('[id="blue Alpha"]').click(modifiers=['Shift'])
        assert page.locator('#mysvg').get_attribute('viewBox') == full_view
        event(page, 'hex-0-1')  # Shift did not leave a selected unit.
        assert copy_json(page)['units'][0]['hex'] == 'hex-0-0'
        event(page, 'blue Alpha')
        event(page, 'hex-0-1')
        event(page, 'blue Alpha')
        event(page, 'red Bravo')
        for field, value in [('maxPhases','8'), ('lossPenalty','-3.5'), ('cityScore','12.5')]:
            page.locator('#' + field).fill(value)
        page.locator('#fogOfWarId').check()
        data = copy_json(page)
    assert set(data) == {'map','units','score'}
    assert data['score'] == {'maxPhases':8,'lossPenalty':-3.5,'cityScore':12.5}
    assert data['map']['fogOfWar'] is True
    assert hex_content(data['map']) == hex_content(creation_map())
    assert [(u['hex'],u['type'],u['faction'],u['currentStrength']) for u in data['units']] == [
        ('hex-2-1','infantry','blue',73), ('hex-0-1','infantry','red',91)]
    assert all(u['echelon'] == 'regiment' and u['fullStrength'] == 100 for u in data['units'])
    path = tmp_path / 'export.scn'
    path.write_text(json.dumps(data), encoding='utf-8')
    loaded = import_server('scenario').from_file_factory(path)()
    assert loaded == data
    game = import_server('game').Game(loaded)
    state = game.initial_state()
    assert game.parameters()['map']['fogOfWar'] is True
    assert [(h.id,h.setup) for h in game.mapData.hexIndex.values() if h.setup] == [
        ('hex-0-0','setup-type-blue'), ('hex-0-1','setup-type-blue'),
        ('hex-2-1','setup-type-red'), ('hex-2-2','setup-type-red')]
    status = import_server('status').Status(loaded, game.mapData)
    assert (status.max_phases,status.score_per_blue_kill,status.total_city_score_per_phase) == (8,-3.5,12.5)
    assert [(u['hex'],u['type'],u['faction'],u['currentStrength']) for u in state['units']] == [
        (u['hex'],u['type'],u['faction'],u['currentStrength']) for u in data['units']]
    assert state['status']['setupMode'] is True
    action = game.legal_actions(state)[0]
    assert action == {'type':'pass'}
    after = game.transition(state, action)
    assert after['status']['onMove'] == 'red'


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K24: scenario load ignores score/fog controls')
def test_scenario_restores_score_and_fog(page, http_base_url):
    with creation_page(page, http_base_url, 'unit-placement'):
        source = scenario()
        prompt_load(page, 'loadScn', source)
        result = copy_json(page)
        assert [u['hex'] for u in result['units']] == ['hex-0-0','hex-2-2']
        if result['score'] == dict(maxPhases=20,lossPenalty=-2,cityScore=24) and result['map']['fogOfWar'] is False:
            raise KnownDefect('K24: score defaults and unchecked fog replace loaded values')
        assert result['score'] == source['score']
        assert result['map']['fogOfWar'] is True


@pytest.mark.parametrize('control', ['loadMap','loadOob'])
def test_canceled_prompts_preserve_export(page, http_base_url, control):
    with creation_page(page, http_base_url, 'unit-placement'):
        prompt_load(page, 'loadScn', scenario())
        before = copy_json(page)
        prompt_load(page, control, None)
        assert copy_json(page) == before


@pytest.mark.parametrize('control', ['loadMap','loadOob','loadScn'])
def test_malformed_prompts_characterization(page, http_base_url, control):
    with creation_page(page, http_base_url, 'unit-placement',
                       expected_errors=['Expected property name or \'}\' in JSON at position 1 (line 1 column 2)']):
        prompt_load(page, 'loadScn', scenario())
        before = copy_json(page)
        page.evaluate("window.promptInputs.push('{')")
        page.locator('#' + control).click()
        assert copy_json(page) == before


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K24: cancel scenario prompt dereferences null')
def test_cancel_scenario_prompt(page, http_base_url):
    with creation_page(page, http_base_url, 'unit-placement',
                       defect_error=('K24', "Cannot read properties of null (reading 'map')")):
        prompt_load(page, 'loadScn', scenario())
        before = copy_json(page)
        prompt_load(page, 'loadScn', None)
        assert copy_json(page) == before


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K24: zero units dereferences first unit')
def test_empty_oob(page, http_base_url):
    with creation_page(page, http_base_url, 'unit-placement',
                       defect_error=('K24', "Cannot read properties of undefined (reading 'hex')")):
        prompt_load(page, 'loadMap', creation_map())
        prompt_load(page, 'loadOob', [])
        assert copy_json(page)['units'] == []


def test_insufficient_setup_cells_characterization(page, http_base_url):
    with creation_page(page, http_base_url, 'unit-placement',
                       expected_errors=['No available setup hex for unit']):
        data = creation_map()
        for h in data['hexes']:
            if h['setup'] == 'setup-type-red':
                h['setup'] = None
        prompt_load(page, 'loadMap', data)
        prompt_load(page, 'loadOob', oob())
        assert page.evaluate('Unit.units.map(u=>u.hex?.id??null)') == ['hex-0-0', None]


@pytest.mark.parametrize('control', ['loadMap','loadOob','loadScn'])
def test_repeated_load_lifecycle_characterization(page, http_base_url, control):
    with creation_page(page, http_base_url, 'unit-placement'):
        prompt_load(page, 'loadScn', scenario())
        if control == 'loadMap':
            prompt_load(page, control, creation_map())
            assert page.locator('[id="blue Alpha"]').count() == 0
            assert len(copy_json(page)['units']) == 2  # model survives removed SVG
            assert page.evaluate("Unit.units[0].hex === GameMap.hexIndex['hex-0-0']") is False
        else:
            prompt_load(page, control, scenario() if control == 'loadScn' else oob())
            assert len(copy_json(page)['units']) == 2
            assert page.evaluate('Object.values(Unit.occupancy).reduce((n,a)=>n+a.length,0)') == 4


@pytest.mark.parametrize('source', ['test-input','sample'])
def test_display_inputs_smoke(page, http_base_url, source):
    with creation_page(page, http_base_url, 'unit-placement'):
        if source == 'test-input':
            page.locator('#test').click()
        else:
            prompt_load(page, 'loadMap', creation_map())
            data = json.loads((REPO_ROOT / 'browser/sample-oobs/oob-all-symbols.json').read_text())
            # A large clear map avoids imposing engine or setup limits on display data.
            from tests.support.builders import make_map
            prompt_load(page, 'loadMap', make_map(10,10))
            prompt_load(page, 'loadOob', data)
        exported = copy_json(page)
        assert len(exported['units']) > 0
        assert len({u['hex'] for u in exported['units']}) == len(exported['units'])
        assert_fitted(page)


def test_scenario_reload_uses_current_controls_characterization(page, http_base_url):
    with creation_page(page, http_base_url, 'unit-placement'):
        prompt_load(page, 'loadScn', scenario())
        page.locator('#maxPhases').fill('37')
        page.locator('#fogOfWarId').check()
        replacement = scenario()
        replacement['map']['fogOfWar'] = False
        prompt_load(page, 'loadScn', replacement)
        data = copy_json(page)
        assert data['score']['maxPhases'] == 37
        assert data['map']['fogOfWar'] is True


def test_large_map_native_shift_zoom_and_restore(page, http_base_url):
    from tests.support.builders import make_map

    with creation_page(page, http_base_url, 'unit-placement'):
        prompt_load(page, 'loadMap', make_map(10,10))
        prompt_load(page, 'loadOob', oob())
        before = copy_json(page)
        full = page.locator('#mysvg').get_attribute('viewBox')
        page.locator('[id="blue Alpha"]').click(modifiers=['Shift'])
        assert page.locator('#mysvg').get_attribute('viewBox') != full
        page.locator('[id="blue Alpha"]').click(modifiers=['Shift'])
        assert page.locator('#mysvg').get_attribute('viewBox') == full
        assert copy_json(page) == before
