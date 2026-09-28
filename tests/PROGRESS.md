# Test implementation progress

Current invocation (2026-09-24): `uv run pytest` from the repository root.
The root `pytest.ini` and installed project plugins supersede the test-local
configuration/overlay commands in the historical entries below.

## 2026-09-25 — S04 completed

Implemented **S04 — Server units, movement, targeting, and detection**.
S01–S04 are complete; S05–S17 remain open. Starting revision:
`36beedec3c6f03ed4d4ffd5378617e5ef6384ec6`. Preserved the pre-existing untracked
`demo_script.txt`. Changes are limited to `tests/` and root `test_plan.md`.

Added **84 passing unit cases** in the three planned files:

- `server_unit/test_unit_state.py`: constructor/default flags, fractional strength,
  registration and faction filtering, empty/unplaced units, duplicate-ID
  characterization, placement/removal/replacement, stacking limits, faction action
  flags, visible-hidden-visible occupancy, ineffective removal, fog input rejection
  and independent portable copies that omit detection.
- `server_unit/test_unit_movement.py`: both movement entry points, all four unit
  types and six terrain types, exact and exceeded budgets, occupied destinations
  and intermediates, increased stacking, boundaries/origin exclusion/uniqueness,
  alternative routes checked against independent Bellman-Ford relaxation over a
  literal six-cell graph; fire filters, both parities, artillery range two, and
  controlled thresholds distinguishing Euclidean distance from hex-step distance.
- `server_unit/test_unit_visibility.py`: below/equal/above probability draws,
  independent detection directions, retained detection at the sight boundary,
  clearing outside sight and reacquisition, friendly/ineffective/empty groups,
  asymmetric observer sight, exact white/blue/red export fields, export side effects,
  removed-unit masking and live-unplaced-unit exception characterizations.

Added a small `unit_world` fixture to load real map/unit objects using the S02
builders and portable movement fixtures. No production algorithm is mocked.
Rule overrides use restoring monkeypatch fixtures and detection draws are finite
at the production lookup site. The shortest-path oracle agreed on all tested
default-rule routes. No new defect ID or xfail was added. KNOWN_ISSUES records
K05's confirmed serialization side effect and unsupported-input characterizations;
other K05 portions remain for S05/S06. README and the plan checklist are updated.

### Validation

Windows / Python 3.14.4, existing project environment. Test commands used
`UV_CACHE_DIR=tests/.cache/uv` and `PYTHONDONTWRITEBYTECODE=1`:

| Command | Result |
| --- | --- |
| `uv run --offline --no-sync pytest tests/server_unit/test_unit_state.py tests/server_unit/test_unit_movement.py tests/server_unit/test_unit_visibility.py -q` | **84 passed in 4.58s**; one sandbox cache-permission warning. |
| `uv run --offline --no-sync pytest tests -q` (approved outside sandbox) | **253 passed, 9 existing xfailed in 62.54s**. |

The full suite includes existing Chromium, async and CPU-model checks, with
**0 failed, 0 warnings, 0 skipped, 0 XPASS and 0 deselected**. All 169 previous
passing cases and nine K01/K02 expected failures retain their outcomes.
The protection report checks **315 files**, with no additions, removals or content
changes and unchanged protected Git diff. `git diff --check` passed.

A documentation-edit helper initially invoked uv without the test-local cache
environment and failed before running Python because the default AppData cache
was inaccessible; rerunning through the existing environment's Python succeeded.
No dependency or configuration changes were required. No launcher smoke game
was needed for test-only work; the full suite includes the existing bounded
deterministic engine episode. Other platforms and Python versions are unverified.

Next step: **S05 — Test game transitions, setup, combat, phases, and scoring**.

## 2026-09-25 — S03 completed

Implemented **S03 — Server geometry, serialization, and rule tables**. S01–S03
are complete; S04–S17 remain open. Starting revision:
`50be5e0a5a350112e223400f0e2d8b0d1a50ede1`. Preserved the pre-existing untracked
`demo_script.txt`. Changes are limited to `tests/` and root `test_plan.md`;
no dependencies, configuration or production files changed.

