# Test implementation progress

## 2026-10-05 - S16 completed

Starting revision: `73980d750bbd292c2711c15e96d2de6198219572`. Preserved the
pre-existing untracked `demo_script.txt`. Changes are confined to `tests/` and
root `test_plan.md`; no production, dependency, scenario or saved-model edits.

Added 72 S16 cases across six ML modules, one focused defect module and four
script modules, plus the fresh-interpreter `support/s16.py` helper.
**68 passing cases and four strict expected failures (K48-K51).** See
[S16_MATRIX.md](S16_MATRIX.md) for all sixteen plan items, controlled external
boundaries, interface/data exclusions and characterization limits.

Real CPU Torch/hexagdly persistence/inference/training-helper checks use tiny
test-owned artifacts, fixed weights/seeds and one thread. NumPy/SciPy and HTTP
checks use real dependencies. SB3 training, logging and absolute demo output
boundaries are recording doubles; unchanged scripts execute in bounded children.
No training jobs, production checkpoint loading or symlinks were needed.

Validation used `UV_CACHE_DIR=tests/.cache/uv` and `uv run --no-sync pytest`:

- Focused S16 run across all new modules: **68 passed, 3 xfailed in 69.34s**.
  This run preceded the fourth Coach defect case.
- Final defect/statistics follow-up: **1 passed, 4 xfailed in 5.23s**; this
  verifies the added Coach case and strengthened paired-test assertions.
  Overlapping cases are not counted twice.
- Independent sixteen-channel literal oracle: **1 passed, 26 deselected**.
- Existing model/import-isolation/fixture/scenario regressions: **72 passed in
  16.93s**, using `tests/ml/test_fixture_model.py`, `test_dlalphabeta.py`,
  `tests/server_unit/test_fixtures.py`, `test_isolation.py` and
  `tests/test_scenario_loading.py`, with `--basetemp=tests/.tmp/s16-regression-final`.
- Final focused collection: **72 tests collected**, no executable examples
  accidentally collected.
- Optional full ML/script and default-core runs were stopped at approximately
  58% and 27% after substantially longer runtime. They showed passes/expected
  failures only before termination, but are incomplete and are not counted as
  successful full regressions. Final targeted checks above provide completion
  evidence. Those two runners initially shared the configured basetemp; all
  later focused checks used distinct directories. No concurrent-run reliability
  claim is made.

These successful checks had no failures, errors, skips or XPASS. Initial sandbox
execution produced 55 setup errors from pytest's existing temporary-directory
WinError 5 restriction; normal-access execution resolved it. First normal-access
S16 run had 53 passes and two test-authoring failures: patched TCPServer before
http.server import, and an incorrect significance expectation for [1,2,3] versus
zero. Both were corrected and rerun. All process output stays test-local.

Protection reports check 315 files with no additions/removals/content changes
and no protected Git diff change. Browser workflow and cross-platform/GPU runs
are not claimed. S17 is the next task.

## 2026-10-01 - S15 completed

Starting revision: `e8e315a3e5729a04397f1d84457cb0206cc07f85`. Preserved the
pre-existing untracked `demo_script.txt`. All changes are under `tests/` or in
root `test_plan.md`. No dependencies, production code, scenarios, replays or
model files changed. S16 is the next task.

Added six ML modules, ML-local import fixtures, and two subprocess helpers.
**789 new cases: 776 passed, 13 strict expected failures.** The two existing
S02/S14 ML cases remain passing. All optional dependencies are required when
this suite is selected; collection does not load executable demos or models.

