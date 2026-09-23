# AGENTS.md - Project Instructions

## Overview

Atlatl is a simple, deterministic hex-based wargame and AI experimentation environment. It combines a Python simulation engine (`server/`), a browser-based SVG interface (`browser/`), and a JSON/WebSocket protocol to support human vs human, human vs AI, and AI vs AI play. The combat model is intentionally compact and uses Lanchester-style attrition tables so researchers, students, and agents can focus on tactical decision-making, AI behavior, and reinforcement learning rather than high-fidelity physics.

## Repository layout and references

- `main.py`: repository-root launcher; handles scenario paths and starts the browser server for human players.
- `server/`: simulation engine, scenario loading and generators, AI implementations, Gymnasium interface, and training examples.
- `server/airegistry.py`: AI registration; `server/scenario_gen_reg.py`: scenario generator and packaged-alias registration.
- `browser/`: JavaScript ES modules, SVG interface, map editor, unit placement, and replay viewer.
- `scenarios/`: self-contained authored scenario packages; smaller test scenarios live in `server/scenarios/`.
- `tests/`: Python `unittest` tests.
- Read `README.md` for setup and usage, and `docs/Atlatl_Documentation.md` for detailed game and development guidance.
- Consult `docs/message-sequence.txt`, `docs/game-api.txt`, and `docs/gym-interface.txt` when changing their respective interfaces. Check documentation against the implementation when they disagree.

## Setup and commands

Use Python 3.14 or newer and `uv`. Run these commands from the repository root:

```sh
# Install dependencies from pyproject.toml and uv.lock.
uv sync

# Run the existing automated tests.
uv run python -m unittest discover -s tests

# Run one headless game as a simulation smoke check.
uv run python main.py city-inf-5 --blueAI pass-agg --redAI passive --nReps 1

# Serve browser tools for manual UI checks.
uv run python -m http.server 8080 --directory browser
```

- Prefer `uv run` so commands use the project environment without requiring shell-specific activation.
- Browser ES modules require HTTP; open the served page at `http://localhost:8080/` instead of opening HTML files directly.
- For direct server commands, use the server working directory, for example `uv run --directory server python server.py test4.scn --blueAI pass-agg --redAI passive --nReps 1`.
- Automated game checks must specify both AI sides and a finite `--nReps` value. Omitting an AI selects a human player and the root launcher starts a browser server in a new terminal.
- Keep dependency changes intentional and update `uv.lock` when dependencies change.

## Implementation and compatibility

- Follow nearby code conventions and keep edits focused on the requested behavior. Avoid unrelated reformatting or dependency upgrades.
- Preserve flat-topped hex geometry, deterministic combat, turn and setup sequencing, and Blue-perspective scoring unless the task explicitly changes those rules. Scenario generation and AI choices may still be stochastic.
- When changing JSON/WebSocket messages, replay data, scenario formats, or Gymnasium observations/actions/rewards, check affected producers and consumers and update them together with the relevant documentation.
- Preserve support for generator names, packaged aliases, bare `.scn` filenames, and explicit scenario paths. Bare filenames resolve under `server/scenarios/`; explicit relative paths passed to the root launcher resolve from the caller's working directory.
- Maintain Windows, macOS, and Linux launcher behavior when touching process or path handling. Use portable path operations and avoid developer-specific absolute paths.

## Authored scenarios

- Read `scenarios/README.md` and the affected package's `map/README.md` and `game/README.md` before editing scenario data.
- Keep authored `.scn` files in their package's `game/` directory; preserve stable aliases such as `lydian-republic` and `ordan-basin`.
- `.scn` files contain JSON and are the authoritative runtime state, including the embedded map. The separate map JSON is the editable geographic source; `oob.json` is the reusable, unplaced force list.
- For geography changes, edit the canonical map and synchronize relevant fields into the `.scn`. Preserve units, placements, setup, ownership, duration, and scoring unless the task changes them.
- Keep affected manifests, visual maps, orders of battle, scenario descriptions, and operational orders consistent with the data. Follow each package's regeneration instructions where available.
- Distinguish engine-enforced mechanics from narrative or player-enforced rules; written orders do not automatically add simulation behavior.

## Validation and completion

- Run relevant automated tests for code changes. Add focused regression coverage for changed behavior where useful; documentation-only edits need link and content checks rather than game execution.
- For simulation, AI, or launcher changes, also run a bounded headless game. Existing scenario-loading tests and a smoke game do not cover all combat, UI, or RL behavior.
- For browser changes, exercise the affected page and interaction over HTTP and check the browser console. Verify replay playback when changing replay handling.
- For scenario changes, verify JSON loading, affected aliases or paths, and consistency between runtime data and supporting materials.
- Use fixed seeds when investigating stochastic failures. Do not start lengthy RL training or large experiment batches as routine validation.
- Keep local environments, generated replays, logs, model checkpoints, and scratch outputs out of changes unless explicitly requested. Avoid overwriting checked-in replay examples during tests.
- Update usage or interface documentation when behavior changes. Report what changed, what checks ran, and any failures or checks that could not be performed.
