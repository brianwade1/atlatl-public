"""GameServer state machine with a finite game and inert transport boundary."""

from copy import deepcopy
import signal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from tests.support.doubles import FiniteDispenser, FiniteGame
from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit, pytest.mark.protocol, pytest.mark.asyncio]


@pytest.fixture
def protocol(engine_imports, monkeypatch):
    module = import_server("gameserver")
    events = []

    class Transport:
        def __init__(self, *args):
            self.args = args
            self.run = Mock()

        async def send(self, payload, client):
            events.append((client.id, deepcopy(payload)))

        async def broadcast(self, payload):
            events.append(("all", deepcopy(payload)))

    monkeypatch.setattr(module, "MessageServer", Transport)
    previous_signal = signal.getsignal(signal.SIGINT)
    servers = []

    def build(**options):
        game = FiniteGame()
        game.transition = Mock(wraps=game.transition)
        dispenser = FiniteDispenser([game, FiniteGame(), FiniteGame()])
        server = module.GameServer(dispenser, [], **options)
        servers.append(server)
        clients = [SimpleNamespace(id=index, send_to_client=AsyncMock()) for index in range(3)]
        return SimpleNamespace(module=module, server=server, clients=clients, events=events,
                               handler=module.message_handler_factory(server))

    try:
        yield build
    finally:
        signal.signal(signal.SIGINT, previous_signal)
        for server in servers:
            server.close_logs()
        assert signal.getsignal(signal.SIGINT) == previous_signal


async def assign(p, auto=False):
    for client, role in zip(p.clients, (p.server.first_player_role, p.server.second_player_role)):
        await p.handler({"type": "role-request", "role": role, "auto_next_game": auto}, client, p.server.message_server)


async def send(p, message, index=0):
    await p.handler(message, p.clients[index], p.server.message_server)


async def test_constructor_new_clients_and_handshake_order(protocol):
    p = protocol(ip="127.0.0.2", port=12345, open_socket=True, verbose=True, n_reps=-1)
    gs = p.server
    assert gs.state is p.module.State.ROLE_ASSIGNMENT
    assert gs.game_state == () and gs.reps_done == 0 and gs.auto_next_game
    assert gs.roleToClient == gs.clientIdToRole == {}
    args = gs.message_server.args
    assert args[0] == [] and callable(args[1]) and callable(args[2])
    assert args[3:] == ("127.0.0.2", 12345, True, True)
    for client in p.clients[:2]:
        await args[2](client, gs.message_server)
        client.send_to_client.assert_awaited_once_with(
            {"type": "parameters", "parameters": {"name": "finite-tree"}}, True)
    await send(p, {"type": "role-request", "role": "red"}, 1)
    assert p.events == [] and gs.state is p.module.State.ROLE_ASSIGNMENT
    await send(p, {"type": "role-request", "role": "blue"})
    assert gs.state is p.module.State.FIRST_PLAYER_TURN
    assert p.events == [(0, {"type": "observation", "observation": {"path": [], "role": "blue"}}),
                        (1, {"type": "observation", "observation": {"path": [], "role": "red"}})]
    gs.run()
    gs.message_server.run.assert_called_once_with()


@pytest.mark.parametrize("debug", [None, {}, {"hex-0-0": "red"}], ids=["absent", "empty-characterization", "colors"])
async def test_actions_transition_once_and_observe_both(protocol, debug):
    p = protocol(n_reps=-1)
    await assign(p)
    p.events.clear()
    await send(p, {"type": "action", "action": "left", "debug": debug})
    p.server.game.transition.assert_called_once_with((), "left")
    assert p.server.game_state == ("left",)
    assert p.server.state is p.module.State.SECOND_PLAYER_TURN
    expected = [(i, {"type": "observation", "observation": {"path": ["left"], "role": role},
                     **({"debug": debug} if debug else {})}) for i, role in enumerate(("blue", "red"))]
    assert p.events == expected
    await send(p, {"type": "action", "action": "low"}, 1)
    assert p.server.game.transition.call_count == 2
    assert p.server.game_state == ("left", "low")
    assert p.server.state is p.module.State.GAME_OVER


@pytest.mark.parametrize("state", ["FIRST_PLAYER_TURN", "SECOND_PLAYER_TURN"])
@pytest.mark.parametrize("next_role", ["blue", "red"])
async def test_nonterminal_turn_retention_and_switch(protocol, state, next_role):
    p = protocol()
    await assign(p)
    gs = p.server
    gs.state = getattr(p.module.State, state)
    gs.game.on_move = Mock(return_value=next_role)
    await send(p, {"type": "action", "action": "left"}, state == "SECOND_PLAYER_TURN")
    assert gs.state is (p.module.State.FIRST_PLAYER_TURN if next_role == "blue" else p.module.State.SECOND_PLAYER_TURN)
    gs.game.transition.assert_called_once_with((), "left")