| S15 items | Implemented coverage |
| --- | --- |
| 1-3 | `test_observation_features.py`: all factories, ineffective/missing units, 17 literal base channels on the asymmetric rectangle, each terrain, appended shape validation, input preservation, faction swap/score negation, float32 Torch output, K38 forwarding probe. |
| 4 | Exact pass/move/fire actor and target masks, unknown and unplaced actors; fire target resolved through the target unit. |
| 5-6 | `test_fog_features.py`: decay across observations, ignored friendlies/dead/unplaced enemies, mutable result identity, hidden/total counts, diffusion, culling, normalization, repeated updates, empty/friendly-only data, initially/newly hidden enemies and finite nonnegative mass. K39-K42 reproduce separate initialization/update failures. |
| 7 | `test_gym_surrogate.py`: both modules/roles through parameters, callback reset/restoration, setup, wait, pause, terminal, reward consumption, reset and fresh parameters. |
| 8 | 608 index/role/parity/location/target cases cover indices 0-18; 72 artillery cases verify the full fire ring. Literal independent coordinate tables plus real engine legality/transition checks. Additional wait/remaining-mover, fully blocked, exhausted, negative/out-of-range/noninteger cases. |
| 9 | AI, AIx2, AITwelve, AI13, AI14, AI16, AI17 and AI18 exact channel tensors, metadata, both factions, empty mover masks, remaining-phase versus elapsed-phase features, doubled coordinates. |
| 10 | Both copies of NoNegativesRewArt/BoronRewArt, negative discount, strength ratio, terminal bonus, fresh reward state and consumption; K43 zero strength and K44 red reward sign. Raw score remains separate. |
| 11 | `test_gym_environment.py`: both Args/wrappers, roles, opponent model, nReps=-1, 7/19/subagent action spaces, feature/doubled shapes, [0,1] float32 declarations, no-op actions, reset/step tuples, seeded Gym RNG, close/render. |
| 12-13 | Real tiny episodes/restarts for both factions through actual engine and function transport, at most eight steps per episode, 45-second child deadlines, explicit task/loop/signal cleanup. Real Gymnasium/SB3 checker failures (K45) and independent signed score bound probe (K46); no casts/clips. Recording scenario generator proves equal Gym seeds do not restart Python generator randomness. |
| 14-15 | `test_multigym.py`: constructor and repeated subagent setup, parameter/latest-observation forwarding, index selection, JSON results, invalid/no-action cases, DQN/PPO production prediction versus training pause, metadata characterization, stale tensor K47. League weighted selection, next-reset switching, space/metadata identity, mismatches/empty data and no-op close/render. |
| 16 | `test_neural_adapters.py` and `support/neural_adapters.py`: PPO/DQN/default loaders, all neural feature subclasses, doubled coordinates, real legal translated move/fire, exhausted movers, dl_alpha_beta constructor/shared/search contracts, state_eval_gpu CPU/shared model identity, bounded multi-batch inference, blue max/red min, reversed queues and partial-ply first action. AlphaZero model/checkpoint/search/translation boundaries are controlled in a fresh child; actual helper internals/checkpoint persistence remain S16. Missing options and the cwd-dependent PortableTorch namespace failure are explicit probes. |

Environment: Windows, Python 3.14.4, pytest 9.1.1, NumPy 2.5.0, Torch 2.12.1,
Gymnasium 1.3.0 and Stable-Baselines3 2.9.0. No training, GPU execution, real
checkpoint loading or browser run was needed. External model loading/search
boundaries are recording doubles; CPU tensor inference and the Gym checkers use
the installed real libraries. PortableTorch/AlphaZero adapters execute in fresh
children to contain flat-module collisions and import-time global state.

Validation commands used `UV_CACHE_DIR=tests/.cache/uv`:

```text
uv run python -B -m pytest tests/ml -q --tb=short --basetemp=tests/.tmp/s15-final -o cache_dir=tests/.cache/s15-final
uv run python -B -m pytest tests/ml -k "not test_all_discrete_actions and not test_all_artillery_fire_offsets" -q --tb=short --basetemp=tests/.tmp/s15-supplement -o cache_dir=tests/.cache/s15-supplement
uv run python -B -m pytest tests/server_unit/test_fixtures.py tests/server_unit/test_isolation.py tests/server_unit/test_game_observations.py tests/server_unit/test_game_actions.py tests/server_unit/test_game_combat.py -q --tb=short --basetemp=tests/.tmp/s15-core -o cache_dir=tests/.cache/s15-core
```

- Full ML: **778 passed, 13 xfailed in 165.83s**, zero deselected.
- Supplemental final assertion/classification check: **98 passed, 13 xfailed,
  680 deselected in 48.97s**. Rechecks all non-matrix cases, including explicit
  ownership forwarding and repeated fully culled updates; these outcomes overlap
  the full run and are not counted twice.
- Focused existing core regression: **152 passed in 26.34s**.
- Commit-review follow-up corrected the K46 probe's success path so repaired
  bounds can produce strict XPASS. Reran
  `uv run python -B -m pytest tests/ml/test_gym_environment.py::test_real_signed_score_space -q --tb=short --basetemp=tests/.tmp/s15-score-review -o cache_dir=tests/.cache/s15-score-review`:
  **one xfailed in 2.53s**, no unexpected failures or warnings. This overlaps
  the full suite count; production bounds remain unchanged.
- All three runs: zero unexpected failures, errors, warnings, skips or XPASS.
  Ignored output transcripts are `tests/.artifacts/s15-{final,supplement,core}.txt`.
- The complete browser, transport, script and default core suites were not rerun.
  No cross-platform or accelerator result is claimed.

Development results retained separately: first observation/fog/surrogate run had
655 passed, six xfailed and five failures, plus two Windows cache warnings.
Four failures came from importing multigym before its circular registry dependency;
the tests now use normal registry-first initialization. One was a Python 3.14
exception-text mismatch (`division by zero`, not `float division by zero`). A
subsequent wrapper/adapter run hit WinError 5 on test-local temporary directories
and could not complete pytest cleanup. Normal-access validation resolved those
environment errors. The first full normal-access run had 687 passed and 13
xfailed before the additional artillery/channel/queue/RNG cases were added.

