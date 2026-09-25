"""S02 boundary installation and actual DOM/module consumers."""

import pytest

from tests.support.browser_helpers import checked_page

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def test_module_fixture_geometry_and_same_page_reload(module_page, hex_geometry):
    for _ in range(2):
        result = module_page.evaluate('''async data => {
            const {Map} = await import('/browser/map.js');
            Map.fromPortable(data.map);
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            document.querySelector('#fixture').append(svg);
            return {count: Map.hexes.length, center: [Map.hexIndex['hex-1-1'].x_grid,
                Map.hexIndex['hex-1-1'].y_grid], namespace: svg.namespaceURI,
                draw: Math.random()};
        }''', hex_geometry)
        assert result == {"count": 12, "center": [5, 5],
                          "namespace": "http://www.w3.org/2000/svg", "draw": 0.25}
        # Real reload, no manual clearing of module indexes/state.
        module_page.reload()


def test_browser_boundaries_are_finite_and_contexts_independent(module_page, new_context, http_base_url):
    values = module_page.evaluate('''() => {
        const socket = new WebSocket('ws://test.invalid');
        let received;
        socket.onmessage = event => { received = event.data; };
        socket.open(); socket.send('out'); socket.receive('in'); socket.close();
        const draws = Array.from({length: 6}, () => Math.random());
        let error;
        try { Math.random(); } catch (e) { error = e.message; }
        localStorage.setItem('player', 'blue');
        return {sent: socket.sent, received, state: socket.readyState, draws, error};
    }''')
    assert values == {"sent": ["out"], "received": "in", "state": 3,
                      "draws": [0.25, 0.75, 0.5, 0.125, 0.875, 0.375],
                      "error": "Deterministic random sequence exhausted"}
    second = new_context().new_page()
    with checked_page(second):
        second.goto(f"{http_base_url}/tests/browser_support/harness.html")
        assert second.evaluate("localStorage.getItem('player')") is None


@pytest.mark.parametrize("kind", ["console", "pageerror", "request", "dialog"])
def test_browser_error_capture_fails_precisely(page, http_base_url, kind):
    with pytest.raises(AssertionError, match="Browser errors|Uncaught browser errors"):
        with checked_page(page):
            page.goto(f"{http_base_url}/tests/browser_support/harness.html")
            if kind == "console":
                page.evaluate("console.error('intentional console failure')")
            elif kind == "pageerror":
                with page.expect_event("pageerror"):
                    page.evaluate("setTimeout(() => { throw new Error('intentional uncaught'); }, 0)")
            elif kind == "request":
                page.route("**/intentional-failure", lambda route: route.abort())
                page.evaluate("fetch('/intentional-failure').catch(() => {})")
            else:
                page.evaluate("alert('intentional dialog')")
