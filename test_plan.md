# Test plan for `server/` and `browser/`

Prepared: 2026-09-23. Status updated: 2026-09-25. Framework: **pytest**. This is an implementation roadmap; S01–S04 are complete, and S05–S17 remain open. Check off a step only after its completion criteria are met and its results are recorded.

For work across days and sessions, use this plan for scope and step status, [tests/PROGRESS.md](tests/PROGRESS.md) for dated implementation details, validation results, deviations, blockers, and the next task, [tests/KNOWN_ISSUES.md](tests/KNOWN_ISSUES.md) for confirmed defects, and [tests/README.md](tests/README.md) for current run commands. Read these records at the start of each session and update the progress log before ending it; do not rely on conversation history alone.

**Current harness:** with user approval, configuration now lives in repository-root `pytest.ini`, and the user installed the test plugins in the project environment. Run `uv run pytest` for core tests or `uv run pytest tests` for all implemented suites. These decisions supersede the original test-local configuration and dependency-overlay instructions below; the original requirements files remain as a version record. Production directories remain protected.

## Major steps and progress checklist

- [x] **S01 — Establish the test harness, baseline, and write restrictions.**
- [x] **S02 — Build deterministic fixtures and isolation helpers.**
- [x] **S03 — Test server map geometry, serialization, and rule tables.**
- [x] **S04 — Test server units, movement, targeting, and detection.**
- [ ] **S05 — Test game transitions, setup, combat, phases, and scoring.**
- [ ] **S06 — Test scenario loading, generators, registries, and game dispensers.**
- [ ] **S07 — Unit-test message transport, game-server routing, and server initialization.**
- [ ] **S08 — Integrate the engine, clients, WebSockets, and replay writer.**
- [ ] **S09 — Test browser map/unit models and Python–JavaScript compatibility.**
- [ ] **S10 — Test SVG utilities, rendering, markers, and viewport behavior.**
- [ ] **S11 — Test map editing, unit placement, and scenario creation pages.**
- [ ] **S12 — Test live-play controls and browser/server communication.**
- [ ] **S13 — Test replay playback and server-to-viewer compatibility.**
- [ ] **S14 — Test AI decisions, search algorithms, and hierarchy helpers.**
- [ ] **S15 — Test observations, rewards, Gymnasium wrappers, and agent adapters.**
- [ ] **S16 — Test model persistence, AlphaZero helpers, and ancillary scripts.**
- [ ] **S17 — Establish coverage reports, repeatability checks, and the daily regression process.**

Suggested order: S01–S08 establish the engine baseline; S09–S13 establish the browser baseline; S14–S16 cover AI/RL and research utilities; S17 is maintained throughout. Complete the harness and fixtures before depending on their results. S09–S11 can begin after S02 without waiting for all server integrations. Prioritize S03–S05 and S09–S13 before major core changes.

## Scope, findings, and rules

### Reviewed surface and existing baseline

The source inventory contains 86 Python files under `server/`, plus 21 JavaScript files, five HTML pages, and `webserver.py` under `browser/`. Review included the engine and transport implementations, browser modules and inline page scripts, AI families, Gymnasium wrappers, search and training utilities, existing tests, and repository documentation. Data files, saved models, and authored scenarios are inputs, not new implementation targets.

The current test file, `tests/test_scenario_loading.py`, contains four unittest methods covering launcher argument handling, default scenario lookup, and the two packaged aliases. Preserve their assertions and existing launcher coverage while migrating them to pytest in S01. New coverage in this plan targets only code in `server/` and `browser/`; extending `main.py` coverage is outside scope.

Pytest baseline verified during this plan revision on 2026-09-23 (Windows, Python 3.14.4, pytest 9.1.1):

```text
uv run --no-sync python -B -m pytest tests/test_scenario_loading.py -q -p no:cacheprovider
4 passed, 2 subtests passed in 0.01s
```

**Pytest is already installed and declared as `pytest>=9.1.1` in `pyproject.toml`.** The existing unittest methods, including both alias subtests, run under pytest before migration. The explicit file selection above avoids collecting executable examples; `-p no:cacheprovider` avoids creating a root pytest cache before the test-local configuration exists. This command needs no new dependency files or configuration.

The planned plugins `pytest-asyncio`, `pytest-playwright`, and `pytest-cov` are not installed in the current environment; provision them during S01 before using their options or fixtures. No game, browser, or ML suite was run during this revision. Passing the existing four tests does not establish correctness of combat, UI, transport, or RL behavior.

Important implementation facts to preserve or investigate:

- The Python engine and browser independently implement map geometry, movement costs, movement targets, and fire ranges. Cross-language tests must use common input fixtures and independently specified expected values.
- `combat.py` and `mobility.py` contain tables; combat resolution itself is in `Game._transition_move`. Browser firepower tables differ from server tables and do not resolve authoritative combat.
- A phase is one faction's opportunity to act. Two setup passes finish setup without consuming ordinary scored phases. Current terminal behavior is based on the phase limit, not elimination of all enemy units.
- `Game` implements `_is_legal_setup` and `_is_legal_move`, but no public `is_legal` method, despite the API notes. Setup `legal_actions()` deliberately enumerates only pass, although setup moves/exchanges can be submitted to `transition()`.
- Fog observations replace an unseen enemy's hex with `"fog"`; other fields remain present. Parameter messages also contain the starting scenario. Do not invent a stronger information-hiding contract.
- Browser modules use singleton objects, closure state, circular imports, SVG geometry, and HTML event handlers. A plain DOM mock does not cover actual layout and interaction.
- `MessageServer` creates and installs its own event loop; `GameServer` installs a signal handler; several scripts train, write files, serve HTTP, or parse CLI arguments at import time.
- The relevant third-party integrations are local libraries and browser APIs: `websockets`, NumPy/SciPy, Gymnasium, Stable-Baselines3, PyTorch, and `hexagdly`. There is no external hosted service to provision for this plan.

### Mandatory change boundaries

1. **Never edit files in `server/`, `browser/`, or `scenarios/` while implementing this plan.** This includes adding exports, adding `__main__` guards, fixing bugs, moving source files, inserting test hooks, updating example replays, or regenerating maps.
2. **All new tests, fixtures, helpers, dependency files, test documentation, configuration, and runners belong under `tests/`.** This requested root `test_plan.md` is the planning exception. Keep implementation progress in `tests/PROGRESS.md` if later iterations are restricted to `tests/` only; otherwise update this checklist as well.
3. Leave root `pyproject.toml`, `uv.lock`, `.gitignore`, and CI configuration unchanged. Preserve the user's existing pytest installation and dependency changes. Use test-local declarations for additional test tools and test-local configuration. Existing project dependencies remain the application's dependency baseline.
4. Keep temporary scenarios, logs, replay files, checkpoints, browser traces, coverage output, caches, and subprocess working directories under a test-local disposable directory. Add `tests/.gitignore` for those paths. Set `PYTHONDONTWRITEBYTECODE=1` for test subprocesses and use `python -B` so imports do not create caches under source directories.
5. Read existing scenario/data files only when testing a loader or compatibility with a real example. Most tests must use small fixtures in `tests/fixtures/`. No scenario package edits are needed.
6. No production fixes are part of this work. Reproduce defects, record them, and continue with independent coverage. A harness may replace an external boundary, such as a socket or model loader; it must not patch the behavior being asserted merely to make a test pass.
7. Keep executable demonstrations outside pytest discovery. The PortableTorch examples are named `simple_demo.py`, `cnn_demo.py`, and `testdir/read_demo.py`; they execute code at import time and must run only in isolation.

### Test types and result policy

**Unit tests** call one function/method/class with controlled collaborators. **Integration tests** exercise real cooperating modules or a real dependency. **Browser workflow tests** use actual pages and DOM events over HTTP. Label the distinction with registered pytest markers and in progress records; a mocked WebSocket is not a transport integration test, and a browser test can still be a unit test when it isolates one module's operation.

Use pytest test functions, plain `assert`, `pytest.raises(..., match=...)`, `pytest.approx`, and `@pytest.mark.parametrize(..., ids=...)`. Put shared setup and teardown in `@pytest.fixture` functions and `conftest.py`; use `monkeypatch`, `tmp_path`, `capsys`/`capfd`, and `caplog` for controlled state, files, output, and logging. Standard-library `Mock`/`AsyncMock` remain useful boundary doubles; do not introduce new `unittest.TestCase` subclasses or a custom test runner. Pytest documents fixture injection and teardown in [How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html).