K38-K47 have exact-signature `KnownDefect` probes and documented desired behavior
in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). Characterizations are labeled separately;
no production fix or test-side replacement of the asserted behavior was made.
Before/after harness manifests verify **315 protected files**, no added/removed/
changed files and unchanged protected Git diff. Scratch files/caches/child work
directories remain ignored under `tests/`. Documentation paths and diff whitespace
were checked before read-only commit review. No staging or commit was performed.

## 2026-10-01 - S14 completed (implemented September 30)

Starting revision: `22159cb58a438b50c78021d6567566803b0a9151`. Preserved the
pre-existing untracked `demo_script.txt`. Changes are limited to `tests/` and
root `test_plan.md`; no dependencies, production modules or scenario data change.

Added the explicit [AI registry matrix](AI_MATRIX.md), seven server unit modules,
one bounded engine/AI integration module, one CPU neural search module, and the
shared `support/ai_contract.py` contract helper.

- Protocol: all 30 ordinary aliases in both roles, role requests, replacement
  parameters, off-turn/terminal silence, setup/pass behavior and real-engine
  action validation. MCTS aliases have separate queue/search defect probes.
  Registry kwargs are copied; optional aliases have named S15/S16 limitations.
- Heuristics: posture and mode overrides, fire/weakest-target priorities, random
  move/fire boundaries, no eligible units, city/friend distances, assault strength,
  escape/encirclement, coordinated fire, remaining-phase scores and safe movement.
- Setup/fog: permitted cells, occupied exchange, pass order, insufficient cells,
  queue replacement, enemy prototype limits, exact small-epsilon diffusion,
  sight culling, normalization/zero mass, uniform setup support and hidden units.
- Search/scoring: real SciPy directed terrain paths including unreachable water,
  per-type costs, finite scores, object/portable round trips, wait versus pass,
  fixed/random/greedy/full plans, Q versus successor boundaries, branch isolation,
  full/partial blue-max/red-min choices, finite UCT, Agenda/minimax/transpositions
  and timed perfect-game reconstruction. Simon helper and recursive entry points
  use hand-solvable positions; recursion runs in ten-second children.
- Hierarchy: weighted centers, ineffective/zero groups, containing hexes, grouping,
  faction-preserving abstraction, clamping/non-mutation, parent distances,
  crowding, commander modes, two abstract levels and playback-shaped debug data.
- Integration: every ordinary alias runs a seed-1729 four-phase game against
  passive in an owned 20-second child with a 32-action bound. No playing-strength
  assertion or fixed stochastic trajectory is required.
- ML: real CPU Torch/hexagdly import, fixed-valued inference, terminal scores,
  cutoff/pruning, both faction signs, invalid depth/root errors, and actual depth
  convention. Feature encoding is a collaborator boundary reserved for S15.

Strict expected failures document K33 stale plans, K34 disconnected MCTS search
queue, K35 color conversion, K36 undefined abstraction global (K16 reproduction),
and K37 containing-hex lattice boundary. Only exact documented wrong signatures
raise KnownDefect; fixes produce strict XPASS. Ordinary MCTS adapter games remain
blocked by K34, with the real search exercised independently. Callback and neural
model adapters remain assigned to S15/S16, not silently skipped.

Environment: Windows, Python 3.14.4, pytest 9.1.1, pytest-asyncio 1.4.0,
pytest-playwright 0.9.0, pytest-cov 7.1.0, Torch 2.12.1 and SciPy 1.18.0.
Commands use `UV_CACHE_DIR=tests/.cache/uv` and the installed project environment.

Validation history:

- Initial protocol/search run: 136 passed, nine xfailed, one setup error and
  three cache/temp warnings. The error was Windows sandbox access to pytest's
  existing temporary directory. Subsequent executions use approved normal access.
- Initial helper/setup/abstraction run: 162 passed, 28 xfailed, six failed.
  Corrected fog fixtures lacking an opponent, an external-center fixture that
  accidentally changed map dimensions, and separated the independently verified
  K37 geometric defect from ordinary aggregation assertions.
- Focused scoring and ML run: **30 passed in 7.93s**. Corrected manually built
  states to mark the opposing faction immobile before ordered-search checks.
- One redirected development run was interrupted before results were emitted;
  no validation credit is taken for it. A baseline command with
  `-p no:cacheprovider` stopped before collection under strict configuration
  (`Unknown config option: cache_dir`); corrected to a separate cache path.

Final successful execution results, retrieved when work resumed October 1:

- Combined S14 run of the nine files in the README command: **389 passed,
  40 xfailed in 873.60s** (429 cases). This includes all 30 complete seeded games
  and the CPU neural case. Thirteen final edge cases were added after collection.
