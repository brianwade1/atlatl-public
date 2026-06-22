# Atlatl

Atlatl is a deliberately simple hex-based wargame simulation and AI experimentation environment. It combines a Python simulation engine, browser-based SVG tools, built-in AI agents, replay support, and Gymnasium-compatible hooks for reinforcement learning with Stable Baselines 3.

The combat model is deterministic and intentionally compact so researchers and students can experiment with tactical AI behavior without first needing to manage a high-fidelity simulation.

## Key features

- Python simulation engine in `server/`
- Browser SVG interface for human play, map editing, unit placement, random scenario creation, and replay playback
- Human vs human, human vs AI, and AI vs AI play
- JSON message protocol for parameters, observations, actions, reset, next-game, and gym-pause messages
- Built-in AI registry with passive, random, shoot-back, potential-field, Dijkstra demo, MCTS, hand-built, neural, and Gymnasium-surrogate agents
- Scenario files plus random scenario generators such as `city-inf-5`, `fog-inf-7`, and `hierarchy-inf-10`
- Replay capture through `--blueReplay` and `--redReplay`
- Gymnasium-compatible surrogate AI for reinforcement learning workflows
- Stable Baselines 3 training examples under `server/sbl3/`
- Exact hexagonal convolution support through `hexagdly`

## Model overview

- Space is a flat-topped hex grid with offset, grid, and SVG coordinate representations.
- Blue and red alternate turns. On a turn, a faction may move or shoot with each unit.
- Some scenarios include a setup phase that lets units start inside marked setup zones.
- Terrain includes clear, water, rough, marsh, and city hexes.
- Unit types include infantry, mechanized infantry, armor, and artillery.
- Most units fire one hex; artillery fires two hexes.
- Combat uses deterministic Lanchester-style attrition tables from `server/combat.py`.
- Units start at 100 strength and are removed once they drop below 50 strength.
- Scoring is from blue's perspective and is based on red losses, blue losses, and city control.

The model omits many real-world factors such as roads, rivers, supply, engineering, minefields, fortifications, air support, and non-trivial command and control.

## Requirements

- Python 3.14 or newer
- `uv`
- Dependencies declared in `pyproject.toml`

## Installation

