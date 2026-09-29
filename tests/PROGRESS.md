# Test implementation progress

Current invocation (2026-09-24): `uv run pytest` from the repository root.
The root `pytest.ini` and installed project plugins supersede the test-local
configuration/overlay commands in the historical entries below.

## 2026-09-28 — S08 completed

Implemented **S08 — Engine/client/WebSocket integration and replay writing**.
S01–S08 are complete; S09–S17 remain open.
Starting revision: `7a9e243ca226d9b6d7425d92210eab05de6c321e`.
Preserved the pre-existing untracked `demo_script.txt`. All changes are under
`tests/` or root `test_plan.md`; dependencies and pytest configuration are unchanged.

Added **24 integration cases**, marked `integration` and `protocol`, in the
explicitly selected `server_integration/` suite:

- `test_function_clients.py` (2): real Game, scenario-generator dispenser,
  GameServer and MessageServer complete one/two tiny games through function
  clients. A literal independent oracle checks every parameter/observation,
  score 50, repetition count, role reassignment, and fresh units/actions.
- `test_websocket_game.py` (6): two real WebSocket clients and mixed
  function/WebSocket play complete the same episode. Separate children check
  both wrong-turn directions, malformed JSON, and clean disconnect, including
  close code 1011, unchanged rejected-action state and retained client mappings.
- `test_server_cli.py` (5): actual bounded CLI runs use both passive AIs,
  `--nReps 1`, seed 1729 and temporary blue/red replay paths. Generator,
  production bare filename and temporary explicit path all finish. The two
  packaged aliases get small read-only loader/dispenser/engine checks.
- `test_ai_process.py` (4): unknown alias, direct Python 3.14 startup, actual
  `--uri`/response/no-response exchanges, and a complete GameServer game against
  the separate AI. Working cases use an explicitly documented existing-loop
  bootstrap; direct startup remains a strict K19 xfail. Normal peer closure
  propagates ConnectionClosedOK/exit 1 and is characterized separately.
- `test_replay_writer.py` (7): complete blue/red arrays, two-game parameters,
  action inclusion/exclusion and order, fog perspectives, Unicode, and strict
  K09 xfails for apostrophe/backslash JavaScript-string escaping.

`support/integration_server.py` provides child ownership, real ephemeral bind
readiness, bounded waits, stdout/stderr capture, watchdog, task/socket/loop/log
cleanup, and terminate/kill fallback for only owned children. The thin serve
wrapper delegates to the real library and reports its actual bound port; it
does not replace transport or routing. Completed episodes must close replay
files in production `do_exit`, before helper cleanup. Child reports verify no
remaining tasks and closed loops/logs. `support/episode_assertions.py` supplies
the literal timeline and JSON-only replay-envelope reader. No checked-in replay
is overwritten. JavaScript execution and viewer compatibility remain S13.

Validation uses Windows/Python 3.14.4, the existing project environment,
`UV_CACHE_DIR=tests/.cache/uv`, and `uv run python -B -m pytest`:

- Initial sandbox run: seven setup errors and nine warnings from the previously
  documented Windows temporary-directory/cache permissions, before test bodies.
- Initial outside-sandbox run: two passes and five failures exposed a test-helper
  shutdown deadlock. Cancelling WebSocket internals before closing sockets was
  incorrect. The helper now cancels application handlers, explicitly closes
  their sockets, waits for the real server to close, then cancels remaining tasks.
  These harness failures were fixed, not skipped or converted to xfails.
- Intermediate expanded suite: **17 passed, 2 xfailed in 14.34s** (19 cases).
- AI-process suite: **3 passed, 1 xfailed in 9.06s**.
- Full regression, `uv run python -B -m pytest tests -q`: **652 passed,
  12 xfailed in 792.41s**, including Chromium and the CPU model preflight.
- Final S08 run in reverse file order (websocket, CLI, replay, function, AI):
  **21 passed, 3 xfailed in 25.01s**. Exact command:

```text
uv run python -B -m pytest tests/server_integration/test_websocket_game.py tests/server_integration/test_server_cli.py tests/server_integration/test_replay_writer.py tests/server_integration/test_function_clients.py tests/server_integration/test_ai_process.py -q
```

