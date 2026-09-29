"""Serve explicit routes without importing browser/webserver.py."""

from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

from tests.support.imports import REPO_ROOT


class TestRequestHandler(SimpleHTTPRequestHandler):
    routes = {
        "/browser/": REPO_ROOT / "browser",
        "/tests/browser_support/": REPO_ROOT / "tests/browser_support",
        "/tests/fixtures/": REPO_ROOT / "tests/fixtures",
    }
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript"}

    def translate_path(self, path):
        decoded = unquote(urlsplit(path).path)
        for prefix, root in self.routes.items():
            if decoded.startswith(prefix):
                relative = decoded[len(prefix):]
                candidate = (root / relative).resolve()
                if candidate.is_relative_to(root.resolve()) and "\\" not in relative:
                    return str(candidate)
        return str(REPO_ROOT / "tests/.tmp/http-not-found/not-found")

    def list_directory(self, path):
        self.send_error(404)
        return None

    def log_message(self, format, *args):
        pass


@contextmanager
def serve_test_files():
    # Chromium can request the whole SVG module graph at once. A five-connection
    # listen backlog can refuse parallel imports on Windows even on loopback.
    class ModuleHTTPServer(ThreadingHTTPServer):
        request_queue_size = 128

    server = ModuleHTTPServer(("127.0.0.1", 0), TestRequestHandler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05},
                    name="atlatl-test-http", daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{url}/tests/browser_support/harness.html", timeout=5) as response:
            assert response.status == 200
        yield url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("Test HTTP server did not shut down")