- Final completion run: **132 passed, two xfailed in 273.20s** (134 cases).
  This includes all 13 added edge cases (11 passing, two strict K35 failures),
  reruns all 60 on-turn alias/role cases, all 29 scoring cases, all 30 games and
  both hidden-enemy cases after strengthening the shared action assertion.
  Those 121 reruns overlap the combined run; they are not counted twice.
- Final collection: **442 cases** in 0.53s, recorded in ignored
  `tests/.artifacts/s14-collection.txt`. Distinct S14 outcomes are therefore
  **400 passed, 42 xfailed**: 411 core cases, 30 engine integrations and one ML
  case. All final collected cases have execution evidence in the runs above.
- Existing core regression, excluding the seven new modules: **623 passed,
  nine xfailed in 763.55s** (632 cases). It ran in a separate test-local temp/cache
  directory while S14 validation continued; no source or shared fixture changed.

All three successful execution runs had **zero failures, errors, warnings,
skips, XPASS and deselected cases**. The complete browser, pre-existing transport
integration and optional ML suites were not rerun for this tests-only change.
Windows/CPU is verified; other operating systems and accelerators are not claimed.
The existing core and new S14 suites were validated separately, not as a single
default-core invocation after the final additions.

Exact supplemental commands (the combined command is in README):

```text
uv run pytest tests/server_unit tests/test_scenario_loading.py --ignore=tests/server_unit/test_ai_protocol.py --ignore=tests/server_unit/test_ai_search.py --ignore=tests/server_unit/test_ai_heuristics.py --ignore=tests/server_unit/test_ai_setup.py --ignore=tests/server_unit/test_ai_scoring.py --ignore=tests/server_unit/test_ai_simon.py --ignore=tests/server_unit/test_abstract_state.py --basetemp=tests/.tmp/s14-baseline -o cache_dir=tests/.cache/s14-baseline -q --tb=short

uv run pytest tests/server_unit/test_ai_protocol.py::test_on_turn_action_applies tests/server_unit/test_ai_scoring.py tests/server_integration/test_ai_games.py tests/server_unit/test_ai_setup.py::test_hidden_enemy_observation_legal_action tests/server_unit/test_abstract_state.py::test_command_distance_and_parent_center tests/server_unit/test_abstract_state.py::test_aggregate_strength_includes_ineffective_member_characterization tests/server_unit/test_ai_simon.py::test_three_unit_pending_plan_applies_in_order tests/server_unit/test_ai_heuristics.py::test_burt_friend_distance_includes_self_characterization tests/server_unit/test_ai_heuristics.py::test_mixed_infinite_debug_distances tests/server_unit/test_ai_heuristics.py::test_dijkstra_debug_colors tests/server_unit/test_ai_heuristics.py::test_tactical_no_enemy_passes tests/server_unit/test_ai_search.py::test_minimax_prunes_inferior_branch_without_changing_value --basetemp=tests/.tmp/s14-final -o cache_dir=tests/.cache/s14-final -q --tb=short
```

The protection report checks **315 unchanged files**, no additions/removals and
no protected Git diff change. Generated outputs remain ignored under `tests/`.
All 49 local Markdown links in the plan and affected test documentation resolve;
`git diff --check` passes. No dependency/configuration updates were needed.
S01-S14 are complete; **S15 is next**. No staging or committing is performed.


## 2026-09-30 - S13 completed

Implemented replay playback and writer/viewer compatibility on starting revision
`25cee5792cf13abc2fa6bcd7dbbbe5c5b42022bf`. Preserved the pre-existing untracked
`demo_script.txt`. All changes are under `tests/` or in root `test_plan.md`.

Added 34 cases: 22 browser unit and 12 browser integration cases.

- `browser_unit/test_playback.py`: initial parameters and echelon control,
  every observation's position/strength/effective/fog state and brightness,
  exhaustion without mutation, controlled animation frames, pause/resume/step,
  repeated Play and init, smaller next-game parameters, visible replacement
  versus retained indexes/occupancy, debug clearing, partial/empty/missing color
  maps, terrain restoration, missing/present echelon levels, cycling, malformed
  JSON, empty/parameters-only/dangling-parameters inputs and unknown/action entries.
- `browser_integration/test_replay_roundtrip.py`: original playback.html with
  routed replay.js content, fresh real-server two-game logs for both perspectives
  with and without fog, each displayed observation compared with the log,
  transcript and terminal Python state, independent score-50 episode oracle,
  Play/Stop/Step and color buttons, native animation completion, repeated clicks,
  generated action-inclusive logs, apostrophe/backslash/Unicode names, and a
  bounded three-step read-only smoke check of the checked-in replay.
- `support/playback.py`: JSON-string replay arrays, original module loading over
  HTTP, controlled requestAnimationFrame queue, exception capture and real SVG
  position/text/fill/visibility assertions. No production behavior is patched.

