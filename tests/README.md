# Test harness

From the repository root, run the default core suite with:

```text
uv run pytest
```

Pytest automatically discovers the repository-root [pytest.ini](../pytest.ini).
The project environment now includes pytest, pytest-asyncio, pytest-playwright,
and pytest-cov, so no dependency overlay or explicit configuration path is needed.

S01 is implemented. Test code, fixture data, and generated artifacts remain under
`tests/`; pytest configuration lives at the repository root. Never edit `server/`,
`browser/`, or `scenarios/` to satisfy these tests. See [PROGRESS.md](PROGRESS.md)
for verified results and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for the defect policy.

Run from the repository root using Python 3.14+ and the project environment.
The original `requirements-test.in` and `requirements-test.txt` are retained as
an optional record of the tested S01 tool versions; normal runs do not use them.

Optional: keep uv downloads under `tests/` and disable bytecode from startup:

```powershell
# PowerShell
$env:UV_CACHE_DIR = Join-Path (Get-Location) 'tests/.cache/uv'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

```sh
# macOS/Linux
export UV_CACHE_DIR="$PWD/tests/.cache/uv"
export PYTHONDONTWRITEBYTECODE=1
```

Provision Chromium once, with network access:

```text
uv run python -B tests/support/install_browser.py
```

This downloads binaries into `tests/.cache/ms-playwright` and uses
`tests/.tmp/browser-install` for temporary files. Normal tests never download
browsers. Add `--offline` to the `uv run` commands after provisioning to forbid uv
network access. Pinned versions were verified on Windows/Python 3.14; other
platforms and browsers remain unverified.

```text
# Original assertions after pytest migration: five cases.
uv run pytest tests/test_scenario_loading.py -v

# Default lightweight suite: original baseline and server_unit harness checks.
uv run pytest

# Check default and full discovery without running tests.
uv run pytest --collect-only -q
uv run pytest tests --collect-only -q

# Explicit browser smoke test, including console/page-error checks.
uv run pytest tests/browser_unit -m browser --browser chromium

# All currently implemented tests, including the browser smoke test.
uv run pytest tests

# Python coverage; this does not instrument browser JavaScript.
uv run pytest --cov --cov-config=tests/coverage.ini --cov-report=term-missing --cov-report=html:tests/.artifacts/coverage-html
```

Run commands from the repository root: cache/output/test paths use that directory.
Neither `-c` nor `--rootdir` is needed.
`--basetemp=tests/.tmp/pytest` is reserved for pytest and is cleared on the next
run; do not store manual work there. Playwright traces/screenshots are retained
on failures under `tests/.artifacts/playwright`. Shared temporary files live in
`tests/.tmp/runtime`. Do not run concurrent pytest sessions against these paths.

Default discovery collects only `tests/test_scenario_loading.py` and
`tests/server_unit/`. `-m browser` alone does not expand collection. Explicitly
select `tests/browser_unit` or `tests/browser_integration` for browser tests,
`tests/server_integration` for future protocol checks, `tests/ml` for future ML
checks, and `tests/scripts` for isolated demonstrations. Empty selections return
pytest's nonzero exit status. Those future suites currently contain no cases.
Executable examples and cached dependency tests are outside default discovery;
pytest also excludes the dot-prefixed cache/temp/artifact directories.

The suite uses plain pytest functions, strict markers/configuration/xfails,
function-scoped strict asyncio loops, and Playwright's fresh context/page
fixtures. Required plugins fail configuration if missing; an explicitly selected
browser test fails setup if its binary is missing. Future optional suites must
provide similarly explicit dependency preflights, not blanket skips.

Use `engine_imports` and `import_server()` for flat engine modules: paths derive
from the helpers' file locations, module origins are asserted, and temporary
path/module entries are restored. For `azg` and `portabletorch`, use
`run_python(..., cwd=tmp_path)` to isolate import collisions and global state.
Inside that subprocess, `explicit_module(name, path)` can load `server/game.py`
as `game` or `server/azg/Game.py` as `Game`, restoring any previous module entry.
Do not import training scripts during collection. Builders and async helpers
are reserved for S02; empty scaffold files do not count as implemented coverage.

The local HTTP fixture binds loopback on an assigned port, checks readiness,
serves JavaScript with the correct MIME type, and shuts down after each test.
Routes expose only `/browser/`, `/tests/browser_support/`, and `/tests/fixtures/`.
It never imports the production fixed-port web server. Use `checked_page` to
collect console and uncaught JavaScript errors in browser tests.

Session hooks compare SHA-256 manifests before collection and after teardown,
including new/ignored files, as well as the protected directories' Git diff.
Existing user modifications form the baseline. A violation fails the session
and writes `tests/.artifacts/protected-paths.json`; it never reverts user files.
The checks detect persistent changes, not a transient write restored before the
final snapshot. The harness disables bytecode before importing production modules
and subprocesses also disable it. For no bytecode at all from startup, use
`uv run python -B -m pytest` or set `PYTHONDONTWRITEBYTECODE=1`.

Harness tests verify guard failures against a disposable tree, import restoration,
HTTP routing, and subprocess settings. They establish infrastructure, not game
rule coverage. No simulation changes or headless-game integration were added in
S01. S02 supplies fixtures; subsequent steps add behavioral coverage.
