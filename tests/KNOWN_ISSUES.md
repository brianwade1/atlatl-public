# Confirmed issues

S03 runtime-confirmed the Python map defects grouped under **K01** and **K02**
in `../test_plan.md`. S04 confirms the serialization/detection side effect in
K05 as characterization, without an expected failure. S05 also confirms K03,
K04, the status/reference portion of K05, and the search-key portion of K16
as characterizations below. S06 confirms factory sharing/RNG effects under K05
and repeated city placement/hierarchy collisions under K06. The other portions
of K03–K18 and browser portions
of K01/K02 remain an investigation queue, not expected failures. Production
files remain unchanged.

## K01 — Edge identity and path serialization/loading

Affected suite: `tests/server_unit/test_map_serialization.py`. These tests express
required edge identity and path round-trip contracts, not approved current behavior.
Run `uv run pytest tests/server_unit/test_map_serialization.py -q -k "reverse_endpoint or adjacent_hexes or path_portable or path_loading"`.

| Test node (within the file above) | Expected | Confirmed wrong signature |
| --- | --- | --- |
| `test_reverse_endpoint_lookup` | Reversed endpoints find the existing edge. | Returns `None` for reversed `edge-1-1-3-1`, while the forward edge is indexed. |
| `test_adjacent_hexes_share_edge_identity` | Two vertically adjacent hexes share one edge object; 11 unique edges. | Separate `edge-3-3-1-3` and `edge-1-3-3-3` objects; 12 edges. |
| `test_path_portable_copy` | Path exports a JSON dictionary with id, hexA, hexB, type. | `AttributeError: 'dict' object has no attribute 'id' and no __dict__ for setting new attributes` at `copy.id` on Python 3.14. The matcher also accepts the exact shorter pre-3.14 wording. |
| `test_path_loading` | Portable road loads into pathIndex and reciprocal hex path slots. | Empty pathIndex and six `None` slots on every hex. |

Reverse lookup fails to construct the reversed key (and includes a literal `$`).
Path serialization assigns attributes to a dictionary; path loading is disabled.
Round trips without paths pass; they compare semantic hex data independently
and do not require an ideal unique edge count on affected multi-hex maps.

## K02 — Map replacement retains stale state

Affected suite: `tests/server_unit/test_map_serialization.py`. Required replacement
contracts have individual strict xfails. Run
`uv run pytest tests/server_unit/test_map_serialization.py -q -k "refreshes_cached or replaces_old or clears_paths"`.

| Test node (within the file above) | Expected | Confirmed wrong signature |
| --- | --- | --- |
| `test_reload_refreshes_cached_dimensions[smaller]` | Loading 1x1 after querying 4x3 dimensions returns 1x1. | Hex count becomes 1, dimensions remain width 4 / height 3. |
| `test_reload_refreshes_cached_dimensions[empty]` | Loading an empty map returns 0x0. | Hex count becomes 0, dimensions remain width 4 / height 3. |
| `test_create_grid_replaces_old_hexes` | Recreating 2x2 as 1x1 leaves only hex-0-0. | All four original hex IDs remain while edgeIndex resets to six edges. |
| `test_replacement_clears_paths[load]` | Loading a path-free map clears old paths. | The old path remains and references the replaced hex object. |
| `test_replacement_clears_paths[grid]` | Recreating a grid clears old paths. | The old path remains and references the replaced hex object. |

Loading does replace hex/edge indexes, and dimensions are correct if not previously
queried; passing tests cover those distinctions. These findings do not establish
the behavior of browser map replacement.

## S04 characterizations and input limitations

These passing tests record existing behavior; they do not approve these
limitations as future requirements or introduce new strict xfails. Reproduce
with `uv run pytest tests/server_unit/test_unit_state.py tests/server_unit/test_unit_visibility.py -q`.

- **K05, serialization portion confirmed:**
  `test_unit_visibility.py::test_observer_fields_and_serialization_side_effect`
  (white/blue/red) makes two successive exports with finite draws at probability
  0.5. Draws 0.9 leave both units undetected; draws 0.1 detect both on the next
  export. Serialization mutates detection and may change enemy locations from
  `fog` to visible. All other fields remain exposed for hidden enemies.
  `Unit.portableCopy` omits detection and does not invoke this update.
  Status sharing is covered by S05 below; scenario-factory portions by S06 below.
- `test_unit_visibility.py::test_live_unplaced_enemy_characterization`
  (`updateDetectionStatus`/`toPortable`): a live unplaced red unit paired with a
  placed blue unit raises `AttributeError: 'NoneType' object has no attribute
  'x_grid'`. Both detection flags have already been cleared. A lone unplaced
  unit serializes successfully, and ineffective unplaced units are skipped.
  These are input limitations; no graceful handling contract is assumed.
