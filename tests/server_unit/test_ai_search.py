"""Finite search oracles; no production model or unbounded rollout budget."""

from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from tests.support.doubles import FiniteGame
from tests.support.ai_contract import construct, scenario, send, MCTS
from tests.support.isolation import KnownDefect
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("initial,expected", [(None, ["left", "low"]), (("right",), ["low"]), (("left", "high"), [])])
def test_uct_sign_initial_state_and_terminal(initial, expected, engine_imports, monkeypatch, rng):
    import mctsearch
    monkeypatch.setattr(mctsearch.psutil, "virtual_memory", lambda: SimpleNamespace(percent=20))
    game = FiniteGame()
    actions = mctsearch.uct_search(game, max_rollouts=80, init_state=initial)
    assert actions == expected
    state = game.initial_state() if initial is None else initial
    for action in actions:
        assert action in game.legal_actions(state)
        state = game.transition(state, action)
    assert game.is_terminal(state)


def test_uct_memory_stop(engine_imports, monkeypatch, capsys):
    import mctsearch
    memory = Mock(return_value=SimpleNamespace(percent=99))
    monkeypatch.setattr(mctsearch.psutil, "virtual_memory", memory)
    assert mctsearch.uct_search(FiniteGame(), max_rollouts=8) == []
    assert memory.call_count == 1
    assert "ending early" in capsys.readouterr().out


@pytest.mark.parametrize("prune", [False, True])
def test_minimax_values(prune, engine_imports, monkeypatch):
    import solver
    game = FiniteGame()
    game.scenarioPo = {}
    monkeypatch.setattr(solver, "statePlusParamHashKey", lambda state, params: state)
    memo = solver.minimax(game, alphaBeta=prune)
    assert memo[()] == 3
    assert memo[("left",)] == 3
    for state, score in game.leaves.items():
        if state in memo:
            assert memo[state] == score


def test_agenda_lifo_and_initial_values(engine_imports):
    import solver
    game = FiniteGame()
    agenda = solver.Agenda()
    for state in [(), ("left",), ("left", "high")]:
        agenda.addState(game, state, -10, 10)
    assert agenda.pop() == (("left", "high"), 5, [], -10, 10)
    assert agenda.pop() == (("left",), float("inf"), ["low", "high"], -10, 10)
    assert agenda.pop() == ((), float("-inf"), ["left", "right"], -10, 10)
    assert agenda.isEmpty()


def test_perfect_game_reconstruction_is_bounded(tmp_path):
    result = run_python('''
from tests.support.imports import server_imports
from tests.support.doubles import FiniteGame
with server_imports():
    import solver
    game = FiniteGame()
    game.scenarioPo = {}
    solver.statePlusParamHashKey = lambda state, params: state
    solver.perfectGame(game, solver.minimax(game))
''', cwd=tmp_path, timeout=10)
    assert "blue left" in result.stdout
    assert "red low" in result.stdout


@pytest.mark.parametrize("alias", MCTS)
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K34: MCTS result never populates actionQueue")
def test_mcts_search_result_is_emitted(alias, engine_globals, monkeypatch, game_factory):
    import ai.mcts as module
    game = game_factory(scenario())
    agent = construct(alias, "blue", game.parameters())
    search = Mock(return_value=[{"type": "pass"}])
    monkeypatch.setattr(module.mctsearch, "uct_search", search)
    monkeypatch.setattr(module.current_game_access, "get_current_game", lambda: game)
    obs = game.observation(game.initial_state(), "blue")
    try:
        reply = send(agent, "observation", observation=obs)
    except IndexError as exc:
        assert str(exc) == "pop from empty list"
        assert agent.im == [{"type": "pass"}]
        assert agent.actionQueue == []
        search.assert_called_once_with(game, merit_const=agent.merit_constant,
                                      max_rollouts=8, init_state=obs, debug=False)
        raise KnownDefect("K34: searched actions stored as im") from exc
    assert reply["action"] == {"type": "pass"}


def test_mcts_existing_queue_fifo_and_off_turn_clear(engine_globals, game_factory):
    game = game_factory(scenario())
    agent = construct("mcts1k", "blue", game.parameters())
    agent.actionQueue = [{"type": "pass"}, {"type": "move"}]
    obs = game.observation(game.initial_state(), "blue")
    assert send(agent, "observation", observation=obs)["action"] == {"type": "pass"}
    obs["status"]["onMove"] = "red"
    assert send(agent, "observation", observation=obs) is None
    assert agent.actionQueue == []


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K34: real MCTS search result is not queued")
def test_mcts_small_real_search(engine_globals, game_factory, monkeypatch, rng):
    import ai.mcts as module
    game = game_factory(scenario())
    monkeypatch.setattr(module.current_game_access, "get_current_game", lambda: game)
    monkeypatch.setattr(module.mctsearch.psutil, "virtual_memory", lambda: SimpleNamespace(percent=10))
    ai = construct("mcts1k", "blue", game.parameters())
    state = game.initial_state()
    try:
        reply = send(ai, "observation", observation=game.observation(state, "blue"))
    except IndexError as exc:
        assert str(exc) == "pop from empty list"
        assert ai.im and ai.actionQueue == []
        for action in ai.im:
            assert action in game.legal_actions(state)
            state = game.transition(state, action)
        raise KnownDefect("K34: real finite search succeeded but queue remains empty") from exc
    assert reply["action"] in game.legal_actions(state)


@pytest.mark.parametrize("prune", [False, True])
def test_minimax_reused_and_terminal_states(prune, engine_imports, monkeypatch):
    import solver
    class Shared(FiniteGame):
        scenarioPo = {}
        def transition(self, state, action):
            assert action in self.legal_actions(state)
            return ("left",) if state == () else ("left", "low")
    monkeypatch.setattr(solver, "statePlusParamHashKey", lambda state, params: state)
    assert solver.minimax(Shared(), alphaBeta=prune)[()] == 3
    terminal = Shared()
    terminal.initial_state = lambda: ("right", "high")
    assert solver.minimax(terminal, alphaBeta=prune) == {("right", "high"): 7}


def test_minimax_prunes_inferior_branch_without_changing_value(engine_imports, monkeypatch):
    import solver
    game = FiniteGame()
    game.scenarioPo = {}
    game.leaves.update({("right", "low"): 8, ("right", "high"): 10})
    monkeypatch.setattr(solver, "statePlusParamHashKey", lambda state, params: state)
    plain = solver.minimax(game, alphaBeta=False)
    pruned = solver.minimax(game, alphaBeta=True)
    assert plain[()] == pruned[()] == 8
    assert ("left", "low") in plain
    assert ("left", "low") not in pruned
