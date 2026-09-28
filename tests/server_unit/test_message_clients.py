"""Client wire/queue contracts; sockets are controlled boundaries."""

import json
from unittest.mock import AsyncMock

import pytest

from tests.support.doubles import RecordingClient
from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit, pytest.mark.protocol]


@pytest.fixture
def transport(engine_imports, monkeypatch):
    module = import_server("messageserver")
    monkeypatch.setattr(module.ClientWrapper, "next_id", 0)
    monkeypatch.setattr(module, "SLEEP_TIME", 0.0)
    return module


def test_unique_ids_and_independent_queues(transport):
    clients = [transport.ClientWrapper("function", RecordingClient()) for _ in range(3)]
    assert [client.id for client in clients] == [0, 1, 2]
    clients[0].send_to_server({"sequence": 1})
    assert [client.from_client for client in clients] == [[{"sequence": 1}], [], []]


@pytest.mark.asyncio
async def test_function_return_callback_and_fifo(transport):
    client = RecordingClient([{"reply": 1}, None, {"reply": 3}])
    wrapper = transport.ClientWrapper("function", client)
    payload = {"type": "parameters", "nested": {"name": "O'Brien λ", "values": [1, None]}}
    await wrapper.send_to_client(payload)
    client.response_fn({"callback": 2})
    await wrapper.send_to_client({"type": "observation"})
    await wrapper.send_to_client({"type": "reset"})
    assert client.received == [payload, {"type": "observation"}, {"type": "reset"}]
    assert wrapper.from_client == [{"reply": 1}, {"callback": 2}, {"reply": 3}]


@pytest.mark.asyncio
async def test_websocket_send_is_awaited_and_serialized_once(transport):
    socket = AsyncMock()
    wrapper = transport.ClientWrapper("websocket", socket)
    payload = {"type": "observation", "text": "\\\"\nλ"}
    await wrapper.send_to_client(payload)
    socket.send.assert_awaited_once_with(json.dumps(payload))
    assert json.loads(socket.send.call_args.args[0]) == payload
    assert wrapper.from_client == []


@pytest.mark.parametrize("payload", [None, [], "{}", 1, True], ids=["none", "list", "string", "int", "bool"])
def test_callback_rejects_non_dictionary(transport, payload):
    wrapper = transport.ClientWrapper("function", RecordingClient())
    with pytest.raises(Exception, match="send_to_server message_O argument must be dict"):
        wrapper.send_to_server(payload)
    assert wrapper.from_client == []


@pytest.mark.asyncio
async def test_malformed_function_return_propagates(transport):
    wrapper = transport.ClientWrapper("function", lambda message, response_fn: "{bad")
    with pytest.raises(json.JSONDecodeError):
        await wrapper.send_to_client({"type": "parameters"})
    assert wrapper.from_client == []


@pytest.mark.asyncio
@pytest.mark.parametrize("reply, expected", [("", []), ("null", [None]), ("[]", [[]])], ids=["empty", "null", "array"])
async def test_return_payload_validation_characterization(transport, reply, expected):
    wrapper = transport.ClientWrapper("function", lambda message, response_fn: reply)
    await wrapper.send_to_client({})
    assert wrapper.from_client == expected


@pytest.mark.asyncio
async def test_verbose_output_truncates_wire_text(transport, capsys):
    wrapper = transport.ClientWrapper("websocket", AsyncMock())
    payload = {"text": "x" * 150}
    await wrapper.send_to_client(payload, verbose=True)
    assert capsys.readouterr().out == f"S->0 {json.dumps(payload)[:100]}\n"