Both final runs used approved execution outside the Windows sandbox and had
**0 failed, 0 warnings, 0 skipped, 0 XPASS and 0 deselected**. The previous 631
passing cases and nine K01/K02 expected failures retain their results; S08 adds
21 passes and three expected failures. The reverse-order run also verifies the
final stricter CLI stderr and socket-error-count assertions. Both protection
reports checked **315 files** with no added, removed or changed protected files
and no protected Git diff change. `git diff --check` passed. Owned children exit
or are reaped by their context managers; successful server reports contain zero
pending tasks and closed loops/logs. No additional launcher smoke was needed:
S08 itself runs three bounded headless CLI games plus transport games.

K08/K09/K19 details and exact reproductions are in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
README documents the explicit S08 run command and lifecycle/format limitations.
No production fixes were made. Other platforms/Python versions remain unverified.

Next step: **S09 — Browser map/unit models and Python–JavaScript compatibility**.

## 2026-09-28 — S07 completed

Implemented **S07 — Message transport, game-server routing, and initialization**.
S01–S07 are complete; S08–S17 remain open.
Starting revision: `05ba3f0ea5e9384560962cfcbf6d5fc48c0d0127`.
Preserved the pre-existing untracked `demo_script.txt`. Changes are limited to
`tests/` and root `test_plan.md`.

Added **129 unit cases**, all marked `core`, `unit`, and `protocol`:

- `server_unit/test_message_clients.py` (13): unique/resettable IDs, separate
  queues, JSON wire delivery, awaited socket sends, function returns/callbacks,
  FIFO order, absent responses, malformed JSON, callback type rejection,
  unsupported return shapes and verbose truncation.
- `server_unit/test_message_routing.py` (11): exact send/broadcast/relay
  recipients and serialization, empty recipients, registration before inbound
  messages, clean/malformed/exceptional closure, retained disconnected clients,
  event-driven function processing, and constructor/run socket scheduling
  inside a child-owned running loop with and without socket startup.
- `server_unit/test_gameserver_protocol.py` (52): constructor forwarding,
  parameter/role/observation order, both turns and same-faction continuation,
  single transitions, debug metadata, every protocol state, wrong/missing
  types/roles/clients/actions, game error propagation, reset/next-game/pause,
  duplicate assignments and stale authorization, all combinations of terminal
  faction/repetition mode (-1/0/1)/auto-next, two-game repetition accounting,
  score output, exit ordering and faction-correct log routing.
- `server_unit/test_server_init.py` (53): generator/file selection, both/no
  faction clients, all AI options/shared models, current-game registration
  before exactly one run, replay/log/socket options, zero seed/cycle, repeated
  initialization and same-alias leakage, all blue/red Gym aliases, accessors
  and reset/submit/resume order, invalid initialization and neural import gating.

`support/server_init_boundary.py` supplies subprocess-only inert constructors
and import boundaries. It executes real initialization and registry gating;
actual model imports remain S15/S16. The subprocess helper forces neural off
at process startup, so gating probes explicitly set/unset the environment
inside the fresh child before importing. Transport tests reuse S02 doubles and
task ownership; no sleeps are used as readiness checks. Constructor children
have ten-second process deadlines, two-second loop watchdogs, and task/loop
cleanup. GameServer tests restore the actual SIGINT handler; stop/exit calls
use inert boundaries. No production behavior is patched to make an assertion
pass. Real socket exchange and replay-file validation remain S08.

Recorded K07/K08 and exact input limitations in KNOWN_ISSUES as passing
characterizations, consistent with S04–S06. No new xfails, production fixes,
dependencies or configuration changes. README includes the S07 run command.

Validation on Windows/Python 3.14.4 with the existing project environment and
`UV_CACHE_DIR=tests/.cache/uv`. Let `S07` mean the four files listed above:

| Command | Result |
| --- | --- |
| `uv run python -B -m pytest S07 -q` (sandbox) | 74 passed, 55 setup errors, 57 warnings; Windows denied pytest temporary-directory access. |
| Same command with approved execution outside sandbox | **129 passed in 38.05s**, no failures, warnings, skips, xfails or deselections. |
| `uv run python -B -m pytest tests -q` (approved outside sandbox) | **631 passed, 9 existing xfailed in 568.30s**. |

