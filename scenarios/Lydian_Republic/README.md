# Defense of the Lydian Republic

> **Scenario status:** Entirely fictional. All countries, political events, military organizations, and geographic locations in this scenario are invented for research and educational use.

This directory contains the complete authored package for **Defense of the Lydian Republic**, an operational-level Atlatl scenario depicting a multinational corps defense against a larger Vostian field army.

This README is also the public player and optional-controller quick reference for baseline play.

![Lydian Republic area of operations](map/lydian_republic_ao_reference.png)

## Quick Start

From the repository root, launch the scenario by its stable alias:

```bash
python main.py lydian-republic
```

The scenario can also be launched directly from its package path:

```bash
python main.py scenarios/Lydian_Republic/game/defense_of_the_lydian_republic.scn
```

The `.scn` file does not need to be copied into `server/scenarios/`. Blue repositions first, Red repositions second, and regular play begins with Blue.

The `.scn` file contains everything required for normal play. The standalone map and order-of-battle files are authoring sources for editing and variant creation.

## Scenario Overview

Play begins on **18 May 2030 at 0600 local time (H+48)**. The RDC Coalition Land Corps must defend widely separated objectives with less combat power, while the Vostian 3rd Field Army must turn its temporary advantage in mass and readiness into a rapid decision.

| Element | Baseline |
| --- | --- |
| Blue | RDC Coalition Land Corps; 9 counters |
| Red | Vostian 3rd Field Army; 12 counters |
| Duration | 20 complete Blue/Red turns; 10 days |
| Playable-unit scale | Maneuver brigades and artillery groups |
| Scored objectives | Kirov, Belas, Velin, and Aradesh |
| Unit information | Open; fog of war disabled |
| Status | Complete playable baseline; balance validation pending |

## Documentation Guide

| Document | Use it for |
| --- | --- |
| [Scenario specification](scenario.md) | Design intent, scope, forces, abstractions, and development status. |
| [Road to war](road_to_war_defense_of_the_lydian_republic.md) | Political background, escalation, and the H+48 invasion chronology. |
| [Game-file guide](game/README.md) | Authoritative runtime configuration, setup, scoring, deployment, and game-file maintenance. |
| [Order of battle](game/order_of_battle.md) | Formation strengths, roles, and command relationships. |
| [Map guide](map/README.md) | Authoritative map contents, geography, editing, and synchronization workflow. |
| [Operations-order index](operations_orders/README.md) | Side-specific index of both briefing hierarchies, synchronization aids, support orders, PDF graphics, and disclosure guidance. |

## Player and Optional Controller Reference

> **Controller-free baseline:** Both players may read this section. A controller may facilitate play under procedures agreed before setup but is not required.

### Before Play and Disclosure

Use closed plans unless both players agree otherwise. The scenario specification, road to war, order of battle, maps, game guide, and engine-visible unit information are shared. Each side's orders, master crosswalk, and operational graphics are private to that side.

Read the [road to war](road_to_war_defense_of_the_lydian_republic.md), [order of battle](game/order_of_battle.md), and [reference map](map/lydian_republic_ao_reference.png), then open only the assigned side's products:

| Side | Senior order | Synchronization aid | Graphics |
| --- | --- | --- | --- |
| Blue | [RDC Coalition Land Corps order](operations_orders/Blue/B-00_rdc_coalition_land_corps_opord.md) | [Blue master crosswalk](operations_orders/Blue/blue_master_synchronization_crosswalk.md) | [Blue graphics](operations_orders/Blue/Blue_operational_graphics.pdf) |
| Red | [Vostian 3rd Field Army order](operations_orders/Red/R-00_vostian_3rd_field_army_opord.md) | [Red master crosswalk](operations_orders/Red/red_master_synchronization_crosswalk.md) | [Red graphics](operations_orders/Red/Red_operational_graphics.pdf) |

