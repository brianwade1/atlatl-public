"""Replay envelopes and perspective; JavaScript execution belongs to S13."""

from copy import deepcopy
import json

import pytest

from tests.support.builders import load_fixture, make_map
from tests.support.episode_assertions import expected_messages, read_replay
from tests.support.integration_server import read_report, running_server
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.integration, pytest.mark.protocol]


@pytest.mark.parametrize("log_actions", [False, True])
def test_two_game_replays_have_ordered_parameters_observations_and_optional_actions(tmp_path, log_actions):
    with running_server(tmp_path, functions=["blue", "red"], reps=2, log_actions=log_actions) as child:
        child.wait()
    report = read_report(tmp_path)
    assert report["production_logs_closed"]
    messages = expected_messages()
    expected = messages[:2]
    for action, observation in zip(load_fixture("scenarios/tiny_episode.json")["actions"], messages[2:]):
        if log_actions:
            expected.append({"type": "action", "action": action})
        expected.append(observation)
    for role in ("blue", "red"):
        assert read_replay(tmp_path / f"{role}.js") == expected * 2


@pytest.mark.parametrize("log_actions", [False, True])
def test_fog_replays_use_the_recipient_perspective(tmp_path, log_actions):
    scenario = load_fixture("scenarios/tiny_episode.json")["scenario"]
    scenario["map"] = make_map(rows=7, cols=1)
    scenario["map"]["fogOfWar"] = True
    scenario["units"][1]["hex"] = "hex-0-6"
    with running_server(tmp_path, functions=["blue", "red"], scenario=scenario,
                        actions=[{"type": "pass"}] * 4, log_actions=log_actions) as child:
        child.wait()
    report = read_report(tmp_path)
    assert report["production_logs_closed"]
    for role in ("blue", "red"):
        replay = read_replay(tmp_path / f"{role}.js")
        assert replay[0] == {"type": "parameters", "parameters": scenario}
        observations = [msg for msg in replay if msg["type"] == "observation"]
        assert len(observations) == 5
        expected = [replay[0]]
        for phase, msg in enumerate(observations):
            if log_actions and phase:
                expected.append({"type": "action", "action": {"type": "pass"}})
            expected.append(msg)
        assert replay == expected
        assert report["transcripts"][role] == [replay[0], *observations]
        for phase, msg in enumerate(observations):
            expected_units = deepcopy(scenario["units"])
            for unit in expected_units:
                unit["canMove"] = unit["faction"] == ("blue" if phase in (0, 2) else "red")
                if unit["faction"] != role:
                    unit["hex"] = "fog"
            assert msg["observation"] == {"units": expected_units, "status": {
                "cityOwner": {}, "score": 0, "phaseCount": phase, "isTerminal": phase == 4,
                "onMove": "blue" if phase % 2 == 0 else "red", "setupMode": False}}


@pytest.mark.parametrize("name", [
    pytest.param("O'Brien", marks=pytest.mark.xfail(strict=True, raises=KnownDefect,
        reason="K09: apostrophe terminates the single-quoted replay string")),
    pytest.param(r"A\B", marks=pytest.mark.xfail(strict=True, raises=KnownDefect,
        reason="K09: JavaScript consumes the backslash layer required by JSON")),
    "λ隊",
], ids=["apostrophe", "backslash", "unicode"])
def test_replay_name_has_safe_javascript_string_envelope(tmp_path, name):
    scenario = load_fixture("scenarios/tiny_episode.json")["scenario"]
    scenario["units"][0]["longName"] = name
    with running_server(tmp_path, functions=["blue", "red"], scenario=scenario,
                        actions=[{"type": "pass"}] * 4) as child:
        child.wait()
    assert read_report(tmp_path)["production_logs_closed"]
    for role in ("blue", "red"):
        path = tmp_path / f"{role}.js"
        messages = read_replay(path)
        assert messages[0]["parameters"]["units"][0]["longName"] == name
        assert all(msg["observation"]["units"][0]["longName"] == name for msg in messages[1:])
    # Match only the exact known wrong writer output. This is a lexical
    # envelope check, not a JavaScript interpreter or proof of viewer playback.
    first_line = (tmp_path / "blue.js").read_text(encoding="utf-8").splitlines()[1]
    wrong_line = "'" + json.dumps({"type": "parameters", "parameters": scenario}) + "',"
    if name == "O'Brien" and first_line == wrong_line:
        assert '"longName": "O\'Brien"' in first_line
        raise KnownDefect("K09: literal apostrophe is unescaped in JS single quotes")
    if name == r"A\B" and first_line == wrong_line:
        assert r'"longName": "A\\B"' in first_line
        # JS evaluates \\ to \; the resulting JSON has invalid escape \B.
        with pytest.raises(json.JSONDecodeError, match="Invalid.*escape"):
            json.loads('"A' + chr(92) + 'B"')
        raise KnownDefect("K09: JSON backslash is not escaped for the outer JS string")
    assert name == "λ隊" or first_line != wrong_line
