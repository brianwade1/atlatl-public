# Confirmed issues

S03 runtime-confirmed the Python map defects grouped under **K01** and **K02**
in `../test_plan.md`. S04 confirms the serialization/detection side effect in
K05 as characterization, without an expected failure. The remaining K03–K18
items and browser portions of K01/K02 remain an investigation queue, not
expected failures. Production files remain unchanged.

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
  Status sharing and scenario-factory portions of K05 await S05/S06.
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
