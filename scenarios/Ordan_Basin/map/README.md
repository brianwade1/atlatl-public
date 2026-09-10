# Ordan Basin Area of Operations Map

This folder contains the machine-readable map, visual previews, and metadata for **The Race for the Ordan Basin**. This guide is the authoritative reference for named geography and geographic editing. See the [scenario landing page](../README.md) for player entry points and the [game-file guide](../game/README.md) for runtime state.

## Map Framework

- Ground scale: approximately 15 km per hex
- Grid: 12 × 12 flat-top hexes
- Operational area: approximately 180 × 150 km
- Blue setup: 24 eligible hexes in columns `x=0` and `x=1`
- Red setup: 24 eligible hexes in columns `x=10` and `x=11`
- Unit information: open; `fogOfWar` is `false`
- Major terrain: Saren Heights, central Ordan Basin, Mora Hills, marshes, and the Arven River
- Terrain totals: 65 clear, 52 rough, 12 marsh, 8 water, and 7 urban hexes

## Named Locations

| Location | Hex | Function |
| --- | --- | --- |
| Veyra | `hex-2-6` | Capital and major Blue political objective. |
| Dalen | `hex-5-3` | Northern principal crossing and scored city. |
| Novar | `hex-5-7` | Central principal crossing and transportation junction. |
| Eren | `hex-4-9` | Southern principal crossing and scored city. |
| Kasar | `hex-9-2` | Northeastern transportation and staging hub. |
| Ruda | `hex-9-6` | Eastern political center and north–south road junction. |
| Selin | `hex-9-9` | Southeastern staging hub and alternate Eren approach. |
| North Pass Bridge | `hex-5-1` | Secondary crossing through the Saren Heights. |
| Central Link Bridge | `hex-5-5` | Secondary diagonal crossing between the northern and central routes. |

There is **no South Pass crossing** in the canonical map. `hex-4-10` is water and no through-road crosses the Arven River in the Mora Hills.

## Package Contents

- [Map JSON](ordan_basin_ao.map.json) — canonical machine-readable source for hex geometry, terrain, roads, river edges, setup zones, and unit visibility.
- [Atlatl SVG](ordan_basin_ao_atlatl.svg) and [PNG](ordan_basin_ao_atlatl.png) — exact hex-grid preview using native Atlatl terrain categories.
- [Reference SVG](ordan_basin_ao_reference.svg) and [PNG](ordan_basin_ao_reference.png) — grid-free planning map for orders, overlays, and mission graphics.
- [Map manifest](ordan_basin_ao_manifest.json) — grid dimensions, named locations, terrain and setup-zone counts, bridge metadata, source commit, and design notes.

The image files are visual products; Atlatl does not load them during play.

## River and Road Representation

The Arven River is a connected chain of native `water` hexes with river-edge data. Dalen, Novar, and Eren are traversable urban crossing hexes. North Pass and Central Link are clear crossing hexes embedded in the river chain and connected to road paths. Atlatl has no separate bridge terrain type.

All 62 road segments are native `path` objects with `type: "road"`, and every segment joins adjacent hexes. Central Link is separated from both neighboring cities by water:

| North-to-south sequence | Hex | Terrain |
| --- | --- | --- |
| Dalen | `hex-5-3` | Urban crossing |
| Intervening river hex | `hex-5-4` | Water |
| Central Link Bridge | `hex-5-5` | Clear crossing |
| Intervening river hex | `hex-5-6` | Water |
| Novar | `hex-5-7` | Urban crossing |

This spacing prevents a unit on Central Link from attacking either city directly from the bridge hex.

## Editing and Synchronization

Load [ordan_basin_ao.map.json](ordan_basin_ao.map.json) in [`browser/map-editor.html`](../../../browser/map-editor.html) using **Load JSON**. Use [`browser/unit-placement.html`](../../../browser/unit-placement.html) only for deployment editing or variant authoring.

The map JSON is the geographic source of truth. The manifest summarizes it, and the visual maps depict it. The completed [scenario](../game/race_for_the_ordan_basin.scn) embeds the same geography while adding units, default positions, neutral city ownership, duration, and scoring. When map geography or visibility changes, synchronize only the corresponding map fields into the `.scn` so scenario-specific runtime state remains intact.

For formations and command relationships, use the [order of battle](../game/order_of_battle.md). For design intent and abstractions, use the [scenario specification](../ordan_basin_scenario.md).
