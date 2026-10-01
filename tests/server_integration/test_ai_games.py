"""Seeded bounded agent/engine episodes; these do not measure playing strength."""

import pytest
from tests.support.ai_contract import ALIASES
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.protocol, pytest.mark.integration]


@pytest.mark.parametrize("alias", ALIASES)
def test_seeded_game_against_passive(alias, tmp_path):
    result = run_python(f'''
import random
from tests.support.imports import server_imports
from tests.support.ai_contract import construct, scenario, send, apply_reply
with server_imports():
    from game import Game
    random.seed(1729)
    params = scenario()
    game = Game(params)
    agents = {{"blue": construct({alias!r}, "blue", params), "red": construct("passive", "red", params)}}
    state = game.initial_state()
    for step in range(32):
        role = game.on_move(state)
        reply = None
        for faction, agent in agents.items():
            response = send(agent, "observation", observation=game.observation(state, faction))
            if faction == role:
                reply = response
            else:
                assert response is None
        if game.is_terminal(state):
            assert reply is None
            break
        try:
            state = apply_reply(game, state, reply)
        except Exception:
            print("seed=1729 state=", state, "reply=", reply)
            raise
    else:
        raise AssertionError("episode exceeded 32 actions; seed=1729 state=" + repr(state))
    assert state["status"]["phaseCount"] == 4
    print("terminated", step)
''', cwd=tmp_path, timeout=20)
    assert "terminated" in result.stdout
