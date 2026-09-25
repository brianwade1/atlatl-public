import pytest

from tests.support.browser_helpers import checked_page
from tests.support.imports import TESTS_DIR


@pytest.fixture
def module_page(page, http_base_url):
    page.add_init_script(path=TESTS_DIR / "browser_support/boundaries.js")
    with checked_page(page):
        page.goto(f"{http_base_url}/tests/browser_support/harness.html")
        yield page
