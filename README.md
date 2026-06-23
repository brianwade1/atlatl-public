# Atlatl

Atlatl is a simple hex-based wargame simulation and AI experimentation environment. It combines a Python simulation engine, browser-based SVG tools, built-in AI agents, replay support, and Gymnasium-compatible hooks for reinforcement learning.

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
- Stable-Baselines3 training examples under `server/sbl3/`
- Exact hexagonal convolution support through `hexagdly`

## Model overview

- Space is a flat-topped hex grid.
- Blue and red alternate turns. On a turn, a faction may move or shoot with each unit.
- Some scenarios include a setup phase that lets units start inside marked setup zones.
- Terrain includes clear, water, rough, marsh, and city hexes.
- Unit types include infantry, mechanized infantry, armor, and artillery.
- Most units fire/attack one hex; artillery can fire up to two hexes away.
- Combat uses Lanchester-style attrition tables (deterministic combat tables) from `server/combat.py`.
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

## Quick start

Verify the installation with a one-command AI-vs-AI test (no browser required):

```bash
python main.py city-inf-5 --blueAI pass-agg --redAI passive --nReps 1
```

The server runs one game and prints the final blue score. If you see a number printed without errors, the setup is working.

## Directory layout

- `server/` - simulation engine, game server, scenarios, AI registry, AI implementations, Gymnasium interface, training examples
- `browser/` - browser GUI, map editor, unit placement tool, random scenario tool, replay viewer
- `docs/` - repo guide, protocol notes, Gymnasium notes, order-of-battle (oob) examples

## Running the server

A **scenario** defines the map, units, and starting conditions. It is either a generator name (like `city-inf-5`) or a `.scn` file in `server/scenarios/`.

`main.py` provides a launcher from the repository root. It detects which sides have human players, opens a browser server in a new terminal window automatically, and prints the URL to open:

```bash
python main.py <scenario> [--redAI NAME] [--blueAI NAME] [--nReps N]
```

Omit `--redAI` or `--blueAI` for a human player on that side. The launcher adds `--openSocket` automatically and opens the browser server when a human is involved.

The lower-level equivalent (from the `server/` directory with the virtual environment active):

```bash
python server.py <scenario> [--redAI NAME] [--blueAI NAME] [--openSocket] [--nReps N]
```

Use `server.py` directly when you need fine-grained control — for example, in RL training scripts, when running external AI processes, or when running headless. Use `main.py` as the starting point for human play.

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
python main.py city-inf-5 --blueAI pass-agg --redAI passive --nReps 1
```

### Human vs AI

```bash
python main.py test4.scn --redAI passive --nReps 1
```

`main.py` opens the browser server in a new terminal and prints the URL. Open it and select Blue.

### Human vs human

```bash
python main.py test4.scn --nReps 1
```

Open the printed URL in two browser tabs. Choose Blue in one tab and Red in the other.

### Capture and replay a game

```bash
uv run --directory server python server.py test4.scn --blueAI pass-agg --redAI passive --nReps 3 --blueReplay ../browser/replay.js
```

Serve the browser UI (`cd browser && python -m http.server 8080`), then open `http://localhost:8080/playback.html`. See `docs/Atlatl_Documentation.md` for full replay details.

### Create a scenario

Use the browser tools at `http://localhost:8080/map-editor.html` and `http://localhost:8080/unit-placement.html`. See `docs/Atlatl_Documentation.md` for step-by-step instructions.

### Train with reinforcement learning

```bash
uv run --directory server python sbl3/train_cnn_sbl3.py
```

See `docs/Atlatl_Documentation.md` for the full Gymnasium compatibility overview, observation details, and reward structure.

## Naval Postgraduate School resources

These videos from a Naval Postgraduate School class include information on how to run and use Atlatl:

- https://www.youtube.com/watch?v=HLnkKUH_BUo&list=PLQ9SUax8KoJycFDK6HG5Flm6pwJiRuNCp&index=17
- https://www.youtube.com/watch?v=5LSzOlrMcy4&list=PLQ9SUax8KoJycFDK6HG5Flm6pwJiRuNCp&index=14
- https://www.youtube.com/watch?v=Q6hauBu8VYg&list=PLQ9SUax8KoJycFDK6HG5Flm6pwJiRuNCp&index=15

## Further information

- `docs/Atlatl_Documentation.md` - comprehensive guide covering the combat model, all running options, scenario creation, AI development, RL workflows, and reference tables
- `docs/gym-interface.txt` - Gymnasium compatibility notes
- `docs/message-sequence.txt` - client/server message sequence
- `docs/game-api.txt` - game and agent API reference
