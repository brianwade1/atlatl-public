# S14 AI coverage matrix

`support/ai_contract.py` lists aliases explicitly; `test_registry_matrix_is_complete`
checks the live non-neural registry and the neural-gated assignments in its AST.
New aliases therefore require an explicit coverage/limitation decision. Constructor
kwargs are deep-copied. No model is loaded for the ordinary agent contracts.

Every ordinary alias below has blue **and** red role requests, off-turn/terminal
silence, replacement parameters, real-engine action validation and setup validation.
Each also plays a complete seed-1729 four-phase game as blue against passive in a
20-second child, capped at 32 actions. These are engine integrations, not socket
tests or strength benchmarks. Ordinary positions have two infantry units, an urban
hex and nested names; focused tests add asymmetric forces, terrain and extra units.

In the table, **pass** means skipping setup, **place** means a setup queue followed
by pass. **Clear** means only full-information ordinary play is claimed; fog support
is not inferred from accepting parameters. **Fog** adds an actual hidden-enemy
observation and distribution tests. **Nested** adds explicit hierarchy aggregation,
commander movement and serializable debug records. All ordinary rows run under
`server_unit/` and `server_integration/test_ai_games.py`.

| Alias | Registry options | Setup | Tested information/hierarchy | Distinctive checks |
| --- | --- | --- | --- | --- |
| passive | none | pass | Clear | always pass |
| random | none | pass | Clear | both random move/fire branches |
| shootback | none | pass | Clear | fire first, absent targets |
| field | none | pass | Clear | opposing city ownership, distance, colors |
| pass-agg | none | pass | Clear | posture, distances, fire priority |
| pass | mode=pass | pass | Clear | forced defense |
| agg | mode=agg | pass | Clear | forced attack |
| pass-agg-fp | none | pass | Clear | full ordered plan, both scoring signs, K33 |
| pass-agg-fog | none | pass | Fog | cull, diffusion, normalization, replacement |
| pass-agg-setup | none | place | Clear | cells/exchange/queue, K33 |
| pass-agg-setup-fog | none | place | Fog | uniform setup support, cells/exchange, K33 |
| dijkstra | none | pass | Clear | real SciPy directed armor costs, unreachable water |
| pass-agg-pseudo-q | score_is_Q=true, search=fixed | pass | Clear | scoring boundary, fire/wait, all four search methods |
| pass-agg-state | score_is_Q=false, search=fixed | pass | Clear | successor scores, isolated branches, K33 |
| stomp-scoring | search=fixed | pass | Clear | per-type paths, finite symmetric scores |
| simon-says | none | place | Clear | maneuver thresholds, six bounded recursive entry points, K33 |
| simple-assault | none | pass | Clear | strengths 74/75/76 |
| simple-disengage | none | pass | Clear | unique safe escape |
| simple-encircle | none | pass | Clear | safe closer destination |
| simple-fire-coordination | none | pass | Clear | limited-target shooter first, both factions |
| simple-movement | none (mode defaults to None) | pass | Clear | explicit Capture/DefendCity/Offensive/DefendUnits/Flee helper cases |
| burt-reynolds-lab2 | none | pass | Clear | force posture, distances, shoot-first |
| burtplus | none | pass | Clear | unique weakest target |
| stomp | none | pass | Clear | per-type paths, full blue-max/red-min plan, K33 |
| stomp-pp | partialPly=true | pass | Clear | partial blue-max/red-min plan |
| hierarchy-template | none | pass | Nested | parent names, crowding, command movement |
| hierarchy-random-commander | mode=random_commander | pass | Nested | seeded abstract movement |
| hierarchy-ignore-commander | mode=ignore_commander | pass | Nested | concrete legality without command attraction |
| deep-hierarchy | none | pass | Nested | two abstract levels, centers and debug schema |
| setup-demo | none | place | Clear | occupied exchange, city ranking, replacement queue |

