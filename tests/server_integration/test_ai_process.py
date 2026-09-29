"""Import-time AI launcher isolated in children; real URI and exchange bounds."""

import asyncio
import json
import sys

import pytest
import websockets

from tests.support.episode_assertions import expected_messages, read_replay
from tests.support.imports import SERVER_DIR
from tests.support.integration_server import owned_child, read_report, running_server
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.integration, pytest.mark.protocol]


def ai_arguments(uri, *, install_loop):
    path = str(SERVER_DIR / "ai_process.py")
    args = [path, "passive", "red", "--uri", uri]
    if not install_loop:
        return args
    # Compatibility bootstrap only: run the entire real CLI with a pre-existing
    # loop. A separate direct-CLI test exposes the Python 3.14 startup defect.
    source = (
        "import asyncio, runpy, sys\n"
        "loop = asyncio.new_event_loop()\n"
        "asyncio.set_event_loop(loop)\n"
        "sys.argv = " + repr(args) + "\n"
        "try:\n"
        "    runpy.run_path(sys.argv[0], run_name='__main__')\n"
        "finally:\n"
        "    loop.run_until_complete(loop.shutdown_asyncgens())\n"
        "    loop.close()\n"
        "    asyncio.set_event_loop(None)\n"
    )
    return ["-c", source]


def test_unknown_ai_cli_reports_exact_alias(tmp_path):
    with owned_child([str(SERVER_DIR / "ai_process.py"), "s08-unknown-ai", "red",
                      "--uri", "ws://127.0.0.1:1"], tmp_path) as child:
        assert child.wait(timeout=60, expected=None) == 1
        assert "KeyError: 's08-unknown-ai'" in child.stderr_path.read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize("install_loop", [
    pytest.param(False, marks=pytest.mark.xfail(strict=True, raises=KnownDefect,
        reason="K19: ai_process requires an existing event loop on Python 3.14")),
    True,
], ids=["direct-cli", "existing-loop-bootstrap"])
async def test_ai_uri_response_and_no_response_messages(tmp_path, install_loop):
    received, errors = [], []
    completed = asyncio.Event()

    async def peer(socket):
        try:
            messages = expected_messages()
            await socket.send(json.dumps(messages[0]))
            received.append(json.loads(await asyncio.wait_for(socket.recv(), 5)))
            # Each ignored message precedes a response-producing sentinel. Any
            # unexpected response is read instead of the expected red pass.
            for ignored in (messages[1], {"type": "reset"}, messages[-1]):
                await socket.send(json.dumps(ignored))
                await socket.send(json.dumps(messages[2]))
                received.append(json.loads(await asyncio.wait_for(socket.recv(), 5)))
                # A duplicate/unsolicited action must not remain in the stream.
                # This is a bounded absence check, not readiness or a retry.
                with pytest.raises(TimeoutError):
                    await asyncio.wait_for(socket.recv(), 0.1)
            await socket.close()
        except Exception as exc:
            errors.append(repr(exc))
        finally:
            completed.set()

    async with websockets.serve(peer, "127.0.0.1", 0) as server:
        uri = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        with owned_child(ai_arguments(uri, install_loop=install_loop), tmp_path) as child:
            # Waiting in a worker keeps this real server's loop servicing IO.
            code = await asyncio.to_thread(child.wait, timeout=60, expected=None)
            stderr = child.stderr_path.read_text(encoding="utf-8")
            if not install_loop and sys.version_info >= (3, 14) and code == 1:
                if "RuntimeError: There is no current event loop in thread 'MainThread'." in stderr:
                    assert "ConnectionClosed" not in stderr
                    assert received == []
                    raise KnownDefect("K19: direct ai_process exits before connecting")
            await asyncio.wait_for(completed.wait(), 5)
            assert errors == []
            assert received == [{"type": "role-request", "role": "red"},
                                *[{"type": "action", "action": {"type": "pass"}}] * 3]
            # The loop never handles graceful peer closure; characterize it.
            assert code == 1
            assert "websockets.exceptions.ConnectionClosedOK" in stderr
            assert "RuntimeWarning" not in stderr
            assert child.stdout_path.read_text(encoding="utf-8").count("Message received by AI over websocket:") == 7


def test_ai_process_plays_real_server_with_existing_loop(tmp_path):
    with running_server(tmp_path, socket=True, functions=["blue"]) as server:
        uri = f"ws://127.0.0.1:{server.ready()['port']}"
        with owned_child(ai_arguments(uri, install_loop=True), tmp_path, "ai") as ai:
            server.wait()
            assert ai.wait(expected=None) == 1
            assert "websockets.exceptions.ConnectionClosedOK" in ai.stderr_path.read_text(encoding="utf-8")
            assert ai.stdout_path.read_text(encoding="utf-8").count("Message received by AI over websocket:") == 6
    report = read_report(tmp_path)
    assert report["reps_done"] == 1 and report["production_logs_closed"]
    assert report["transcripts"]["blue"] == expected_messages()
    assert read_replay(tmp_path / "red.js") == expected_messages()
