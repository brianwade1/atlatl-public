# The Race for the Ordan Basin

An operational-level, entirely fictional ground-combat scenario for [Atlatl](https://github.com/brianwade1/atlatl-public). A political crisis in the nonaligned Republic of Orda triggers competing Western Compact and Karsovian interventions. Both forces enter from opposite sides of the country and race to control the Arven River crossings, rival political centers, and the road network that connects them.

![Ordan Basin area of operations](ordan_basin_ao_overview.png)

## Scenario Summary

| Item | Description |
| --- | --- |
| Start | 12 September 2031, 0600 local time |
| Duration | 18 turns / 9 days; two 12-hour turns per day |
| Scale | Approximately 15 km per hex on a 12 × 12 map |
| Blue | Western Compact–Ordan Joint Land Corps |
| Red | Karsovian Eastern Army |
| Playable units | 13 counters per side; brigade-sized formations and artillery groups |
| Core challenge | Secure the crossings and transportation network without dispersing the force or exposing a political center |

Blue begins closer to several central objectives and fields one additional artillery group, but its Ordan formations are understrength. Red possesses a 90-point aggregate strength advantage and one additional mechanized brigade, but must advance from the eastern edge while maintaining secure lines of communication. The result is a meeting engagement in which tempo, concentration, bridge control, and reserve timing drive the outcome.

## Central Operational Problem

Can Blue preserve the elected government in Veyra and prevent a Karsovian territorial fait accompli before Red secures the central basin? Both commanders must decide which river crossings are indispensable, where to accept risk, whether to use the restrictive northern and southern pass routes, and when to commit their armored reserve.

## Package Contents

| File | Purpose |
| --- | --- |
| [`ordan_basin_scenario.md`](ordan_basin_scenario.md) | Scenario overview, strategic setting, operational problem, player objectives, and victory framework |
| [`ordan_basin_order_of_battle.md`](ordan_basin_order_of_battle.md) | Command structure, playable formations, strengths, suggested setup hexes, and balance notes |
| [`ordan_basin_oob.json`](ordan_basin_oob.json) | Reusable Atlatl-compatible unit data with placement fields intentionally unset |
| [`ordan_basin_ao_overview.svg`](ordan_basin_ao_overview.svg) / [`PNG`](ordan_basin_ao_overview.png) | General political and operational reference map |
| [`ordan_basin_atlatl_map.svg`](ordan_basin_atlatl_map.svg) / [`PNG`](ordan_basin_atlatl_map.png) | Matching 12 × 12 native hex map |
| [`ordan_basin.map.json`](ordan_basin.map.json) | Atlatl map-editor data with terrain, water hexes, river-bank edges, setup zones, and road paths |
| [`ordan_basin_map_notes.md`](ordan_basin_map_notes.md) | Map crosswalk, key-hex index, and terrain interpretation |
| [`generate_ordan_basin_maps.py`](generate_ordan_basin_maps.py) | Reproducible source for the overview map, game map, and map JSON |
| [`ordan_basin_scenario_package.zip`](ordan_basin_scenario_package.zip) | Downloadable starter package containing the current scenario assets |

## Map Framework

The general AO map and the native Atlatl map depict the same geography. The **Arven River** is represented by connected `water` hexes, with three principal urban crossings at **Dalen**, **Novar**, and **Eren**. Secondary crossings at **North Pass**, **Central Link**, and **South Pass** create additional maneuver options. The **Saren Heights** and **Mora Hills** restrict off-road movement, while the open central basin favors armored and mechanized operations.

Roads are stored as native Atlatl `path` objects. Each road segment connects adjacent hexes and follows the hex geometry rather than an abstract overlay. The network uses irregular lateral connectors and off-map continuation routes instead of a rigid grid.

## Force Balance

| Side | Armor | Mechanized | Infantry | Artillery | Counters | Nominal strength |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Blue | 3 | 5 | 2 | 3 | 13 | 1,210 |
| Red | 3 | 6 | 2 | 2 | 13 | 1,300 |

The sides are counter-balanced but deliberately asymmetric. Blue's four Ordan formations begin at 75–80 percent strength; all Western Compact and Karsovian formations begin at full strength. Headquarters, reconnaissance, engineers, air defense, logistics, aviation, and other enabling capabilities are incorporated into parent formations or represented through scenario rules rather than separate counters.

## Quick Start

1. Review [`ordan_basin_scenario.md`](ordan_basin_scenario.md) for the political context, operational problem, and objectives.
2. Load [`ordan_basin.map.json`](ordan_basin.map.json) in the Atlatl map editor or unit-placement tool.
3. Import [`ordan_basin_oob.json`](ordan_basin_oob.json).
4. Place units using the recommended coordinates in [`ordan_basin_order_of_battle.md`](ordan_basin_order_of_battle.md).
5. Apply the current 18-turn duration and preliminary victory framework, then adjust scoring and terrain effects during playtesting.

## Authoring Notes

- The map JSON is the machine-readable source for Atlatl terrain, river, road, and setup data.
- The SVG files are editable visual masters; the PNG files are high-resolution previews.
- The OOB JSON intentionally leaves `hex` as `null` and `canMove` as `false`, matching the reusable placement convention. Starting positions belong in the scenario setup or eventual `.scn` file.
- Changes to geography should be made in `generate_ordan_basin_maps.py`, then propagated to the SVG, PNG, and map JSON outputs.
- Duration, terrain modifiers, reinforcement timing, casualty scoring, and final objective values remain preliminary until playtesting is complete.

## Current Status

The scenario overview, order of battle, OOB JSON, aligned maps, and map JSON are available. The package is suitable for setup and initial playtesting. A fully playable `.scn` file and finalized scoring model remain to be developed after the first balance tests.

