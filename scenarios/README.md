# Authored Scenarios

This directory contains complete, fictional scenario packages for Atlatl. Each package combines an engine-readable game with the narrative, maps, orders of battle, player briefings, and authoring sources needed to play, facilitate, study, or modify it.

These authored packages are different from the small scenario files and procedural generators under [`server/`](../server/). They are designed as self-contained operational settings rather than only as test cases for the simulation engine.

> All countries, political events, military organizations, and geographic locations in these packages are fictional. They were invented for wargaming research and education purposes only.

## Available Scenarios

| Scenario | Situation | Forces | Map | Duration | Launcher alias |
| --- | --- | --- | --- | --- | --- |
| [Defense of the Lydian Republic](Lydian_Republic/README.md) | An outnumbered coalition corps defends four objectives against a Vostian field army. | 9 Blue, 12 Red | 20 x 14 hexes | 20 complete turns / 10 days | `lydian-republic` |
| [The Race for the Ordan Basin](Ordan_Basin/README.md) | Western Compact and Karsovian forces enter from opposite sides of the basin and compete for seven initially neutral cities. | 13 Blue, 13 Red | 12 x 12 hexes | 18 complete turns / 9 days | `ordan-basin` |

Both scenarios use open unit information and begin with setup activations: Blue repositions first, Red repositions second, and regular play begins with Blue. See each scenario's landing page and game-file guide for its setup zones, objectives, scoring, and default deployment.

## Quick Start

From the repository root, install the dependencies once:

```bash
uv sync
```

Launch either package by its stable alias:

```bash
python main.py lydian-republic
python main.py ordan-basin
```

The `.scn` files stay in their package directories; they do not need to be copied into `server/scenarios/`.

With no AI options, both sides are human-controlled. The launcher starts a local browser server in a new terminal and prints a URL. Open that URL in two browser tabs, select Blue in one and Red in the other, and leave the launcher and browser-server terminals running during play.

## Other Ways to Run

Run these commands from the repository root. Omit an AI option for whichever side will be human-controlled.

### Human vs. AI

Play Blue against the built-in `pass-agg` Red AI:

```bash
python main.py lydian-republic --redAI pass-agg --nReps 1
```

Play Red against the built-in `pass-agg` Blue AI:

```bash
python main.py ordan-basin --blueAI pass-agg --nReps 1
```

The launcher starts the browser server because a human player is involved. Open the printed URL and select the human side.

### AI vs. AI

Run one complete game without the browser interface:

```bash
python main.py lydian-republic --blueAI pass-agg --redAI pass-agg --nReps 1
python main.py ordan-basin --blueAI pass-agg --redAI pass-agg --nReps 1
```

Use `--nReps N` to run multiple games. AI-controlled sides accept the supplied default deployment unless the selected AI implements setup movement; `pass-agg-setup` is available when automated repositioning is desired.

### Launch by File Path

Aliases are the shortest interface, but the package files can also be launched directly:

```bash
python main.py scenarios/Lydian_Republic/game/defense_of_the_lydian_republic.scn
python main.py scenarios/Ordan_Basin/game/race_for_the_ordan_basin.scn
```

