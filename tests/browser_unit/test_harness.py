"""S01 infrastructure smoke check, not browser game-rule coverage."""

import pytest

from tests.support.browser_helpers import checked_page


pytestmark = [pytest.mark.browser, pytest.mark.integration]


def test_production_es_module_loads_over_http(page, http_base_url):
    with checked_page(page):
        response = page.goto(f"{http_base_url}/tests/browser_support/harness.html")
        assert response.status == 200
        assert page.evaluate("""async () => {
            const { Combat } = await import('/browser/combat.js');
            return typeof Combat === 'object';
        }""") is True
