# Lydian Republic Area of Operations Map

This folder contains the machine-readable map, visual previews, and map metadata for the fictional 2030 Defense of the Lydian Republic scenario. This guide is the authoritative reference for the map package, named geography, and geographic editing and synchronization. See the [scenario landing page](../README.md) for player entry points.

## Map framework

- Ground scale: approximately 10 km per hex
- Grid: 20 × 14 hexes
- Operational area: approximately 200 km east–west × 140 km north–south
- Vostian border: east edge
- Lydian capital and Regional Defense Coalition theater-support areas: off-map west
- Major terrain: Drovna Heights, Aradesh Plain, Maren Lowlands, and Arel River

## Named locations

| Location | Hex | Function |
| --- | --- | --- |
| Kirov | `hex-5-3` | Northern Arel crossing and transport hub |
| Belas | `hex-5-7` | Central Arel crossing and operational hinge |
| Velin | `hex-5-11` | Southern Arel crossing and anchor for firm routes through the Maren Lowlands |
| Aradesh | `hex-12-6` | Principal eastern political objective |

## Bridge routes

- **Northwest Bridge:** the road leaves the northern route near `hex-8-3`, crosses between `hex-6-2` and `hex-5-1`, and reaches the north map edge at `hex-3-0` before continuing off-map northwest.
- **Maren Bridge:** the road leaves the southern route near `hex-10-11`, crosses between `hex-6-10` and `hex-5-9`, and connects to the western road at `hex-0-7`.
- No vertical road links Kirov, Belas, and Velin.

## Package contents

- [Map JSON](lydian_republic_ao.map.json): canonical machine-readable source for the map's geometry, terrain, roads, and rivers.
- [Atlatl SVG](lydian_republic_ao_atlatl.svg) and [PNG](lydian_republic_ao_atlatl.png): exact hex-grid preview using native Atlatl terrain categories.
- [Reference SVG](lydian_republic_ao_reference.svg) and [PNG](lydian_republic_ao_reference.png): presentation map showing named regions, cities, roads, the Arel River, the Vostian border, and the Northwest and Maren bridge routes.
- [Map manifest](lydian_republic_ao_manifest.json): grid dimensions, named-location coordinates, terrain counts, bridge metadata, and the Atlatl commit used for the map.

## Editing and synchronization

### Map editing

Load `lydian_republic_ao.map.json` in `browser/map-editor.html` using **Load JSON**.

### Variant authoring

Load the map JSON in `browser/unit-placement.html` using **Load Map JSON**, then load [oob.json](../game/oob.json) if the variant uses the baseline forces. Scenario-specific setup zones and starting locations must be configured or preserved separately.

### Source and derived artifacts

The map JSON is the canonical source for hex geometry, terrain, roads, rivers, and other geographic features. The completed scenario derives its geography from this source but expands the scenario-specific Blue `setup` assignments and adds initial city ownership, units, default starting positions, and scoring. When the map JSON changes, synchronize the geographic fields while preserving the scenario-specific configuration, then review both visual representations for consistency.

The SVG and PNG files are visual products; Atlatl does not load them during play.

> Roads and river edges are native visual overlays in the current Atlatl implementation. Water, marsh, rough, urban, and clear terrain fills provide the playable movement effects. Atlatl has no separate bridge type, so each bridge is represented as a road across an intentionally traversable river-gap edge.

All geography and political entities are fictional and intended for research and educational wargaming.

For normal play, setup, scoring, and deployment instructions, use the [game-file guide](../game/README.md). For formations and command relationships, use the [order of battle](../game/order_of_battle.md).