Seven strict expected failures cover K09 escaping (two), K30 duplicate loops
(two), K31 retained initialization index (one) and K32 undeclared orders-color
variable (two). K31/K32 are precise reproductions of the older K12 investigation
item. Only documented wrong signatures raise KnownDefect; fixes cause strict
XPASS and other errors fail. Action logs and malformed inputs are explicit
unsupported-input characterizations. K20 stale indexes/occupancy are retained
as characterization; visible replacement works. Orders colors for a present
level remain blocked by K32, with missing-level cycling tested independently.

Validation on Windows/Python 3.14.4 and Chromium, using the installed project
environment and `UV_CACHE_DIR=tests/.cache/uv`:

- Initial sandbox run: 31 setup errors from blocked Windows Playwright pipes,
  two cache warnings, and one test-source escape warning corrected immediately.
  No behavioral assertions ran.
- First approved focused run: 23 passed, six xfailed, two failed. Both failures
  were the new helper comparing Python `50.0` text with JavaScript `50`; corrected
  the numeric display expectation without changing production.
- Expanded focused run: **26 passed, seven xfailed in 54.88s** (33 cases), no
  warnings or unexpected failures. Added the missing-echelon/next-observation
  case and tightened the backslash error signature for the final regression.
- Final full regression: `uv run pytest tests -q --tb=short`: **915 passed,
  57 xfailed, one failed in 1225.35s** (973 cases). All 34 S13 cases completed:
  **27 passed and seven strict expected failures**. No warnings, skips, XPASS,
  errors or deselections. Output: ignored `tests/.artifacts/s13-full.txt`.
- The failure was the unchanged S08
  `test_complete_websocket_game[function-and-websocket]`: Windows raised
  PermissionError reading the child's temporary `ready.json`, before connecting.
  This run therefore was not wholly green; no game assertion failed in that
  case. Reran the unchanged affected module with
  `uv run pytest tests/server_integration/test_websocket_game.py -q --tb=short`:
  **six passed in 2.50s**, no warnings/failures/skips/xfails. The permission
  failure did not reproduce; its cause is not established. No retry loop,
  exception suppression, source change or weakened deadline was added.
  Output: ignored `tests/.artifacts/s13-websocket-recheck.txt`.
- Full-run protection report: all **315 files** unchanged, no additions/removals,
  unchanged protected Git diff. Local Markdown links resolve and
  `git diff --check` passes.

S01-S13 are complete; S14-S17 remain open.

No dependency changes, production fixes, replay-file replacements, fixed-port
listeners or fixed browser sleeps were introduced. Server reports verify finite
completed repetitions, closed logs/loop and zero pending tasks. Other browser
engines/platforms remain unverified. S14 is the next planned implementation step.

## 2026-09-30 - S12 completed

Implemented S12 live-play controls and browser/server communication. Starting
revision: `a842e1dd6fb79e1a3655662284b8fc071d82df9d`. Preserved the pre-existing
untracked `demo_script.txt`. All changes are in `tests/` and root `test_plan.md`.

Added 37 cases: 31 browser unit cases and six browser/server integration cases.

- `browser_unit/test_play_protocol.py` (16): socket open/close/error and private
  message callbacks, initial map/unit rendering, both role buttons, every
  exported sender, waiting/input/terminal controls, score/phase/on-move text,
  setup/city markers, brightness, fog/killed units, reset observation semantics,
  malformed/unknown messages, phase lookup and smaller next-game parameters.
- `browser_unit/test_human_controls.py` (15): waiting/exhausted selection,
  friendly selection, move/fire/self markers, single sends, resetGuiState and
  End Phase, setup move/exchange/rejected destinations, direct-hex error and
  explicit wrong-faction/terminal/stale-mode probes.
- `browser_integration/test_live_game.py` (6): two browser contexts and browser
  versus scripted function AI, complete move/fire/pass episodes with all wire
  messages matching the independent S02 oracle and final score 50; setup move,
  setup passes, reset restoring positions and retaining roles, next-game role
  reassignment, native fog disappearance/reappearance, and both Reset and Next
  Game after terminal state followed by a second completed game.
- `support/live_play.py`: unchanged play.html over the existing HTTP fixture;
  existing recording socket for unit tests and a native WebSocket constructor
  wrapper for real transport. The wrapper changes only the exact hardcoded URL
  to the owned ephemeral loopback endpoint and records incoming messages.

Six individual strict expected failures cover four newly documented issues:
K26 wrong phaseCount nesting, K27 direct-hex undefined moveTargets, K28 missing
faction/terminal selection guards (two cases), K29 observation/next-parameters
stale selection mode (two cases). Only matching wrong signatures raise
KnownDefect; unrelated errors fail and fixes produce strict XPASS. Browser
console, request and uncaught-error checks stay active. Production is unchanged.

Validation on Windows/Python 3.14.4 and Chromium, with the installed project
environment and `UV_CACHE_DIR=tests/.cache/uv`:

