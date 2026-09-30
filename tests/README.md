# Test harness

S13 replay coverage is in `browser_unit/test_playback.py` and
`browser_integration/test_replay_roundtrip.py`. Run it with:

```text
uv run pytest tests/browser_unit/test_playback.py tests/browser_integration/test_replay_roundtrip.py -q
```

`support/playback.py` supplies arrays of JSON message strings, original modules
in the HTTP harness, an explicit animation-frame queue, and SVG/model assertions.
Real-page tests route only the replay.js request to fixture or freshly generated
server content; the checked-in file is never replaced. Real server logs cover
both perspectives, fog and two completed games, compared with transcripts,
the independent episode oracle and Python terminal state. Controls run through
native clicks, with separate native-animation completion coverage. Debug colors,
malformed inputs, action-log limitations, stale indexes and narrow strict xfails
for K09/K30/K31/K32 are documented in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
No score/phase UI is assumed for playback.html.

From the repository root, run the default core suite with:

```text
uv run pytest
```

Pytest automatically discovers the repository-root [pytest.ini](../pytest.ini).
The project environment now includes pytest, pytest-asyncio, pytest-playwright,
and pytest-cov, so no dependency overlay or explicit configuration path is needed.

S01–S13 are implemented. Test code, fixture data, and generated artifacts remain under
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

# Default core suite: original baseline, harness checks, and engine unit tests.
uv run pytest

# S03 geometry, serialization, and all combat/mobility coefficients.
uv run pytest tests/server_unit/test_map_geometry.py tests/server_unit/test_map_serialization.py tests/server_unit/test_rule_tables.py

# S04 unit state, occupancy, movement, targeting, and deterministic detection.
uv run pytest tests/server_unit/test_unit_state.py tests/server_unit/test_unit_movement.py tests/server_unit/test_unit_visibility.py

# S05 status, setup, actions, combat, observations and search keys.
uv run pytest tests/server_unit/test_status.py tests/server_unit/test_game_setup.py tests/server_unit/test_game_actions.py tests/server_unit/test_game_combat.py tests/server_unit/test_game_observations.py tests/server_unit/test_game_state_key.py

# S06 scenario loading, generators, registries and game dispensers.
uv run pytest tests/server_unit/test_scenario_factories.py tests/server_unit/test_scenario_registry.py tests/server_unit/test_game_dispenser.py

# S07: transport, protocol routing, and isolated server initialization.
uv run pytest tests/server_unit/test_message_clients.py tests/server_unit/test_message_routing.py tests/server_unit/test_gameserver_protocol.py tests/server_unit/test_server_init.py

# S08: real function/WebSocket games, CLI/AI children, and replay files.
uv run pytest tests/server_integration -q

# Check default and full discovery without running tests.
uv run pytest --collect-only -q
uv run pytest tests --collect-only -q

# Browser models and harness, including console/page-error checks.
uv run pytest tests/browser_unit -m browser --browser chromium

# S09 shared Python/JavaScript geometry, movement, targeting and combat audit.
uv run pytest tests/browser_integration -q

# S10 native SVG utilities, rendering, viewport, markers, and symbols.
uv run pytest tests/browser_unit/test_svg_util.py tests/browser_unit/test_svg_rendering.py tests/browser_unit/test_svg_markers.py tests/browser_unit/test_unit_symbols.py -q

# S11 editor/placement controllers and all three creation pages.
uv run pytest tests/browser_unit/test_editor_controls.py tests/browser_unit/test_placement_controls.py tests/browser_integration/test_map_editor_page.py tests/browser_integration/test_unit_placement_page.py tests/browser_integration/test_random_scenario_page.py -q

# All currently implemented tests, including browser model contracts.
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
`tests/server_integration` for real protocol/CLI/replay checks, `tests/ml` for ML
checks, and `tests/scripts` for isolated demonstrations. The ML suite currently
contains one CPU-model fixture preflight; browser integration contains S09
model compatibility checks and S11 creation-page workflows, and scripts remains
empty. Empty selections return pytest's nonzero exit status.
Executable examples and cached dependency tests are outside default discovery;
pytest also excludes the dot-prefixed cache/temp/artifact directories.

