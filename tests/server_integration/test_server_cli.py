"""Actual CLI entry points in bounded, test-owned working directories."""

import json

import pytest

from tests.support.builders import load_fixture
from tests.support.episode_assertions import read_replay
from tests.support.imports import SERVER_DIR, import_server
from tests.support.integration_server import owned_child

pytestmark = [pytest.mark.integration, pytest.mark.protocol]


@pytest.mark.parametrize("kind", ["generator", "bare-filename", "explicit-path"])
def test_server_cli_finishes_one_headless_game(tmp_path, kind):
    if kind == "generator":
        selection = "clear-inf-5"
        expected_parameters = None
    elif kind == "bare-filename":
        selection = "test4.scn"
        expected_parameters = json.loads((SERVER_DIR / "scenarios" / selection).read_text(encoding="utf-8"))
    else:
        path = tmp_path / "scenario with spaces.scn"
        expected_parameters = load_fixture("scenarios/tiny_episode.json")["scenario"]
        path.write_text(json.dumps(expected_parameters), encoding="utf-8")
        selection = str(path)
    args = [str(SERVER_DIR / "server.py"), selection, "--blueAI", "passive", "--redAI", "passive",
            "--nReps", "1", "--scenarioSeed", "1729", "--blueReplay", str(tmp_path / "blue.js"),
            "--redReplay", str(tmp_path / "red.js")]
    with owned_child(args, tmp_path) as child:
        child.wait(timeout=60)
        assert child.stderr_path.read_text(encoding="utf-8") == ""
        output = child.stdout_path.read_text(encoding="utf-8").splitlines()
    blue, red = [read_replay(tmp_path / f"{role}.js") for role in ("blue", "red")]
    assert blue == red
    assert blue[0]["type"] == "parameters"
    parameters = blue[0]["parameters"]
    if expected_parameters is not None:
        assert parameters == expected_parameters
    else:
        assert len(parameters["map"]["hexes"]) == 25
        assert parameters["score"]["maxPhases"] == 10
    observations = blue[1:]
    assert all(msg["type"] == "observation" for msg in observations)
    assert sum(msg["observation"]["status"]["isTerminal"] for msg in observations) == 1
    terminal = observations[-1]["observation"]
    assert terminal["status"]["phaseCount"] == parameters.get("score", {}).get("maxPhases", 20)
    assert float(output[-1]) == terminal["status"]["score"]
    # Passive clients never change placement or strength, even through setup.
    assert [(u["hex"], u["currentStrength"]) for u in terminal["units"]] == [
        (u["hex"], u["currentStrength"]) for u in parameters["units"]]


@pytest.mark.parametrize("alias", ["lydian-republic", "ordan-basin"])
def test_packaged_alias_remains_a_read_only_real_game_input(engine_imports, alias):
    registry = import_server("scenario_gen_reg")
    constructor, options = registry.scenario_generator_registry[alias]
    dispenser = import_server("game_dispenser").ScenarioGeneratorGameDispenser(constructor(**options))
    game = dispenser.get_next_game()
    assert game.parameters()["units"]
    assert game.on_move(game.initial_state()) == "blue"
    assert not game.is_terminal(game.initial_state())