@pytest.mark.parametrize("state, message, index, error, pattern", [
    ("ROLE_ASSIGNMENT", {"type": "action"}, 0, Exception, "Only role requests"),
    ("ROLE_ASSIGNMENT", {"type": "reset-request"}, 0, Exception, "Only role requests"),
    ("ROLE_ASSIGNMENT", {"type": "role-request", "role": "green"}, 0, Exception, "Unknown role green"),
    ("ROLE_ASSIGNMENT", {"type": "role-request"}, 0, KeyError, "role"),
    ("FIRST_PLAYER_TURN", {"type": "action", "action": "left"}, 1, Exception, "Only first player"),
    ("SECOND_PLAYER_TURN", {"type": "action", "action": "low"}, 0, Exception, "Only second player"),
    ("FIRST_PLAYER_TURN", {"type": "unknown"}, 0, Exception, "Only action messages"),
    ("SECOND_PLAYER_TURN", {"type": "role-request", "role": "red"}, 1, Exception, "Only action messages"),
    ("FIRST_PLAYER_TURN", {"type": "action"}, 0, KeyError, "action"),
    ("FIRST_PLAYER_TURN", {"type": "action", "action": "left"}, 2, KeyError, "2"),
    ("GAME_OVER", {"type": "action", "action": "left"}, 0, Exception, "Game is over"),
    ("GAME_OVER", {"type": "unknown"}, 0, Exception, "Game is over"),
    ("ROLE_ASSIGNMENT", {}, 0, KeyError, "type"),
], ids=["early-action", "early-reset", "unknown-role", "missing-role", "wrong-first-client",
        "wrong-second-client", "bad-first-type", "bad-second-type", "missing-action", "unassigned-client",
        "terminal-action", "terminal-type", "missing-type"])
async def test_protocol_rejections(protocol, state, message, index, error, pattern):
    p = protocol()
    if state != "ROLE_ASSIGNMENT":
        await assign(p)
    p.server.state = getattr(p.module.State, state)
    p.events.clear()
    with pytest.raises(error, match=pattern):
        await send(p, message, index)
    assert p.events == [] and p.server.game_state == ()
    p.server.game.transition.assert_not_called()
    assert p.server.state is getattr(p.module.State, state)


async def test_illegal_game_action_propagates_without_observation(protocol):
    p = protocol()
    await assign(p)
    p.events.clear()
    with pytest.raises(ValueError, match="Illegal finite-tree action"):
        await send(p, {"type": "action", "action": "invalid"})
    p.server.game.transition.assert_called_once_with((), "invalid")
    assert p.events == [] and p.server.game_state == ()


@pytest.mark.parametrize("state", ["ROLE_ASSIGNMENT", "FIRST_PLAYER_TURN", "SECOND_PLAYER_TURN", "GAME_OVER"])
async def test_next_game_from_every_state_and_stale_reverse_maps(protocol, state):
    p = protocol()
    await assign(p)
    gs = p.server
    old_game = gs.game
    gs.state = getattr(p.module.State, state)
    gs.game_state = ("left",)
    p.events.clear()
    await send(p, {"type": "next-game-request"}, 2)
    assert gs.game is not old_game and gs.game_state == ()
    assert gs.state is p.module.State.ROLE_ASSIGNMENT
    assert gs.roleToClient == {}
    assert gs.clientIdToRole == {0: "blue", 1: "red"}  # K08
    assert p.events == [("all", {"type": "parameters", "parameters": {"name": "finite-tree"}})]
    await send(p, {"type": "role-request", "role": "blue"})
    assert len(p.events) == 1
    await send(p, {"type": "role-request", "role": "red"}, 1)
    assert [item[0] for item in p.events] == ["all", 0, 1]


@pytest.mark.parametrize("state", ["FIRST_PLAYER_TURN", "SECOND_PLAYER_TURN", "GAME_OVER"])
async def test_reset_observations_precede_broadcast(protocol, state):
    p = protocol()
    await assign(p)
    gs = p.server
    gs.state, gs.game_state, gs.reps_done = getattr(p.module.State, state), ("left",), 4
    old_game = gs.game
    p.events.clear()
    await send(p, {"type": "reset-request"}, 2)
    assert gs.game is old_game and gs.game_state == () and gs.reps_done == 4
    assert gs.state is p.module.State.FIRST_PLAYER_TURN
    assert p.events == [(i, {"type": "observation", "observation": {"path": [], "role": role}})
                        for i, role in enumerate(("blue", "red"))] + [("all", {"type": "reset"})]


@pytest.mark.parametrize("state", ["ROLE_ASSIGNMENT", "FIRST_PLAYER_TURN", "SECOND_PLAYER_TURN", "GAME_OVER"])
async def test_pause_in_every_state_uses_loop_boundary(protocol, monkeypatch, state):
    p = protocol()
    p.server.state = getattr(p.module.State, state)
    loop = Mock()
    monkeypatch.setattr(p.module.asyncio, "get_event_loop", lambda: loop)
    await send(p, {"type": "gym-pause"}, 2)
    loop.stop.assert_called_once_with()
    assert p.server.state is getattr(p.module.State, state) and p.events == []