The suite uses plain pytest functions, strict markers/configuration/xfails,
function-scoped strict asyncio loops, and Playwright's fresh context/page
fixtures. S02 also scopes the Playwright driver/browser dependency chain to each
test: a session-scoped synchronous driver leaves a running loop that conflicts
with pytest-asyncio when browser cases run first. This intentionally trades
browser startup time for reliable cleanup and order independence, while reusing
the plugin fixture implementations and artifact handling. Required plugins fail
configuration if missing; an explicitly selected
browser test fails setup if its binary is missing. Future optional suites must
provide similarly explicit dependency preflights, not blanket skips.

Use `engine_imports` and `import_server()` for flat engine modules: paths derive
from the helpers' file locations, module origins are asserted, and temporary
path/module entries are restored. For `azg` and `portabletorch`, use
`run_python(..., cwd=tmp_path)` to isolate import collisions and global state.
Inside that subprocess, `explicit_module(name, path)` can load `server/game.py`
as `game` or `server/azg/Game.py` as `Game`, restoring any previous module entry.
Do not import training scripts during collection. See [fixture schemas](fixtures/README.md)
for the S02 factory defaults and reusable inputs.

The local HTTP fixture binds loopback on an assigned port, checks readiness,
serves JavaScript with the correct MIME type, and shuts down after each test.
Routes expose only `/browser/`, `/tests/browser_support/`, and `/tests/fixtures/`.
It never imports the production fixed-port web server. Use `checked_page` to
collect console errors, uncaught JavaScript exceptions, failed requests and
unexpected dialogs, checked during teardown. Its `expected_page_errors` argument
matches an exact ordered list for a specific defect reproduction; other errors
still fail. The browser-unit `module_page` fixture installs finite random draws
and recording WebSocket boundaries before navigation/imports. Real transport
tests should use ordinary `page` with `checked_page`, not the WebSocket fake.

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
S01. S02 supplies fixtures and consumer checks; subsequent steps add full
behavioral coverage. S03 adds 92 cases (83 passing contracts/characterizations
and 9 strict expected failures for K01/K02). Each expected failure matches only
the documented wrong signature; unrelated exceptions fail and fixes produce
strict XPASS failures for review. The scripted S02 four-phase game runs directly
through the engine and does not invoke the stochastic launcher smoke scenario.

S04 adds 84 passing unit cases across unit state, movement and visibility. Use
`unit_world` to construct fresh real map/unit objects from portable builders or
an explicit `map_input`, without invoking serialization/detection. Movement
expectations use literal destination sets plus independent Bellman-Ford costs
on a hand-written neighbor graph. Probability, sight, range and stacking overrides
use pytest's restoring monkeypatch fixture; randomness uses finite draws at
`unit.random`. Passing characterizations for duplicate IDs, live unplaced units,
partial observations and serialization side effects are documented in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md); S04 adds no expected failures.

S05 adds 149 cases: 148 unit cases and one scripted setup-to-terminal integration
sequence. The six files above cover public accessors, setup, legal/invalid actions,
phase and city timing, all 16 attacker/target pairings, damage thresholds, scoring
signs, state isolation, fog observations and search keys. `game_factory` constructs
the real engine with finite detection draws; combat expectations are literal
hand calculations and table overrides use restoring monkeypatches. Characterized
validation gaps, overkill, shared references and key limitations are recorded in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md); S05 adds no expected failures.

S06 adds 100 passing cases (94 unit, six integration) across the three files
above. Coverage includes temporary scenario paths and UTF-8 loading, exact
regions, shallow color flips, all three generator families, seed zero, cycles,
balanced pairs, hierarchy names, city attempts, registry consumers and dispenser
identity. Placement comparisons exclude only `detected`; separate tests verify
ambient detection draws and caller RNG effects. Invalid inputs and hierarchy
collisions run in subprocesses with ten-second timeouts. K05/K06 and unsupported
input behavior are characterized in [KNOWN_ISSUES.md](KNOWN_ISSUES.md), with no
new xfails. Packaged scenarios are only read; generated inputs stay test-local.

S07 adds transport and game-server unit tests in the four files above. Socket
iteration/send and game transitions use controlled collaborators; these are not
real WebSocket integration tests. Function-client tasks use events, bounded
waits and cancellation/await teardown. Constructor/run tests use a child-owned
loop with a watchdog, fake socket context, and explicit task/loop cleanup.
GameServer tests restore the SIGINT handler and replace transport, exit and
loop-stop boundaries so the pytest runner survives unchanged.

