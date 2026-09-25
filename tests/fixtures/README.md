# Fixture data

S02 supplies JSON inputs, independent expectations, and a tiny CPU model. Every
JSON file has a `note` explaining the oracle. Function-scoped fixtures read these
files anew; mutations never affect another case. Do not overwrite these inputs
or production scenarios/replays. Generated archives belong in `tmp_path`.

| Fixture | Schema and independently specified expectation |
| --- | --- |
| `hex_geometry` | `map`, `dimensions`, `oracles`, `subsets`. Manually tabulated 4x3 centers; clockwise vertices and ordered neighbors for boundary/even/odd cells. Single/empty/irregular subsets list hex IDs. Serialized edges are intentionally empty: both loaders construct them from hex coordinates. Do not use this input to assert edge round-trip preservation. |
| `movement_corridors` | `line`, `alternative`, `types`, `terrains`, `origin`, `blocker`, `exact_budget`, `over_budget`. Clear vertical line gives infantry 100/200 and armor/artillery 100/150 boundaries; a second column permits a route around the blocker. Terrain/type variants are explicit lists. Build the selected actor with `make_unit`. |
| `combat_duel` | `scenario`, `action`, `expected_strength`, `expected_score`. Adjacent 100-strength infantry, spare blue B, no cities: 50 damage and +50 score without phase advance. |
| `setup_exchange` | `scenario`, `move`, `exchange`, `enemy_destination`. Two blue units, empty blue zone hex, occupied friendly hex, and red outside blue zone. |
| `city_scoring` | `scenario`, `owners`, `per_city`. Two cities, two phases, total city score 12, blue loss penalty -2; each city gives +6/-6/0 for blue/red/neutral. |
| `fog_sequence` | `scenario`, `frames[{name,truth,observations:{blue,red}}]`. Before detection, exact sight boundary, out of sight, removed and reappearing opponent. Radius 2 and pDetect=1; `white` uses truth. Removal leaves an ineffective record; hidden hex is `fog`, not a deleted record. |
| `rectangular_features` | `scenario`, `state`, `terrains`, `variant_coordinate`. 4x3 map, blue 75 at (0,2), red 60 at (3,0), score -7, phase 2. Apply each terrain at (1,2). |
| `tiny_episode` | `scenario`, ordered `actions`, `final_score`, `final_phase`. Move, pass, fire, pass; four ordinary phases and final blue score 50. No random action selection. |
| `hierarchy_units` | `scenario` plus grid weighted/unweighted and engine Euclidean centers. Nested names, unequal strengths, ineffective leaf, separate red faction. Effective blue weighted grid center (2,10/3); Euclidean center (0,4 sqrt(3)/3). |
| `protocol_messages` | `valid` named decoded wire objects and `malformed` inputs. Includes both roles, parameters, observations, ordinary/setup actions, reset/next-game/gym-pause and debug data. Debug colors use hex IDs; echelons are arrays of hex/color records. |
| `replay_sequences` | Named arrays of decoded messages; encode each message with `JSON.stringify`/`json.dumps` for the viewer's `replayData`. Includes second-game parameters, debug, fog/removal, empty and action-inclusive arrays. `invalid` and `truncated` are intentionally invalid JavaScript replay text. These are inputs for S13, not completed playback coverage. |
| `model_and_numeric_data` | Numeric oracle plus `archive`, `data_file`, `model_source` Paths. `sample.data` has one scalar per line (1,2,3,4), mean 2.5. Temporary archive contains float32 `matrix`, float32 `results` (row means 2,3) and int64 `timesteps` (10,20). `TinyCPU` has parameters implementing y=2x+1. No trained binary or download. |

The `make_map`, `make_unit`, `make_scenario` and `make_state` factory fixtures
return portable dictionaries, not engine instances. Their pure implementations
and defaults are in [builders.py](../support/builders.py). Map dimensions are
`rows, cols`; overrides are keyed by `(column, row)`. Names are unique within a
faction, with portable IDs such as `blue A`; repeated A across factions is valid.
Scenario/state builders deep-copy supplied inputs. `make_state` does not infer
initial setup, ownership, or movement flags: use `Game.initial_state()` when
testing initialization. The ordinary map builder emits complete deduplicated
edges for browser rendering, but must never supply geometry expected values.

Consumer tests validate that data loads and the independent oracles are coherent.
The full behavioral matrices, negative contracts, playback workflows and model
persistence tests remain in S03-S16.