- `test_unit_state.py::test_duplicate_ids_characterization`: loading the same
  faction/name twice replaces the indexed unit but leaves the original in its
  old occupancy list. Valid inputs require unique IDs.
- `test_unit_state.py::test_hex_full_characterization`: an absent occupancy key
  returns false even with stacking limit zero; a present empty list returns
  true at zero. Normal limit-one and temporarily increased capacity are covered.
- `test_unit_state.py::test_partial_observation_visible_hidden_visible`:
  strength, action and ineffective flags update, but `detected` is not copied.
  Hidden and ineffective units leave occupancy, and visible reappearance restores
  it without duplicates. `test_fog_is_not_ground_truth_input` separately records
  `KeyError('fog')` when a partial observation is passed to `fromPortable`.

Movement's independent shortest-path oracle agrees with the current rule tables
for the tested occupied/rough/water alternative routes. No movement defect or
new issue ID was confirmed by S04.

## S05 characterizations and input limitations

These passing characterizations record the existing implementation, not approved
future rules. No new xfails are introduced: the plan explicitly calls for probing
and triaging these behaviors, and does not establish replacement contracts.
Run `uv run pytest tests/server_unit/test_status.py tests/server_unit/test_game_setup.py tests/server_unit/test_game_actions.py tests/server_unit/test_game_combat.py tests/server_unit/test_game_observations.py tests/server_unit/test_game_state_key.py -q`.

- **K03, setup validation:**
  `test_game_setup.py::test_setup_validation_gaps_characterization`
  accepts a move onto an occupied friendly hex (both units remain there), an
  exchange with an enemy located inside the mover's setup zone (positions swap),
  and an ineffective, unplaced mover (it gets a hex while remaining ineffective).
  Expected validation constraints need a future rule decision. Wrong-faction
  moves and destinations/exchanges outside the faction's zone are rejected.
- **K03, terminal calls:**
  `test_game_actions.py::test_terminal_transition_characterization` passes an
  already-terminal phase-one state again: phase becomes two, faction alternates,
  and the terminal flag stays true. No terminal guard exists; callers must stop
  issuing transitions. Tests use the existing private legality methods and do
  not introduce a public `is_legal` contract.
- **K04, overkill:**
  `test_game_combat.py::test_overkill_credit_characterization` (both factions)
  fires strength-100 infantry at strength-60 artillery in marsh. Calculated
  damage is 150, remaining strength is -90, and the target is removed. Credit is
  +150 for red losses or -300 for blue losses, rather than credit capped at the
  remaining 60. Capping damage/credit is a future scoring decision. Separate
  passing contracts verify ordinary below-threshold cleanup credits the full
  original strength, and exactly 50 strength remains effective.
- **K05, references:**
  `test_game_observations.py::test_parameters_shared_reference_characterization`
  confirms `parameters()` returns the original scenario; changing its units
  affects future initial states. `test_observation_both_players_and_fog_modes`
  confirms observation status is the input status object, while observation
  units are fresh and their detection updates do not mutate input units.
  `test_status.py::test_construction_and_portable_ownership` confirms Status
  exports its owner dictionary by reference but imports it with a copy.
- **K16, search-key limitations:**
  `test_game_state_key.py::test_omitted_fields_collide_characterization` confirms
  collisions for strength 100 versus 100.9, names, detection, ineffective flags,
  ordinary on-move faction, terminal flags, scoring parameters, fog and setup-zone
  metadata. `test_second_stacked_unit_omitted_characterization` confirms only
  the first occupant is represented (reordering different occupants changes
  the key). `test_unused_terrain_exception_characterization` records exact
  `KeyError('unused')`. These restrict use as a search key; full state identity
  is not an established contract. The unrelated abstract-state portion of K16
  remains for S14.
- `test_status.py::test_advance_past_limit_characterization` records inconsistent
  handling of manually supplied at/past-limit states: `matchComplete` returns
  true, but advancing a nonterminal flag past the limit does not set it true.
  Ordinary sequential play terminates exactly at the configured limit.
  `test_advance_phase_flags_and_terminal_boundary` records that final flags are
  retained because the terminal return precedes the usual flag reset.
- `test_game_actions.py::test_off_faction_flag_characterization` and
  `test_status.py::test_phase_complete_counts_off_faction_characterization`
  record that availability trusts `canMove`, even for the off-move faction in
  inconsistent input. Normal transitions set those flags correctly.