Initialization tests run in fresh ten-second subprocesses using
`support/server_init_boundary.py`: fake AI constructors, scenario/dispenser
factories and an inert GameServer capture arguments and registration order.
Neural-gating probes execute the real registry with inert AI import boundaries;
they do not exercise actual optional model imports or claim Torch-free startup.
K07/K08 and unsupported-message behavior are characterized in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md). Real sockets, full games through transport,
and replay output validation are covered separately in S08.

S08 adds 24 integration cases in `server_integration/` (including three strict
expected failures for K09/K19). `support/integration_server.py` starts a real
GameServer/MessageServer in an owned child, reports an ephemeral loopback port
only after the real bind, and cleans up sockets, tasks, logs and the loop.
The parent records stdout/stderr and enforces deadlines with terminate/kill
fallbacks for only its own children. No readiness retries can turn a failed
game into a pass. Completed games must close replay logs through production
`do_exit`; the helper closes interrupted-game logs during teardown.

The shared literal episode oracle checks every parameter and observation,
including the independently calculated score 50, two-game reset and fresh role
requests. Real sockets cover both factions, mixed function/socket clients,
wrong-turn errors, malformed JSON and retained disconnected clients. CLI tests
use the active interpreter, both passive AIs, `--nReps 1`, seed 1729, and explicit
test-local replay paths; aliases are small read-only engine checks.

AI-process tests expose the Python 3.14 direct-startup loop error separately
from working exchanges with a test-only existing-loop bootstrap. Graceful server
closure currently raises `ConnectionClosedOK` in the AI child. The replay reader
decodes JSON inside the writer's JavaScript envelope without evaluating code.
Blue/red fog perspectives, action inclusion, fresh parameters per game, and
complete file closure are covered. Apostrophe/backslash escaping defects have
exact-signature strict xfails; Unicode-only names pass. Actual JavaScript
execution and viewer/action-log compatibility are covered by S13 above. Generated replay files
stay in pytest's disposable directory; S13 reuses `running_server` and
`read_replay` to generate fresh inputs without changing `browser/replay.js`.


S09 adds model tests in `browser_unit/test_map_model.py`, `test_unit_model.py`,
`test_rule_data.py`, and shared contracts in `browser_integration/test_engine_parity.py`.
Run all S09 cases with:

```text
uv run pytest tests/browser_unit/test_map_model.py tests/browser_unit/test_unit_model.py tests/browser_unit/test_rule_data.py tests/browser_integration -q
```

`support/browser_models.py` loads six original ES modules over HTTP in a fresh
page/context. The game Map uses the test-only `GameMap` alias so the JavaScript
built-in Map remains available. Only SVG symbol creation is replaced by a
recording boundary: S09 makes no rendering claim. Same-page replacement tests
never reset the modules between loads. Exact-signature strict xfails distinguish
confirmed defects from unsupported-input/display-format characterizations.
See [BROWSER_COMPATIBILITY.md](BROWSER_COMPATIBILITY.md) for shared fixture scope,
semantic serialization comparisons and the separate firepower-difference audit.
Actual SVG rendering is covered by S10 below and creation pages by S11;
live play is covered by S12 below; replay is covered by S13 above.

S10 adds 99 browser cases across the four files in the command above.
`browser_support/svg.js` loads original rendering/model modules; `svg_page`
uses a fresh context, fixed 1000x800 viewport, attached SVG elements and native
`getBBox`/transforms over HTTP. Unlike the S09 model fixture, it does not replace
symbol creation. Small literal inputs and numeric tolerances are the main
oracles; `browser/sample-oobs/oob-all-symbols.json` is a read-only compatibility
smoke input. Screenshots and traces remain diagnostics.

Coverage includes fitted bounds and zoom clamping/restoration, rectangular maps,
primitives/layout, all view factories, palette generation, terrain/debug colors,
setup/city/action markers, all 28 symbol switch aliases, echelons, brightness,
observations, movement and selection. Controller callbacks are recording
boundaries only in wiring tests; DOM events verify callback registration, not
full editing or live-play behavior. Play-view root mousedown currently invokes
UnitPlacementControl, while hex callbacks invoke HumanPlayerControl.

K10/K13/K22/K23 have narrowly matched strict xfails; see KNOWN_ISSUES.md for
reproductions. The test HTTP server has a 128-connection listen backlog to
accommodate parallel module imports on Windows; no request retries or ignored
browser errors are introduced. Production renderers and geometry APIs remain
unchanged. Editing and placement workflows are covered by S11 below and live
play by S12; replay is covered by S13 above.