After installing [uv](https://docs.astral.sh/uv/), navigate to the repo directory and install all dependencies:

```bash
uv sync
```

Activate the virtual environment:

```bash
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

## Directory layout

- `server/` - simulation engine, game server, scenarios, AI registry, AI implementations, Gymnasium interface, training examples
- `browser/` - browser GUI, map editor, unit placement tool, random scenario tool, replay viewer
- `docs/` - repo guide, protocol notes, Gymnasium notes, order-of-battle examples

## Running the server

From the `server/` directory with the virtual environment active:

```bash
python server.py <scenario> [--redAI NAME] [--blueAI NAME] [--openSocket] [--nReps N]
```

Or from the repository root using `uv run`:

```bash
uv run --directory server python server.py <scenario> [--redAI NAME] [--blueAI NAME] [--openSocket] [--nReps N]
```

`<scenario>` is either a scenario generator name or a `.scn` file in `server/scenarios/`.

Useful options:

- `-v` prints message traffic.
- `--redAI` and `--blueAI` select agents from `server/airegistry.py`; omit an AI to let that side connect through the browser.
- `--openSocket` opens the websocket for browser or external clients.
- `--nReps N` runs N completed games and then exits. Use `--nReps 1` for a single game.
- `--blueReplay FILE` and `--redReplay FILE` capture replay data.
- `--scenarioSeed` and `--scenarioCycle` control generated scenarios.
- `--redNeuralNet` and `--blueNeuralNet` pass model files to neural AIs.

## Common workflows

### AI vs AI

```bash
uv run --directory server python server.py city-inf-5 --blueAI pass-agg --redAI passive --nReps 1
```

### Human vs AI

Start the game server:

```bash
uv run --directory server python server.py test4.scn --redAI passive --openSocket --nReps 1
```

In a separate terminal, serve the browser UI from the `browser/` directory:

```bash
cd browser
python -m http.server 8080
```

Open `http://localhost:8080/play.html` and choose Blue.

### Human vs human

Start the server:

```bash
uv run --directory server python server.py test4.scn --openSocket --nReps 1
```

Serve the browser UI:

```bash
cd browser
python -m http.server 8080
```

Open `http://localhost:8080/play.html` in two browser tabs. Choose Blue in one tab and Red in the other.

### Capture and replay a game

```bash
uv run --directory server python server.py test4.scn --blueAI pass-agg --redAI passive --nReps 3 --blueReplay ../browser/replay.js
```

The replay is written directly into `browser/`. Serve the browser UI, then open `http://localhost:8080/playback.html`.

### Create a scenario

Serve the browser tools from the `browser/` directory:

```bash
cd browser
python -m http.server 8080
```

Then use:

- `http://localhost:8080/map-editor.html` to create or edit terrain and setup zones.
- `http://localhost:8080/unit-placement.html` to load a map, load an order of battle, place units, and set scoring/time limits.
- `http://localhost:8080/random-scenario.html` to experiment with random scenario generation.

Order-of-battle examples are in `docs/oob-*.json` and `browser/sample-oobs/`. Scenario files live in `server/scenarios/`.

### Train with reinforcement learning

Training examples are under `server/sbl3/`. For example:

```bash
uv run --directory server python sbl3/train_cnn_sbl3.py
```

The Gymnasium compatibility layer treats each learning action as an order for a single unit to move, fire, or hold. The action space maps integer actions to target hexes within range two. Observation and reward details are implemented across `server/gym_interface.py`, `server/ai/gym_ai_surrogate.py`, and `server/observation.py`.

## Browser tools

After serving `browser/` with `python -m http.server 8080`, open:

- `http://localhost:8080/play.html` for interactive play
- `http://localhost:8080/playback.html` for replay playback
- `http://localhost:8080/map-editor.html` for map creation
- `http://localhost:8080/unit-placement.html` for scenario setup and force placement
- `http://localhost:8080/random-scenario.html` for random scenarios

GUI notes:

- Blue moves first.
- Shift-left-click zooms large maps out; a second shift-left-click zooms in at the mouse location.
- A faction's phase ends automatically if all of its units have acted. Otherwise, use the End Phase button.
- Use `--nReps 1` for human games so the server does not immediately advance to a new game after the terminal state.

## Stock AIs

Common AI names from `server/airegistry.py` include:

- `passive` - does nothing
- `random` - takes a random legal action
- `shootback` - does not move, but shoots random targets in range
- `field` - potential-field movement toward opposing forces and cities
- `dijkstra` - random-action AI that demonstrates Dijkstra path planning
- `pass-agg` - hand-built AI that switches between aggressive and defensive behavior based on relative strength
- `mcts1k`, `mcts10k`, `mctsd` - Monte Carlo tree search variants
- `gym`, `gymx2`, `gym12`, `gym13`, `gym14`, `gym16`, `multigym` - Gymnasium surrogate and multi-AI training agents
- `neural`, `cnn`, `hex12`, `hex13`, `hex14`, `hex14dqn` - neural-network-backed agents (require `ATLATL_NEURAL=1`)
- `alphazero`, `dlalphabeta`, `state-eval-gpu` - additional search/neural agents (require `ATLATL_NEURAL=1`)

## Architecture

Atlatl uses a Python game server and a browser or AI client interface. The server sends fixed game parameters, receives a role request, then repeatedly sends observations and accepts actions from the side on move.

Simplified message sequence:

```text
parameters <- server
role-request -> server

repeat:
  observation <- server
  action -> server, when this client is on move and the state is non-terminal
```

Additional message types include `reset-request`, `next-game-request`, `reset`, and `gym-pause`.

Message structures are JSON-compatible Python dictionaries or JavaScript objects. Important top-level message types include:

- `parameters` - map, units, and scoring configuration
- `role-request` - requested role, usually `blue` or `red`
- `observation` - visible units and status such as score, phase, terminal state, setup mode, and side on move
- `action` - move or fire order
- `reset-request` and `next-game-request` - game control messages

See `docs/message-sequence.txt`, `docs/gym-interface.txt`, and `docs/game-api.txt` for more protocol detail.

## Naval Postgraduate School resources

These videos from a Naval Postgraduate School class include information on how to run and use Atlatl:

- https://www.youtube.com/watch?v=HLnkKUH_BUo&list=PLQ9SUax8KoJycFDK6HG5Flm6pwJiRuNCp&index=17
- https://www.youtube.com/watch?v=5LSzOlrMcy4&list=PLQ9SUax8KoJycFDK6HG5Flm6pwJiRuNCp&index=14
- https://www.youtube.com/watch?v=Q6hauBu8VYg&list=PLQ9SUax8KoJycFDK6HG5Flm6pwJiRuNCp&index=15

## Further information

- `docs/ATLATL_REPO_GUIDE.md` - comprehensive guide covering the combat model, installation, running Atlatl, scenario creation, AI development, and reinforcement learning workflows
- `docs/gym-interface.txt` - Gymnasium compatibility notes
- `docs/message-sequence.txt` - client/server message sequence
- `docs/game-api.txt` - game and agent API reference