- Initial sandbox run: 30 setup errors and two environment warnings from blocked
  Windows Playwright subprocess pipes. No behavioral assertions ran.
- First approved unit run: 25 passed, four xfailed, one strict XPASS. Inspection
  showed visible map replacement works; removed the speculative xfail and kept
  the replacement contract passing. Stale controller state is a separate K29
  reproduction, not a visible-map failure.
- Initial real-transport run: four passed in 5.99s.
- Expanded focused run: 29 passed, six xfailed in 37.35s (35 cases). Two terminal
  restart cases were then added for the full regression run.

- Final full regression: `uv run pytest tests -q --tb=short`: **889 passed,
  50 xfailed in 510.55s**, 939 cases total. Includes all 37 S12 cases: **31 passed
  and six strict expected failures**. Zero unexpected failures/errors, warnings,
  skips, XPASS or deselections. Output: ignored `tests/.artifacts/s12-full.txt`.
- Final protection report: all **315 files** unchanged, no added/removed files,
  and unchanged protected Git diff. Local Markdown links resolve and
  `git diff --check` passes.

S01-S12 are complete; S13-S17 remain open.

No separate launcher smoke was needed for test-only changes; the full suite
includes bounded engine/CLI integrations. No dependency changes, production
patches, fixed-port listeners, screenshots as oracles, or fixed browser sleeps
were introduced. Owned server reports verify completed repetitions, closed
logs/loop and zero pending tasks. Alternate browsers/platforms and replay viewer
behavior remain unverified. Next task: S13, replay playback and compatibility.

## 2026-09-29 — S11 completed

Implemented **S11 — Editors and scenario creation pages**. S01–S11 are complete;
S12–S17 remain open. Starting revision:
`eaf8f7c57511bbecb38f62921c506197f8e65246`. Preserved the existing untracked
`demo_script.txt`. Changes are confined to `tests/` and root `test_plan.md`.

Added **46 cases (18 browser unit and 28 browser integration/workflow cases)**:

- `browser_unit/test_editor_controls.py` (13): all fill/edge palettes, setup
  replace/erase, drag continuation and mouse-up, consecutive path segments,
  replacement/removal and SVG styling, independent K10 palette identity, Shift
  zoom without painting and normal editing afterward.
- `browser_unit/test_placement_controls.py` (5): select, move, exchange,
  same-unit selection, selection termination, occupancy and symbol transforms,
  Shift ignoring selection/movement, and occupied-hex stacking characterization.
- `browser_integration/test_map_editor_page.py` (4): rows/columns/width,
  DOM-driven painting, map load/cancel/reload/malformed input, intercepted copy,
  actual Chromium clipboard, and SVG data URI decoded and parsed as XML.
- `browser_integration/test_unit_placement_page.py` (17): map/OOB/scenario
  controls, automatic placement, movement/exchange, fitting and native Shift
  zoom, numeric score/fog export, real Python loader/initial state/legal setup
  pass, empty/insufficient setup inputs, every prompt's cancellation or malformed
  input behavior, repeated loads, score/fog restoration, Test Input and sample
  symbols. Engine round-trip assertions cover setup, positions, faction/type,
  strength, scoring and fog; display-only metadata is preserved in exported JSON.
- `browser_integration/test_random_scenario_page.py` (7): finite random sequence,
  default 10×10 and nonsquare 8×12 generation twice per page, city/setup geography,
  unique occupancy, rich metadata, small-map defect, repeated/canceled/malformed
  OOB loading and successful empty-OOB generation.

`support/creation_pages.py` supplies fresh builder inputs and only prompt/copy
boundary replacements. Original modules and HTML remain unchanged. Attached
real SVG elements receive controller/DOM events; selected workflows also use
native mouse clicks. The real clipboard smoke grants loopback-origin browser
permissions. Geographic-content comparisons exclude edge identity only because
K01 has dedicated S03/S09 tests. Fixed random draws are finite and nonzero;
engine RNG changes are isolated. Temporary exported scenarios remain test-local.

Five individual strict xfails cover K10 palette IDs, K24 ignored scenario
settings/canceled scenario prompt/empty OOB, and K25 small-map city placement.
Only exact signatures raise `KnownDefect`; unrelated errors fail and fixes
produce strict XPASS. K20 stale occupancy/index effects and unsupported-input
behavior are explicitly named characterizations. No production fixes were made.

Validation on Windows/Python 3.14.4 and Chromium, installed project environment,
with `UV_CACHE_DIR=tests/.cache/uv`:

- First sandbox invocation: 41 setup errors and two environment warnings;
  Playwright could not create Windows subprocess pipes. No assertions ran.
- First approved focused run: 29 passed, five xfailed, seven test assertion
  failures. Corrected the selection marker oracle (root sibling, not symbol
  child) and geographic comparisons (known K01 edge reorientation).
