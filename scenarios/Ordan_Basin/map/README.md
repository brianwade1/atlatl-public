# Ordan Basin Area of Operations Maps

This folder contains the operational reference map and native Atlatl map for the **Race for the Ordan Basin** scenario. The maps depict the same fictional geography at different levels of abstraction: the reference map supports planning and mission graphics, while the Atlatl map provides the authoritative hex-based terrain and road network used for play.

## Map Files

| File | Purpose |
| --- | --- |
| `ordan_basin_ao_reference.svg` | Editable, grid-free operational reference map for planning, orders, overlays, and mission graphics |
| `ordan_basin_ao_reference.png` | High-resolution preview of the operational reference map |
| `ordan_basin_ao_atlatl.svg` | Editable visual master of the 12 × 12 native Atlatl hex map |
| `ordan_basin_ao_atlatl.png` | High-resolution preview of the Atlatl map |
| `ordan_basin_ao.map.json` | Map data for Atlatl's map editor or unit-placement tool |

## Relationship Between the Maps

| Operational feature | Atlatl representation |
| --- | --- |
| Approximately 180 × 150 km area of operations | 12 × 12 flat-top, offset-column grid at approximately 15 km per hex |
| Arven River | Connected chain of native `water` hexes running generally north to southwest |
| Saren Heights | `rough` terrain along the northern map edge |
| Mora Hills | `rough` terrain along the southern map edge |
| Wooded areas | Native `marsh` hexes, shown in green |
| Cities and major junctions | Native `urban` hexes, shown in gray |
| Road network | Native `paths` with `type: "road"`; every segment connects adjacent hexes |

The reference map uses the same restrained terrain palette and visual style as the Lydian Republic scenario. It omits the hex grid and coordinate labels, but its terrain, cities, river crossings, and roads correspond to the native Atlatl map.

## Key Hexes

| Location | Hex | Function |
| --- | --- | --- |
| Veyra | 2,6 | Capital and major Blue political objective |
| Dalen | 5,3 | Northern urban crossing and objective |
| Novar | 5,7 | Central urban crossing and principal transportation junction |
| Eren | 4,9 | Southern urban crossing and objective |
| Kasar | 9,2 | Northeastern transportation hub |
| Ruda | 9,6 | Eastern political center and north–south road junction |
| Selin | 9,9 | Southeastern transportation hub |
| North Pass Bridge | 5,1 | Secondary crossing through the Saren Heights |
| Central Link Bridge | 5,5 | Secondary crossing on the diagonal connector between the northern and central routes |

## Central Link Separation

The Central Link Bridge is deliberately separated from both Dalen and Novar by water terrain:

| North-to-south sequence | Hex | Terrain |
| --- | --- | --- |
| Dalen | 5,3 | Urban |
| Intervening river hex | 5,4 | Water |
| Central Link Bridge | 5,5 | Clear crossing |
| Intervening river hex | 5,6 | Water |
| Novar | 5,7 | Urban |

This spacing prevents a unit occupying the Central Link Bridge from attacking either city directly from the bridge hex. Novar and its east–west road have been shifted one hex south to preserve the transportation network.

## Terrain and Road Notes

- **Clear:** Normal open terrain for movement and combat.
- **Rough:** High ground in the Saren Heights and Mora Hills; apply the movement or defensive effects defined by the scenario rules.
- **Marsh:** Green wooded or broken terrain represented with Atlatl's native `marsh` category.
- **Water:** The Arven River is represented by native `water` hexes rather than a visual overlay.
- **Urban:** Cities and major junctions use native `urban` terrain.
- **Roads:** All roads follow valid center-to-center hex connections and are stored as native Atlatl road paths.

The former far-southern **South Pass road and bridge have been removed**. Hex `4,10` is therefore a water hex, and there is no through-road crossing the Arven River in the Mora Hills.

## Using the Map in Atlatl

1. Load `ordan_basin_ao.map.json` in Atlatl's map editor or unit-placement tool.
2. Use the JSON terrain and road data as authoritative for adjudication.
3. Use `ordan_basin_ao_atlatl.svg` or `.png` as the visual reference for hex coordinates.
4. Use `ordan_basin_ao_reference.svg` or `.png` for operational planning products and mission graphics.
