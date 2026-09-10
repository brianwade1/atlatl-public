# Ordan Basin Atlatl Game Files

This folder contains the engine-readable artifacts for **The Race for the Ordan Basin**. This guide is the authoritative reference for runtime configuration, setup, scoring, deployment, and game-file maintenance. See the [scenario landing page](../README.md) for player entry points and the [map guide](../map/README.md) for geographic sources.

## Current Artifacts

- [race_for_the_ordan_basin.scn](race_for_the_ordan_basin.scn) — complete playable scenario with the map, all 26 units, default positions, setup zones, open unit information, neutral initial city ownership, and scoring.
- [oob.json](oob.json) — placement-ready order of battle containing 13 Blue and 13 Red counters with intentionally unset locations.
- [order_of_battle.md](order_of_battle.md) — narrative order of battle, represented capabilities, formation roles, and command relationships.

The `.scn` file is already JSON. A second `.json` copy of the scenario is unnecessary.

## Scenario Configuration

| Setting | Value |
| --- | --- |
| Scenario start | 12 September 2031, 0600 local time |
| Scenario end | 21 September 2031, 0600 local time |
| Map | 12 columns × 12 rows; approximately 15 km per hex |
| Forces | 13 Blue; 13 Red; 26 total |
| Duration | 36 player phases (18 complete Blue/Red game turns) |
| Scenario time represented | 9 days |
| Unit information | Open; all units are visible |
| Initial city ownership | Neutral for all seven cities |
| Blue loss penalty | −1 point per Blue strength point lost |
| Red loss value | +1 point per Red strength point lost |
| Total city score | 70 points per player phase, divided equally among seven urban hexes |

Atlatl calls each side's activation a **phase**. Consequently, 36 regular player phases produce 18 complete two-sided game turns. Setup activations are excluded from that count and do not award city points.

## Setup Zones and Default Deployment

### Blue

Blue may reposition its 13 units on eligible non-water hexes in the two westernmost columns, `x=0` and `x=1`. The zone contains 24 eligible hexes.

### Red

Red may reposition its 13 units on eligible non-water hexes in the two easternmost columns, `x=10` and `x=11`. The zone contains 24 eligible hexes.

All supplied default positions are valid, unstacked, and outside the seven cities. Blue repositions first and ends its setup phase; Red then repositions and ends its setup phase. Regular play begins with Blue. The edge-zone starts model formations entering the area of operations rather than occupying cities before play.

## Objectives and Scoring

| Location | Hex |
| --- | --- |
| Kasar | `hex-9-2` |
| Dalen | `hex-5-3` |
| Veyra | `hex-2-6` |
| Novar | `hex-5-7` |
| Ruda | `hex-9-6` |
| Eren | `hex-4-9` |
| Selin | `hex-9-9` |

All seven cities begin neutral. An occupied city changes to the occupier's faction at the end of a regular player phase; an empty city retains its owner. The `cityScore` value of 70 is divided equally, so each Blue-controlled city adds 10 points and each Red-controlled city subtracts 10 points per phase. A neutral city awards nothing.

The engine score is from Blue's perspective. Blue losses reduce it and Red losses increase it. Atlatl reports a raw score and applies no Ordan-specific victory bands. Use matched playtests to evaluate score balance before assigning result labels.

## Runtime Use

From the repository root, launch the scenario with `python main.py ordan-basin`. The stable alias loads `race_for_the_ordan_basin.scn` from this directory, so the file does not need to be copied into `server/scenarios/`. An explicit path also works: `python main.py scenarios/Ordan_Basin/game/race_for_the_ordan_basin.scn`.

Use `browser/unit-placement.html` only to change default positions or author a variant. Load the complete scenario directly for normal play; the separate `oob.json` is not required after the `.scn` has loaded.

## Authoring Boundaries

- The scenario embeds the canonical Ordan Basin area-of-operations map and adds runtime state.
- Make terrain, road, river, setup-zone, or visibility changes in the [map source](../map/ordan_basin_ao.map.json) first, then synchronize the embedded map.
- Keep `oob.json` unit locations as `null`; it is the reusable placement OOB. Default locations belong in the `.scn`.
- Keep all default starts in the owning side's setup zone and outside cities unless a later documented variant explicitly changes the premise.
- If duration changes, remember that `maxPhases` counts individual player phases rather than complete Blue/Red game turns.
- Treat the values in this guide as runtime facts. Broader narrative and design intent belong in the [scenario specification](../ordan_basin_scenario.md).
