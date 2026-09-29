"""Real TCP/WebSocket integration; each disruptive input owns a fresh server."""

from contextlib import ExitStack
import json

import pytest
from websockets.exceptions import ConnectionClosedError
from websockets.sync.client import connect

from tests.support.builders import load_fixture
from tests.support.episode_assertions import expected_messages, read_replay
from tests.support.integration_server import read_report, running_server

pytestmark = [pytest.mark.integration, pytest.mark.protocol]


def receive(socket):
    return json.loads(socket.recv(timeout=5))


def join(stack, uri, role):
    socket = stack.enter_context(connect(uri, open_timeout=5, close_timeout=2))
    assert receive(socket) == expected_messages()[0]
    socket.send(json.dumps({"type": "role-request", "role": role}))
    return socket


@pytest.mark.parametrize("mixed", [False, True], ids=["two-websockets", "function-and-websocket"])
def test_complete_websocket_game(tmp_path, mixed):
    with running_server(tmp_path, socket=True, functions=["blue"] if mixed else []) as child:
        uri = f"ws://127.0.0.1:{child.ready()['port']}"
        with ExitStack() as stack:
            sockets = {role: join(stack, uri, role) for role in (["red"] if mixed else ["blue", "red"])}
            expected = expected_messages()
            for phase, message in enumerate(expected[1:]):
                for socket in sockets.values():
                    assert receive(socket) == message
                if phase < 4:
                    role = message["observation"]["status"]["onMove"]
                    if role in sockets:
                        sockets[role].send(json.dumps({"type": "action", "action": load_fixture("scenarios/tiny_episode.json")["actions"][phase]}))
            child.wait()
        assert child.stderr_path.read_text(encoding="utf-8") == ""
    report = read_report(tmp_path)
    assert report["reps_done"] == 1
    assert report["state"] == expected[-1]["observation"]
    if mixed:
        assert report["transcripts"]["blue"] == expected
    for role in ("blue", "red"):
        assert read_replay(tmp_path / f"{role}.js") == expected


@pytest.mark.parametrize("fault", ["red-wrong-turn", "blue-wrong-turn", "malformed-json", "disconnect"])
def test_disrupted_socket_retention_characterization(tmp_path, fault):
    with running_server(tmp_path, socket=True) as child:
        uri = f"ws://127.0.0.1:{child.ready()['port']}"
        with ExitStack() as stack:
            blue = join(stack, uri, "blue")
            red = join(stack, uri, "red")
            initial = expected_messages()[1]
            assert receive(blue) == receive(red) == initial
            offender, survivor = red, blue
            if fault == "blue-wrong-turn":
                blue.send(json.dumps({"type": "action", "action": load_fixture("scenarios/tiny_episode.json")["actions"][0]}))
                initial = expected_messages()[2]
                assert receive(blue) == receive(red) == initial
                offender, survivor = blue, red
            if fault == "disconnect":
                red.close()
            else:
                offender.send("{" if fault == "malformed-json" else json.dumps({"type": "action", "action": {"type": "pass"}}))
                with pytest.raises(ConnectionClosedError) as closed:
                    offender.recv(timeout=5)
                assert closed.value.rcvd.code == 1011
            # Pause uses a real protocol message after the close handshake.
            survivor.send(json.dumps({"type": "gym-pause"}))
            child.wait()
        errors = child.stderr_path.read_text(encoding="utf-8")
        assert errors.count("connection handler failed") == (0 if fault == "disconnect" else 1)
        if fault == "red-wrong-turn":
            assert "Only first player should send messages during the first player turn" in errors
        elif fault == "blue-wrong-turn":
            assert "Only second player should send messages during the second player turn" in errors
        elif fault == "malformed-json":
            assert "json.decoder.JSONDecodeError" in errors
        else:
            assert errors == ""
    report = read_report(tmp_path)
    assert report["reps_done"] == 0
    assert report["state"]["status"] == initial["observation"]["status"]
    expected_units = (initial["observation"]["units"] if fault == "blue-wrong-turn" else
                      load_fixture("scenarios/tiny_episode.json")["scenario"]["units"])
    assert report["state"]["units"] == expected_units
    # K08: current server retains closed wrappers and their role mappings.
    assert report["clients"] == 2
    assert sorted(report["roles"].values()) == ["blue", "red"]
