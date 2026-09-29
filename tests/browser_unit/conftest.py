import pytest

from tests.support.browser_models import model_page  # noqa: F401

from tests.support.browser_helpers import checked_page
from tests.support.imports import TESTS_DIR


@pytest.fixture
def module_page(page, http_base_url):
    page.add_init_script(path=TESTS_DIR / "browser_support/boundaries.js")
    with checked_page(page):
        page.goto(f"{http_base_url}/tests/browser_support/harness.html")
        yield page


@pytest.fixture
def svg_page(module_page):
    """Fresh HTTP page with real renderers and native SVG geometry (no mocks)."""
    module_page.set_viewport_size({"width": 1000, "height": 800})
    module_page.evaluate("() => import('/tests/browser_support/svg.js')")
    return module_page