Use pytest-asyncio with `@pytest.mark.asyncio` tests and `@pytest_asyncio.fixture` async fixtures, strict mode, and function-scoped event loops. Keep real server-owned event loops in dedicated subprocesses or isolated synchronous tests. Strict mode requires explicit async markers and fixture decorators; see [pytest-asyncio concepts](https://pytest-asyncio.readthedocs.io/en/stable/concepts.html).

Use pytest-playwright's synchronous `browser`, `context`, `page`, and `new_context` fixtures for browser tests. Share only the browser process; use a fresh context/page per test and separate server subprocesses. Extend fixtures in test-local `conftest.py` files for HTTP serving, console checks, and boundary fakes, with JavaScript helpers under `tests/`. See [Playwright's pytest integration](https://playwright.dev/python/docs/test-runners).

Distinguish three kinds of assertions:

- **Required behavior:** hand-checked game rules and supported interface contracts. These should pass and detect regressions.
- **Characterization:** explicitly named observations of existing behavior, especially aliasing, ordering, exceptions, or unsupported inputs. Do not represent these as approved future requirements.
- **Known defect:** a minimal test expressing the desired contract that demonstrably fails. Record a stable issue ID in `tests/KNOWN_ISSUES.md`, including reproduction, actual/expected result, and affected suites. Use `@pytest.mark.xfail(strict=True, reason="Kxx: ...", raises=KnownDefect)` on the individual case or `pytest.param`. A small test-local helper should raise `KnownDefect` only after matching the documented wrong result or exception signature; other failures must propagate normally. An unexpected pass must fail the suite. Never broadly xfail a class or catch every assertion as a known defect. See [pytest skip and xfail behavior](https://docs.pytest.org/en/stable/how-to/skipping.html).

The default pytest collection targets only the lightweight core. When an optional suite is explicitly selected by path, its preflight fixtures must fail for missing required dependencies/browser binaries rather than yield a misleading all-skipped success. Use `pytest.skip` or `@pytest.mark.skipif` only for individually documented capability limits, such as a CUDA-only case on a CPU host. Track passed, failed, skipped, XFAIL, XPASS, deselected, and unimplemented cases separately.

## S01 — Establish the harness and baseline

**Status: COMPLETE.** Implemented on 2026-09-23; root-configuration follow-up verified on 2026-09-24. Original baseline assertions were preserved and migrated to five pytest cases. The harness includes strict configuration, import/subprocess helpers, test-local HTTP serving, a Chromium module-load check, and protected-directory manifests. Default and full discovery were verified. Latest validation: `uv run pytest` — **13 passed**; `uv run pytest tests -q` — **14 passed**, including Chromium, with no warnings or failures. All 315 protected files remained unchanged.

The user-approved root `pytest.ini` and installed project plugins replace the original configuration location and overlay workflow specified below. See [tests/PROGRESS.md](tests/PROGRESS.md) for the case mapping, exact validation commands, environment versions, and completion evidence, and [tests/README.md](tests/README.md) for current usage. No additional S01 implementation work remains. S02 is also complete; S03 is also complete; S04 is also complete; S05 is next.

**Priority:** P0. **Dependencies:** none. **Deliverables:** pytest configuration and fixtures, test-local documentation, baseline and issue records.

1. Preserve all pre-existing work and baseline assertions in `tests/`. Re-run the explicit-file pytest baseline above before adding configuration or plugins; pytest supports collecting the existing unittest classes. Then migrate its methods to plain pytest functions: replace `self.assertEqual` with `assert`, use `monkeypatch.chdir` for working-directory restoration, and replace the alias `subTest` loop with parametrization and descriptive IDs. Preserve both alias cases and all launcher checks; splitting only the alias loop gives five collected tests instead of four methods plus two subtests, so record the old-to-new case mapping. Do not inject pytest fixture arguments into the old TestCase methods. See [pytest's unittest migration guidance](https://docs.pytest.org/en/stable/how-to/unittest.html). Record the revision, Python/plugin versions, OS, command, and results in `tests/PROGRESS.md`.
2. Create the following organization. Pytest does not require `__init__.py` for test collection; add it to `tests/` and `tests/support/` if helpers use package imports. Use pytest's importlib import mode and configure the repository root on the test import path. Avoid calling a test package `server`, `map`, `unit`, `game`, or `utils`, which would shadow production imports.

```text
tests/
  test_scenario_loading.py         # migrate syntax; preserve existing coverage
  pytest.ini                      # collection, registered markers, plugin options
  conftest.py                      # shared fixtures and session validation hooks
  README.md
  PROGRESS.md
  KNOWN_ISSUES.md
  requirements-test.in
  requirements-test.txt            # resolved, pinned test-tool dependencies
  coverage.ini
  .gitignore
  support/
    imports.py
    builders.py
    isolation.py
    async_helpers.py
    process_helpers.py
    http_server.py
    browser_helpers.py
  fixtures/
    maps/
    scenarios/
    observations/
    protocol/
    replay/
    models/
  server_unit/
  server_integration/
  browser_unit/                    # pytest functions using Playwright fixtures
  browser_integration/
  browser_support/                 # harness.html and JS boundary fakes
  ml/
  scripts/
  .artifacts/                      # ignored generated results
  .cache/                          # pytest cache and installed browser binaries
  .tmp/                            # ignored temporary working directories
```

3. Implement `support/imports.py` using paths derived from `__file__`. Add the real `server/` directory to the import path for its flat imports. Assert module `__file__` values when testing ambiguous names. Use isolated subprocess imports for `azg` and `portabletorch`, whose `Game`, `game`, `utils`, and `cnn` names can collide, especially on Windows. Load the intended `game.py` and `azg/Game.py` explicitly under their expected names where required; restore any temporary `sys.modules` entries.
4. Configure `tests/pytest.ini` with `testpaths` listing `tests/test_scenario_loading.py` and `tests/server_unit`, `python_files = test_*.py`, importlib import mode, `--strict-config`, `--strict-markers`, `-ra`, `xfail_strict = true`, and `asyncio_mode = strict`. Run from the repository root with `-c tests/pytest.ini --rootdir=.` so the invocation directory and pytest root agree and default `testpaths` apply. Using `python -m pytest` from that directory also makes the repository root importable; keep flat server imports in the explicit helper from item 3. Set async test/fixture loop scopes to function. Register suite markers `core`, `protocol`, `browser`, `ml`, and `scripts`, plus `unit`, `integration`, and `slow`; use module-level `pytestmark` or collection hooks for consistent classification. With no positional paths, collection covers only core; explicit paths select optional suites, and the explicit `tests` path selects all. Markers filter the paths already collected, so `-m browser` alone does not expand the default core paths. Keep expensive imports inside fixtures/test bodies or subprocesses so collection cannot start training or require a browser. Do not collect fixture model source or executable examples as tests.
5. Reuse installed pytest 9.1.1, which supports the existing `subTest` baseline; installation of the runner is already complete. Recheck the environment at implementation time. Put `pytest==9.1.1`, `pytest-asyncio`, `pytest-playwright`, `pytest-cov`, and their resolved dependencies in the test-local requirements files, retaining the installed pytest version unless a documented compatibility issue requires a change. Verify plugin compatibility with Python 3.14 and the existing environment, then pin tested versions under `tests/`. Provision these plugins before enabling plugin-specific configuration such as `asyncio_mode`; `--strict-config` must not encounter unknown options. Do not install or upgrade application dependencies merely to make a test pass. A temporary dependency overlay can use `uv run --no-sync --with-requirements tests/requirements-test.txt ...`; uv documents these overlays in [Running commands in projects](https://docs.astral.sh/uv/concepts/projects/run/).
6. Implement test-local HTTP serving with explicit routes for `/browser/`, `/tests/browser_support/`, and fixtures. Serve production browser files unchanged with JavaScript MIME types; bind loopback on an OS-assigned port, report readiness, and shut down cleanly. Do not import `browser/webserver.py` to serve ordinary tests: it starts a fixed-port server immediately.
7. Use `pytest_sessionstart` and `pytest_sessionfinish` hooks in `tests/conftest.py` to compare before/after content manifests for protected directories, including untracked/new files and collection-time effects, in addition to `git diff`. Fail the session on a violation without deleting or reverting the user's files. Capture the baseline before collection so existing local modifications are respected. Scope other autouse fixtures narrowly; core collection must not import ML libraries or start a browser just to initialize shared fixtures.
8. Set `cache_dir = tests/.cache/pytest` in `tests/pytest.ini`; this is relative to the explicitly selected repository root. Set `--basetemp=tests/.tmp/pytest` for root-invoked runs and use it only for pytest-owned files: pytest clears its basetemp on a subsequent run. Configure Playwright output under `tests/.artifacts/playwright` and browser binaries under `tests/.cache/ms-playwright`. Keep discovery and fixtures serial initially because of process-global module state; defer pytest-xdist until isolation has been demonstrated.

**Completion:** baseline assertions pass through pytest before and after syntax migration; `--collect-only` shows the intended default and full case lists; a trivial browser module loads over HTTP; optional suites require explicit selection; all new files and outputs stay within the allowed paths. Harness setup alone does not count as application coverage.

## S02 — Build fixtures and isolation helpers

**Status: COMPLETE (2026-09-25).** Fresh builders, all twelve reusable fixture families, RNG/global/task/loop isolation, finite boundary doubles, browser error capture, and CPU model inputs are implemented. Consumer checks verify independent geometry/score oracles, failure-path cleanup, and real engine/browser compatibility. See [tests/PROGRESS.md](tests/PROGRESS.md) for commands, results and the documented function-scoped Playwright lifecycle deviation; [tests/fixtures/README.md](tests/fixtures/README.md) documents schemas. S03 is also complete; S04 is also complete; S05 is next.

**Priority:** P0. **Dependencies:** S01. **Deliverables:** `support/builders.py`, isolation helpers, and documented fixture schemas.

1. Build fresh objects with function-scoped pytest fixtures. Provide factory fixtures exposing `make_map(rows, cols, terrain_overrides, setup_overrides)`, `make_unit(...)`, `make_scenario(...)`, and `make_state(...)`, with defaults explicit in helper documentation. Put broadly shared fixtures in `tests/conftest.py` and specialized ones in the relevant suite's `conftest.py`; keep pure builder functions in `support/builders.py`. Use distinct unit names per faction and portable IDs such as `"blue A"`. Return deep copies of reusable JSON data; do not share mutable fixture objects between parametrized cases.
2. Maintain at least one manually authored map with verified centers, vertices, and neighbors. Other fixtures may use the real map builder for convenience, but geometry tests must not derive their expected output using the geometry function being tested.
3. Prepare these reusable fixtures; add a short explanation of each expected result beside its data.

| Fixture | Fixed contents and purpose |
| --- | --- |
| `hex_geometry` | A 4-column by 3-row flat-topped map, plus single-hex, empty, and irregular subsets; even/odd columns, boundaries, dimensions. |
| `movement_corridors` | Infantry/armor/artillery on clear, rough, marsh, water, urban, and unused terrain; blocked and alternative routes; exactly 100 movement points and over-budget routes. |
| `combat_duel` | Adjacent blue/red units at known strengths; spare friendly unit when phase auto-advance would obscure `canMove`; no cities for isolated damage assertions. |
| `setup_exchange` | Separate blue/red setup zones, two friendly units, empty destination, occupied destination, and enemy outside the permitted zone. |
| `city_scoring` | Two urban hexes, blue/red/neutral ownership variants, explicit `maxPhases`, `cityScore`, and `lossPenalty`; short phase limit. |
| `fog_sequence` | Ground truth and role-specific observations before detection, at the sight boundary, out of sight, after removal, and after reappearance. |
| `rectangular_features` | Width 4, height 3, asymmetric positions, differing factions/strengths, every terrain across variants, signed score, known phase. Catches transposed axes. |
| `tiny_episode` | A small valid scenario with two to four ordinary phases and scripted legal pass/move/fire actions; independently calculated final score. |
| `hierarchy_units` | Nested names such as `1/1/1`, unequal strengths, one ineffective subordinate, and separate factions; known centers of mass. |
| `protocol_messages` | Parameters, role requests, observations, move/fire/pass/setup actions, reset, next-game, gym-pause, optional debug, and malformed variants. |
| `replay_sequences` | Parameters followed by observations; later parameters for a second game; debug colors/echelons; fog/removal; empty/truncated/invalid/action-inclusive cases. |
| `model_and_numeric_data` | A tiny CPU model defined under `tests/fixtures/models/`, small tensors, `.data` files, and generated `.npz` files. No trained binary download required. |

4. Implement RNG isolation with yield fixtures and `try/finally`: snapshot and restore Python and NumPy states; use fixed Torch seeds in ML tests and restore relevant settings; use `monkeypatch.setattr` on `unit.random` at its lookup site for detection boundaries. A seed alone is insufficient for a test intended to exercise a particular random branch. Give browser tests a finite deterministic random sequence or seeded generator, avoiding an endless zero sequence in Box–Muller sampling.
5. Snapshot/restore mutable globals: rule tables when patched, both registries including nested option dictionaries, `current_game_access.server`, `server.server`/`gym_ai`, `messageserver.SLEEP_TIME`, `ClientWrapper.next_id`, AI counters, and `PortableTorch.cnt`. Account for shared table objects such as mechanized-infantry/armor mobility. Restore in cleanup even if assertions fail.
6. Use pytest's `tmp_path` for per-test working/output directories and `tmp_path_factory` only for intentionally shared immutable artifacts, with the test-local basetemp from S01. Use `monkeypatch.chdir/setenv` for process state. Resource-owning yield fixtures must register cleanup as each resource is acquired, before a later setup failure can bypass the yield. Retain only requested diagnostic artifacts under `tests/.artifacts/`. Child processes inherit no developer model paths. Set a fixed `PYTHONHASHSEED` at process creation for repeatability-sensitive set iteration; runtime assignment does not change the active interpreter's hash seed.
7. Provide recording function clients, async WebSocket doubles, finite async iterators, small fake dispensers/games, controlled model predictions, and a finite game tree. Keep their protocol interfaces faithful to the real collaborators.
8. Browser fixtures depend on pytest-playwright's function-scoped `context`/`page`, install boundary fakes before navigation/module imports, and import unchanged files using `await import('/browser/map.js')` from a test harness page. Use `new_context` for the second player in two-client tests so cleanup is managed for both. Share a session-scoped HTTP server only if it serves immutable data; keep mutable routing and received-message state per test. Use actual DOM/SVG nodes. Test same-page reloads explicitly without clearing indexes first; otherwise the fixture would conceal stale-state bugs.
9. Capture uncaught browser exceptions, console errors, failed requests, and unexpected dialogs in a page-dependent yield fixture; inspect them at teardown before the page closes. Treat unexpected errors as failures. A defect reproduction may match one precise expected exception; never suppress all page errors. Use `capsys` for Python output, `capfd` where file-descriptor capture is needed, and `caplog` for logging assertions; attach child-process output and Playwright traces to failure reports.
10. Implement terrain/type, coordinate parity, faction, action index, and registry matrices with `@pytest.mark.parametrize`, using descriptive IDs and `pytest.param` for case-specific marks. Use native NumPy/Torch comparison helpers for arrays and `pytest.approx` for scalar floating-point results. Function-scoped fixtures must also reset state between parametrized cases.

**Completion:** fixture consumers do not share mutable objects; normal cleanup restores RNG/global/loop state and deletes owned temporary outputs; assertions use an independent oracle. Validate these properties through actual tests that consume the helpers rather than building an oversized fixture-testing framework.

## S03 — Server geometry, serialization, and rule tables

**Status: COMPLETE (2026-09-25).** Added 92 cases across the three proposed files:
83 passing cases and nine narrowly matched strict expected failures for confirmed
K01/K02 edge, path, cached-dimension and replacement defects. Both parities,
negative coordinates, all directions, boundary truncation, distinct distances,
portable JSON round trips, map queries and every rule-table coefficient are covered.
See [tests/PROGRESS.md](tests/PROGRESS.md) for validation and
[tests/KNOWN_ISSUES.md](tests/KNOWN_ISSUES.md) for exact reproductions. S04 is also complete; S05 is next.

**Priority:** P0. **Dependencies:** S02. **Proposed files:** `server_unit/test_map_geometry.py`, `test_map_serialization.py`, `test_rule_tables.py`.

1. Test `offsetToGridCenters`: `(0,0) -> (2,2)`, `(1,0) -> (5,3)`, `(2,1) -> (8,4)`. For `offsetToCube`/`cubeToOffset`, table-test positive/negative even and odd columns, verify round trips and `q+r+s == 0` without reusing the conversion as the sole oracle.
2. Test `getNeighborHex`, `getNeighborHexes`, and `directionFrom` in all six directions for both parities. Assert interior neighbor IDs, corner/edge truncation, reciprocal opposite directions, and `None` for a non-neighbor or absent neighbor.
3. Separate `gridDistance` from `hexDistance`: the former is Euclidean distance in grid coordinates; the latter is integer hex distance in offset coordinates. Test identity, symmetry, adjacent distance 1, two-step positions, and a position where Euclidean and hex distances differ. Use tolerances for floating point.
4. Test `Hex.getPoints`, `Hex.portableCopy`, `Edge.toPortable`, and generic-object loaders: six correctly ordered vertices, expected IDs, terrain/setup fields, and absence of object references in portable data. Probe shared edge identity in reverse endpoint order as a defect candidate.
5. Test `MapData.createHexGrid`, `hexes`, `edges`, `getDimensions`, `getCityHexes`, `hasSetupHexes`, and `getSetupHexes`: empty/single/rectangular maps, urban-only city selection, faction setup filtering, and repeated grid/load operations. Include larger-to-smaller reload after dimensions have already been queried.
6. Test `toPortable`, `toString`, and `fromPortable` with JSON serialization and reloading. Compare semantic geometry/terrain/setup data with explicit field expectations. Do not demand preservation of fields these serializers do not implement, such as scenario-level metadata. Separately record path handling: Python path loading is commented out and `Path.portableCopy` uses dictionary attribute assignment.
7. Table-test all four engine unit types against all six terrain names in `mobility.cost`; include impassable infinities, armor/mechanized clear cost 50, infantry clear cost 100, artillery marsh prohibition, and stacking limit 1.
8. Test combat range, sight, detection probability, scaling, threshold, and every attacker/target and target/terrain table combination. Pin relevant numeric values as independent fixture data; checking dictionary completeness alone will not detect a changed coefficient.

**Completion:** both column parities, all terrain/unit combinations, JSON round trips, empty maps, reloads, and distinct distance definitions have assertions; confirmed edge/path/cache issues have reproductions and issue IDs.

## S04 — Server units, movement, targeting, and detection

**Status: COMPLETE (2026-09-25).** Added 84 passing cases in the three proposed
files, covering identity/flags, occupancy lifecycle, movement budgets and an
independent shortest-path oracle, geometric fire eligibility, partial observations,
finite detection draws and observer serialization. Unsupported inputs and K05's
serialization side effect are explicit characterizations; no new xfails were added.
Full validation: **253 passed, 9 existing xfailed**, with all 315 protected files
unchanged. See [tests/PROGRESS.md](tests/PROGRESS.md) and
[tests/KNOWN_ISSUES.md](tests/KNOWN_ISSUES.md). S05 is next.

**Priority:** P0. **Dependencies:** S03. **Proposed files:** `server_unit/test_unit_state.py`, `test_unit_movement.py`, `test_unit_visibility.py`.

1. Test `Unit.__init__`, `UnitData.units/getFaction`, and `fromPortable`: ID derivation, explicit/default flags, strengths, supplied detection state, faction filtering, and registration. Characterize duplicate IDs and unplaced units separately from valid scenarios.
2. Exercise `setHex` and `remove` through a sequence of moves, repeated placement on the same hex, removal, and replacement. Assert old/new occupancy, no duplicate membership for a valid move, and the fact that removal does not delete the unit from `unitIndex`.
3. Test `hexFull` at zero, one, and temporarily varied stacking limits. Test `setCanMove` on both factions and ineffective units. Restore any changed rule table afterward.
4. Test `_findMoveTargets` and `findMoveTargets` with literal expected destination sets. Cover infantry one-step movement, armor/mechanized/artillery two-clear-hex movement, mixed terrain budgets, impassable terrain, occupied intermediates/destinations, off-map bounds, excluded origin, and no duplicate destinations. Add an alternative-route case checked against a small independent shortest-path oracle; if disagreement appears, record it rather than copying the production search into the test.
5. Test `findFireTargets`: exclude friendlies, ineffective and unplaced targets; include exactly-on-range targets and exclude just-outside targets; exercise artillery range 2 and both parities. `canMove` is filtered by game action generation, not this geometric helper. Verify that target eligibility uses Euclidean `gridDistance`.
6. Test `partialObsUpdate` with normal movement, strength/flag changes, `"fog"`, ineffective removal, and later visible reappearance. Assert occupancy as well as fields. Keep fog observations distinct from ground-truth data passed to `fromPortable`, which cannot directly construct a unit on a `"fog"` hex.
7. Test `updateDetectionStatus` with patched random values at/below/above `pDetect`, already-detected enemies, distance boundaries, friendly-only groups, ineffective enemies, and units leaving sight. Assert detection is retained while still in sight when previously detected, but cleared out of sight.
8. Test `UnitData.toPortable` for white/blue/red observers, including the exact fields exposed for fogged enemies, and `Unit.portableCopy` separately because it omits `detected`. Verify serialization invokes detection rather than assuming it is a pure getter. Record behavior for live unplaced units if detection dereferences a missing hex.

**Completion:** movement, occupancy, fire range, and visibility have independent assertions and controlled randomness; a visible-hidden-visible sequence passes without stale occupancy.

## S05 — Game transitions, setup, combat, and scoring

**Priority:** P0. **Dependencies:** S03–S04. **Proposed files:** `server_unit/test_status.py`, `test_game_setup.py`, `test_game_actions.py`, `test_game_combat.py`, `test_game_observations.py`, `test_game_state_key.py`.

1. Test `Status` construction/defaults, `fromPortable/toPortable`, and `Game.initial_state`, `players`, `on_move`, `parameters`, `score`, `max_player`, and `is_terminal`. Assert initial blue movement, setup inference, city ownership from occupying units, and fresh initial units on repeated calls. Characterize shared references in `parameters()` and observation status rather than assuming every getter deep-copies.
2. Test setup transitions explicitly: blue setup move within its zone, red move within its zone, friendly exchange, pass to red setup, then pass to blue movement. Verify ordinary phase count and city score remain unchanged during setup. Rejected wrong-faction/out-of-zone moves must not mutate input state. Probe occupied setup destinations, enemy exchange targets, and ineffective movers as potential validation gaps.
3. Test `legal_actions`: one pass, moves/fires only for active effective units in ordinary play, exhaustion after a unit acts, and only pass enumeration during setup. Validate setup actions through `transition` and `_is_legal_setup`; do not require them to appear in the deliberately restricted list.
4. Test a legal move with another friendly still available, then a move by the final friendly. Assert destination, consumed action, unchanged other units, and automatic phase advance only after the last available unit acts. Test explicit pass while other actions remain.
5. Test rejection of invalid movement/fire and `None`; separately characterize malformed action fields, unknown IDs, extra fields, and terminal-state calls. The current code may raise `KeyError` rather than a structured validation error. Do not assert a nonexistent public `is_legal()` API.
6. Use hand-calculated combat expectations, through `transition`, with no cities unless scoring interactions are intentional:

| Case | Expected result under current rule values |
| --- | --- |
| Strength-100 infantry fires at strength-100 infantry on clear | Damage 50; target remains effective at exactly 50. |
| Strength-100 infantry fires at strength-75 infantry on clear | Initial damage 50 leaves 25, below threshold; target removed; total credited loss 75. |
| Strength-100 infantry fires at strength-100 infantry in urban/rough | Damage 25 because the target infantry terrain multiplier is 0.5. |
| Red damages blue by 50 with default loss penalty -2 | Score delta -100; direction remains blue perspective. |
| Defensive fire term exceeds offensive term in a controlled table patch | Damage clamps to zero; no strength increase. Restore tables afterward. |

7. Expand damage cases across attacker/target types, target terrain, fractional strengths, just-below/equal/above the 50 threshold, and overkill. Check shooter action consumption, target location/removal, ineffective flag, occupancy rebuilt from output, and score. Overkill can expose scoring above remaining strength; characterize and triage rather than silently capping expected output.
8. Test `Status.dscoreKill`, `updateCityOwnership`, and `endPhaseDeltaCityScore`: positive red loss, configurable negative blue loss, equal city-share division, neutral cities, persistent ownership of a vacated city, occupation changes, and zero-city maps. Verify ownership/scoring timing at phase boundaries, including a city entered before the last unit acts.
9. Test `phaseComplete`, `advancePhase`, and `matchComplete`: no available effective units; faction alternation and flags; setup sequence; exact phase limit; terminal final score. Demonstrate that elimination alone does not currently terminate a match. Probe already-at/past-limit input separately.
10. Test state isolation: deep-copy the input scenario/state, execute a transition, compare input afterward, and create two successor branches to ensure one does not alter the other. Use `Game.observation` for both fog modes and both players, with deterministic detection; test status/reference behavior explicitly.
11. Test `statePlusParamHashKey` on readable tiny fixtures: changes in terrain, unit position/type/strength/action availability, city owner, phase, and setup faction. Investigate collisions for fields not represented, fractional strengths truncated to integers, and omitted terrain codes such as `unused`. Treat this as a search key with limitations, not a cryptographic hash.

**Completion:** a scripted setup-to-terminal sequence has exact states/scores; normal and invalid action branches, damage thresholds, scoring signs, city timing, and input immutability are covered.

## S06 — Scenarios, registries, and dispensers

**Priority:** P1. **Dependencies:** S02 and S05. **Proposed files:** `server_unit/test_scenario_factories.py`, `test_scenario_registry.py`, `test_game_dispenser.py`.

1. Extend server-side path coverage around `resolve_scenario_path`: bare name, explicit relative path, absolute path, supplied relative/absolute `scenario_dir`, user-home expansion using a controlled home resolver, paths with spaces, and working-directory independence. Use temporary `.scn` files, not copied authored packages.
2. Test `from_file_factory` with valid UTF-8 JSON, missing files, invalid JSON, and schema-incomplete JSON. Distinguish JSON loading from later `Game` schema consumption. Characterize that successive factory calls return the same parsed scenario object; consumers should deep-copy fixtures instead of mutating shared loaded data.
3. Table-test `get_setup_hex_ids` for north/south/east/west/middle strips and margins; test `get_rect_region_ids` including single cells and empty ranges. Assert exact IDs on a small map.
4. Test `flip_colors`: only factions change, order and non-faction fields remain, applying twice restores values, and shallow sharing of nested map/unit data is documented.
5. Test `clear_square_factory`, `hierarchy_factory`, and `invasion_factory` with fixed seeds. Compare independently constructed factories, multiple successive calls, positive cycle lengths, and balanced alternating pairs where supported. Compare deterministic map/placement results separately from `detected` fields: conversion to portable units can consume ambient RNG after generator state restoration.
6. Check generated dimensions, strength, unit count ranges, hierarchy names/depth/branching, setup membership, terrain vocabulary, scoring parameters, fog flag, and invasion initial red ownership. Validate actual unique city count separately from placement attempts; random city placement can select a cell more than once.
7. Probe minimum size, over-capacity unit requests, hierarchy occupancy collisions across branches, invalid depths, and invalid count combinations with finite timeouts. Record actual exceptions/unsupported inputs; do not invent graceful validation absent from production. Check global RNG effects on both successful and failing factory calls.
8. Test registry entry structure and a small representative generator from each family. For packaged aliases, retain existing read-only smoke checks; test `packaged_scenario_factory` accepting unused generator options without writing packages. Avoid large default generators in the fast suite.
9. Test `ScenarioGeneratorGameDispenser.get_next_game` produces a new `Game` for each generated scenario, and `ConstantGameDispenser` returns its exact supplied game object. Test `current_game_access.set_gameserver/get_current_game`, restoring the original singleton.

**Completion:** supported path forms and all three generator families have repeatable small examples, cycle/balance checks, and explicit characterization of shared data/RNG behavior.

## S07 — Transport, routing, and initialization unit tests

**Priority:** P0/P1. **Dependencies:** S02, S05–S06. **Proposed files:** `server_unit/test_message_clients.py`, `test_message_routing.py`, `test_gameserver_protocol.py`, `test_server_init.py`.

1. Test `ClientWrapper`: unique IDs; dictionary-to-JSON delivery; function return JSON added to the queue; callback delivery through `response_fn`; `None` response; WebSocket `send` awaiting; invalid callback payload type; malformed returned JSON; FIFO queue order. Reset the ID counter between independent cases.
2. Test `MessageServer.send/broadcast/relay` with recording wrappers. Assert exact recipients and payloads, relay exclusion, empty client lists, and no accidental double serialization.
3. Test `serve_function_factory` with a finite async socket iterator: new-client registration precedes inbound messages; JSON is parsed once; handler sees the correct wrapper; `SLEEP_TIME` changes are isolated. Test malformed JSON, clean closure, and exceptional closure as current behavior; probe stale entries after disconnect.
4. Run `process_function_client` as a task with an event-controlled handler; assert initial parameters/queued message ordering and cancel/await the infinite processing task. Use event readiness and deadlines, not arbitrary sleeps.
5. For `MessageServer.__init__`/`run`, use a dedicated synchronous pytest test or subprocess because it installs its own loop. Verify socket setup is scheduled inside a running loop and function clients are registered. Never let it replace the loop managed by pytest-asyncio. Handler-only async tests use `@pytest.mark.asyncio` and async yield fixtures, with an inert transport replacement in `gameserver.MessageServer` where needed. Cancel and await all test-owned tasks before fixture teardown completes.
6. Test `new_client_handler_factory`, `message_handler_factory`, and `GameServer` against a tiny fake game/dispenser and async recording transport. Cover role assignment, first/second turn, game over, invalid role/type, wrong client, gym-pause, reset, and next-game. Patch exit/loop-stop boundaries so tests cannot stop the runner.
7. Assert ordering: new clients receive parameters; both role requests precede first observations; an action transitions exactly once and sends observations to both roles. Debug metadata is attached when supplied. Reset sends fresh observations before the reset broadcast in the current implementation. Next-game broadcasts parameters and requires role assignment again.
8. Exercise `n_reps` values -1, 0, and 1, terminal actions from either faction, `auto_next_game`, repetition count, and final score printing. Do not call an unbounded real `run()` in these unit tests. Probe duplicate role requests, unassigned clients, and stale reverse mappings after `clear_roles`.
9. Test `server.init` using fake constructors and an inert `GameServer`: generator vs `.scn` resolution; both faction options; neural/shared-model/depth/search/sub-AI arguments; gym surrogate selection; current-game registration; replay/log options; invocation of `run` exactly once. Exercise seed 0 and repeated initialization with different options to detect registry dictionary leakage.
10. Test `mapDimensionBackdoor`, `getGymAI`, `reset`, and `addMessageRunLoop` with controlled globals. Verify reset requests the next game, and action submission precedes loop resume. Check `airegistry.py` import-time neural gating in a fresh process for `ATLATL_NEURAL` and relevant argv values; actual optional imports belong in S15/S16. Do not equate disabled neural aliases with a Torch-free import: the registry also imports `multigym_ai`, which imports observation and Stable-Baselines3 code.

**Completion:** every protocol state and legal message transition has a positive case and relevant rejection case; runner loop/signal handlers survive testing unchanged.

## S08 — Server integration and replay writing

**Priority:** P0/P1. **Dependencies:** S05–S07. **Proposed files:** `server_integration/test_function_clients.py`, `test_websocket_game.py`, `test_server_cli.py`, `test_replay_writer.py`; subprocess bootstrap under `tests/support/`.

1. Integrate real `Game`, dispensers, `GameServer`, and `MessageServer` with two small function clients. Complete `tiny_episode`, compare all observations and the independently computed terminal score, and test two-game role re-assignment. Assert the first game's units/actions do not carry into the second.
2. Run real local `websockets` clients against the real transport in a child process. The test bootstrap constructs `GameServer` with a loopback ephemeral port and finite `n_reps`; report ready only after binding succeeds. Perform the actual parameters/roles/observations/actions handshake, both factions, wrong-turn handling, and disconnect cleanup. Put each disruptive input in a separate case so one closed connection does not invalidate later assertions.
3. Cover a mixed function-client/WebSocket-client game. This specifically checks that the two transport types share serialization and routing semantics.
4. Exercise `server/server.py` as a bounded CLI subprocess with explicit blue/red AIs, `--nReps 1`, a fixed seed or tiny scenario path, and no socket unless intentionally testing it. Use the active interpreter by absolute path; use an owned temporary working directory and explicit fixture/replay paths. Test generator, bare filename, and explicit scenario path. Retain alias loading as a small read-only check.
5. Test the separate AI client in `ai_process.py` against a local server using its `--uri`; it parses arguments and runs at import, so use a subprocess instead of importing it. Set readiness, exchange count, timeout, and termination bounds. Cover CLI error for an unknown AI and response/no-response behavior of `client` using controlled dependencies where useful.
6. Generate blue and red replays only under `tests/.tmp/`, with and without `log_actions`. Verify parameters are first, observations have the correct perspective, actions appear only when requested, a second game inserts parameters, and closing writes a complete replay array.
7. Replay output is JavaScript containing JSON strings (`replayData = [...]`), not a raw JSON document. Validate ordinary entries by JSON decoding their message strings and validate executable file syntax with the browser in S13. Include apostrophes, backslashes, and Unicode in names to expose escaping problems. Do not use Python `eval` on generated replay text.
8. Implement cleanup with `try/finally`: cancel/await child tasks, close sockets/loops, restore signal handlers in in-process units, close logs, terminate then kill only owned child processes if deadlines expire, and collect stdout/stderr. Keep timeout failures visible rather than retrying them into a pass.

**Completion:** a real local WebSocket game and a function-client game terminate, produce expected scores/messages, leave no processes behind, and produce replay input that S13 can consume. No checked-in replay file is overwritten.

## S09 — Browser models and cross-language contracts

**Priority:** P0. **Dependencies:** S02–S04 and the browser harness. **Proposed files:** `browser_unit/test_map_model.py`, `test_unit_model.py`, `test_rule_data.py`; `browser_integration/test_engine_parity.py`.

1. Import `Map`, `Unit`, `Mobility`, `Combat`, `Terrain`, and `Style` from their original modules in the harness page. Invoke methods in page JavaScript and return plain values to Python assertions. Access the private `Hex`, `Edge`, and `Path` implementations through `Map.createHexGrid`, `Map.hexIndex`, and path operations; do not add exports.
2. Repeat the independent geometry vectors from S03 for generated hex centers, vertices, dimensions, neighbor IDs, coordinate lookup, and `gridDistance`. Test `Map.hasSetupHex`, `toPortable/toString`, and `fromPortable/fromString`, including malformed JSON.
3. Test `Map.addPath/removePath`: two adjacent hexes, both endpoint directions, shared endpoint references, serialization/reloading, replacing/removing a path, and removal when absent. Probe nonadjacent endpoints separately. Test reversed shared-edge lookup via public map construction.
4. Load a large map then a smaller map in the **same page**, and create a new grid after loading paths. Assert stale hexes, paths, dimensions, and edge references do not survive where replacement is intended. Record failures rather than resetting the module between these operations.
5. Test `Unit.init`, `Unit.Unit`, `setHex/remove`, `placeUnit/placeUnits`, `toPortable`, `fromPortable`, and `fromPortable2`. Cover registration, occupancy, exhausted setup space, faction-specific setup placement, no-setup placement, and derivation of IDs/default display fields for the server format. Check that `fromPortable2` differs from the richer browser format intentionally.
6. Repeat movement/fire target fixtures from S04, using `unit.findMoveTargets`/`findFireTargets`. Include an ineffective or fog-hidden target, occupancy, and artillery range. Test `partialObsUpdate` and corresponding occupancy across movement/hiding/reappearance/removal. Probe unplaced serialization and repeated loads for stale indexes.
7. Table-test `Terrain.idToName`, palette objects' `getUniqueID`, default terrain, and supported `Style` entries. Check every palette terrain/edge/path ID maps back to a supported style. This should catch paths constructed with the edge-type constructor rather than masking the ID mismatch.
8. Maintain one JSON contract fixture with inputs and independently expected results shared by Python and JavaScript. Compare centers, neighbor sets, distances, mobility costs, stacking, fire ranges, and legal move/fire target sets. Normalize infinity explicitly, for example as `"impassable"`, before JSON transport; JSON itself cannot faithfully represent infinity.
9. Compare semantic map/unit fields, not raw serialized object equality: browser units have display metadata absent from the engine; Python map loading does not implement paths. Preserve action sequence order, but compare unordered target sets as sorted IDs.
10. Audit browser/server combat table differences in a separate compatibility report. Require parity for live shared behavior such as range and mobility. Do not impose whole-firepower-table equality as a passing baseline: the browser lacks the server infantry firepower row and other coefficients differ. Add a tracked contract test if full parity is an agreed intended requirement later.

**Completion:** shared geometry/movement/targeting fixtures run against both implementations; model loading and same-page replacement are covered; intentional data-format differences and actual defects are distinguishable.

## S10 — SVG utilities, rendering, markers, and viewport

**Priority:** P0/P1. **Dependencies:** S09. **Proposed files:** `browser_unit/test_svg_util.py`, `test_svg_rendering.py`, `test_svg_markers.py`, `test_unit_symbols.py`.

Production modules: `svg-util.js`, `svg-map-view.js`, `svg-create-view.js`, `svg-gui.js`, `svg-setup-marker.js`, `svg-city-marker.js`, `svg-map-editor-palette.js`, and `svg-unit-symbol.js`. Test `MapEditorPalette.add` through generated palette items here and their actions in S11.

1. Test `SVGUtil.gridToSVG` against numeric coordinates for zero/nonzero margins and multiple widths. Test `makeSvgElement/recreateMysvg`, primitive rectangle/label/line helpers, `setFill`, and `setPathStyle` for namespace, required attributes, replacement of the old root, and text content.
2. Test `VerticalCenteredLayout.add`, spaces, and `drawFrame` using actual attached SVG elements. Assert order, increasing offsets, centered placement, and frame containment with tolerances. Avoid exact font-dependent bounding-box snapshots.
3. Test `getTransformedBBox` with no transform, translation, and scale; probe rotation/skew as separate cases because current implementation may not compute the full enclosing box for them.
4. Test `ViewBoxControl.fitToContent`: one-unit padding, stored fitted bounds, aspect ratio/style, empty content no-op, and rectangular maps. Test `toggleZoom` at the center and each edge/corner, clamping inside fitted bounds, small maps, legacy no-fit path, and restoration of exact fitted bounds after zooming out. Use fixed viewport dimensions and numeric tolerance; verify the native `getBBox` path with a real browser.
5. Test `SVGMapView.add`: map hex/edge/path shapes, terrain fill, handler attachment, setup markers, urban ownership markers, and identifiers. Test `set_colors` with complete/partial debug maps and `terrain_color` restoration. Do not assert a mathematically ideal edge count until duplicate-edge behavior from S03/S09 is resolved.
6. Test all three `SVGCreateView` factories: `createMapEditorView`, `createUnitPlacementView`, and `createPlayView`. Repeated calls should replace the visible root and install the intended controller listeners; use event-driven assertions as well as node checks.
7. Test `SVGSetupMarker.init/addMarker/removeMarker/removeAllMarkers/setAllVisible` and `SVGCityMarker.init/addMarkers/setVisible`. Check add/replacement/removal, model setup changes, per-faction visibility, neutral cities, and new-map initialization. Verify no detached marker remains reachable in a way that affects a later map.
8. Test `SVGUnitSymbol.create`, `moveSymbolToHex`, `partialObsUpdate`, selection marking, and brightness methods. Assert IDs, labels/strength, positions, faction fill, action dimming, hidden/ineffective removal, and reattachment on reappearance. Test company/regiment/battalion/squadron branches and supported symbol types through `create`; private icon functions need no new exports.
9. Use a compact table covering infantry, armor, mechinf/heavy, infantry/light, artillery, HQ/tisr, and the additional air/naval/support symbol aliases in the switch. Read `sample-oobs/oob-all-symbols.json` for a compatibility smoke check, while retaining small test-owned fixtures as the main oracle. Unknown types/echelons should have an explicit characterization test.
10. Test `SVGGui.markHex/clearMarks`: marker placement, color/ID, action callback, repeated clear, and redraw after unit size/map changes. Probe marking with no live visible units and repeated selection/unselection as separate defect cases.

**Completion:** actual SVG geometry and DOM interaction are exercised over HTTP; all exported utility/renderer groups have behavioral coverage; browser console/page errors are checked. Screenshots are diagnostic artifacts, not the primary correctness oracle.

## S11 — Editors and scenario creation pages

**Priority:** P0/P1. **Dependencies:** S09–S10. **Proposed files:** `browser_unit/test_editor_controls.py`, `test_placement_controls.py`; `browser_integration/test_map_editor_page.py`, `test_unit_placement_page.py`, `test_random_scenario_page.py`.

1. Unit-test `MapEditorControl` through exported palette and mouse handlers, using real elements as `this`. Test paint-fill, paint-edge, paint-path, paint-setup, erase, drag continuation, mouse-up ending a drag, and selection of each palette type. Assert both model changes and SVG attributes.
2. Test consecutive path segments and their replacement/removal; expose the path palette ID issue independently of `Map.addPath`. Test clicking/dragging with Shift updates viewport without painting and that a normal click resumes editing afterward. Inspect same-page controller closure state through visible effects, not added test exports.
3. Unit-test `UnitPlacementControl`: selecting a unit, moving to an empty hex, exchanging positions with another unit, selecting the same unit, and ending selection. Assert both units' occupancy and symbol transforms. Shift-click must not select/move a unit. Characterize placement onto occupied hexes rather than assuming gameplay stacking enforcement exists in this editor.
4. Open unchanged `map-editor.html`. Change rows/columns/width, draw a map, paint terrain/edges/setup, load a fixture through the prompt, cancel loading, and try malformed JSON. Capture `document.execCommand('copy')` at the boundary and inspect the temporary textarea content; separately smoke-test actual clipboard behavior where the browser/environment supports it.
5. Exercise map SVG export via the actual page control; decode the data URI, parse it as XML, and assert SVG namespace, root, and expected map content. Do not compare every floating-point path character.
6. Open unchanged `unit-placement.html`; load a map, unplaced OOB, and complete scenario through actual controls. Verify automatic placement, movement/exchange, viewport fit, fog checkbox, numeric scoring inputs, and exported `{map, units, score}` JSON. Test zero units, insufficient setup cells, repeated map/OOB/scenario loads, and canceled/invalid prompts. Specifically probe whether loading a scenario restores its score/fog settings before copying it again.
7. Send exported scenario JSON to the real Python loader and `Game.initial_state`, then apply one legal action. Verify unit positions, type/faction/strength, map setup, scoring and fog values. Preserve browser-only metadata where exported but do not require the engine to interpret it.
8. Open unchanged `random-scenario.html`; load a test-owned rich-format OOB, generate with a controlled random sequence, and export. Check terrain vocabulary, city/setup placement, unique unit occupancy, sufficient setup cells, and a second generation in the same page. Include the supported default 10x10 map and a non-square map; treat dimensions below the generator's hard-coded geographic assumptions as defect probes.
9. Keep `browser/test-data.js` and `sample-oobs/*.json` unchanged. Smoke-test the page's Test Input control and representative sample data. Legacy, scratch, or non-engine symbol types belong in display compatibility tests, not a blanket assertion that every sample OOB can be played by the engine.

**Completion:** all three creation pages complete a real DOM-driven load/edit/export workflow, exported game data loads in Python, repeat-load cases are accounted for, and unexpected console errors fail the test.

## S12 — Live play and browser/server integration

**Priority:** P0. **Dependencies:** S07–S10. **Proposed files:** `browser_unit/test_play_protocol.py`, `test_human_controls.py`; `browser_integration/test_live_game.py`.

1. Install a recording WebSocket fake before `Play.init`. Deliver open/close/error/message events and record outbound strings. Exercise private message handlers through the socket's assigned callbacks; do not modify their visibility in production.
2. Deliver real-shaped parameters and observations. Assert the map and initial units render; blue/red role controls become available; role selection sends `role-request` with `auto_next_game: false`; waiting/input/game-over buttons match state; score, phase, on-move text, setup markers, city markers, and unit brightness update.
3. Test every exported sender: `sendMove`, `sendFire`, `sendSetupMove`, `sendSetupExchange`, `sendReset`, `sendNextGame`, and `endMovePressed`. Assert exact action/message keys and IDs after JSON parsing, not whitespace formatting. Test both role buttons and end-phase clearing of GUI marks.
4. Test `HumanPlayerControl.unitMouseDownHandler`, `markerMouseDown`, `hexMouseDownHandler`, and `resetGuiState` using selected elements and events. Cover waiting, exhausted units, selecting an eligible friendly, move marker, fire marker, self-marker cancellation, valid setup move, and friendly exchange. Verify no duplicate send from one interaction. Add explicit wrong-faction/terminal selection probes; do not assume all guards already exist.
5. Keep normal marker-based movement and direct-hex clicks as distinct cases. The latter currently refers to names not defined/imported in the module; record its precise failure without stubbing those names into existence.
6. Deliver fog disappearance/reappearance, killed units, score changes, new phase, reset, terminal status, and next-game parameters of different dimensions. Assert stale selection/highlights/units/map cells do not affect the new game. Probe the phase lookup at `observation.phaseCount` versus the actual nested `observation.status.phaseCount`.
7. Test unknown message types and malformed JSON through the fake boundary, with explicit expected exceptions. Do not claim there is graceful reconnect or error UI unless the test demonstrates it; reset currently has an empty dedicated handler and relies on observations.
8. Integrate unchanged `play.html` with a real local `GameServer` and `websockets`. Use two browser contexts for two human roles, then a browser vs function-AI case. Complete a scripted setup/move/fire/pass-to-terminal sequence and compare UI state and final score with the engine oracle.
9. The browser hardcodes `ws://localhost:9999`. In test setup only, wrap the native WebSocket constructor to replace that exact URL with the test server's ephemeral loopback address, while retaining a real WebSocket connection. Document this as endpoint configuration; it does not mock messages or transport. Alternatively use a serialized dedicated-port job, but never connect to or terminate an unrelated process on that port.
10. Run reset and next-game through actual controls and real messages, checking their different semantics and role selection behavior. Await an observed message/state/DOM condition with deadlines rather than fixed sleeps. Close both pages, contexts, sockets, and the owned server afterward.

**Completion:** a real browser action reaches the engine, produces the correct transition, and renders the returned observation; both factions, setup, fog, terminal, reset, and next-game have end-to-end coverage.

## S13 — Replay playback and writer/viewer compatibility

**Priority:** P0/P1. **Dependencies:** S08–S10. **Proposed files:** `browser_unit/test_playback.py`, `browser_integration/test_replay_roundtrip.py`.

1. Provide fixture `replayData` as an array of JSON message strings. For module tests use the test harness; for real `playback.html` route its `replay.js` request to fixture/generated content from the test process. Do not replace `browser/replay.js` on disk. Playwright's [page API](https://playwright.dev/python/docs/api/class-page) documents request routing, initialization scripts, and page evaluation used by this harness.
2. Test `Playback.init` renders the initial parameters and initializes the echelon control, then `next_message` applies each observation's position, strength, effective/fog state, and brightness. Assert return values at the end of data and no extra mutation after exhaustion.
3. Test a second parameters record midstream to represent another game, including changed unit count/map dimensions. Test repeated `init` explicitly; do not reset the closure's message index externally. Check stale units/occupancy/markers after switching scenarios.
4. Test `set_play_mode`, `play`, pause, resume, and stepping. Supply a controlled `requestAnimationFrame` queue for unit tests to advance one frame at a time; verify the real page's Play/Stop/Step controls separately. Bound repeated clicks so multiple frame loops cannot go unnoticed.
5. Test `false_color`, `terrain_color`, `orders_color`, and echelon cycling with present/missing/empty debug data, missing levels, partial color maps, and observation messages without debug after messages with debug. Assert actual fills and control values. Reproduce undeclared `echelonColorData` if orders rendering throws.
6. Test malformed JSON, empty replay, parameters-only replay, final dangling parameters, unknown message type, and action-inclusive logs. The current viewer assumes observation entries; treat action logs as a compatibility gap until supported, not as passing input merely because the writer can emit them.
7. Take an actual S08-generated ordinary replay, load it in the real page, step to completion, and compare displayed final unit states with the logged observations and Python terminal state. Test blue/red perspectives separately. With debug data, verify colors; do not require score/phase UI that the playback page does not contain.
8. Add the escaped-name writer case from S08 to the browser load test so invalid JavaScript quoting cannot pass a JSON-only assertion. Read the checked-in replay only for a bounded compatibility smoke check, not as the principal golden baseline.

**Completion:** generated default replays play through unchanged viewer code; multi-game, controls, debug coloring, fog, malformed data, and writer/viewer format limitations have explicit outcomes.

## S14 — AI, search, and hierarchy

**Priority:** P1/P2. **Dependencies:** S03–S08. **Proposed files:** `server_unit/test_ai_protocol.py`, `test_ai_heuristics.py`, `test_ai_setup.py`, `test_ai_search.py`, `test_abstract_state.py`; bounded AI integration cases in `server_integration/`.

1. Build a reusable AI protocol contract: parameters produce the correct role request; on-turn observation produces a valid action for supported scenarios; off-turn and terminal observations produce no action; setup follows the agent's declared behavior; reset/new parameters do not leave stale plans. Validate actions by applying them to the real engine. Setup actions require the setup validator rather than membership in `legal_actions`.
2. Drive the contract with an explicit registry matrix, copying kwargs for each construction. Record role, required options/model, fog/setup/hierarchy support, and suite. Give every registered alias either coverage or a named limitation. Treat `gym-pause` and callback-based agents under S15, not as ordinary move-producing AIs. Avoid high default MCTS rollout counts and production neural model requirements.
3. Add focused helper/decision tests for each group below. Use unique-best-choice positions when asserting a particular move; ties should assert membership in equally acceptable choices or patch tie selection, not incidental set/dictionary order.

| Files and principal targets | Focused assertions |
| --- | --- |
| `ai/base.py`: `AI.process`, `scenario_available`, queued actions | Hook invoked after parameters; off-turn/terminal behavior; planned actions consumed in intended order; new scenario invalidates stale plans as a defect probe. Use a tiny test subclass for the abstract decision hook. |
| `ai/passive.py`, `random_actor.py`, `shootback.py`: `AI.process`, `takeRandomAction` | Passive always passes on turn; random chooses only available move/fire options; shootback fires when possible and otherwise passes; no eligible units. |
| `ai/pass_agg.py`, `potential_field.py`, `burt_reynolds_lab2.py`, `burtplus.py`: distance/color helpers, `getPosture`, `takeBestAction` | Unequal/equal force strengths; pass/agg mode; absent enemies/cities; faction-specific cities; shoot-first decisions; weakest-target selection where implemented; valid six-digit debug colors including ties/infinities. |
| `ai/pass_agg_setup.py`, `pass_agg_setup_fog.py`, `setup_demo.py`: `getSetupMoves`, `_setupActions`, `_hexesToClosestCity` | Permitted setup cells; occupied-cell exchange; queue/pass order; insufficient cells; both factions; rebuilding a setup queue for a new game. |
| `ai/pass_agg_fog.py`, `pass_agg_setup_fog.py`: `OpforDistrib`, `colorsFromDict` | Initial/uniform support; mass movement with a safe small epsilon; visible-hex culling; normalization/zero mass; absent enemy prototype; no stale distribution in another game. |
| `ai/simpleMovement.py`: closest-target helpers, `getScore`, `findNewBestAction` | Capture/defend/offensive choices, avoidance of threat ranges, remaining-phase scoring, no legal destination. |
| `ai/simpleAssault.py`, `simpleDisengage.py`, `simpleEncircle.py`, `simpleFireCoordination.py`: `findNewBestAction` | Assault strength threshold around 75; escape choices for threatened units; encirclement distances; limited-target shooters and coordinated fire; exhausted/ineffective units; empty targets. |
| `ai/simon_says.py`: distance/setup helpers, maneuver/attack/counterattack/assault-group methods, `getPendingUnitsNextActions` | Hand-solvable two/three-unit tactical positions; queued actions remain legal when applied in order; remaining-phase and strength thresholds; bounded recursion; reset clears pending plans. |
| `ai/dijkstra_demo.py`, `stomp.py`, `stomp_scoring.py`: `runDijkstra`, `runDijkstraType`, `getScore`, action selection | Real SciPy sparse shortest paths against a tiny independently calculated directed terrain-cost graph; unreachable cells; per-type terrain; finite scores; blue-max/red-min choices; partial/full action ordering. |
| `ai/scoring.py`: converters and `AI` search methods; `pass_agg_scoring.py`, `pass_agg_fp.py` | Portable/object action round trips; wait for one unit vs pass for the phase; fixed/random/greedy/full methods; pseudo-Q versus successor-state scoring; no available units; legal ordered sequences; branch state isolation. |
| `ai/hierarchy.py`, `hierarchy_template.py`: `bossId`, crowding/command distance, abstract movement and debug helpers | Nested/root names; centers and parent relationships; crowding radii; role/commander modes; movement at multiple echelons; serializable debug colors/echelons consumable by playback. |

4. Test `abstract_state.getCM` with unequal strengths and ignored ineffective units, including all-ineffective/zero-strength groups. Test `getContainingHex` at centers and boundary offsets, `subUnits` grouping, `abstractUnitData` faction preservation/aggregation/clamping, and input non-mutation. Reproduce `createScenario` using an undefined module-global `abstate` when called outside its demo.
5. Test `mctsearch.uct_search` on a finite toy game tree with known winning/losing branches, fixed RNG, small nonzero rollout budget, and controlled `psutil.virtual_memory`. Assert legal sequences, score sign across faction changes, supplied initial state, terminal root, and memory-stop behavior. Keep debug off unless `input` is controlled; zero rollouts can mean an unbounded memory-limited run and is not a safe default.
6. Test `solver.Agenda`, `minimax`, and `perfectGame` on a tiny finite scenario/tree. For abstract toy states, patch only the state-key collaborator; separately test the real key via S05. Compare alpha-beta on/off root values, terminal state values, reused states, and reconstructed action legality. Put potentially unbounded reconstruction cases in timed subprocesses.
7. Test `ai/mcts.py` queue behavior with a mocked search boundary, then one small real search. Test `dlalphabeta.dlab/_state_value` with a fixed-valued tiny neural callable: terminal exact score, depth cutoff, red minimum/blue maximum, pruning, depth below one, and terminal initial-state error. Place these Torch-dependent cases in `ml/test_dlalphabeta.py` so the fast search tests do not eagerly import Torch. Assert the implementation's actual depth convention rather than assuming one call equals one faction turn.
8. Run a bounded, seeded game against passive for representative supported agent families. Check legality and termination, not playing strength, win rate, or exact stochastic trajectories across library versions. Capture the seed and smallest failing state in the issue record.

**Completion:** every AI family has protocol coverage and its distinctive helper/decision tests; all registry aliases are accounted for; search tests are finite and independent of model quality.

## S15 — Observation tensors, rewards, and Gymnasium

**Priority:** P1. **Dependencies:** S05–S08 and appropriate S14 helpers. **Proposed files:** `ml/test_observation_features.py`, `test_fog_features.py`, `test_gym_surrogate.py`, `test_gym_environment.py`, `test_multigym.py`, `test_neural_adapters.py`.

1. Test every feature function/factory in `observation.py` on individual units/hexes: strength normalization, factions, movable/effective flags, unit types, terrain, ownership, and constants. Test `feature` with the asymmetric rectangular fixture and missing/unplaced units to establish channel/row/column orientation.
2. Test `observation_np`: exactly 17 base channels, their documented order, per-cell values, phase channel `1 - 0.9**phaseCount`, score divided by 1000, optional appended channels, and shape validation behavior for an incompatible appended feature. Test flipped factions swap strength/ownership channels and negate score without changing terrain or input state.
3. Test `observation`: float32 Torch output, equality with the expected NumPy result, appended features, and forwarding of `flipFactions`. The wrapper currently passes `False` regardless of its argument; reproduce and track this rather than copying that mistake into the desired-contract oracle.
4. Test `zero_map`, `actor_map`, and `action_maps` for pass/move/fire with exact nonzero coordinates and unknown/removed actors. Ensure the fire target mask marks the target unit's hex, not its ID treated as a hex.
5. Test `FadingTrailFeature.update` over several controlled observations: visible enemy writes current strength, prior tracks decay, friendly/ineffective/unplaced units are ignored, and returned matrix mutation semantics are explicit. Test `fractionHiddenOpforFeature` returns counts, including no enemies, rather than assuming it already divides them.
6. Test `observation.OpforDistrib` separately from similarly named AI classes: initialization, newly hidden units, diffusion, visibility culling, normalization, repeated updates, no enemies, zero prior hidden count, and fully culled mass. Check keys remain hex IDs and all supported outputs are finite/nonnegative for an appropriate epsilon. Candidate divide-by-zero/key issues require their own reproductions.
7. Test `gym_ai_surrogate.AI.process/reset/updateLocalState/sendToServer/action_result`: parameter handshake, callback lifecycle, setup pass, wait, gym-pause when ready/terminal, accumulated reward consumed once, terminal info, and attempted-mover bookkeeping. Repeat for both factions and across next-game/reset.
8. Exhaustively test `actionMessageDiscrete` for indices 0–18 on both even/odd columns and boundary/interior locations. Cover wait, legal move, legal fire, occupied friendly, impassable/off-map target, another remaining mover versus final mover, and no mover. Test out-of-range/noninteger inputs as characterization cases. Verify emitted non-null actions are accepted by the engine; a null result is an intentional no-server-action result in some paths.
9. Test `AIx2`, `AITwelve`, `AI13`, `AI14`, `AI16`, `AI17`, and `AI18` directly, even though AI17 has no registry alias. Compare `getNFeatures()` with actual channels and expected channel meanings; AIx2 inherits three features and maps to `(channels, 2*height+1, width)` at row `2*y + x%2`. Some variants use `0.9**phaseCount`, unlike `observation_np`; test each contract separately.
10. Test both copies of `NoNegativesRewArt` and `BoronRewArt` in `gym_ai_surrogate.py` and `multigym_ai.py`: negative rewards become zero, repeated-negative discount `10/(10+n)`, strength ratio, terminal bonus, reset, and zero initial surviving strength. Separate raw blue-perspective score from shaped reward. Probe red reward sign; comments alone do not establish that the sign is flipped.
11. Unit-test `gym_interface.Args/GymEnvironment` and `multigym.Args/GymEnvironment` with a fake server boundary. Check role/AI arguments, deliberate `nReps=-1`, spaces, discrete 7/19 actions or sub-AI count, reset `(observation, info)`, step `(observation, reward, terminated, truncated, info)`, no-op handling, and current no-op render/close behavior.
12. Run a real tiny Gym episode in an isolated child process using actual engine/transport/surrogate, with step count and wall-clock bounds. Assert reset/step shapes, values, dtype, observation-space containment, terminal flags, info, and restart. Gym's declared float32 `[0,1]` box can conflict with float64 arrays and signed score channels; report violations rather than casting/clipping in the harness. `reset(seed=...)` seeds Gym but may not reseed the scenario generator; test that distinction explicitly.
13. Run the real Gymnasium/SB3 environment checkers in the dedicated ML suite. A failed checker is a recorded integration result, not grounds to change the wrapper in this phase. Ensure test-owned teardown handles the current empty `close()` method and global server singleton; do not assume two real environments in one process are independent.
14. Test `ai.multigym_ai.AI.setSubAIs/actionMessageDiscrete/process` with recording subagents: parameter/observation forwarding, selection by index, returned JSON action, duplicate setup calls, production model prediction versus training pause, invalid index, and subagent returning no action. Assert actual 17-channel observation against the wrapper; characterize differing feature-count metadata.
15. Test `LeagueEnvironment` with small fake environments: controlled weighted selection on reset, forwarding spaces/metadata and selected-env step, switch on next reset, empty/mismatched inputs, step before reset, and current no-op close/render. Use real wrappers only in isolated processes.
16. Test `ai/neural.py`, `ai/dl_alpha_beta.py`, `ai/state_eval_gpu.py`, and `ai/azero.py` with controlled model-load/search boundaries: chosen loader, constructor arguments, CPU selection, action translation, exhausted movers, observations, action queues, shared-model identity, scoring direction, and bounded batch handling. Keep a separate real tiny-model integration in S16. Probe missing required model options/import dependencies explicitly.

**Completion:** all channel layouts and action indices have exact expectations, both roles and episode restart are covered, reward shaping is separated from raw scoring, and library-contract failures remain visible.

## S16 — Models, AlphaZero, statistics, and executable examples

**Priority:** P2. **Dependencies:** S14–S15. **Proposed files:** `ml/test_portabletorch.py`, `test_network_shapes.py`, `test_alphazero_game.py`, `test_alphazero_search.py`, `test_alphazero_training_helpers.py`; `scripts/test_stats.py`, `test_read_log.py`, `test_examples.py`, `test_browser_webserver.py`.

1. Test `portabletorch.import_from_path` and `PortableTorch.save/load/print/test` using a tiny CPU model with fixed weights and source under `tests/fixtures/models/`. Save to a temporary directory, assert metadata/source/dependency copying, reload, compare weights and predictions with tolerance, verify eval mode and CPU map-location behavior, and reload two distinct models without module collision. Test missing metadata/source/weights, malformed JSON, wrong class, and incompatible weights. Load only test-owned model code/data.
2. Test `portabletorch/model.py:Model.forward`, `portabletorch/cnn.py:HexBlock/CNN`, `dlalphabeta.py:AtlatlDataset/HexBlock/CNN`, and the three saved-model architecture files `ai/A5b_M3/cnn.py`, `ai/A5b_LX3/cnn.py`, `ai/pass-v-pass-g3/cnn.py`. Use small supported constructor dimensions/MLPs, CPU tensors, and fixed seeds; assert batch/output shapes, finite values, residual behavior, dataset indexing/dtype, and repeated construction without configuration leakage.
3. For each architecture's `train` helper, use one tiny batch and fixed optimizer to assert parameters change and loss/gradient values are finite. Where a helper references an undefined global `device`, first record the unconfigured failure; an explicit test-provided CPU device can then exercise the remaining helper body, clearly labeled as configured behavior. Do not train checked-in models or allocate their large default MLPs unnecessarily.
4. Test `azg/alphazero_game.py:AtlatlGame` with its supported 5x5 scenarios and a controlled registry: initial board, size, 151-action mode, pass index 150, legal masks, move/fire index round trips for both column parities, off-map/empty-origin behavior, transition delegation, terminal and raw score, canonical faction changes, city owners, score sign, and source-board non-mutation. Test the advertised wider-action mode separately: much conversion code is hard-coded for 151 actions. Do not assume arbitrary board sizes are supported.
5. Test `azg/alphazero_observation.py` feature helpers, `nnetObservation`, and `make_observation` using a board whose state differs from parameters. Assert that current state drives placement/strength; the current parameter-based unit construction makes this a specific defect candidate. Check the 16-channel order, movable-unit and legal-target masks, phase value `0.9**(maxPhases-1-phaseCount)`, score divided by 1000, and shape. Test the standalone mover feature helper without requiring a dedicated mover channel in this tensor. Check faction/ownership channel swapping and investigate red score sign separately. Test `getSymmetries` as the actual one-element feature/policy result; do not require unimplemented rotations/reflections.
6. Test `azg/MCTS.py:MCTS.getActionProb/search` on a finite fake game with fixed neural policy/value: invalid-action masking, probability normalization, zero-prior fallback, temperature-zero one-hot choice, finite simulation count, terminal scores, reused-node visit/Q updates, and value signs when consecutive actions retain or change the acting faction.
7. Test `azg/Arena.py:Arena.playGame/playGames`: selected player across faction changes, legal-action validation, terminal score, switching players for the second half, wins/losses/draws, and odd game-count behavior. Test `Coach.executeEpisode` with a two-step fake game, controlled MCTS/sample choices, heuristic target adjustment, and bounded example collection. Do not assume players alternate after every unit action.
8. Test `Coach.learn` in `azg/Coach.py` with recording network/Arena collaborators for one iteration: history bounds, skip-first-self-play, reject/accept threshold branches, and correct checkpoint calls. Test checkpoint/example save/load with test-owned temporary files and controlled responses to missing-file prompts. Verify `getCheckpointFile` naming.
9. Test `azg/alphazero_nnet.py:NNetWrapper.loss_pi/loss_v` with hand-calculated small tensors, then `predict` and checkpoint save/load with a tiny compatible network boundary. Add one real `AtlatlNNet/HexBlock` forward pass from `azg/alphazero_atlatl_nnet.py` with appropriate batch size/eval mode. Check normalized policy and finite value; probe repeated eval predictions because dropout is forced active in `forward`. Do not mistake resetting RNG before every call for proof of deterministic evaluation.
10. Test `azg/utils.py:AverageMeter` weighted updates/reset-by-construction/formatting, and `dotdict` lookup and pickle round trip. Base `azg/Game.py` and `NeuralNet.py` are interface stubs: verify concrete implementations satisfy the used protocol; avoid meaningless tests that merely assert every stub returns `None`. Empty `__init__.py` files need no dedicated behavior tests.
11. Test `azg/util.py:playAndScore` with a short real game and controlled agents, plus both-agents-act and neither-agent-progress defect cases under deadlines. Test `azg/alphazero_main.py:main` orchestration with game/network/coach replacements; do not start self-play training. Isolate its logging setup and optional `coloredlogs` import. The historical `azg/README.txt` mentions external path/symlink assumptions; report unresolved imports instead of adding symlinks under protected source directories.
12. Test `stats.compute_mean/compute_sem/ttest/means/ttests` from a temporary working directory, capturing import-time `means()` output. Use data `[1,2,3]` for mean 2 and SEM `1/sqrt(3)`; test missing `.data` returning `"unknown"`, unequal paired lengths raising `ValueError`, known paired differences, empty/single-element/non-numeric data, and reported comparisons. Assert numeric content, not incidental float formatting.
13. Test `read_log.py` as a subprocess or controlled `runpy` script with a small generated `evaluations.npz` in its working directory. Check array names, row means, and missing-file/key behavior. It has no callable library API to unit-test directly.
14. Test `browser/webserver.py` by executing the unchanged script with a fake `socketserver.TCPServer` context that records binding and does not block in `serve_forever`. Retrieve `NoCacheHTTPRequestHandler` from the resulting namespace, then serve a test file with the real handler on an ephemeral port. Assert body/MIME and `Cache-Control`, `Pragma`, and `Expires` headers. This covers both script wiring and actual HTTP behavior without occupying port 8000.
15. Inventory all executable examples: `gym_main.py`; `sbl3/train_cnn_sbl3.py`, `train_mlp_sbl3.py`, `train_multigym.py`, `train_viz_demo.py`; `portabletorch/simple_demo.py`, `cnn_demo.py`, and `testdir/read_demo.py`. Execute unchanged source only in an isolated test subprocess with controlled dependencies and output paths. For training scripts, intercept `os.chdir(SERVER_DIR)` so work stays test-local, substitute finite fake environments and recording PPO/DQN/evaluation/callback boundaries before execution, and verify configuration/learn/save wiring. Then test any retrieved `HexBlock/MyCNN` classes with real small tensors. Do not extract and rewrite function bodies or claim mocked training is an SB3 integration test.
16. Guard test script writes against protected paths even when current directory is redirected; absolute output paths and callbacks must also be controlled. If an example cannot be safely isolated without changing its logic, mark that individual case blocked with a concrete reason. `gym_main.py`'s Gymnasium import/legacy result assumptions and script-specific missing symbols are defect candidates, not reasons to execute long training.

**Completion:** tiny real CPU persistence/inference and third-party numeric integrations pass; orchestration tests cover script wiring without training; each legacy/research file has coverage, a precise blocked case, or a justified interface/data exclusion.

## S17 — Coverage, daily execution, and readiness gates

**Priority:** continuous. **Dependencies:** applies from S01; final gate after the chosen scope of S03–S16.

1. Keep a source-to-test manifest in `tests/PROGRESS.md` with module, major callable group, case IDs, type (unit/integration/workflow), state, and known-issue link. The map below is the initial allocation; split rows as implementations arrive.

| Production surface | Owning steps |
| --- | --- |
| `map.py`, `combat.py`, `mobility.py` | S03, S09 parity |
| `unit.py`, `status.py`, `game.py` | S04–S05, S08 |
| `scenario.py`, `scenario_gen_reg.py`, `game_dispenser.py`, `current_game_access.py` | S06–S08 |
| `messageserver.py`, `gameserver.py`, `server.py`, `ai_process.py` | S07–S08, S12–S13 |
| `airegistry.py` | S07 import/registration behavior, S14 alias matrix, S15–S16 optional adapters |
| `abstract_state.py`, `mctsearch.py`, `solver.py`, `dlalphabeta.py` | S14, S16 |
| All `ai/` heuristic/setup/fog/hierarchy/scoring modules | S14 |
| `observation.py`, `gym_interface.py`, `multigym.py`, `league_env.py`, `ai/gym_ai_surrogate.py`, `ai/multigym_ai.py` | S15 |
| `ai/neural.py`, `ai/azero.py`, `ai/dl_alpha_beta.py`, `ai/state_eval_gpu.py`, bundled `ai/*/cnn.py` | S15–S16 |
| All `azg/` and `portabletorch/` source; all `sbl3/` examples; `gym_main.py`, `stats.py`, `read_log.py` | S16 |
| `browser/map.js`, `unit.js`, `combat.js`, `mobility.js`, `terrain.js`, `style.js` | S09 |
| All eight `browser/svg-*.js` modules | S10; palette interactions also S11 |
| `map-editor-control.js`, `unit-placement-control.js`, `map-editor.html`, `unit-placement.html`, `random-scenario.html` | S11 |
| `play.js`, `human-player-control.js`, `play.html` | S12 |
| `playback.js`, `playback.html`, generated/checked-in replay inputs | S13 |
| `browser/webserver.py` | S16 |
| `browser/test-data.js`, `sample-oobs/*.json`, `server/scenarios/*.scn`, model metadata/binaries | Read-only inputs to targeted compatibility tests; no generated edits or blanket runtime assertions. |

2. Define stable IDs such as `MAP-001`, `COMBAT-003`, `WS-004`, `PLAY-002`, and `GYM-007`. Test names should identify condition and result, for example `test_fire_leaves_target_effective_at_exactly_50` and `test_next_game_replaces_previous_map_cells`. Keep a failure small enough to diagnose without a full replay dump.
3. Use pytest-cov with `tests/coverage.ini`, sources `server` and `browser`, branch measurement for Python, explicit report/data paths under `tests/.artifacts/`, and exclusions only for justified demo/interface code. Keep a fast-core report and a separate full-suite report. Configure coverage's subprocess support for the pinned pytest-cov/coverage versions; current pytest-cov uses coverage's `[run] patch = subprocess`, not its former implicit child-process support. Resolve configuration/output paths for children that change working directory and verify a known child-executed function appears in coverage before claiming integration coverage. See [pytest-cov subprocess support](https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html). Python coverage does not measure browser JavaScript: collect Chromium JavaScript coverage via the browser automation/CDP boundary or another test-local instrumenter, and report script/function coverage separately. Never inject instrumented code back into `browser/`.
4. Establish current measurements before imposing numerical thresholds. Aim for at least 90% statement and 85% branch coverage of `map.py`, `unit.py`, `status.py`, and `game.py` once their steps are complete, with every P0 behavior case implemented. Treat these as proposed readiness targets, not an assertion about present coverage. Tables need semantic value checks even though line coverage marks them covered after import. Record browser function coverage and the explicit parity/interaction cases until reliable branch instrumentation exists.
5. Validate selected meaningful assertions with small mutation checks if useful: threshold `<` to `<=`, score-sign inversion, odd/even neighbor change, or movement-budget boundary. Because source is read-only, create any mutated temporary source copy beneath `tests/.tmp/`, isolate its imports, verify its provenance, and never overwrite the original. This is an optional diagnostic for test quality, not a prerequisite for every test.
6. Verify repeatability once each suite stabilizes: run it twice from clean fixtures, then once in a different test order; replay the same fixed stochastic seeds. Add Windows/Linux/macOS and a secondary browser run when environments are available. Record unavailable platforms as unverified, not passed. Do not repeat the entire suite after every documentation or helper typo when targeted checks suffice.
7. Start with modest budgets: core unit tests should be seconds to roughly a minute; individual transport cases have explicit deadlines, typically 5–15 seconds after readiness; full subprocess smoke cases allow startup plus a finite episode, initially 30–60 seconds; browser actions have bounded waits; CPU ML jobs have a separately declared budget. Calibrate from measurements and report slow cases. Never rely on a speed threshold as a test of algorithmic correctness.
8. Do not add CI workflow files outside `tests/` under this restriction. Use pytest's exit status and strict xfails, with test-local hooks/preflight fixtures making protected-path changes or missing required suite dependencies fail the session. Unexpected failures, XPASS, timeouts, and empty selections must return nonzero. Report skips/XFAIL explicitly with `-ra`; do not enable retries that conceal flaky tests. A later authorized CI integration can invoke these pytest commands directly.

### Commands to implement and document

Run from the repository root. Before S01 creates the configuration and pinned plugin requirements, use the installed pytest directly:

```text
# Current baseline; works now without planned configuration or plugins.
uv run --no-sync python -B -m pytest tests/test_scenario_loading.py -q -p no:cacheprovider

# Inspect existing tests without executing them or writing a pytest cache.
uv run --no-sync python -B -m pytest tests/test_scenario_loading.py --collect-only -q -p no:cacheprovider
```

The commands below are the target interface after S01 creates the pinned requirements and configuration; they have not been run as part of this plan revision. Retain `--rootdir=.` even though the configuration file lives under `tests/`. The `tests/pytest.ini` settings keep cache/temp/output paths under `tests/`. Explicit paths select optional suites; markers and node IDs narrow that selection. Use `--collect-only` to verify migration and selection before running longer suites. Use these commands in the future `tests/README.md` and progress records.

```text
# Baseline assertions with the completed harness, before and after syntax migration.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests/test_scenario_loading.py -v

# Default lightweight core, from pytest.ini testpaths.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=.

# Inspect the full planned suite without executing tests.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests --collect-only -q

# Explicit protocol, browser, ML, and script suites.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests/server_integration -m protocol
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests/browser_unit tests/browser_integration -m browser --browser chromium
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests/ml -m ml
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests/scripts -m scripts

# Full suite, including optional integrations; missing prerequisites fail preflight.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests

# Targeted iteration: filter a file's parametrized cases by name or use a node ID.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. tests/server_unit/test_game_combat.py -k threshold -v

# Core coverage; add the explicit tests path for full-suite coverage.
uv run --no-sync --with-requirements tests/requirements-test.txt python -B -m pytest -c tests/pytest.ini --rootdir=. --cov --cov-config=tests/coverage.ini --cov-report=term-missing --cov-report=html:tests/.artifacts/coverage-html
```

Install the pinned Playwright browser binary once during S01 using a test-local setup helper or the same dependency overlay's `python -B -m playwright install chromium`. The helper and pytest configuration hooks must set `PLAYWRIGHT_BROWSERS_PATH` to `tests/.cache/ms-playwright`, resolved from the repository root, before installation or browser launch. Set pytest-playwright's output to `tests/.artifacts/playwright` and retain traces/screenshots on failure. Keep browser installation separate from normal tests; a disconnected test run must not try to download dependencies. If the project's Python environment is absent, complete the repo's normal environment setup before testing without altering tracked dependency files.

### Multi-day iteration procedure

1. **Start:** read this checklist, the latest `tests/PROGRESS.md`, and open issue entries. Inspect the working tree and respect unrelated user changes. Record revision/environment changes since the previous session.
2. **Choose:** select one step or a named subsection whose prerequisites are complete. Record specific case IDs and intended fixtures before implementation; keep the session small enough to finish and review.
3. **Implement:** add pytest fixtures/helpers only when the selected behavior needs them; write positive, boundary, and relevant negative cases with independent expected results. Parametrize equivalent cases with useful IDs and apply suite/type markers. Keep all changes under `tests/`.
4. **Run:** select targeted pytest node IDs or paths with `-k`/`-m`, then execute the appropriate completed regression suites. Use `--collect-only` when collection or parametrization changes. Core engine additions should also run one existing bounded headless integration once available; browser additions must run their actual page/interaction over HTTP and check console errors.
5. **Triage:** reduce any unexpected failure to one fixture/action sequence. Record confirmed defect, environment limitation, unsupported behavior, or incorrect test assumption. Do not fix protected source or broadly skip a family of tests.
6. **Record:** update completed case IDs and pytest node IDs, collected/selected counts, exact commands, passed/failed/XFAIL/XPASS/skipped/deselected results, duration, artifacts, and next action. Include the date, revision, and pytest/plugin versions so later work can distinguish an old failure from a new regression.
7. **Close:** verify the protected-path content manifest and Git status, stop owned processes, and remove only owned transient outputs. Mark a major step complete only when its completion criteria hold; otherwise leave it open with remaining cases listed.

Suggested progress entry:

```text
Date / revision / environment:
Step, case IDs, and pytest node IDs:
Files added or changed under tests/:
Fixtures and expected-value rationale:
Commands, collection counts, and results (passed / failed / XFAIL / XPASS / skipped / deselected):
Defect IDs or external blockers:
Protected-directory check and cleanup result:
Next smallest unfinished task:
```

**Final readiness gate:** all P0 behavior cases and the chosen P1 scope pass; all remaining defects/skips are individually identified; no unknown browser errors or leaked processes remain; engine/browser parity and generated-replay playback have real integration coverage; no prohibited file changed. Unimplemented P2 cases remain explicit backlog items rather than being counted as coverage. Coverage percentages support this decision but cannot replace the behavioral gates.

## Initial investigation register

These are findings from source review, **not runtime-confirmed defect reports from this planning task**. Create minimal reproductions before assigning expected-failure status. Some represent deliberately limited behavior rather than a defect; record that decision explicitly.

| Candidate ID | Observation and first reproduction | Owning step |
| --- | --- | --- |
| K01 | Reverse-edge lookup does not reverse endpoints in either implementation; Python's reverse key also contains a literal `$`. Create two adjacent hexes and compare shared-edge references. Python `Path.portableCopy` assigns attributes on a dict, and path loading is disabled. | S03, S09 |
| K02 | Python caches dimensions and grid creation does not fully reset all indexes; JavaScript `fromPortable` retains old `hexIndex`/`pathIndex`. Load a large map then a smaller map with paths in one instance/page. | S03, S09–S13 |
| K03 | Setup validation checks faction/zone but not all occupancy/exchange constraints; direct terminal transitions are not guarded; the documented public `is_legal` is absent. Test each behavior separately. | S05 |
| K04 | Damage can exceed a target's remaining strength, and loss credit follows calculated damage. Test overkill separately from below-threshold removal and decide the intended scoring contract. | S05 |
| K05 | Observation generation shares status references and serialization updates stochastic detection. Factories return shared/shallow data in several places. Test identity/mutation/RNG effects without assuming pure getters. | S04–S06 |
| K06 | Scenario generation can select the same city repeatedly; hierarchy placement can reuse locations across branches. Validate unique counts/occupancy with small fixed seeds. | S06 |
| K07 | `server.init` mutates registry kwargs, tests seed/cycle options by truthiness, and recognizes different gym variants for blue/red. Test two initializations and seed 0, then a red-role variant. | S07, S15 |
| K08 | Role assignment can overwrite a role, `clear_roles` leaves client-ID mappings, and disconnected sockets remain in the client list. Test duplicate assignment, next-game, and disconnect routing. | S07–S08 |
| K09 | Replay JSON is wrapped in single-quoted JavaScript strings without escaping apostrophes. Logs may include actions, but the viewer expects observations. Test escaped names and `log_actions` separately. | S08, S13 |
| K10 | Browser `Terrain.paths` uses `EdgeType`, so generated IDs conflict with path-name slicing. Test clicking Road/Path on the actual palette. | S09–S11 |
| K11 | Human direct-hex movement references undefined `moveTargets`, `fireTargets`, and `SVGUnitSymbol`; `Play` reads phase count at the wrong nesting level. Test marker movement and direct-hex movement separately. | S12 |
| K12 | Playback uses undeclared `echelonColorData`, advances after parameters without checking an observation exists, and does not reset `message_index` in `init`. Test orders, truncated replay, and reinitialization. | S13 |
| K13 | SVG company-echelon drawing references `strokeWidth` outside its scope; repeated marker/index initialization and no-live-unit highlighting have edge cases. Create a company symbol and repeat render/clear cycles. | S10 |
| K14 | `observation.observation` ignores `flipFactions`; `OpforDistrib.add` can divide by zero and use a hex object as a key. Use asymmetric faction data and a first newly hidden opponent. | S15 |
| K15 | Gym observations can be float64 or outside declared bounds; red reward sign is not flipped in `updateLocalState`; real environment `close` is empty; multi-gym feature metadata differs from its tensor. Check each contract independently. | S15 |
| K16 | `abstract_state.createScenario` reads `abstate` instead of its parameter; state keys omit/truncate some distinctions. Use direct function calls outside demos and minimally differing states. | S05, S14 |
| K17 | AlphaZero adapter/action-size assumptions, agent constructor calls, player bookkeeping, and forced dropout need compatibility tests. Some legacy scripts/imports reference missing or obsolete APIs. Use tiny board/model collaborators and explicit import provenance. | S15–S16 |
| K18 | AlphaZero observation construction initializes units from parameters without applying current state; the red score channel also needs a perspective check. Move/damage a unit after initialization and compare exact tensor cells for both factions. | S16 |

Maintain the full reproduction details and later discoveries in `tests/KNOWN_ISSUES.md`; this table is the starting investigation queue, not permission to alter production behavior.
