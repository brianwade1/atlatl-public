"""S11 unchanged map-editor page load/edit/export workflows over HTTP."""
import json
from urllib.parse import unquote
from xml.etree import ElementTree

import pytest

from tests.support.creation_pages import (creation_page, creation_map, prompt_load,
    copy_json, event, assert_fitted, hex_content)

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def test_draw_edit_copy_and_svg_export(page, http_base_url):
    with creation_page(page, http_base_url, 'map-editor'):
        for field, value in [('rows','3'), ('cols','2'), ('width','7')]:
            page.locator('#' + field).fill(value)
        page.locator('#draw').click()
        assert page.locator('[id^="hex-"]').count() == 6
        assert page.evaluate('Number(SVGCreateView.param.width)') == 7
        assert_fitted(page)
        page.locator('#fill-type-urban').click()
        page.locator('#hex-0-0').click()
        event(page, 'edge-type-river')
        event(page, 'mysvg')
        edge_id = page.evaluate('GameMap.edges[0].id')
        event(page, edge_id, 'mouseover')
        event(page, 'mysvg', 'mouseup')
        event(page, 'setup-type-blue')
        event(page, 'hex-0-1')
        event(page, 'mysvg', 'mouseup')
        data = copy_json(page)
        assert len(data['hexes']) == 6
        assert data['hexes'][0]['terrain'] == 'urban'
        assert next(h for h in data['hexes'] if (h['x_offset'],h['y_offset']) == (0,1))['setup'] == 'setup-type-blue'
        assert next(e for e in data['edges'] if e['id'] == edge_id)['type'] == 'river'
        page.locator('#save').click()
        uri = page.locator('#link').get_attribute('href')
        assert uri.startswith('data:image/svg+xml;charset=utf-8,')
        root = ElementTree.fromstring(unquote(uri.split(',',1)[1]))
        assert root.tag == '{http://www.w3.org/2000/svg}svg'
        nodes = {e.get('id'): e for e in root.iter() if e.get('id')}
        assert nodes['hex-0-0'].get('fill') == 'lightgray'
        assert nodes[edge_id].get('stroke') == 'blue'


def test_load_cancel_and_repeated_map_export(page, http_base_url):
    with creation_page(page, http_base_url, 'map-editor'):
        data = creation_map()
        prompt_load(page, 'load', data)
        first = copy_json(page)
        assert hex_content(first) == hex_content(data)
        assert_fitted(page)
        prompt_load(page, 'load', None)
        assert copy_json(page) == first
        data['hexes'][0]['terrain'] = 'water'
        prompt_load(page, 'load', data)
        assert hex_content(copy_json(page)) == hex_content(data)
        assert page.locator('#mysvg').count() == 1


def test_malformed_json_characterization(page, http_base_url):
    with creation_page(page, http_base_url, 'map-editor',
                       expected_errors=['Expected property name or \'}\' in JSON at position 1 (line 1 column 2)']):
        prompt_load(page, 'load', creation_map())
        before = copy_json(page)
        page.evaluate("window.promptInputs.push('{')")
        page.locator('#load').click()
        assert copy_json(page) == before


def test_native_clipboard_smoke(page, context, http_base_url):
    context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=http_base_url)
    with creation_page(page, http_base_url, 'map-editor', clipboard=False):
        prompt_load(page, 'load', creation_map())
        page.locator('#copy').click()
        assert hex_content(json.loads(page.evaluate('navigator.clipboard.readText()'))) == hex_content(creation_map())
