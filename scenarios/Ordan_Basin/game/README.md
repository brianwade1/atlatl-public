# Ordan Basin Atlatl Game Files

This folder contains the engine-readable artifacts for **The Race for the Ordan Basin**. This guide is the authoritative reference for runtime configuration, setup, scoring, deployment, and game-file maintenance. See the scenario landing page and map guide in the parent folders for narrative and geographic context.

## Current Artifacts

- [race_for_the_ordan_basin.scn](race_for_the_ordan_basin.scn) — complete playable scenario with the canonical map, all 26 units, setup zones, fog of war, neutral initial urban control, and victory settings.
- [oob.json](oob.json) — placement-ready order of battle containing 13 Blue and 13 Red counters.
- [order_of_battle.md](order_of_battle.md) — narrative order of battle and command relationships.

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
| Unit information | Hidden by fog of war |
| Initial urban ownership | Neutral in the Atlatl game state |
| Blue loss penalty | −1 point per Blue strength point lost |
| Red loss value | +1 point per Red strength point lost |
| Total urban score | 70 points per player phase, divided equally among seven urban hexes |

Atlatl calls each side's activation a **phase**. Consequently, 36 phases produce 18 complete two-sided game turns.

## Setup Zones

### Blue

Blue may position its 13 counters on any hex in columns `x=0` and `x=1`. These 24 western-edge hexes represent forces entering from Lestara and Ordan loyalist assembly areas.

### Red

Red may position its 13 counters on any hex in columns `x=10` and `x=11`. These 24 eastern-edge hexes represent the Karsovian intervention force entering the basin.

The scenario includes balanced default positions inside these zones. Blue deploys first, Red deploys second, and regular play begins with Blue. The separate `oob.json` leaves every `hex` value `null` for reusable placement.

## Objectives and Scoring

The seven urban objective hexes are:

| Location | Hex | Significance |
| --- | --- | --- |
| Kasar | `hex-9-2` | Northeastern logistics and staging hub |
| Dalen | `hex-5-3` | Northern principal crossing |
| Veyra | `hex-2-6` | National capital and elected government's seat |
| Novar | `hex-5-6` | Central crossing and decisive transportation junction |
| Ruda | `hex-9-6` | Emergency council's seat and eastern hub |
| Eren | `hex-4-9` | Southern principal crossing |
| Selin | `hex-9-9` | Southeastern staging area and alternate Eren approach |

The `cityScore` value of 70 is divided equally among the seven urban hexes, so each occupied city is worth 10 points at the end of every player phase. Blue possession adds points; Red possession subtracts points. Combat losses also affect the score.

All seven objectives begin neutral in Atlatl. This preserves the final map's exact 24-hex setup zones and makes the opening a true race for the political centers and crossing network. The narrative allegiance of Veyra and Ruda remains important to the scenario's victory interpretation, but it is not represented as automatic initial control.

The engine's aggregate score should be interpreted alongside the scenario victory framework:

- **Blue decisive victory:** retain or recover Veyra, control Novar and at least one of Dalen or Eren, and prevent a continuous Red corridor from the eastern edge to the Arven River.
- **Red decisive victory:** control Novar and at least one of Dalen or Eren, isolate or capture Veyra, and maintain a continuous corridor to the eastern edge.
- **Marginal victory:** control a majority of the key objectives while retaining an effective field force and a viable line of communication.
- **Draw:** both political centers and opposing bridgeheads survive, leaving Orda effectively partitioned.

## Map Notes

The `.scn` embeds the canonical final Ordan Basin map:

- 12 × 12 flat-top hexes.
- Blue setup in the western two columns; Red setup in the eastern two columns.
- Seven urban objective hexes.
- A connected Arven River water obstacle.
- Principal crossings at Dalen, Novar, and Eren.
- Secondary crossings at North Pass and Central Link.
- No South Pass crossing.
- Roads represented only between adjacent hexes.

## Runtime Use

Place `race_for_the_ordan_basin.scn` in `server/scenarios/`, or retain this folder as the authored source and copy the file there when deploying. The Atlatl launcher loads named `.scn` files from that directory.

Use `browser/unit-placement.html` only to change the default starting positions or author a variant. Load the complete scenario directly for normal play; the separate `oob.json` is not required after the `.scn` has been loaded.

## Authoring Boundaries

- The scenario embeds the canonical Ordan Basin area-of-operations map.
- Make terrain, road, river, bridge, or setup-zone changes in the map source first, then synchronize the embedded map.
- Keep `oob.json` location values as `null`; it is the reusable placement OOB. Starting locations belong in the `.scn` file.
- If the duration changes, remember that `maxPhases` counts individual player phases, not complete Blue/Red game turns.
- Keep the four Ordan formations at their reduced initial strengths unless playtesting supports a balance change.
- Treat this guide as the source for runtime facts. Broader narrative and design intent belong in the scenario overview.