- Expanded focused run: 39 passed, five xfailed, one test assertion failure.
  Corrected the tiny-map zoom expectation: fitting below the target size clamps
  zoom. Added a separate native large-map zoom test.
- Final placement-file run: **14 passed, three xfailed in 16.74s**, including the
  Python round trip and native zoom.
- Final full regression: `uv run python -B -m pytest tests -q --tb=short`:
  **858 passed, 44 xfailed in 330.90s**, 902 cases total. This includes all final
  S11 cases: **41 passed and five strict expected failures**. Zero unexpected
  failures/errors, warnings, skips, XPASS or deselections.

The final protection report checked **315 files**, with no added, removed or
changed protected files and no protected Git diff change. Local Markdown links
in all four edited documentation files resolve; `git diff --check` passes.

No separate launcher smoke is needed for test-only changes; the full suite
includes the existing bounded headless integrations. Native clipboard support
and parser-error strings were verified only in Chromium on this Windows host.
No browser coverage percentage is claimed. Next task: **S12**, live-play controls
and browser/server communication.

## 2026-09-29 — S10 completed

Implemented **S10 — SVG utilities, rendering, markers, and viewport**.
S01–S10 are complete; S11–S17 remain open.
Starting revision: `aaf78e6acd81480a9a758a242ff12bfd5df492f1`.
Preserved the existing untracked `demo_script.txt`. All changes are under
`tests/` or root `test_plan.md`; production and dependency files are unchanged.

Added **99 browser unit cases: 85 passing and 14 strict expected failures**:

- `browser_unit/test_svg_util.py` (42): coordinate conversion, roots, primitive
  attributes/text/styles, attached layouts and frames, native transformed bounds,
  fit padding/style, empty/legacy paths, 27 zoom/clamp/restore combinations and
  two rendered rectangular maps. Rotation/skew and spacer positioning have
  separate exact-signature defect cases.
- `browser_unit/test_svg_rendering.py` (7): map shapes/IDs, edge/path styles,
  handlers, setup/city rendering, path removal, complete/partial debug colors,
  terrain restoration, repeated factories and generated palette items.
- `browser_unit/test_svg_markers.py` (10): setup replacement/model/removal,
  neutral/per-faction city visibility, new-map indexes, repeated city creation,
  action geometry/callback/clear/redraw, no-visible-unit cases and resized symbols.
- `browser_unit/test_unit_symbols.py` (40): all 28 type/alias switch cases,
  echelon branches, unsupported-type/echelon characterizations, labels/strength,
  movement, observations, fog/ineffective removal/reappearance, faction/global
  brightness, selection cycles and the read-only sample OOB smoke check.

The test-only `browser_support/svg.js` imports original modules with no renderer
replacement. `svg_page` uses a fresh HTTP page/context, fixed 1000x800 viewport,
and native SVG geometry. Controller callbacks are recording boundaries in
factory/palette wiring tests; DOM events verify their installation. Play-view
root mousedown currently uses UnitPlacementControl, while hex events use
HumanPlayerControl. This is wiring characterization, not full S11/S12 behavior.
Numeric tolerances avoid font-dependent snapshots. Console/page errors, failed
requests and unexpected dialogs remain checked. No screenshot is a test oracle.

Confirmed K13 company/marker/selection defects and K10 generated path palette
IDs. Added K22 transformed bounds and K23 double-positioned layout spacers.
All expected failures match only the documented result or exact exception;
unrelated errors fail and fixes produce strict XPASS. See KNOWN_ISSUES.md.

Validation on Windows/Python 3.14.4 with Chromium and the installed environment,
using `UV_CACHE_DIR=tests/.cache/uv`:

- Initial sandbox run: 96 setup errors and two environment warnings; Windows
  denied Playwright subprocess pipes. No browser assertions executed. Subsequent
  runs used approved execution outside the sandbox.
- First browser run: 79 passed, 12 xfailed, three failures in test coordinate
  expectations, and four setup/teardown errors from two refused module imports.
  Corrected the expectations from grid coordinates. Increased the test HTTP
  server listen backlog from five to 128 for parallel imports; no retries or
  suppression of browser errors were added.
- Corrected focused run (98 cases): 85 passed, 13 xfailed, one Playwright
  `Tracing.stop: file data stream has unexpected number of bytes` teardown error.
  Test source was edited during this run, which may explain the trace-export
  failure. Final validation kept test sources fixed; the error did not recur.
- Final full regression: `uv run python -B -m pytest tests -q --tb=short`:
  **817 passed, 39 xfailed in 946.75s**, 856 cases, including all final 99 S10
  cases, S09 browser parity, real server integrations and CPU model checks.
  Zero unexpected failures/errors, warnings, skips, XPASS or deselections.

