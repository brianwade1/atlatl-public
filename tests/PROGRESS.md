# Test implementation progress

Current invocation (2026-09-24): `uv run pytest` from the repository root.
The root `pytest.ini` and installed project plugins supersede the test-local
configuration/overlay commands in the historical entries below.

## 2026-09-23 — S01 completed

The request's “501” is interpreted as **S01 — Establish the harness and baseline**
in `../test_plan.md`. The root plan is unchanged because implementation is limited
to `tests/`. S02–S17 remain unimplemented; scaffolding is not behavioral coverage.

Revision: `581cdc3440a7939db2e0575ae8645ae6406ec10a` plus pre-existing user changes.
Existing changes to `.gitignore`, `pyproject.toml`, `uv.lock`, PortableTorch files,
and untracked planning/demo files were preserved.

Environment: Windows 11 (`10.0.26200`), CPython 3.14.4 (64-bit), uv 0.12.5,
pytest 9.1.1, pluggy 1.6.0, pytest-asyncio 1.4.0, pytest-playwright 0.9.0,
pytest-base-url 2.1.0, pytest-cov 7.1.0, coverage 7.16.1, Playwright 1.63.0.
Chromium: Chrome for Testing 153.0.8010.12, Playwright build 1243.
All 22 test-tool dependencies are pinned in `requirements-test.txt`.
No application dependencies were installed or upgraded.

### Deliverables and case mapping

| S01 item | Result |
| --- | --- |
| 1. Baseline and migration | Original 4 methods + 2 alias subtests passed; migrated 5 pytest cases passed. |
| 2. Organization | Test-local configuration, documentation, support modules, fixture and suite directories created. Builders/async helpers and future suites are explicitly reserved. |
| 3. Import isolation | File-derived paths, origin checks, flat-engine context, explicit named-module loading/restoration, bounded subprocess helper. |
| 4. Pytest configuration | Importlib mode, strict configuration/markers/xfails, explicit default paths, function-scoped strict asyncio, required plugins and registered suite/type markers. |
| 5. Dependencies | Test-only requirements resolved; pinned overlay and plugins executed with Python 3.14.4. |
| 6. HTTP/browser | Loopback/assigned-port server with readiness, MIME types, restricted routes, cleanup, and real Chromium module-load/console check. |
| 7. Write guard | Before-collection/after-teardown content manifests and protected Git diff; added/changed/deleted cases fail on disposable trees without reverting files. Finish check also runs if another finish hook raises. |
| 8. Artifacts | Cache, temporary work, browser binaries, coverage configuration, and failure artifacts stay under ignored test-local directories. |

Baseline nodes remain in `tests/test_scenario_loading.py`. Each original
`ScenarioPathTests.test_*` method maps to the same pytest function name:

| Original method | Migrated node(s) | Preserved assertions |
| --- | --- | --- |
| `test_launcher_preserves_bare_filenames_and_generator_names` | Same function | Bare filename and generator name are unchanged. |
| `test_launcher_makes_explicit_relative_path_absolute` | Same function | Expected authored scenario path; cwd restored by monkeypatch. |
| `test_bare_filename_uses_default_scenario_directory` | Same function | Bare path resolves under server/scenarios. |
| `test_packaged_aliases_load_expected_scenarios` | Same function, `[lydian-republic]` and `[ordan-basin]` | Lydian 280 hexes/21 units; Ordan 144 hexes/26 units. |

New harness nodes in `tests/server_unit/test_harness.py`:

- `test_protected_manifest_fails_session_without_reverting[added/changed/removed]`
  (three separate cases; synthetic files only, including an untracked `.pyc`).
- `test_flat_engine_import_checks_provenance_and_restores_state`.
- `test_explicit_import_restores_colliding_module[normal/import-error]`
  (two separate cases; synthetic module with independently chosen value 42).
- `test_subprocess_uses_test_local_working_directory_and_no_bytecode`.
- `test_http_serves_javascript_and_limits_routes`.

Browser node:
`tests/browser_unit/test_harness.py::test_production_es_module_loads_over_http[chromium]`.
It imports unchanged `browser/combat.js` over HTTP and checks the exported object,
with no console or uncaught page errors. It does not claim combat-table coverage.

### Commands and results

All commands ran from the repository root. After the initial cache-access error,
all uv commands used these environment settings:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) 'tests/.cache/uv'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

Setup commands:

```text
uv pip compile tests/requirements-test.in --output-file tests/requirements-test.txt
uv run --no-sync --with-requirements tests/requirements-test.txt python -B tests/support/install_browser.py
```

For compactness, `P` in the table below expands exactly to:

```text
uv run --offline --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=.
```