- Malformed fields/unknown setup IDs raise exact `KeyError`s; unknown ordinary
  action IDs are rejected with the ordinary legality exception. Extra action
  fields are ignored. These are characterized input limits, not a promised
  structured validation API.

## S06 characterizations and input limitations

Affected suite: `tests/server_unit/test_scenario_factories.py`. Run
`uv run pytest tests/server_unit/test_scenario_factories.py -q`.
These passing characterizations describe existing behavior; they do not approve
it as a future contract or invent graceful validation. No new xfails are added.

- **K05, loaded/shared data:**
  `test_file_factory_utf8_eager_loading_and_shared_object` confirms eager UTF-8
  parsing and the same mutable object on each call, even after the file is
  deleted. `test_flip_colors_values_and_shallow_sharing` confirms fresh outer
  scenario/unit dictionaries but shared map, score and nested unit metadata.
  `test_balance_alternates_and_cycles_generated_pairs` confirms balanced pairs
  retain that sharing, and cycle length counts generated scenarios, not the
  additional flipped returns. Consumers needing isolation must deep-copy.
- **K05, RNG:** `test_rng_restored_before_serialization_characterization` checks
  all three families: construction preserves the caller's RNG; successful
  generation restores it before serialization, which then consumes two draws
  per opposing pair when all are in sight. `test_detection_uses_ambient_rng_not_scenario_seed`
  produces identical maps/placements from a fixed scenario seed but false versus
  true detection flags from ambient seeds 0 and 4. Balanced flipped returns
  consume no draws. Empty-unit generation also preserves caller RNG.
- **K06, cities:** `test_city_attempts_can_repeat_and_invasion_score_is_configurable`
  requests ten city placements into a two-cell red region and gets two unique
  cities. `test_square_city_attempts_are_not_unique_city_counts` confirms the
  same distinction for clear/hierarchy generators. `num_cities` is a count of
  placement attempts, not guaranteed unique objectives.
- **K06, hierarchy occupancy:**
  `test_hierarchy_cross_branch_collisions_characterization` uses seed 7, size 10,
  two parents, depth three and branching three. All 36 units exist, and each
  sibling leaf group occupies three unique cells, but different branches share
  cells. Candidate removal is local to each leaf group, not faction-wide.
  Unique faction-wide occupancy is not guaranteed; a correction remains future
  production work.
- `test_invalid_inputs_bounded_and_rng_leak` checks exact exception types and
  matching messages in ten-second subprocesses. Clear size 3 and hierarchy size
  9 raise the minimum-size `Exception`; reversed count bounds raise `ValueError`;
  clear/invasion over-capacity and invasion city placement with no free red cells
  raise `IndexError`. Hierarchy depth zero/one raises `TypeError` adding `None`
  to an integer, depth five and excessive leaf branching raise `IndexError`.
  Invasion height one with seed 7 raises `KeyError('hex-0--1')`. Every tested
  failure leaves caller RNG changed, rather than restoring it.
- `test_nonpositive_counts_produce_empty_units_characterization` records accepted
  negative clear/invasion counts and zero hierarchy branching producing no units.
  `test_setup_regions` (the `unknown` side case) records
  that unknown side names fall through to the east/west middle strip.
- `test_file_factory_defers_schema_consumption` loads schema-incomplete JSON
  successfully. Missing `map` fails during `Game` construction; missing `units`
  fails only on `initial_state()`. Loading is not schema validation.
- `test_game_dispenser.py::test_current_game_without_server_characterization`
  records `AttributeError` before a server is bound. Singleton tests restore the
  previous binding after every case.

## Failure policy and environment notes

When a later step reproduces an issue, record its stable ID, minimal pytest node
ID and command, expected result, exact observed result/exception, affected suites,
and whether it is a required contract or characterization. Use individual strict
xfails with `raises=KnownDefect` from `tests.support.isolation`. Raise that exception
only after matching the documented wrong signature. Unexpected failures must
propagate, and an unexpected pass must fail. Do not patch production code.

Environment note: this Windows sandbox denied pytest's restricted temporary
directories and Playwright subprocess named pipes. Running the same suite with
approved execution outside the sandbox passed. This is not a production defect
or a reason to skip the browser test. Browser installation is a separate explicit
setup step; missing plugins/binaries fail instead of producing skipped successes.

S02 harness issue (resolved): pytest-playwright's session-scoped synchronous
driver retained a running event loop after browser cases, causing the subsequent
pytest-asyncio cases to fail with `Runner.run() cannot be called from a running
event loop`. The test-local conftest now reuses the plugin's driver/browser
fixture bodies with function scope, so teardown stops the driver before the next
test. This is a harness lifecycle issue, not a production defect or an xfail.