@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("n_reps", [-1, 0, 1])
@pytest.mark.parametrize("auto", [False, True])
async def test_terminal_repetitions_exit_auto_next_and_score(protocol, monkeypatch, capsys, role, n_reps, auto):
    p = protocol(n_reps=n_reps)
    await assign(p, auto=auto)
    gs = p.server
    old_game = gs.game
    gs.game_state = ("left",)
    gs.state = p.module.State.FIRST_PLAYER_TURN if role == "blue" else p.module.State.SECOND_PLAYER_TURN
    exiting = AsyncMock()
    monkeypatch.setattr(p.module, "do_exit", exiting)
    p.events.clear()
    await send(p, {"type": "action", "action": "low"}, role == "red")
    old_game.transition.assert_called_once_with(("left",), "low")
    assert gs.reps_done == 1
    assert capsys.readouterr().out == ("3\n" if n_reps >= 0 else "")
    assert [item[0] for item in p.events[:2]] == [0, 1]
    assert all(item[1]["observation"]["path"] == ["left", "low"] for item in p.events[:2])
    if n_reps == 1:
        exiting.assert_awaited_once_with(gs)
    else:
        exiting.assert_not_awaited()
    if n_reps == 0 and auto:
        assert gs.game is not old_game and gs.state is p.module.State.ROLE_ASSIGNMENT
        assert p.events[2] == ("all", {"type": "parameters", "parameters": {"name": "finite-tree"}})
    else:
        assert gs.game is old_game and gs.state is p.module.State.GAME_OVER
        assert len(p.events) == 2


async def test_repetition_count_accumulates_across_games(protocol, monkeypatch, capsys):
    p = protocol(n_reps=2)
    exiting = AsyncMock()
    monkeypatch.setattr(p.module, "do_exit", exiting)
    for completed in (1, 2):
        await assign(p, auto=True)
        await send(p, {"type": "action", "action": "left"})
        await send(p, {"type": "action", "action": "low"}, 1)
        assert p.server.reps_done == completed
        assert exiting.await_count == completed - 1
    assert capsys.readouterr().out == "3\n3\n"


async def test_duplicate_roles_and_same_client_characterization(protocol):
    p = protocol()
    await send(p, {"type": "role-request", "role": "blue", "auto_next_game": False})
    await send(p, {"type": "role-request", "role": "blue"}, 2)
    assert p.server.roleToClient == {"blue": p.clients[2]}
    assert p.server.clientIdToRole == {0: "blue", 2: "blue"}
    assert p.server.auto_next_game  # Last request wins, including default True.
    await send(p, {"type": "role-request", "role": "red"}, 2)
    assert p.server.roleToClient == {"blue": p.clients[2], "red": p.clients[2]}
    assert p.server.clientIdToRole == {0: "blue", 2: "red"}
    assert [item[0] for item in p.events] == [2, 2]
    # Superseded client still passes reverse-map authorization.
    await send(p, {"type": "action", "action": "left"})
    assert p.server.game_state == ("left",)


@pytest.mark.parametrize("log_actions", [False, True])
@pytest.mark.parametrize("role", ["blue", "red"])
async def test_action_and_observation_log_routing(protocol, role, log_actions):
    p = protocol(first_player_role="red", second_player_role="blue", log_actions=log_actions)
    await assign(p)
    gs = p.server
    gs.blue_logfile, gs.red_logfile = Mock(), Mock()
    gs.log_blue, gs.log_red = Mock(), Mock()
    gs.state = p.module.State.FIRST_PLAYER_TURN if role == "red" else p.module.State.SECOND_PLAYER_TURN
    action = {"type": "action", "action": "left"}
    await send(p, action, role == "blue")
    for faction, logger in (("blue", gs.log_blue), ("red", gs.log_red)):
        expected = ([action] if log_actions else []) + [
            {"type": "observation", "observation": {"path": ["left"], "role": faction}}]
        assert [call.args[0] for call in logger.call_args_list] == expected


async def test_exit_closes_logs_stops_loop_then_exits(protocol, monkeypatch):
    p = protocol()
    events = []
    monkeypatch.setattr(p.server, "close_logs", lambda: events.append("close"))
    monkeypatch.setattr(p.module.asyncio, "get_running_loop", lambda: SimpleNamespace(stop=lambda: events.append("stop")))

    def exit_process(code):
        events.append(("exit", code))
        raise SystemExit(code)

    monkeypatch.setattr(p.module.sys, "exit", exit_process)
    with pytest.raises(SystemExit) as error:
        await p.module.do_exit(p.server)
    assert error.value.code == 0 and events == ["close", "stop", ("exit", 0)]
