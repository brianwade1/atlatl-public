"""Failure-path consumers for S02 isolation and finite boundary collaborators."""

import asyncio
from copy import deepcopy
import json
import random
from types import SimpleNamespace

import numpy as np
import pytest

from tests.support.async_helpers import installed_loop, owned_tasks
from tests.support.doubles import (RecordingClient, WebSocketDouble, FiniteDispenser,
                                   FiniteGame, ControlledPrediction)
from tests.support.imports import import_server
from tests.support.isolation import isolated_rng, preserve_globals
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.core, pytest.mark.unit]


def test_rng_restores_after_failure(rng):
    python_state, numpy_state = random.getstate(), np.random.get_state()
    samples = []
    for _ in range(2):
        with pytest.raises(RuntimeError, match="deliberate"):
            with isolated_rng(42):
                samples.append((random.random(), np.random.random(3)))
                raise RuntimeError("deliberate")
        assert random.getstate() == python_state
        current = np.random.get_state()
        assert current[0] == numpy_state[0]
        np.testing.assert_array_equal(current[1], numpy_state[1])
        assert current[2:] == numpy_state[2:]
    assert samples[0][0] == samples[1][0]
    np.testing.assert_array_equal(samples[0][1], samples[1][1])


@pytest.mark.parametrize("registry, attribute, key", [
    ("airegistry", "ai_registry", "mcts1k"),
    ("scenario_gen_reg", "scenario_generator_registry", "city-inf-5"),
], ids=["ai-options", "generator-options"])
def test_globals_restore_nested_aliases_on_failure(engine_globals, registry, attribute, key):
    mobility = engine_globals["mobility"]
    module = engine_globals[registry]
    table = mobility.cost
    armor = table["armor"]
    registry_object = getattr(module, attribute)
    options = registry_object[key][1]
    before = deepcopy(options)
    with pytest.raises(AssertionError, match="deliberate"):
        with preserve_globals((mobility, "cost"), (module, attribute)):
            armor["clear"] = -123
            table["mechinf"] = {}
            options["nested"] = {"changed": [1]}
            setattr(module, attribute, {})
            raise AssertionError("deliberate")
    assert mobility.cost is table
    assert table["armor"] is table["mechinf"] is armor
    assert armor["clear"] == 50
    assert getattr(module, attribute) is registry_object
    assert registry_object[key][1] is options
    assert options == before


def test_global_bindings_counters_and_missing_attributes(engine_globals):
    messages = engine_globals["messageserver"]
    current = engine_globals["current_game_access"]
    import ai.gym_ai_surrogate as ai
    original = (messages.SLEEP_TIME, messages.ClientWrapper.next_id, current.server, ai.action_count)
    uninitialized = SimpleNamespace()
    with preserve_globals((messages, "SLEEP_TIME"), (messages.ClientWrapper, "next_id"),
                          (current, "server"), (ai, "action_count"),
                          (uninitialized, "gym_ai")):
        messages.SLEEP_TIME = 99
        messages.ClientWrapper("function", RecordingClient())
        current.server = object()
        ai.action_count = 100
        uninitialized.gym_ai = object()
    assert (messages.SLEEP_TIME, messages.ClientWrapper.next_id, current.server, ai.action_count) == original
    assert not hasattr(uninitialized, "gym_ai")


def test_detection_patch_targets_lookup_site(engine_imports, detection_draws):
    module = import_server("unit")
    detection_draws([0.499, 0.5])
    assert module.random() < 0.5
    assert not module.random() < 0.5
    with pytest.raises(AssertionError, match="sequence exhausted"):
        module.random()


@pytest.mark.asyncio
async def test_finite_clients_with_real_wrapper(engine_globals, protocol_messages):
    wrapper = engine_globals["messageserver"].ClientWrapper
    message = protocol_messages["valid"]["parameters"]
    reply = protocol_messages["valid"]["blue_role"]
    client = RecordingClient([reply])
    function = wrapper("function", client)
    await function.send_to_client(message)
    assert client.received == [message]
    assert function.from_client == [reply]
    client.response_fn({"type": "gym-pause"})
    assert function.from_client[-1] == {"type": "gym-pause"}
    socket = WebSocketDouble([json.dumps(reply)])
    remote = wrapper("websocket", socket)
    await remote.send_to_client(message)
    assert [json.loads(v) for v in socket.sent] == [message]
    assert [json.loads(v) async for v in socket] == [reply]
    assert [v async for v in socket] == []
    await socket.close()
    assert socket.closed


@pytest.mark.asyncio
async def test_owned_tasks_cleanup_when_setup_fails():
    started, cleaned = asyncio.Event(), asyncio.Event()

    async def worker():
        try:
            started.set()
            await asyncio.Future()
        finally:
            cleaned.set()

    with pytest.raises(RuntimeError, match="setup failed"):
        async with owned_tasks() as start:
            task = start(worker())
            await asyncio.wait_for(started.wait(), 2)
            raise RuntimeError("setup failed")
    assert task.cancelled()
    assert cleaned.is_set()


def test_subprocess_loop_globals_and_environment_cleanup(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLATL_MODEL_PATH", "developer-only-model")
    result = run_python('''
import asyncio, os
from tests.support.async_helpers import installed_loop
from tests.support.imports import server_imports, import_server
from tests.support.isolation import preserve_globals
assert 'ATLATL_MODEL_PATH' not in os.environ
assert os.environ['PYTHONHASHSEED'] == '1729'
with installed_loop() as previous:
    try:
        with installed_loop(previous) as owned:
            owned.create_task(asyncio.sleep(100))
            raise ValueError('deliberate')
    except ValueError:
        pass
    assert owned.is_closed()
    assert asyncio.get_event_loop() is previous
assert previous.is_closed()
with server_imports():
    server = import_server('server')
    before = {name: getattr(server, name) for name in ('server', 'gym_ai') if hasattr(server, name)}
    with preserve_globals((server, 'server'), (server, 'gym_ai')):
        server.server = object()
        server.gym_ai = object()
    assert {name: getattr(server, name) for name in ('server', 'gym_ai') if hasattr(server, name)} == before
print('restored')
''', cwd=tmp_path)
    assert result.stdout.strip() == "restored"


@pytest.mark.parametrize("action_index, expected", [(0, 3), (1, -2)], ids=["left-minimum", "right-minimum"])
def test_finite_tree_and_prediction(action_index, expected):
    game = FiniteGame()
    dispenser = FiniteDispenser([game])
    assert dispenser.get_next_game() is game
    with pytest.raises(StopIteration):
        dispenser.get_next_game()
    state = game.initial_state()
    prediction = ControlledPrediction([action_index])
    index, recurrent = prediction.predict(game.observation(state, "blue"), deterministic=True)
    assert recurrent is None
    branch = game.transition(state, game.legal_actions(state)[index])
    scores = [game.score(game.transition(branch, action)) for action in game.legal_actions(branch)]
    assert min(scores) == expected
    assert prediction.calls[0][-1] is True
    with pytest.raises(StopIteration):
        prediction.predict({})