The full run includes existing Chromium, async and CPU model tests, with
**0 failed, 0 warnings, 0 skipped, 0 XPASS and 0 deselected**. All previous 502
passing cases and nine K01/K02 expected failures retain their outcomes.
Both protection reports checked **315 files**, with no additions, removals,
content changes or protected Git diff changes. `git diff --check` passed.
No launcher smoke game was needed for test-only work; existing bounded engine
episodes ran in the full suite. Other platforms/Python versions remain unverified.

Next step: **S08 — Engine/client/WebSocket integration and replay writing**.

## 2026-09-28 — S06 completed

Implemented **S06 — Scenarios, registries, and dispensers**. S01–S06 are
complete; S07–S17 remain open. Starting revision:
`6a8a3f15cf1daacc83ece8b028ef2b13f43a98ca`. Preserved the pre-existing untracked
`demo_script.txt`. Changes are limited to `tests/` and root `test_plan.md`.

Added **100 passing cases** (94 unit, six integration):

- `server_unit/test_scenario_factories.py` (89): temporary path forms including
  spaces/home/custom directories and cwd independence; UTF-8/eager/shared loading;
  missing/invalid/incomplete files; exact setup/rectangle regions; shallow color
  flips; three-family seeded sequences and cycles including seed zero; balanced
  pairs; dimensions, counts, names, depths/branching, placement, terrain, scoring,
  fog and ownership; ambient detection RNG and failure-state leakage; repeated
  city attempts and hierarchy collisions. Invalid inputs/collisions use bounded
  subprocesses with ten-second timeouts and test-owned working directories.
- `server_unit/test_scenario_registry.py` (six): registry structure/signatures,
  one representative of each family through real Game consumption, and both
  read-only packaged aliases accepting unused generator options. Large default
  hierarchy/clear generators are not exercised. The original alias and launcher
  baseline tests remain unchanged.
- `server_unit/test_game_dispenser.py` (five): fresh Games/maps for successive
  generator calls, shared scenario parameters, exact constant-game identity,
  error propagation and current-game binding/replacement/restoration.

Reused existing isolation, builder and subprocess helpers. Placement sequences
exclude only detection flags; separate tests explicitly verify detection and
RNG effects. Coordinate/count/name expectations are independent of generation;
setup helper expectations are literal ID tables. No production methods are
replaced to satisfy assertions. Rule overrides use restoring monkeypatches.

Updated KNOWN_ISSUES with K05 factory sharing/RNG behavior and K06 repeated city
placement/cross-branch occupancy, plus unsupported-input exception signatures.
These are passing characterizations, not newly approved rules; no new xfails
or production fixes were introduced. Updated README commands and plan status.

### Validation

Windows / Python 3.14.4, existing project environment, with
`UV_CACHE_DIR=tests/.cache/uv`. Commands use `python -B` and the existing harness
also disables subprocess bytecode. Let `S06` denote these exact paths:

```text
tests/server_unit/test_scenario_factories.py tests/server_unit/test_scenario_registry.py tests/server_unit/test_game_dispenser.py
```

| Command | Result |
| --- | --- |
| `uv run python -B -m pytest S06 -q` (initial sandbox run, before final additions) | 55 passed, 28 setup errors, 30 warnings; Windows denied pytest temp/cache access. |
| Same command outside sandbox (initial implementation) | 82 passed, one failed expectation: invasion height one produces `hex-0--1`, not `hex-0-1`; corrected the characterization to the observed negative-row lookup. |
| `uv run python -B -m pytest S06 -q` (final, approved outside sandbox) | **100 passed in 8.92s**. |
| `uv run python -B -m pytest tests -q` (approved outside sandbox) | **502 passed, 9 existing xfailed in 95.33s**. |

The final full run includes existing Chromium, async and CPU model tests. It
has **0 failed, 0 warnings, 0 skipped, 0 XPASS and 0 deselected**. All previous
402 passing tests and nine K01/K02 expected failures retain their outcomes.
The protection report checks **315 files**, with no added/removed/changed files
and unchanged protected Git diff. `git diff --check` passed. No dependencies,
configuration or production files changed. No launcher smoke game was needed
for test-only work; existing bounded engine episodes ran in the full suite.
Other platforms and Python versions remain unverified.

