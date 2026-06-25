# Atlatl Documentation

Atlatl is an ultra-simple Python-based wargame and combat-modeling framework designed for experimentation with artificial intelligence, reinforcement learning, and human-vs-AI tactical play. The project includes a deterministic combat simulation, browser-based interfaces, scenario creation tools, replay tools, and hooks for reinforcement learning workflows, and [Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/index.html) trained agents.

This guide is adapted from a slide deck by [Dr. Chris Darkin](https://nps.edu/faculty-profiles/-/cv/cjdarken), a professor at the Naval Postgradute School, who developed the atlatl simulation. This repo is a fork from his original [atlatl](https://github.com/cjdarken/atlatl-public) simulation.

For installation and quick-start workflows see `README.md` in the repo root.

## Table of Contents

- [Project Overview](#project-overview)
- [Motivation](#motivation)
- [Combat Model](#combat-model)
- [Scoring](#scoring)
- [Software Architecture](#software-architecture)
- [Installation](#installation)
- [Quick Test](#quick-test)
- [Running Atlatl](#running-atlatl)
- [Running Atlatl with a Pre-Existing AI](#running-atlatl-with-a-pre-existing-ai)
- [Creating Scenarios](#creating-scenarios)
- [Stock AIs](#stock-ais)
- [Saving and Replaying Games](#saving-and-replaying-games)
- [AI Message Interface](#ai-message-interface)
- [Writing an AI](#writing-an-ai)
- [Useful Code Patterns](#useful-code-patterns)
- [Reinforcement Learning Support](#reinforcement-learning-support)
- [Troubleshooting](#troubleshooting)
- [Reference Tables](#reference-tables)

## Project Overview

Atlatl provides a simple combat model and surrounding infrastructure for experimenting with AI control of two opposing factions: **blue** and **red**.

Key characteristics:

- The combat model is deterministic and intentionally crude to make experimentation easier.
- Performance is scored using kills, losses, and control of cities.
- Human users can play through a browser-based interface.
- AI agents can control one or both sides.
- Reinforcement learning hooks and several Stable-Baselines3 workflows.
- Browser-based replay tools allow review of AI-vs-AI matches.

The name **Atlatl** comes from an Aztecan word for a simple but highly effective military tool used to increase the power and penetration of a spear or dart.

## Motivation

The project is intended to build experience applying modern AI methods to tactical problems and to explore their strengths and weaknesses.

Example research questions include:

- Can reinforcement learning and game-theoretic algorithms learn basic tactics such as maneuver and fires?
- Which algorithms work best?
- Which parameters make each algorithm perform well?
- How much computation is required?
- Can the algorithms find globally optimal solutions?
- How do AI solutions perform against human players?
- Are learned solutions spatially invariant?
- Do results from simple models transfer to larger Department of Defense simulation environments?

## Combat Model

### Space

Atlatl uses a hexagonal grid. See [this link](https://www.redblobgames.com/grids/hexagons/) for info regarding the use of such tilings

- Unit positions are located at the centers of hexes.
- Hex grids are roughly rectangular, with all columns having the same length.
- Hexes are flat side up.

The project uses three coordinate systems:

| Coordinate Type | Description |
| --- | --- |
| Offset coordinates | The upper-left hex is `(0, 0)`. The top of the second column is `(1, 0)`. The hex below `(0, 0)` is `(0, 1)`. |
| Grid coordinates | Integer coordinates corresponding to position on the plane. The spacing in x and y is not the same. |
| SVG coordinates | Floating-point coordinates used for browser rendering in the SVG element. |

### Time and Turns

- Red and blue take successive turns.
- On its turn, a faction may take one action for each unit.
- Actions are either move or fire/attack.
- Some scenarios include a setup phase that allows the player/AI to arrange their forces to begin anywhere in a specified setup zone.

Important tactical implications:

- Defenders receive an advantage because attackers often must move into range and be shot before they can return fire.
- Artillery currently moves two hexes, so it can potentially “kite” foot-mobile infantry by shooting and moving away.

### Terrain

Hexes are best interpreted as being somewhat less than 10 km across.

| Terrain | Color | Effect |
| --- | --- | --- |
| Clear | White | Good mobility for all unit types. |
| Water | Blue | Impassible for all unit types. |
| Rough | Tan | Slower movement; good defense for infantry. |
| Marsh | Green | Slower movement; poor defense for most unit types. |
| City (Urban) | Gray | Good defense for infantry; may contribute to score if held. |

Roads and rivers are not currently modeled.

### Units

Atlatl includes four unit types:

- Infantry
- Motorized/mechanized infantry ("mechinf")
- Armor ("Tanks")
- Artillery

Key rules:

- All units except infantry are considered motorized and move faster in clear terrain.
- All units have a range of one hex, except artillery, which has a range of two hexes.
- Units are high-echelon entities, roughly Brigade or Brigade Combat Teams (BCTs) in scale.
- Fires attrit targets through a deterministic salvo equation.
- Firepower depends on shooter type, target type, and target terrain.
- When a unit drops below 50% strength, it becomes combat ineffective and is removed from the simulation.

### Model Omissions

The model intentionally omits many combat factors, including:

- Rivers and streams
- Roads and paths
- Engineering
- Minefields
- Fortifications
- Supply
- Non-trivial command and control
- Air support

## Scoring

Scoring is from the perspective of **blue**. Parameters can be adjusted during scenario creation.

Default scoring:

| Event | Score |
| --- | ---: |
| Red strength point killed or made combat ineffective | `+1` |
| Blue strength point killed or made combat ineffective | `-2` |
| City hex controlled per phase | `24 / num_cities` |

Notes:

- Units begin with 100 strength points.
- If a unit drops below 50 strength, it is removed and all remaining strength is counted as lost.
- City hexes start under neither faction’s control.
- City hex control changes only when a unit from the opposing faction enters the city hex.
- Leaving a city hex does not automatically lose control of it.

## Software Architecture

Atlatl includes a Python simulation engine and JavaScript browser clients.

### Python Simulation Engine

The engine can run:

- As a single process for testing.
- As a training environment for machine learning.
- With AI agents in the same process.
- With AI agents communicating through sockets.

### JavaScript GUI

The browser directory includes several HTML tools (all must be served over HTTP — see [Running Atlatl with a Pre-Existing AI](#running-atlatl-with-a-pre-existing-ai)):

| Tool | URL | Purpose |
| --- | --- | --- |
| `play.html` | `http://localhost:8080/play.html` | Human player interface for live games |
| `playback.html` | `http://localhost:8080/playback.html` | Replay viewer for recorded games |
| `map-editor.html` | `http://localhost:8080/map-editor.html` | Terrain and setup-zone editor |
| `unit-placement.html` | `http://localhost:8080/unit-placement.html` | Force placement and scenario export |
| `random-scenario.html` | `http://localhost:8080/random-scenario.html` | Random scenario generation |

All use SVG graphics for crisp, scalable rendering.

### Ports

Two servers run simultaneously during interactive play:

- **Game server** — WebSocket on `ws://localhost:9999`. The browser and external AIs connect here.
- **HTTP server** — `http://localhost:8080`. Serves the browser HTML/JS files.

Both must be running for browser-based play. `main.py` starts both automatically; the manual steps are in [Running Atlatl with a Pre-Existing AI](#running-atlatl-with-a-pre-existing-ai).

### AI Communication

The simulation communicates with AIs using JSON-format messages. These become:

- JavaScript objects in browser code.
- Python dictionaries after JSON parsing in Python AI code.

A concise Game API reference is in `docs/game-api.txt`.

## Installation

Atlatl is written in Python 3.

A recommended development setup includes:

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for environment and package management
- Visual Studio Code
- WSL2 on Windows, optional

After installing [uv](https://docs.astral.sh/uv/), navigate to the repo directory. Then install all dependencies from `pyproject.toml`:

```bash
uv sync
```

Activate the virtual environment:

```bash
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

## Quick Test

From the repo root, run:

```bash
python main.py city-inf-5 --blueAI pass-agg --redAI passive --nReps 1
```

This runs an AI-vs-AI game using the `city-inf-5` scenario generator and prints the final blue score. No browser window is needed because both sides are AIs. If you see a score printed without errors, the setup is working.

## Running Atlatl

General form:

```bash
python server.py <scenario-generator-or-file> <optional-arguments>
```

Scenario files end in `.scn` and are located in the `server/scenarios` subdirectory.

Common optional arguments:

| Argument | Description |
| --- | --- |
| `-v` | Verbose mode; prints message traffic. |
| `--redAI REDAI` | AI name to use for red. Omit for a human websocket player. |
| `--blueAI BLUEAI` | AI name to use for blue. Omit for a human websocket player. |
| `--blueReplay BLUEREPLAY` | Capture blue replay to a file. |
| `--redReplay REDREPLAY` | Capture red replay to a file. |
| `--openSocket` | Allows human players to connect through websocket. |
| `--exitWhenTerminal` | Exit and print score when game completes. |
| `--scenarioSeed SCENARIOSEED` | Random seed for scenario generators. |
| `--scenarioCycle SCENARIOCYCLE` | Number of scenarios to generate. |
| `--nReps NREPS` | Number of runs. |
| `--redNeuralNet REDNEURALNET` | Neural net to use for red AI, if needed. |
| `--blueNeuralNet BLUENEURALNET` | Neural net to use for blue AI, if needed. |

## Running Atlatl with a Pre-Existing AI

> **Shortcut:** `python main.py <scenario> [--redAI NAME] [--blueAI NAME]` (from the repo root) automates the steps below — it opens the HTTP server in a new terminal and prints the URL. The manual steps are here for reference or when you need finer control.

The browser files use ES modules and must be served over HTTP — opening them directly from the filesystem will not work. You will need **two or three terminals**: one for the game server, one for the HTTP server, and (optionally) one for an external AI process.

**Terminal 1 — HTTP server** (run once; leave it running):

Navigate to the `browser/` directory and launch the server:

```bash
cd browser
python -m http.server 8080
```

**Terminal 2 — Game server** (run for each game):

All game commands below run from the **`server` directory** in a separate terminal. Once the game is spawned, open the browser at `http://localhost:8080/play.html`.

### Human vs. AI

To play as blue against a pre-existing AI playing red:

```bash
cd server
python server.py YourScenario.scn --redAI pass-agg --openSocket
```

For example:

```bash
cd server
python server.py test4.scn --redAI pass-agg --openSocket
```

Open `http://localhost:8080/play.html` in a browser and select **Blue**. During the setup phase, place units on the highlighted hexes, then end the phase. Blue moves first; the AI responds automatically on red's turns.

To play as red instead, specify `--blueAI` and select **Red** in the browser.

### Human vs. Human

Start the server with no AI arguments:

```bash
cd server
python server.py YourScenario.scn --openSocket
```

Open `http://localhost:8080/play.html` in one browser tab and select **Blue**. Open it in a second tab and select **Red**.

### Watching AI vs. AI

Run both sides as AIs and write the replay directly into the `browser/` directory:

```bash
cd server
python server.py YourScenario.scn --blueAI pass-agg --redAI pass-agg --nReps 1 --blueReplay ../browser/replay.js
```

After the game completes, open `http://localhost:8080/playback.html` in a browser to step through the game.

### Running an AI as a Separate Process

AIs selected with `--blueAI` / `--redAI` run in-process. Some AI files also support running as a **separate process** that connects over a websocket. Start the server with `--openSocket` but omit that side's AI argument:

```bash
cd server
python server.py YourScenario.scn --openSocket
```

Then, in a third terminal, start the external AI from the `server` directory:

```bash
cd server
python ai/passive.py red
```

### GUI Notes

- For large maps, **Shift + left click** zooms the map out.
- A second **Shift + left click** zooms in at the mouse location.
- Depending on the setup and client state, the phase may need to be ended manually with the **End Phase** button.

## Creating Scenarios

Scenario creation uses browser-based tools.

### Step 1: Create or Edit the Map

Open `http://localhost:8080/map-editor.html` in a browser (requires the HTTP server from [Running Atlatl with a Pre-Existing AI](#running-atlatl-with-a-pre-existing-ai)).

Then:

1. To start from an existing map, copy the existing JSON to the clipboard, click **Load JSON**, and paste it.
2. Otherwise, choose the map width and height.
3. Optionally click **Random** to experiment with map generation.
4. Use the palette on the left to paint terrain and setup zones.
5. Click **Copy JSON to Clipboard**.

Alternatively, open `http://localhost:8080/random-scenario.html` to generate a complete random scenario (map + units) in one step without using the editor.

### Step 2: Place Units

Open `http://localhost:8080/unit-placement.html` in a browser.

Then:

1. Click **Load Map JSON** and paste the map JSON.
2. Create an order-of-battle JSON file in a text editor. Example OoB files are in `docs/` (`oob-*.json`) and `browser/sample-oobs/`.
3. Click **Load OoB JSON** and paste the order of battle.
4. Place units by clicking units and hexes.
5. Set time limits and scoring parameters using the text boxes at the top.
6. Click **Copy Placement JSON to Clipboard**.
7. Paste the result into a scenario file such as:

```text
server/scenarios/yourfilename.scn
```

Existing `.scn` files contain `map` and `unit` fields in the correct format for reuse as maps and orders of battle.

## Stock AIs

Atlatl includes several built-in AIs.

| AI | Description |
| --- | --- |
| `passive` | Does nothing. |
| `shootback` | Does not move, but shoots randomly at targets in range. |
| `random` | Takes a random legal action. |
| `field` | If no targets are in range, moves via a potential field algorithm toward opposing forces and city hexes. |
| `dijkstra` | Similar to `random`, but demonstrates shortest path planning using Dijkstra’s algorithm. |
| `pass-agg` | Hand-built AI that is aggressive when the faction's aggregate strength is stronger and defensive otherwise. Intended for `city-inf-5`. |
| `pass` | Fixed passive posture. |
| `agg` | Fixed aggressive posture. |
| `pass-agg-fp` | Like `pass-agg`, but performs full-ply lookahead for the best team move. |
| `pass-agg-fog` | Like `pass-agg`, but works with fog of war by estimating opposing force density. |
| `burtplus` | Strong hand-built AI against `pass-agg` on `city-inf-5`. |
| `mando-fun-lab3` | Reinforcement learning AI against `pass-agg` on `city-inf-5`. |
| `mcts1k` | Monte Carlo tree search with 1,000 random play-throughs. |
| `mcts10k` | Monte Carlo tree search with 10,000 random play-throughs. |
| `stomp` | Full-ply lookahead to maximize a fictitious differential attrition. |
| `stomp-pp` | Greedy action-selection version of `stomp`. |

Neural AIs (`neural`, `cnn`, `hex12`, `hex13`, `hex14`, `hex16`, etc.) require PyTorch and are not loaded by default. Enable them by setting the `ATLATL_NEURAL` environment variable before running the server:

```bash
ATLATL_NEURAL=1 python server.py ...          # Linux/macOS
$env:ATLATL_NEURAL=1; python server.py ...    # Windows PowerShell
```

Some AIs use false terrain coloring as a debugging aid. This is visible in replay mode through `playback.html`.

### `pass-agg` AI Summary

The `pass-agg` AI:

- Always shoots when possible.
- If stronger than the opponent, it favors movement toward city hexes and opposing forces.
- If weaker, it favors movement toward city hexes only.
- Strength is determined by summing current unit strengths.
- Hexes are scored by distance to the nearest city hex, and when aggressive, also by distance to the nearest opposing force.
- The minimum-score hex is selected.

## Saving and Replaying Games

Pass `--blueReplay` or `--redReplay` with a path to capture a replay. Write directly into the `browser/` directory so it is immediately accessible to the HTTP server:

```bash
python server.py test4.scn --blueAI neural --redAI passive --nReps 3 --blueReplay ../browser/replay.js
```

After the game completes, open `http://localhost:8080/playback.html` in a browser to step through it.

## AI Message Interface

Atlatl sends JSON messages between the server and clients/AIs. A quick-reference version of the message sequence is in `docs/message-sequence.txt`.

### Message Sequence for Blue

```text
parameters <- server
role-request -> server

Repeat:
    observation <- server
    action -> server, if blue is on move and the state is non-terminal

At any time:
    reset-request -> server
    reset <- server

At any time:
    next-game-request -> server
    parameters <- server
    role-request -> server

When on move and emulating a Gym environment:
    gym-pause -> server
```

### Message Types

| Message | Contents |
| --- | --- |
| `parameters` | Map, hexes, edges, unused paths, units, and score parameters. |
| `role-request` | Role requested by a player or AI. |
| `observation` | Units and status, including score, phase, terminal state, and side on move. |
| `action` | Move or fire action. |
| `reset-request` | No content. |
| `next-game` | No content. |
| `gym-pause` | No content. |

### Action Message Formats

Move action:

```json
{
  "type": "action",
  "action": {
    "type": "move",
    "mover": "mover ID",
    "destination": "hex ID"
  }
}
```

Fire action:

```json
{
  "type": "action",
  "action": {
    "type": "fire",
    "source": "shooter ID",
    "target": "target ID"
  }
}
```

### Example Observation Message

```json
{
  "type": "observation",
  "observation": {
    "units": [
      {
        "type": "infantry",
        "faction": "blue",
        "longName": "1/1/1",
        "currentStrength": 100,
        "hex": "hex-0-0",
        "canMove": true,
        "ineffective": false,
        "detected": true
      },
      {
        "type": "infantry",
        "faction": "red",
        "longName": "10/1/5",
        "currentStrength": 100,
        "hex": "hex-0-1",
        "canMove": false,
        "ineffective": false,
        "detected": true
      }
    ],
    "status": {
      "cityOwner": {},
      "score": 0,
      "phaseCount": 0,
      "isTerminal": false,
      "onMove": "blue",
      "setupMode": true
    }
  }
}
```

## Writing an AI

Before writing your own AI, read `server/ai/passive.py` (does nothing — the simplest possible AI) and `server/ai/random_actor.py` (takes a random legal action). These are the shortest complete examples and show the full message-handling pattern.

An Atlatl AI is a Python class named `AI` that lives in a file under `server/ai/`. The minimum interface is:

```python
class AI:
    def __init__(self, role, kwargs={}):
        self.role = role  # "blue" or "red"

    def process(self, message, response_fn=None):
        ...
```

- `process` receives a JSON string from the server and returns a JSON string (or `None` to send no reply).
- Message type (`msgD['type']`) determines the expected response: `"parameters"` → send a `role-request`; `"observation"` → send an `"action"` when on move; terminal observations and `"reset"` → return `None`.
- `response_fn` is used only by specialized AI code that emulates a Gym environment.

### Registering an AI

AIs must be registered in `server/airegistry.py` to be selectable from the command line. Add an import and a registry entry:

```python
import ai.my_ai

ai_registry["my-ai"] = (ai.my_ai.AI, {"option": value})
```

The kwargs dict is passed to `AI.__init__` and allows one class to expose multiple named configurations — for example, `"pass"` and `"agg"` both map to `ai.pass_agg.AI` with different `mode` values.

To add a new AI:

1. Create `server/ai/my_ai.py` with an `AI` class implementing `__init__` and `process`.
2. Add `import ai.my_ai` and a registry entry in `server/airegistry.py`.
3. Reference it by name on the command line: `--blueAI my-ai`.

AI files that import PyTorch or stable-baselines3 must be added under the `if IMPORT_NEURAL:` block in `airegistry.py` so they are not loaded on every startup.

### Handling `parameters` Messages

Create empty map and unit objects:

```python
self.mapData = map.MapData()
self.unitData = unit.UnitData()
```

Extract data from the message:

```python
param = msgD["parameters"]
map.fromPortable(param["map"], self.mapData)
unit.fromPortable(param["units"], self.unitData, self.mapData)
```

Then send a message selecting the requested role.

### Handling `observation` Messages

The observation content is stored in:

```python
obs = message["observation"]
```

Update visible units:

```python
for unitObs in obs["units"]:
    uniqueId = unitObs["faction"] + " " + unitObs["longName"]
    un = self.unitData.unitIndex[uniqueId]
    un.partialObsUpdate(unitObs, self.unitData, self.mapData)
```

## Useful Code Patterns

### `unit.py` Overview

`UnitData`:

```python
unitIndex = {unitId: unitObj}
units() -> [unitObj]
getFaction(faction) -> [unitObj]
```

`Unit` properties and methods:

```python
type
longName
faction
currentStrength
detected
uniqueId
hex
setHex(hex, unit)
remove(unitData)
findMoveTargets(mapData, unitData) -> [hexObj]
findFireTargets(unitData) -> [unitObj]
```

### `map.py` Overview

`MapData` selected properties and methods:

```python
hexIndex = {hexId: hexObject}
hexes() -> [hexObjects]
getCityHexes() -> [cityHexObjects]  # urban/city hexes; gray hexes on the map
getDimensions() -> {width, height}
toString() -> JSON
toPortable() -> {...}
```

`Hex` selected properties:

```python
terrain
x_offset
y_offset
id
```

Useful functions:

```python
getNeighborHexes(hexObj, mapData) -> [neighbors]
directionFrom(hexObjA, hexObjB) -> i
# i is 0 for north through 5 for northwest, if the hexes are neighbors

gridDistance(xA, yA, xB, yB) -> float
# Euclidean distance between hexes A and B
```

### Common Tasks

Get legal actions:

```text
See server/ai/random_actor.py:AI.takeRandomAction()
```

Determine terrain at coordinates `(x, y)`:

```python
mapData.hexIndex[f"hex-{x}-{y}"].terrain
```

Measure shortest air-path distance between two hexes in units of hex width:

```python
map.gridDistance(hA.x_grid, hA.y_grid, hB.x_grid, hB.y_grid)
```

Measure shortest path between two hexes, neglecting terrain, in number of hexes traversed:

```python
map.hexDistance(hA.x_offset, hA.y_offset, hB.x_offset, hB.y_offset)
```

Select an action:

```python
import json

# Move a unit to a hex
action = {
    "type": "action",
    "action": {
        "type": "move",
        "mover": unit.uniqueId,       # e.g. "blue 1/1/1"
        "destination": target_hex.id  # e.g. "hex-3-2"
    }
}
return json.dumps(action)

# Fire at an enemy unit
action = {
    "type": "action",
    "action": {
        "type": "fire",
        "source": unit.uniqueId,        # shooter's uniqueId
        "target": target_unit.uniqueId  # target's uniqueId
    }
}
return json.dumps(action)
```

Iterate over all units:

```python
for unit in unitData.units():
    ...
```

Iterate over all hexes:

```python
for hex in mapData.hexes():
    ...
```

Determine legal move distance from every hex to a given hex:

```text
See server/ai/dijkstra_demo.py:AI.runDijkstra()
```

## Reinforcement Learning Support

Atlatl includes support for reinforcement learning. Included in this repo are workflows through [Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/index.html). If you are new to reinforcement learning environments, the [Gymnasium documentation](https://gymnasium.farama.org/) is the best starting point. An overview of how the Gymnasium interface is implemented in Atlatl is in `docs/gym-interface.txt`.

### Gymnasium Compatibility Layer

Reinforcement learners repeatedly choose actions based on observations from the environment.

Important details:

- Actions may represent an order for a single unit to attack a target unit or move to a target hex.
- The next unit moved is fixed by the scenario.
- This fixed unit order is a limitation of the current Gymnasium compatibility layer.
- Actions are integers from `0` to `18`.
- These represent all target hexes within range two, including the current hex, which acts as a “do nothing” action.
- If dismounted infantry are ordered to move two hexes by a neural net, the move is suppressed and converted to a hold-position order.

### Image-Format Observations

For learning to move an entire faction via an existing AI, observations use 17 image channels matching the map size.

Channels include:

- Can move
- Blue strength
- Red strength
- Unit type features for infantry, mech infantry, armor, and artillery
- Terrain features for clear, water, rough, urban, marsh, and unused
- City hex ownership for blue and red
- Phase value
- Normalized score
- Optional selected-unit image when one unit has been preselected

Implemented in:

```text
observation.py
```

### Recommended Reward

The recommended reward structure assumes blue is being trained.

A simple increment in score can be problematic because attackers are usually fired on first. This can create a punishing reward that causes RL agents to avoid fighting.

Instead, Atlatl uses an engineered reward, or `rewArt`, intended to produce more desirable behavior:

- Default reward is the increment in score scaled by the fraction of original friendly force strength that remains.
- If the score increment is negative, the reward is zero.
- A terminal bonus of 25 points, scaled by remaining strength, is given when the state is terminal.
- The terminal bonus is intended to discourage moving into enemy fires on the final move.
- Set `terminal_bonus` to `0` if this behavior appears to be misbehaving.

Implemented in:

```text
gym_ai_surrogate.py / BoronReWart
```

### Train a Convolutional Policy Network

The file:

```text
server/sbl3/train_cnn_sbl3.py
```

provides an example for training a convolutional policy network using DQN.

Run from the `sbl3` subdirectory.

Notes:

- Network architecture details can be specified through the `net_arch` keyword argument passed to `DQN`.
- Role, opposing AI, and scenario are hardcoded in the training files.
- The trained model is saved automatically to:

```text
sbl3/model_save.zip
```

### Test a Trained CNN Network Against AI

Example from the server directory:

```bash
python server.py city-inf-5 --blueAI hex18dqn --blueNeuralNet sbl3/model_save.zip --redAI passive --nReps 3
```

### Test a Trained CNN Network Against a Human

Start the server:

```bash
python server.py city-inf-5 --blueAI hex18dqn --blueNeuralNet sbl3/model_save.zip --openSocket
```

Then open `http://localhost:8080/play.html` and select **Red**.

### Train an MLP Policy Network

The file:

```text
server/sbl3/train_mlp_sbl3.py
```

provides an example of training a multilayer perceptron policy network using PPO.

Other `server/train_*.py` files demonstrate additional techniques.

Notes:

- Role, opposing AI, and scenario are hardcoded in the Python files.
- After training, the network is saved to:

```text
server/ppo_save.zip
```

### Test a Trained MLP Network Against AI

Example:

```bash
python server.py atomic-city.scn --blueAI neural --blueNeuralNet ppo_save.zip --redAI passive --nReps 3
```

## Troubleshooting

### Browser shows "Not Connected"

The browser must connect over HTTP, not the filesystem. Make sure:

1. The HTTP server is running from the `browser/` directory: `cd browser && python -m http.server 8080`
2. You opened `http://localhost:8080/play.html`, not a `file://` path.
3. The game server is running and listening (`--openSocket` is required for browser connections).

### Browser shows 404

The HTTP server is running from the wrong directory. It must be started from `browser/`, not `server/` or the repo root.

### "Not Connected" persists even with the HTTP server running

The browser connects to the game server WebSocket at `ws://localhost:9999`. If the game server exited (e.g., after `--nReps 1` completed), restart it.

### `ModuleNotFoundError` when starting the server

The virtual environment is not active. Run `uv sync` and then activate:

```bash
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

### Neural AI fails to load

Neural AIs are not imported by default. Set `ATLATL_NEURAL=1` before running (see [Stock AIs](#stock-ais) for the exact syntax).

## Reference Tables

### Firepower Table: Shooter Type vs. Target Type

Values are firepower multipliers based on shooter and target type.

| Shooter \ Target | Infantry | MechInf | Armor | Artillery |
| --- | ---: | ---: | ---: | ---: |
| Infantry | 1.00 | 1.00 | 0.50 | 1.50 |
| MechInf | 0.75 | 1.00 | 1.00 | 1.50 |
| Armor | 0.75 | 0.75 | 1.00 | 1.00 |
| Artillery | 1.00 | 0.75 | 0.50 | 1.50 |

### Firepower Table: Target Type vs. Target Terrain

Values are terrain-based firepower multipliers applied to the target.

| Target \ Terrain | Clear | Rough | Marsh | Urban |
| --- | ---: | ---: | ---: | ---: |
| Infantry | 1.00 | 0.50 | 1.00 | 0.50 |
| MechInf | 1.00 | 1.00 | 2.00 | 1.00 |
| Armor | 1.00 | 1.00 | 2.00 | 1.00 |
| Artillery | 1.00 | 1.00 | 2.00 | 1.00 |

A global modifier of `0.5` is applied to all fires.

### Shooting Example

Armor at 100 strength fires at mechanized infantry at 100 strength standing in marsh.

Calculation:

```text
damage = shooter strength × shooter/target multiplier × terrain multiplier × global multiplier
damage = 100 × 0.75 × 2.0 × 0.5
damage = 75
```

The mechanized infantry unit loses 75 strength points, dropping to 25. Since this is below 50, the unit is destroyed and removed from the simulation.

### Mobility Table

Values are the percentage of turn time required to enter one hex.

| Mover \ Terrain Entered | Clear | Rough | Marsh | Urban |
| --- | ---: | ---: | ---: | ---: |
| Infantry | 100 | 100 | 100 | 100 |
| MechInf | 50 | 100 | 100 | 100 |
| Armor | 50 | 100 | 100 | 100 |
| Artillery | 50 | 100 | N/A | 100 |
