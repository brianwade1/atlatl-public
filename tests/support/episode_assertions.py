"""Independent, literal S02 episode expectations shared across transports."""

from copy import deepcopy
import json

from tests.support.builders import load_fixture


def expected_messages():
    scenario = load_fixture("scenarios/tiny_episode.json")["scenario"]
    messages = [{"type": "parameters", "parameters": deepcopy(scenario)}]
    # Terminal advance switches onMove but returns before refreshing canMove.
    for phase, (blue_hex, red_strength, blue_moves, red_moves) in enumerate([
        ("hex-0-0", 100, True, False), ("hex-0-1", 100, False, True),
        ("hex-0-1", 100, True, False), ("hex-0-1", 50, False, True),
        ("hex-0-1", 50, False, True),
    ]):
        units = deepcopy(scenario["units"])
        units[0].update(hex=blue_hex, canMove=blue_moves, detected=True)
        units[1].update(currentStrength=red_strength, canMove=red_moves, detected=True)
        messages.append({"type": "observation", "observation": {"units": units, "status": {
            "cityOwner": {}, "score": 50 if phase >= 3 else 0, "phaseCount": phase,
            "isTerminal": phase == 4, "onMove": "blue" if phase % 2 == 0 else "red",
            "setupMode": False}}})
    return messages


def read_replay(path):
    """Decode the writer's envelope, NOT JavaScript evaluation (deferred to S13)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "replayData = ["
    assert lines[-1] == "]"
    result = []
    for line in lines[1:-1]:
        assert line.startswith("'") and line.endswith("',")
        result.append(json.loads(line[1:-2]))
    return result