S11 adds 46 cases across the five files listed above. Controllers use original
exported handlers with attached real elements and DOM events. Page workflows
load unchanged HTML over HTTP, exercise controls, inspect SVG/model changes,
copy JSON, parse the SVG data URI as XML, and send an exported scenario through
the real Python loader, initial state and one legal setup pass.

`support/creation_pages.py` supplies small fresh map/OOB inputs and prompt/copy
boundary recording. Ordinary error checks remain active. Defect probes allow
only a single exact page error, raising `KnownDefect` after checking all other
browser errors; fixes produce strict XPASS. A separate Chromium clipboard smoke
test grants clipboard permissions to the loopback origin and calls the real
clipboard API. Other browsers/clipboard environments remain unverified.

Generation uses a finite nonzero random sequence and covers default 10×10,
nonsquare 8×12 and same-page regeneration, plus a small-dimension defect probe.
Repeat loads, cancellation, malformed JSON, empty/insufficient OOBs, score/fog
controls, Test Input and sample symbols have explicit coverage. Known K01 edge
identity is excluded only from geographic-content comparisons; its dedicated
tests remain in S03/S09. K10/K24/K25 have five individual strict xfails. K20
replacement effects and unsupported inputs are named characterizations, not
approved future contracts. See KNOWN_ISSUES.md for exact signatures.

Use `rng` for Python/NumPy seed isolation. ML subprocesses use
`isolated_rng(torch_module=torch)` to preserve CPU RNG, deterministic-algorithm
settings and thread count; GPU state requires a separate device-specific guard.
Use `detection_draws([values...])` to patch `unit.random` at its lookup site.
Finite draws fail on exhaustion. Browser draws are nonzero to avoid a stuck
Box-Muller rejection loop.

`engine_globals` protects rule tables, both registries and nested options,
current-game binding, transport sleep/IDs and loaded AI counters. It retains
nested object identities, including shared armor/mechanized tables. For globals
loaded later, register `global_guard((object, 'attribute'), ...)` before mutation;
this also handles missing `server.server`/`gym_ai`, AI instance counters and
`PortableTorch.cnt`. Import server initialization and PortableTorch in bounded
subprocesses. `run_python` fixes the child hash seed, removes inherited model/
checkpoint/neural environment settings, and includes stdout/stderr in failures.
Explicit model environment overrides must point at test-owned artifacts.

`owned_tasks` registers tasks immediately and cancels/awaits them at teardown;
`installed_loop(previous=...)` is synchronous-only and restores the supplied
prior loop. Use pytest-asyncio's loop in async tests. `doubles.py` provides
recording function clients, finite async WebSockets, a finite dispenser/game
tree, and controlled model predictions. They are boundary doubles, not claims
of transport or model integration coverage.

```text
# S02 fixture and isolation consumers.
uv run pytest tests/server_unit/test_fixtures.py tests/server_unit/test_isolation.py

# Explicit CPU model preflight; missing Torch fails rather than skips.
uv run pytest tests/ml
```


S12 covers live-play socket callbacks, exact outbound messages, controller
selection/actions, and observation rendering in 31 browser unit cases, plus six
real browser/server integration cases. Run just S12 with:

```text
uv run pytest tests/browser_unit/test_play_protocol.py tests/browser_unit/test_human_controls.py tests/browser_integration/test_live_game.py -q
```

`support/live_play.py` loads unchanged `play.html` over HTTP. Unit cases install
the existing recording WebSocket before Play.init and invoke private message
handling through its assigned callback. Actual SVG/model behavior is retained.
A delegating spy observes phase initialization without replacing its behavior.
Six exact-signature strict xfails document K26–K29; other errors fail normally.

Integration cases use two fresh browser contexts or a browser against the
existing scripted function client, a real GameServer and native WebSockets.
A constructor wrapper substitutes only the exact hardcoded localhost:9999 URL
with the owned server's ephemeral loopback endpoint and records incoming JSON;
it does not replace messages or transport. DOM mousedown events exercise unit,
hex and marker listeners; ordinary control buttons use Playwright clicks.
Complete episodes match the independent S02 message/score oracle (score 50).
Setup, role swapping, reset, next-game, terminal restart and deterministic
sight-range fog transitions have end-to-end coverage. All owned servers finish
bounded repetitions and report task/loop/log cleanup. Conditions and messages
are awaited with deadlines, without browser sleeps. Generated logs stay under
pytest's disposable directory. Replay viewer coverage is in S13 above.