See the [repository README](../README.md#running-the-server) for all launcher options and additional play modes.

## Package Structure

Each authored scenario follows this general structure:

```text
Scenario_Name/
|-- README.md
|-- scenario*.md
|-- road_to_war*.md
|-- game/
|   |-- README.md
|   |-- *.scn
|   |-- oob.json
|   `-- order_of_battle.md
|-- map/
|   |-- README.md
|   |-- *.map.json
|   |-- *_manifest.json
|   |-- *_atlatl.svg and .png
|   `-- *_reference.svg and .png
`-- operations_orders/
    |-- README.md
    |-- Blue/
    |   |-- <unit_orders>.md
    |   |-- blue_master_synchronization_crosswalk.md
    |   `-- Blue_operational_graphics.pdf
    `-- Red/
        |-- <unit_orders>.md
        |-- red_master_synchronization_crosswalk.md
        `-- Red_operational_graphics.pdf
```

The filenames vary slightly between packages, but the roles of the files are consistent.

### Scenario-Level Material

| Material | Purpose |
| --- | --- |
| `README.md` | Scenario landing page, player and optional-controller quick reference, documentation index, and player entry points. |
| `scenario*.md` | Design specification covering intent, scale, forces, abstractions, runtime rules, and development status. |
| `road_to_war*.md` | Shared fictional background and the chronology that leads to the opening situation. |

These documents provide context but are not loaded by the game engine. They are used to guide players in determining their military objectives and desired outcomes of the conflict. Military conflict supports political objectives.

### `game/`

| Material | Purpose |
| --- | --- |
| `*.scn` | The complete playable scenario. It contains the embedded map, units, starting positions, setup state, ownership, duration, and scoring used by the engine. |
| `oob.json` | Reusable placement order of battle. Unit locations are intentionally unset so it can be used to create variants. It is not needed for normal play. |
| `order_of_battle.md` | Human-readable formation strengths, roles, represented capabilities, and command relationships. |
| `README.md` | Authoritative guide to runtime configuration, setup, objectives, scoring, and game-file maintenance. |

The `.scn` file is JSON despite its extension. For normal play, launch it through its alias or path rather than loading the separate map and OOB files. For more realistic wargaming play, players should pay attention to command relationships. In actual combat, units in a given command will operate together. Actual combat is chaotic, so command boundaries help separate forces and assign areas of responsibility.

### `map/`

| Material | Purpose |
| --- | --- |
| `*.map.json` | Canonical editable source for hex geometry, terrain, roads, rivers, and other geographic properties. Some packages also keep setup zones and visibility here. |
| `*_manifest.json` | Summary metadata such as dimensions, named coordinates, terrain counts, bridge data, and source provenance. |
| `*_atlatl.svg` and `*_atlatl.png` | Visual previews using Atlatl's native hex grid and terrain categories. |
| `*_reference.svg` and `*_reference.png` | Presentation and planning maps with named geography and other operational context. |
| `README.md` | Authoritative map guide, including editing and synchronization procedures. |

Atlatl loads map data embedded in the `.scn`; it does not load the SVG or PNG previews during play.

### `operations_orders/`

The `Blue/` and `Red/` directories contain side-specific orders, support orders, master synchronization crosswalks, and operational graphics. Start with the senior headquarters order (whose identifier ends in `-00`) identified by the package's operations-order index, then read the applicable subordinate and fire-support orders. Each side's master synchronization crosswalk provides a consolidated view of how the higher headquarters and subordinate formations execute the operation across each phase.

For opposed play, players should normally read only their assigned side's orders, crosswalks, and operational graphics unless the group agrees to open plans. Controllers and scenario administrators may use both sides' material.

The orders guide player decisions but do not add automated mechanics. Players enforce command relationships, reserve-release authority, operational phases, control measures, fires priorities, weather effects, and reporting requirements. An optional controller may assist under procedures agreed before play. PDF briefing sets are the only published operational graphics.

Remember, no plan survives first contact but to not plan is to plan for failure. The red and blue plans provide a starting point for players, but players should react to the evolving situation and make adjustments to the plan as play evolves. As players make these adjustments, keep in mind the overall political and military objectives as well as the command relationships of the forces they control.

## Recommended Reading by Role

### Player

1. Use the scenario landing page's quick-reference sections, then read the road-to-war document.
2. Review the shared order of battle and reference map.
3. Open only your side's senior order and operational graphics.
4. Follow links to the subordinate or support orders that apply to your formations.
5. Launch the game and complete the Blue-then-Red setup sequence.

### Controller or Facilitator

1. Use the scenario landing page's quick-reference sections, then read the scenario specification and game-file guide.
2. Review both sides' complete order hierarchies and graphics.
3. Use synchronization matrices or crosswalks to track phases, handoffs, decisions, and command requirements.
4. Adjudicate written requirements that the Atlatl engine does not model.

### Scenario Author

1. Treat the map JSON as the geographic source of truth.
2. Treat `oob.json` as the reusable, unplaced force list.
3. Treat the `.scn` as the authoritative runtime state for the completed game.
4. Keep narrative intent and abstractions in the scenario specification and player-enforced behavior in the written orders.
5. Follow the package's `map/README.md` and `game/README.md` when synchronizing changes.

## Editing Maps and Creating Variants

Serve the browser tools from the repository root:

```bash
python -m http.server 8080 --directory browser
```

Then use:

- `http://localhost:8080/map-editor.html` to load and edit the package's `*.map.json` file.
- `http://localhost:8080/unit-placement.html` to load the map and `game/oob.json`, place units, and create a variant.

When geography changes, update the canonical map first and synchronize only the relevant map fields into the completed `.scn`. Preserve scenario-specific units, locations, setup configuration, ownership, duration, and scoring unless the variant deliberately changes them. Regenerate or review the visual map products and manifest so they remain consistent with the machine-readable source.

## Sources of Truth

| Subject | Authoritative source |
| --- | --- |
| Normal playable state | `game/*.scn` |
| Geography and terrain authoring | `map/*.map.json` |
| Reusable unplaced forces | `game/oob.json` |
| Runtime configuration and scoring guidance | `game/README.md` |
| Design intent and abstractions | `scenario*.md` |
| Player-enforced plans and constraints | `operations_orders/` |
| Map summary and visual products | Manifest, SVG, and PNG files derived from the map source |

## Adding a Packaged Scenario

When adding another authored package:

1. Use the structure above and include a complete `.scn`, a scenario landing page with public player/controller reference material, and a game-file guide.
2. Keep editable sources separate from the complete runtime file and document which artifact owns each kind of information.
3. Add a stable launcher alias to [`server/scenario_gen_reg.py`](../server/scenario_gen_reg.py).
4. Add the package to the scenario table in this README.
5. Verify both alias-based and path-based launching, validate relative links, and keep directory-name casing consistent for cross-platform use.

## Further Documentation

- [Atlatl repository guide](../README.md)
- [Comprehensive Atlatl documentation](../docs/Atlatl_Documentation.md)
- [Defense of the Lydian Republic](Lydian_Republic/README.md)
- [The Race for the Ordan Basin](Ordan_Basin/README.md)
