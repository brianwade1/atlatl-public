"""Real engine/dispenser/protocol/function transport through terminal exit."""

import pytest

from tests.support.episode_assertions import expected_messages, read_replay
from tests.support.integration_server import read_report, running_server

pytestmark = [pytest.mark.integration, pytest.mark.protocol]


@pytest.mark.parametrize("reps", [1, 2], ids=["one-game", "role-reassignment"])
def test_complete_function_games(tmp_path, reps):
    with running_server(tmp_path, functions=["blue", "red"], reps=reps) as child:
        child.wait()
        assert child.stderr_path.read_text(encoding="utf-8") == ""
        assert child.stdout_path.read_text(encoding="utf-8").splitlines() == ["50.0"] * reps
    report = read_report(tmp_path)
    assert report["reps_done"] == reps
    expected = expected_messages() * reps
    for role in ("blue", "red"):
        assert report["transcripts"][role] == expected
        assert read_replay(tmp_path / f"{role}.js") == expected
    assert report["state"] == expected[-1]["observation"]
    # The exact second transcript checks reset phase, units, strength and script.
    assert report["clients"] == 2
