# Lydian Republic Atlatl Game Files

This folder contains the engine-readable artifacts for **Defense of the Lydian Republic**. This guide is the authoritative reference for runtime configuration, setup, scoring, deployment, and game-file maintenance. See the [scenario landing page](../README.md) for player entry points and the [map guide](../map/README.md) for geographic sources.

## Current Artifacts

- [defense_of_the_lydian_republic.scn](defense_of_the_lydian_republic.scn) — complete playable scenario with the map, all 21 units, setup zones, open unit information, initial city ownership, and victory settings.
- [oob.json](oob.json) — placement-ready order of battle containing nine Blue and twelve Red counters.
- [order_of_battle.md](order_of_battle.md) — narrative order of battle and command relationships.

The `.scn` file is already JSON. A second `.json` copy of the scenario is unnecessary.

## Scenario Configuration

| Setting | Value |
| --- | --- |
| Scenario start | 18 May 2030, 0600 local time (H+48) |
| Scenario end | 28 May 2030, 0600 local time |
| Map | 20 columns x 14 rows |
| Forces | 9 Blue; 12 Red; 21 total |
| Duration | 40 player phases (20 complete Blue/Red game turns) |
| Scenario time represented | 10 days |
| Unit information | Open; all units are visible |
| Initial city ownership | Blue |
| Blue loss penalty | -1 point per Blue strength point lost |
| Red loss value | +1 point per Red strength point lost |
| Total city score | 60 points per player phase, divided equally among the four urban hexes |

Atlatl calls each side's activation a **phase**. Consequently, 40 phases produce 20 complete two-sided game turns.

## Setup Zones

The standalone map and completed `.scn` use the same baseline setup assignments. The map JSON is the authoring source for those zones, while the embedded copy in the `.scn` is authoritative during play. Regeneration or synchronization must preserve equality between their per-hex `setup` values.

### Blue

Blue may reposition its nine units on any non-water hex from the western map edge through column `x=14`, inclusive. Aradesh is at `hex-12-6`; the eastern limit is therefore two columns east of the city. This gives Blue 199 eligible setup hexes and permits a forward defense, a defense in depth, or a rearward defense along the Arel River.

### Red

Red may reposition its twelve units in columns `x=18` and `x=19`, providing 28 eligible setup hexes on the eastern map edge.

The scenario includes doctrinally sensible default positions, but these are starting suggestions rather than mandatory dispositions. During the setup sequence, Blue repositions first and ends its setup phase; Red then repositions and ends its setup phase. Regular play begins with Blue.

This asymmetry is intentional. Blue establishes the defense first across its broad setup area; Red, as the attacking force, then observes that defensive disposition and adjusts its setup before regular play begins. Open unit information makes that offensive adjustment an explicit part of the scenario design.

## Objectives and Scoring

The four urban objective hexes are:

| Location | Hex |
| --- | --- |
| Kirov | `hex-5-3` |
| Aradesh | `hex-12-6` |
| Belas | `hex-5-7` |
| Velin | `hex-5-11` |

All four begin under Blue control. The `cityScore` value of 60 is divided equally among them, so each controlled urban hex is worth 15 points at the end of every player phase. Blue possession adds points to the score; Red possession subtracts points. Combat losses also affect the score, making the final result a combination of objective control and force preservation.

## Runtime Use

From the repository root, launch the scenario with `python main.py lydian-republic`. The stable alias loads `defense_of_the_lydian_republic.scn` from this directory, so the file does not need to be copied into `server/scenarios/`. An explicit path also works: `python main.py scenarios/Lydian_Republic/game/defense_of_the_lydian_republic.scn`.

Use `browser/unit-placement.html` only if you want to change the default starting positions or author a variant. Load the complete scenario directly for normal play; the separate `oob.json` is not required once the `.scn` has been loaded.

## Authoring Boundaries

- The scenario embeds the canonical Lydian Republic area-of-operations map.
- Make terrain, road, river, or bridge changes in the map source first, then synchronize the embedded map.
- Keep `oob.json` location values as `null`; it is the reusable placement OOB. Starting locations belong in the `.scn` file.
- If the scenario duration changes, remember that `maxPhases` counts individual player phases, not complete Blue/Red game turns.
- Treat the values in this guide as runtime facts. Broader narrative and design intent belong in the [scenario specification](../scenario.md).