The final protection report checked **315 files**, with no added, removed or
changed protected files and no protected Git diff change. No separate headless
game was needed for test-only changes; existing bounded server integrations ran
in the full regression. Cross-platform/browser-engine behavior remains unverified.
The test plan, README commands and known-issue records are updated.

Next task: **S11 — Map editing, unit placement, and scenario creation pages**.

## 2026-09-29 — S09 completed

Implemented **S09 — Browser models and Python–JavaScript compatibility**.
S01–S09 are complete; S10–S17 remain open.
Starting revision: `2b1b3603dd5493f9506da82767d3d00ea0991e69`.
Preserved the existing untracked `demo_script.txt`. All edits are within `tests/`
or root `test_plan.md`; no application, dependency or configuration changes.

Added **93 cases** (80 passing, 13 strict expected failures):

- `browser_unit/test_map_model.py` (19): public geometry, dimensions, lookup,
  defaults/setup, serialization/malformed JSON, both path orientations,
  replacement/removal, reversed shared edges, and same-page grid/load state.
- `browser_unit/test_unit_model.py` (16): constructor registration, occupancy,
  init/remove, both loader formats, defaults, setup placement/exhaustion,
  ordered observation movement/fog/reappearance/removal, unplaced export,
  loader fog input and repeated loads with distinct/same IDs.
- `browser_unit/test_rule_data.py` (5): every palette ID/name, supported style
  entry, default fill and exact path-prefix defect cases.
- `browser_integration/test_engine_parity.py` (53): shared JSON oracles against
  both implementations (33 movement, 10 fire, 7 coordinate vectors, combined
  geometry/rules, semantic serialization, combat difference audit). These carry
  `browser` and `integration`; the other 40 carry `browser` and `unit`.
  Movement/fire matrices live in the shared suite to exercise identical fixtures
  in both languages without duplicating browser cases.

`support/browser_models.py` imports original Map, Unit, Mobility, Combat,
Terrain and Style ES modules over the local HTTP harness. GameMap is a test-only
alias, preserving native JavaScript Map. SVGUnitSymbol.create is the only model
collaborator replaced, by a recording boundary; no model behavior is patched.
Fresh pages isolate tests, but same-page replacement probes perform no hidden
reset between operations. Existing console/page-error/network/dialog checks
remain active. Drawing and actual page workflows remain S10 onward.

`fixtures/browser_contract.json` contains independent S03 geometry vectors,
normalized infinity, all mobility/range coefficients, and S04 movement/fire
cases including terrain, occupied/intermediate hexes, alternate routes, stacking,
fog/ineffective targets, artillery and Euclidean distance. Named maps avoid
repeated inputs. Semantic map/unit assertions distinguish browser metadata and
Python's unsupported path loading. `BROWSER_COMPATIBILITY.md` records the absent
browser infantry firepower row and all six differing coefficients separately
from required live-behavior parity.

Confirmed K01/K02 browser defects, K10 path palette IDs, new K20 unit replacement
leaks and K21 negative-odd coordinate mismatch have exact-signature strict xfails.
Unsupported inputs and constructor/display defaults are passing characterizations,
not newly imposed requirements. See KNOWN_ISSUES.md for individual reproductions.

Validation on Windows/Python 3.14.4 and Chromium, using the installed project
environment and `UV_CACHE_DIR=tests/.cache/uv`:

- First sandbox run: 79 setup errors (Playwright Windows pipe WinError 5), two
  environment warnings; no model assertions executed. Approved outside-sandbox
  execution was required, as in earlier steps.
- Initial harness run: 79 failures because assigning the game Map to window.Map
  broke Playwright's native Map use. Fixed only the test alias. A single-case
  diagnostic reproduced the same error. No production defect was inferred.
- Corrected initial S09: **70 passed, 9 xfailed in 64.52s** (79 cases).
- A full-suite collection attempt found a wrong named-map reference in the new
  stacking case; corrected `armor-clear` to the deduplicated `infantry-clear`.
- Full regression: `uv run --no-sync python -B -m pytest tests -q --tb=short --maxfail=3`:
  **727 passed, 23 xfailed in 208.01s**, 750 collected, including CPU model and
  real server integrations. The seven final coordinate cases were added after
  this collection and checked in the focused final run below.
- Final S09: `uv run --no-sync python -B -m pytest tests/browser_unit/test_map_model.py tests/browser_unit/test_unit_model.py tests/browser_unit/test_rule_data.py tests/browser_integration -q --tb=short`:
  **80 passed, 13 xfailed in 75.33s**, all 93 final S09 cases.

Successful runs had zero unexpected failures, warnings, skips, XPASS or
deselections. Protected manifests checked all 315 files with no additions,
removals, content changes or protected Git diff changes. `git diff --check` and
local Markdown link/content checks passed. No live application code changed;
the full existing bounded server integrations provide the simulation regression.
No rendering or cross-platform claim is made. Next task: **S10**.

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
