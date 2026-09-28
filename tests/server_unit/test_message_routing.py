"""Routing units and a bounded child-process check of transport loop ownership."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.support.async_helpers import owned_tasks
from tests.support.doubles import RecordingClient, WebSocketDouble
from tests.support.imports import import_server
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.core, pytest.mark.unit, pytest.mark.protocol]


@pytest.fixture
def transport(engine_imports, monkeypatch):
    module = import_server("messageserver")
    monkeypatch.setattr(module.ClientWrapper, "next_id", 0)
    monkeypatch.setattr(module, "SLEEP_TIME", 0.0)
    return module


@pytest.mark.asyncio
@pytest.mark.parametrize("operation, recipients", [("send", [1]), ("broadcast", [0, 1, 2]), ("relay", [0, 2])])
async def test_exact_routing(transport, operation, recipients):
    # Bypass only the constructor's loop installation, not any routing method.
    server = transport.MessageServer.__new__(transport.MessageServer)
    sockets = [WebSocketDouble() for _ in range(3)]
    server.clients = [transport.ClientWrapper("websocket", socket) for socket in sockets]
    server.verbose = True
    payload = {"type": "parameters", "data": [1, {"x": "λ"}]}
    args = (payload,) if operation == "broadcast" else (payload, server.clients[1])
    await getattr(server, operation)(*args)
    assert [socket.sent for socket in sockets] == [
        [json.dumps(payload)] if index in recipients else [] for index in range(3)]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["broadcast", "relay"])
async def test_empty_routing(transport, operation):
    server = transport.MessageServer.__new__(transport.MessageServer)
    server.clients, server.verbose = [], False
    await getattr(server, operation)({}, *([] if operation == "broadcast" else [object()]))


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["clean", "malformed", "exceptional"])
async def test_socket_registration_parse_and_disconnect_characterization(transport, ending, capsys):
    events = []
    server = SimpleNamespace(clients=[])

    class Socket(WebSocketDouble):
        async def __anext__(self):
            try:
                return await super().__anext__()
            except StopAsyncIteration:
                if ending == "exceptional":
                    raise ConnectionError("peer disconnected")
                raise

    incoming = [json.dumps({"type": "role-request", "role": "blue"})]
    if ending == "malformed":
        incoming.append("{bad")
    socket = Socket(incoming)

    async def connected(client, actual_server):
        assert actual_server is server
        assert server.clients == [client]
        assert client.client is socket
        events.append("connected")
        await client.send_to_client({"type": "parameters"})

    async def message(payload, client, actual_server):
        assert actual_server is server and client is server.clients[0]
        events.append(payload)

    serve = transport.serve_function_factory(message, connected, server, verbose=True)
    if ending == "clean":
        await serve(socket)
    elif ending == "malformed":
        with pytest.raises(json.JSONDecodeError):
            await serve(socket)
    else:
        with pytest.raises(ConnectionError, match="peer disconnected"):
            await serve(socket)
    assert events == ["connected", {"type": "role-request", "role": "blue"}]
    assert socket.sent == [json.dumps({"type": "parameters"})]
    assert transport.SLEEP_TIME == 0.01
    assert len(server.clients) == 1  # K08: disconnect does not deregister.
    await socket.close()
    with pytest.raises(RuntimeError, match="WebSocket double is closed"):
        await server.clients[0].send_to_client({})
    assert capsys.readouterr().out.startswith('0->S {"type": "role-request"')


@pytest.mark.asyncio
async def test_function_processing_initial_parameters_fifo_and_cancellation(transport):
    events = []
    ready, release, drained = asyncio.Event(), asyncio.Event(), asyncio.Event()
    client = RecordingClient([{"sequence": 2}])
    wrapper = transport.ClientWrapper("function", client)
    wrapper.send_to_server({"sequence": 1})
    server = object()

    async def connected(actual, actual_server):
        assert actual is wrapper and actual_server is server
        events.append("connected")
        await actual.send_to_client({"type": "parameters"})

    async def message(payload, actual, actual_server):
        assert actual is wrapper and actual_server is server
        events.append(payload)
        if payload == {"sequence": 1}:
            ready.set()
            await release.wait()
        if payload == {"sequence": 3}:
            drained.set()

    async with owned_tasks() as start:
        task = start(transport.process_function_client(wrapper, message, connected, server, True))
        await asyncio.wait_for(ready.wait(), 2)
        client.response_fn({"sequence": 3})
        release.set()
        await asyncio.wait_for(drained.wait(), 2)
        assert events == ["connected", {"sequence": 1}, {"sequence": 2}, {"sequence": 3}]
        assert wrapper.from_client == []
        assert not task.done()
    assert task.cancelled()


@pytest.mark.parametrize("open_socket", [False, True])
def test_constructor_and_run_own_loop_in_child(tmp_path, open_socket):
    run_python(f'''
import asyncio
from unittest.mock import patch
from tests.support.imports import server_imports, import_server
with server_imports():
    module = import_server("messageserver")
    previous = asyncio.new_event_loop()
    asyncio.set_event_loop(previous)
    events = []
    class SocketContext:
        async def __aenter__(self):
            events.append("socket-enter")
        async def __aexit__(self, *args):
            events.append("socket-exit")
    def serve(handler, ip, port):
        assert asyncio.get_running_loop() is server.loop
        assert callable(handler) and (ip, port) == ("127.0.0.1", 45678)
        events.append("serve")
        return SocketContext()
    def client(message, response_fn=None):
        return None
    async def connected(wrapper, actual):
        assert actual is server and wrapper.client is client
        events.append("client")
        server.loop.call_soon(server.loop.stop)
    async def message(*args):
        raise AssertionError("No queued messages")
    with patch.object(module.websockets, "serve", serve):
        server = module.MessageServer([client], message, connected,
                                      port=45678, openSocket={open_socket!r}, verbose=True)
        try:
            assert asyncio.get_event_loop() is server.loop
            assert server.loop is not previous and not previous.is_closed()
            assert events == []
            assert len(server.clients) == 1 and server.verbose
            watchdog = server.loop.call_later(2, server.loop.stop)
            server.run()
            watchdog.cancel()
            assert events == (["serve", "socket-enter", "client"] if {open_socket!r} else ["client"])
        finally:
            pending = asyncio.all_tasks(server.loop)
            for task in pending:
                task.cancel()
            server.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            server.loop.run_until_complete(server.loop.shutdown_asyncgens())
            server.loop.close()
            asyncio.set_event_loop(previous)
        assert events[-1] == ("socket-exit" if {open_socket!r} else "client")
        assert asyncio.get_event_loop() is previous
    previous.close()
    asyncio.set_event_loop(None)
''', cwd=tmp_path, timeout=10)