MCTS aliases have blue/red parameter, off-turn, terminal and replacement contracts,
FIFO/off-turn queue tests, and individual strict K34 action probes. The adapter
stores search output in `im` and pops an empty `actionQueue`, so completed games
and setup actions are blocked by that defect. A real eight-rollout adapter probe
confirms search produces legal actions before the same exception. Search itself
has finite toy-tree winning/losing branches, red minimization, terminal/supplied
roots and memory-stop coverage. No zero/unlimited rollout budget is used.

| Alias | Registry defaults | Test override | Limitation |
| --- | --- | --- | --- |
| mcts1k | max_rollouts=1000, debug=false | 8, false | K34; stale queue K33 |
| mcts10k | max_rollouts=10000, debug=false | 8, false | K34 |
| mctsd | max_rollouts=10000, debug=true | 8, false | K34; interactive debugger excluded |

The following aliases are inventoried, **not executed as move-producing S14 AIs**.
All accept role selection in their APIs, but blue/red, setup, fog and hierarchy
behavior is deferred to the named adapter suites. Missing models are not skipped
tests and no production checkpoints are required. `gym-pause` is a callback
protocol response, not a registered alias.

| Alias | Required options/model or boundary | Suite / named limitation |
| --- | --- | --- |
| gym | callback and discrete action consumer | S15 |
| gymx2 | doubled observation adapter | S15 |
| gym12 | 12-feature callback adapter | S15 |
| gym13 | 13-feature callback adapter | S15 |
| gym14 | 14-feature callback adapter | S15 |
| gym16 | 16-feature callback adapter | S15 |
| gym18 | 18-feature callback adapter | S15 |
| multigym | mode=training, callback | S15 |
| multi-ai-rl | mode=production, dqn=true, policy model | S15 |
| multi-ai-rl-ppo | mode=production, dqn=false, policy model | S15 |
| neural | doubledCoordinates=false, policy model | S15 neural adapter |
| cnn | doubledCoordinates=true, policy model | S15 neural adapter |
| hex12 | doubledCoordinates=false, policy model | S15 neural adapter |
| hex13 | doubledCoordinates=false, policy model | S15 neural adapter |
| hex14 | doubledCoordinates=false, policy model | S15 neural adapter |
| hex14dqn | dqn=true, doubledCoordinates=false, policy model | S15 |
| hex18dqn | dqn=true, doubledCoordinates=false, policy model | S15 |
| mando-fun-lab3 | ai/mandofun_c0.zip, dqn=true, doubledCoordinates=false | S15; no packaged checkpoint loading |
| alphazero | neuralNet=temp | S16 AlphaZero adapter |
| dlalphabeta | debug=false, neural callable/model | Adapter deferred; search tested in ml/test_dlalphabeta.py |
| state-eval-gpu | partialPly=false, GPU/model | S15/S16 optional model adapter |
| state-eval-gpu-pp | partialPly=true, GPU/model | S15/S16 optional model adapter |
| pascal | ai/pass-v-pass-g3, depthLimit="1", debug=false | Model-loading adapter deferred; shared search tested |
| ibarra-m3 | ai/A5b_M3, depthLimit="1", debug=false | Model-loading adapter deferred; shared search tested |
| ibarra-lx3 | ai/A5b_LX3, depthLimit="1", debug=false | Model-loading adapter deferred; shared search tested |

The CPU neural search case imports real Torch/hexagdly in a bounded child and fails
if dependencies are absent. Its fixed-valued callable and observation boundary
isolate terminal scores, cutoff evaluation, pruning and actual depth semantics:
`dlab(depth_limit=1)` considers a root action plus one further action. Feature
encoding belongs to S15. No training or GPU is used.

Setup cell shortages and an absent enemy prototype in fog distributions are named
unsupported-input characterizations. Pending-plan reset defects, six-digit color
conversion, abstraction serialization and a geometric boundary defect are tracked
in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). Three-digit colors currently parse as CSS
shorthand, but do not preserve the intended six-digit channel values. Debug records
are checked against the playback schema; the existing S13 browser suite owns actual
viewer execution (orders coloring remains blocked by K32).
