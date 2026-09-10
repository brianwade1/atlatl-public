# The Race for the Ordan Basin

> **Scenario status:** Entirely fictional. All countries, political events, military organizations, and geographic locations in this scenario are invented for research and educational use.

This directory contains the complete authored package for **The Race for the Ordan Basin**, an operational-level Atlatl scenario depicting competing Western Compact and Karsovian interventions during an Ordan constitutional crisis.

![Ordan Basin area of operations](map/ordan_basin_ao_reference.png)

## Quick Start

From the repository root, launch the scenario by its stable alias:

```bash
python main.py ordan-basin
```

The scenario can also be launched directly from its package path:

```bash
python main.py scenarios/Ordan_Basin/game/race_for_the_ordan_basin.scn
```

The `.scn` file does not need to be copied into `server/scenarios/`. Blue repositions first, Red repositions second, and regular play begins with Blue.

The `.scn` file contains everything required for normal play. The standalone map and order-of-battle files are authoring sources for editing and variant creation.

## Scenario Overview

Play begins on **12 September 2031 at 0600 local time**. The Western Compact–Ordan Joint Land Corps and Karsovian Eastern Army enter from opposite map edges and race for seven initially neutral cities, five Arven River crossings, and the basin's transportation network.

| Element | Baseline |
| --- | --- |
| Blue | Western Compact–Ordan Joint Land Corps; 13 counters; 1,210 current strength |
| Red | Karsovian Eastern Army; 13 counters; 1,300 current strength |
| Duration | 18 complete Blue/Red turns; 36 player phases; 9 days |
| Playable-unit scale | Maneuver brigades and artillery groups |
| Scored objectives | Veyra, Dalen, Novar, Eren, Kasar, Ruda, and Selin |
| Initial city ownership | Neutral for all seven cities |
| Unit information | Open; fog of war disabled |
| Default deployment | All playable units outside cities in opposing edge setup zones |
| Status | Complete playable baseline; balance validation pending |

## Documentation Guide

| Document | Use it for |
| --- | --- |
| [Scenario specification](ordan_basin_scenario.md) | Design intent, scope, forces, abstractions, runtime rules, and development status. |
| [Road to war](road_to_war_race_for_the_ordan_basin.md) | Political background, escalation, and the transition to the 12 September meeting engagement. |
| [Game-file guide](game/README.md) | Authoritative runtime configuration, setup, scoring, deployment, and game-file maintenance. |
| [Order of battle](game/order_of_battle.md) | Formation strengths, roles, command relationships, and represented capabilities. |
| [Map guide](map/README.md) | Authoritative map contents, geography, editing, and synchronization workflow. |
| [Operations-order index](operations_orders/README.md) | Controller-facing index of both briefing hierarchies, master crosswalks, support orders, graphics, and disclosure guidance. |

## Player Briefings

For opposed play, Blue and Red operations orders, master synchronization crosswalks, and operational graphics are **side-specific**. Each player should normally use only the assigned side's link unless the group agrees to open plans. Unit information in the engine is open, but that does not make the opposing plan open.

| Side | Start here | Controller aid |
| --- | --- | --- |
| Blue | [Western Compact–Ordan Joint Land Corps order](operations_orders/Blue/B-00_wco_joint_land_corps_opord.md) | [Blue master synchronization crosswalk](operations_orders/Blue/blue_master_synchronization_crosswalk.md) |
| Red | [Karsovian Eastern Army order](operations_orders/Red/R-00_karsovian_eastern_army_opord.md) | [Red master synchronization crosswalk](operations_orders/Red/red_master_synchronization_crosswalk.md) |

Controllers and scenario administrators can use the [operations-order index](operations_orders/README.md) to reach the complete hierarchy and both sets of graphics.

## Authoring Boundaries

| Source | Owns |
| --- | --- |
| [`race_for_the_ordan_basin.scn`](game/race_for_the_ordan_basin.scn) | Playable runtime state, including units, default positions, setup sequence, ownership, duration, and scoring. |
| [`ordan_basin_ao.map.json`](map/ordan_basin_ao.map.json) | Canonical hex geometry, terrain, roads, river representation, setup zones, and open-information flag. |
| [`oob.json`](game/oob.json) | Reusable 26-counter placement OOB with intentionally unset locations. |
| [Written orders](operations_orders/README.md) | Player-enforced command relationships, phases, priorities, control measures, and reporting requirements. |

When geography changes, synchronize it from the map source into the completed scenario without overwriting scenario-specific runtime state. Detailed procedures belong in the [map](map/README.md) and [game-file](game/README.md) guides.