If using a controller or special adjudication, agree on the controller's authority and any unmodeled effects before setup. The [operations-order index](operations_orders/README.md) provides the complete order hierarchy and disclosure guidance.

### Setup Checklist

1. Blue may reposition all nine units on eligible non-water hexes in columns `x=0–14`, inclusive.
2. After Blue ends setup, Red may reposition all twelve units on eligible hexes in columns `x=18–19`.
3. Default positions are suggestions. End setup with every unit in its permitted zone and no stacked units.
4. Red may adjust after observing Blue's defense. This asymmetry and open unit information are intentional.
5. Setup phases do not count toward the 40 regular player phases and award no city points. Regular play begins with Blue.

### Objectives, Scoring, and End Conditions

| Objective | Hex | Value each regular player phase |
| --- | --- | --- |
| Kirov | `hex-5-3` | 15 points |
| Aradesh | `hex-12-6` | 15 points |
| Belas | `hex-5-7` | 15 points |
| Velin | `hex-5-11` | 15 points |

All four cities begin under Blue control. At the end of each regular player phase, an occupied city changes to the occupier's faction; an empty city retains its owner. Blue control adds points and Red control subtracts them. Each Blue strength point lost subtracts one point; each Red strength point lost adds one point. A unit reduced below 50 percent strength is removed, and its remaining strength is counted as lost. Play ends after 40 regular player phases even if one side has lost all units. The engine reports a raw score from Blue's perspective but applies no validated victory bands.

### Engine and Player Responsibilities

| Enforced by Atlatl | Enforced by players |
| --- | --- |
| Map and unit state; movement and combat procedures; city ownership; player-phase count; raw scoring | Command relationships; reserve-release authority; Operational Phases; main-effort and fires-priority changes; boundaries and control measures; handoffs; weather guidance; reporting requirements |

- A player phase is one side's engine activation. A capitalized **Operational Phase** is a stage of the written plan and changes only when its stated conditions and proper headquarters authority are satisfied.
- In controller-free play, the player or team controlling the proper headquarters records phase transitions, reserve commitments, handoffs, and accepted risks. No controller approval is required.
- Do not abandon an assigned city, crossing, route, seam, or guard responsibility until the receiving formation accepts the handoff or the proper headquarters records the risk.
- Operational graphics are planning products. Translate their control measures into map hexes; they are not an engine overlay.
- Do not invent combat modifiers for weather, visibility, logistics, intelligence, or other unmodeled capabilities unless both players agreed to an adjudication method before setup.

### Optional Controller and End-of-Game Checklist

- Protect closed-plan information and confirm legal setup without advising either side.
- Record consequential phase changes, reserve commitments, passages, handoffs, accepted risks, and rulings.
- Apply the same interpretation to both sides. Resolve conflicts using the signed orders and their stated precedence; do not become an additional commander.
- Add no reinforcements, capabilities, modifiers, or injects unless authorized by the agreed scenario procedure.
- At completion, players or the optional controller record the final raw score, city ownership, strength losses, reserve status, narrative objectives, major handoffs, and unresolved order conflicts.

## Authoring Boundaries

| Source | Owns |
| --- | --- |
| [`defense_of_the_lydian_republic.scn`](game/defense_of_the_lydian_republic.scn) | Playable runtime state, including units, starting positions, setup zones, ownership, duration, and scoring. |
| [`lydian_republic_ao.map.json`](map/lydian_republic_ao.map.json) | Canonical hex geometry, terrain, roads, rivers, and geographic features. |
| [`oob.json`](game/oob.json) | Reusable placement OOB with intentionally unset locations. |
| [Written orders](operations_orders/README.md) | Player-enforced command relationships, phases, priorities, control measures, and reporting requirements. |

When geography changes, synchronize it from the map source into the completed scenario without overwriting scenario-specific runtime state. Detailed procedures belong in the [map](map/README.md) and [game-file](game/README.md) guides.