| Invocation | Collected / result | Pytest duration |
| --- | --- | --- |
| `uv run --no-sync python -B -m pytest tests/test_scenario_loading.py -q -p no:cacheprovider` (before migration/configuration) | 4 passed, 2 subtests passed | 0.01s |
| `P tests/test_scenario_loading.py -v` | 5 passed; one sandbox cache warning | 0.53s |
| `P tests -v` (approved execution outside sandbox) | 14 passed | 6.17s |
| `P --collect-only -q` | 13 collected; browser excluded | 0.03s |
| `P tests --collect-only -q` | 14 collected; no examples, fixture sources, or dependency tests | 0.04s |
| `P -q` (final core configuration) | 13 passed | 0.65s |
| `P tests/browser_unit -m browser --browser chromium -q` (final runtime-temp configuration) | 1 passed | 1.69s |

Successful execution runs had **0 failed, 0 XFAIL, 0 XPASS, 0 skipped, and
0 deselected**. Full collection/execution is limited to currently implemented
S01 cases. The full run and subsequent default run also exercised the baseline
before/after harness checks in different file orders.

Environment failures recorded separately:

- Initial baseline invocation could not access uv's default AppData cache; using
  `tests/.cache/uv` resolved it before any baseline tests were changed.
- Initial dependency resolution could not reach PyPI through the sandbox;
  approved network execution resolved and installed the test-only overlay.
- First sandboxed full run collected 14 cases: 7 reached PASS, 7 errored in
  setup, followed by a pytest cleanup exception. Windows denied pytest temp
  directory access and Playwright named pipes. The same full command passed
  outside the sandbox. These were environment errors, not xfails or skips.

No production defect IDs were assigned. macOS, Linux, alternate Python versions,
and additional browser engines remain unverified. Coverage configuration was
added; no coverage percentage is claimed. No headless game was run because this
step adds harness infrastructure and preserves baseline loading assertions,
without changing simulation code or adding engine behavior tests.

### Protected paths and cleanup

All successful configured sessions reported **315 protected files**, no added,
removed, or changed files, and an unchanged protected Git diff. An independent
comparison against `tests/.artifacts/protected-before.json`, captured before
implementation, also found no differences. Existing source edits remain intact.
Final Git status outside `tests/` matches the initial status.

Owned HTTP servers stop in fixture teardown; Playwright closes its browser via
the plugin fixtures; subprocesses use bounded waits. Test caches/binaries and
disposable temporary outputs remain ignored under `tests/` for reuse. The latest
session report is `tests/.artifacts/protected-paths.json`. No production files
were deleted, reverted, regenerated, or edited.

Next smallest task: **S02**, deterministic fixture data/builders and expanded
isolation helpers. Do not count the reserved modules/directories as S02 work.

## 2026-09-23 — Unconfigured pytest invocation

Reproduced the reported four warnings and interrupted collection using
`uv run --offline --no-sync python -B -m pytest --collect-only -q -p no:cacheprovider`
with the test-local uv cache. Root-level discovery did not load `tests/pytest.ini`:
four unknown-marker warnings preceded an import mismatch between the browser and
server `test_harness.py` modules. The application environment also does not include
the test overlay's plugins.

Added an early configuration check in `tests/conftest.py` that reports the exact
supported command instead of collecting with missing configuration; added the
command and explanation at the top of `tests/README.md`. No root configuration or
production file was changed. A plain invocation still requires the explicit
configuration and dependency overlay; this is now an actionable setup error.

Validation: the unconfigured collection now exits nonzero with only the setup
message and no marker warnings. Using the `P -q` command defined above passes
**13 tests in 0.71s**, with zero failures, warnings, skips, XFAIL, or XPASS.

## 2026-09-24 — Root pytest configuration

With user authorization, moved `tests/pytest.ini` to repository-root `pytest.ini`.
Its test selection, cache, temporary, and Playwright output paths already used
repository-root-relative paths and remain under `tests/`. `pythonpath = .` now
also resolves directly to the repository root. Removed the obsolete test-local
configuration guard from `tests/conftest.py` and simplified the README commands
to use the plugins the user installed in the project environment. Updated the
browser installer description; retained the original requirements files as a
historical/optional version record. No production files were edited.

Validation on Windows/Python 3.14.4 with the project environment:

- `uv run pytest`: **13 passed in 0.84s**, root configuration auto-discovered.
- `uv run pytest tests -q`: **14 passed in 12.61s**, including Chromium.

Both runs had zero warnings, failures, skips, XFAIL, or XPASS. Commands used
`UV_CACHE_DIR=tests/.cache/uv` and approved execution outside the Windows sandbox
for pytest temporary directories/browser pipes. No test dependency overlay,
explicit configuration argument, or rootdir override was used. Both protection
reports checked 315 files with no added, removed, or changed protected files
and no protected Git diff change. Source directories remain untouched.