Next step: **S07 — Message transport, game-server routing and initialization**.

## 2026-09-28 — S05 completed

Implemented **S05 — Game transitions, setup, combat, phases, and scoring**.
S01–S05 are complete; S06–S17 remain open. Starting revision:
`bc1c10eaa92b85a04d42cbdd2b82484aae4abf03`. Preserved the pre-existing untracked
`demo_script.txt`. Changes are limited to `tests/` and root `test_plan.md`.

Added **149 passing cases** (148 unit cases and one integration sequence) in
the six planned files:

- `server_unit/test_status.py`: defaults/configuration, portable ownership,
  kill-score signs and configurable penalties, city-share division, neutral and
  vacated cities, capture, zero-city maps, phase availability, faction flags,
  phase limits and elimination behavior.
- `server_unit/test_game_setup.py`: both factions' placement, friendly exchange,
  setup passes without score/phase increments, rejection/input preservation,
  malformed fields, setup validation gaps, and a scripted setup-to-terminal
  sequence with exact full states and a final score of 24.
- `server_unit/test_game_actions.py`: legal action filtering and exhaustion,
  ordinary moves and automatic/explicit phase advance, delayed city capture,
  invalid actions, malformed/unknown IDs, extra fields, terminal calls,
  off-faction flags and independent successor branches.
- `server_unit/test_game_combat.py`: all 16 attacker/target type pairings,
  terrain effects, both firing factions, fractional strengths, below/equal/above
  the 50 threshold, defensive clamp, overkill, action consumption, rebuilt
  occupancy, last-shooter phase advance and elimination without termination.
- `server_unit/test_game_observations.py`: fresh initial units/city ownership,
  public accessors, parameter aliasing, both players with/without fog and within/
  outside sight, deterministic detection draws and status reference behavior.
- `server_unit/test_game_state_key.py`: literal readable keys, represented fields,
  terrain and city-owner codes, omitted/truncated fields, stacked-unit ordering
  and the unsupported `unused` terrain exception.

Added a local `game_factory` fixture in `server_unit/conftest.py`, using existing
builders and finite detection draws. No production behavior is mocked. Combat
expectations are hand-calculated constants; the defensive-fire rule override
uses pytest's restoring monkeypatch. The setup episode is explicitly marked
integration; single-operation cases are marked unit.

KNOWN_ISSUES documents K03/K04, K05 reference behavior and K16 key limitations
as passing characterizations, not approved future rules. Replacement validation,
overkill scoring and key-identity contracts remain future design decisions.
No new issue IDs or xfails were needed. README and the plan status are updated.

### Validation

Windows / Python 3.14.4, existing project environment. Commands used
`UV_CACHE_DIR=tests/.cache/uv` and `PYTHONDONTWRITEBYTECODE=1`:

| Command | Result |
| --- | --- |
| `uv run --offline --no-sync pytest tests/server_unit/test_status.py tests/server_unit/test_game_setup.py tests/server_unit/test_game_actions.py tests/server_unit/test_game_combat.py tests/server_unit/test_game_observations.py tests/server_unit/test_game_state_key.py -q` | Initial implementation: **130 passed in 58.33s**; one sandbox cache-permission warning. |
| `uv run --offline --no-sync pytest tests -q` (approved outside sandbox) | Final implementation: **402 passed, 9 existing xfailed in 492.51s**. |

The final full run includes all 149 S05 cases after adding the remaining type
pairings and malformed setup cases, plus the existing Chromium, async and CPU
model checks. It has **0 failed, 0 warnings, 0 skipped, 0 XPASS and 0 deselected**.
All 253 previous passing cases and nine K01/K02 expected failures retain their
outcomes. The protection report checks **315 files**, with no additions,
removals or content changes and unchanged protected Git diff. `git diff --check`
passed. No dependencies, configuration or production files changed.

No launcher smoke game was needed for test-only work; the suite includes the
new bounded setup-to-terminal sequence and the previous deterministic engine
episode. Other platforms and Python versions remain unverified.

Next step: **S06 — Scenarios, registries, and dispensers**.

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