Added **92 unit cases** in the three planned files:

- `server_unit/test_map_geometry.py`: independent positive/negative coordinate
  vectors and cube round trips; all six directions for both parities; reciprocal
  directions, corner/edge truncation and non-neighbors; distinct Euclidean and
  hex distances; ordered vertices; empty/single/rectangular grids, cities and setup.
- `server_unit/test_map_serialization.py`: explicit portable hex/edge fields,
  generic loaders, forward edge reuse, JSON round trips and input/output ownership;
  replacement of hex/edge indexes; separate minimal K01/K02 reproductions for
  reverse lookup, duplicate shared edges, path export/load, cached dimensions,
  retained hexes and stale path references. Nine individual strict xfails match
  only documented wrong signatures via `KnownDefect`.
- `server_unit/test_rule_tables.py`: independent numeric constants for all 24
  mobility and 24 terrain-multiplier combinations, all 16 attacker/target pairs
  for both offensive and defensive firepower, every range/sight/scalar rule,
  table domains and explicitly named characterization of shared row identities.

Reused S02's independent vertex fixture and portable builders. No production
behavior is mocked or patched. K01/K02 are now runtime-confirmed for Python;
browser portions and K03–K18 remain unconfirmed. Updated KNOWN_ISSUES with exact
nodes, commands, expected contracts and observed signatures, README with the
focused invocation, and the root plan checklist/status.

### Validation

Windows / Python 3.14.4, existing project environment. Both commands used
`UV_CACHE_DIR=tests/.cache/uv` and `PYTHONDONTWRITEBYTECODE=1`:

| Command | Result |
| --- | --- |
| `uv run --offline --no-sync pytest tests/server_unit/test_map_geometry.py tests/server_unit/test_map_serialization.py tests/server_unit/test_rule_tables.py -q` (initial sandbox run) | 83 passed, 8 xfailed, 1 failed, 2 cache-permission warnings in 19.17s. |
| `uv run --offline --no-sync pytest tests -q` (final, approved outside sandbox) | **169 passed, 9 xfailed in 207.58s**. |

The initial failure was the intentionally narrow path exception matcher: Python
3.14 includes `and no __dict__ for setting new attributes` in its AttributeError.
The test now accepts that exact observed message as well as the exact older
wording, while unrelated exceptions still propagate. No production fix was made.
The final complete suite includes existing Chromium, async and CPU-model checks:
**0 failed, 0 warnings, 0 skipped, 0 XPASS, 0 deselected**. S03 contributes 83
passes and 9 expected failures; all 86 pre-existing cases still pass.

The protection report checks **315 files**, with no added, removed or changed
protected files and unchanged protected Git diff. `git diff --check` passed.
No launcher smoke game was needed for test-only work; the full suite includes
the existing deterministic bounded engine episode. Browser behavior for these
new cases, other operating systems and other Python versions remain unverified.
No coverage percentage is claimed. Generated artifacts remain ignored under tests.

Next step: **S04 — Test server units, movement, targeting, and detection**.

## 2026-09-25 — S02 completed

Implemented **S02 — Build fixtures and isolation helpers**. S01-S02 are complete;
S03-S17 remain open. The root plan checklist and current test/fixture READMEs
are updated. Revision at start: `295e98303e7e4ac66cc1af3233908e7479d97193`.
The pre-existing untracked `demo_script.txt` was preserved. All implementation
changes are under `tests/`; only `test_plan.md` changed at the root. Dependencies,
root pytest configuration and production directories were not modified.

### Deliverables

- Pure fresh portable builders and function-scoped factory fixtures for maps,
  units, scenarios and states, with explicit defaults and deep-copy ownership.
- All twelve S02 fixture families, with adjacent explanations and documented
  schemas in [fixtures/README.md](fixtures/README.md). Geometry centers, vertices
  and neighbors are hand-tabulated independently of production geometry.
  Movement fixtures cover exact/over-budget, blocked and alternative routes;
  a scripted four-phase episode has independently calculated final score 50.
- Python/NumPy RNG restoration, optional CPU Torch seed/settings restoration,
  finite detection draws patched at `unit.random`, and nonzero finite browser
  draws. No training, GPU requirement, model download or random action selection.
- Global preservation retains nested dict/list/set identities and table aliases,
  including registry option dictionaries. Fixtures protect rule tables, both
  registries, current-game binding, transport IDs/sleep and loaded AI counters;
  explicit guards cover late-loaded server/gym bindings and PortableTorch count.
- Recording function clients, finite async iterators/WebSocket doubles, finite
  dispenser and game tree, and controlled prediction collaborator. Consumers
  use the real ClientWrapper to validate wire/callback signatures.
- Immediate task registration, bounded cancel/await cleanup, synchronous owned
  loop cleanup/restoration, test-local numeric archives removed at teardown,
  fixed child hash seed, inherited model-path filtering and captured subprocess
  diagnostics. Failure-path consumers deliberately raise then check restoration.
- Browser boundaries installed before navigation/imports, real DOM/SVG nodes,
  unchanged `/browser/map.js` import, same-page navigation reloads, separate
  player contexts and strict console/page/request/dialog capture. Error-capture
  consumers intentionally provoke each error and assert that it fails.

Added **72 collected cases**: 55 fixture consumers, 10 isolation/double consumers,
6 browser consumers and 1 isolated CPU-model preflight. Existing 14 S01 cases
remain. Terrain/type, coordinate parity/subsets, factions, city ownership,
registry options and action-index cases use parametrization. Cooperating engine
consumers and real browser/ML boundaries are marked integration; isolated helper
and geometry operations are marked unit. This validates fixtures and isolation,
not completion of the later engine/UI/protocol/ML behavioral steps.

### Validation and resolved harness problems

Commands ran from the root with the existing Windows/Python 3.14.4 project
environment and installed plugins. Environment settings:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) 'tests/.cache/uv'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

| Command | Result |
| --- | --- |
| `uv run --offline --no-sync pytest tests/server_unit/test_fixtures.py -q` (sandbox) | 46 passed, 1 setup error, 3 warnings: existing Windows temp/cache permission restriction. |
| `uv run --offline --no-sync pytest tests -q` (first full run, approved outside sandbox) | 76 passed, 2 failed: sync Playwright/pytest-asyncio loop conflict; associated teardown warnings. |
| Same full command after lifecycle correction and expanded inputs | 85 passed in 58.96s. |
| `uv run --offline --no-sync pytest -q` (final core cases) | **78 passed in 28.46s**. |
| `uv run --offline --no-sync pytest tests -q` (final complete suite) | **86 passed in 58.54s**, including Chromium, async consumers and CPU Torch subprocess. |

Successful final runs had **0 failed, 0 warnings, 0 skipped, 0 XFAIL, 0 XPASS
and 0 deselected**. Final whitespace validation: `git diff --check` passed.
No production defect was confirmed and no expected-failure marker was added.

**Documented deviation:** retaining pytest-playwright's session-scoped sync
driver left its event loop active when later pytest-asyncio cases ran, producing
`Runner.run() cannot be called from a running event loop`. The harness now
reuses the plugin's fixture bodies/options/artifact handling but scopes the
driver/browser dependency chain per function. This costs browser launches but
releases the loop before subsequent async tests, without changing event-loop
internals, suppressing errors or relying on collection order. The full suite
executes browser cases before async cases and passes with this correction.

The small manually authored geometry map intentionally omits serialized edges;
both real loaders construct them. The ordinary builder supplies complete edges
for renderable scenarios. This distinction is documented so future edge
serialization tests do not accidentally use an incomplete oracle.

No launcher smoke command was needed for these test-only changes. The tiny
episode does exercise a bounded headless engine game directly, with exact legal
actions, terminal phase count and score assertions. Full replay playback, broad
combat behavior, GPU, macOS, Linux and other browsers remain unverified.

Every configured run checked **315 protected files** with no added, removed or
changed files and unchanged protected Git diff. The final report is
`tests/.artifacts/protected-paths.json`. Temporary/cache/browser artifacts remain
under ignored test-local directories; no production replay/log/model was written.

Next step: **S03 — Test server map geometry, serialization, and rule tables**.

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
