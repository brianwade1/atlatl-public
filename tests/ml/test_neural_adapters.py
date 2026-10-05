"""Model loading/search are controlled boundaries; no training or checkpoints."""

from unittest.mock import Mock
import numpy as np
import pytest
from tests.support.builders import make_scenario, make_state
from tests.support.process_helpers import run_python
from tests.ml.test_gym_surrogate import deliver

pytestmark = [pytest.mark.ml, pytest.mark.unit]


@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("dqn", [False, True])
@pytest.mark.parametrize("doubled", [False, True])
def test_neural_prediction_loader_and_exhausted_movers(engine_imports, monkeypatch, role, dqn, doubled):
    import ai.neural as module
    model = Mock(); model.predict.return_value = (0, None)
    loader = Mock(return_value=model)
    monkeypatch.setattr(module.DQN if dqn else module.PPO, "load", loader)
    ai = module.AI(role, {"dqn":dqn, "doubledCoordinates":doubled, "neuralNet":"fixture.zip"})
    loader.assert_called_once_with("fixture.zip")
    scenario = make_scenario(); state = make_state(scenario["units"], on_move=role)
    assert deliver(ai, "parameters", scenario) == {"type":"role-request", "role":role}
    assert deliver(ai, "observation", state) == {"type":"action", "action":{"type":"pass"}}
    actual = model.predict.call_args.args[0]
    expected = np.zeros((3,7 if doubled else 3,4))
    expected[1,0,0] = 1
    expected[2,5 if doubled else 2,3] = 1
    expected[0,0 if role == "blue" else (5 if doubled else 2),0 if role == "blue" else 3] = 1
    np.testing.assert_array_equal(actual, expected)
    assert ai.nextMover() is None
    assert ai.moveMessage() == {"type":"action", "action":{"type":"pass"}}
    assert model.predict.call_count == 1
    state["status"]["isTerminal"] = True
    assert deliver(ai, "observation", state) is None
    deliver(ai, "reset")
    assert ai.attempted_moveD == {} and ai.phaseCount == 0


def test_neural_default_and_required_option(engine_imports, monkeypatch):
    import ai.neural as module
    load = Mock()
    monkeypatch.setattr(module.PPO, "load", load)
    with pytest.raises(KeyError, match="doubledCoordinates"):
        module.AI("blue", {})
    load.assert_called_once_with("model_save.zip")


@pytest.mark.parametrize("index,target", [(1, "move"), (3, "fire")])
def test_neural_prediction_translates_action(engine_imports, monkeypatch, index, target):
    import ai.neural as module
    from game import Game
    from tests.support.builders import make_unit
    model = Mock(); model.predict.return_value = (index, None)
    monkeypatch.setattr(module.PPO, "load", Mock(return_value=model))
    ai = module.AI("blue", {"doubledCoordinates":False})
    scenario = make_scenario(units=[make_unit(hex="hex-1-1"), make_unit(faction="red", hex="hex-2-2", can_move=False)])
    state = make_state(scenario["units"])
    deliver(ai, "parameters", scenario)
    action = deliver(ai, "observation", state)["action"]
    expected = {"type":"move", "mover":"blue A", "destination":"hex-1-0"} if target == "move" else {"type":"fire", "source":"blue A", "target":"red A"}
    assert action == expected
    assert action in Game(scenario).legal_actions(state)


@pytest.mark.parametrize("name,n", [("AITwelve",12), ("AI13",13), ("AI14",14), ("AI18",18)])
def test_neural_feature_variants(engine_imports, monkeypatch, rectangular_game, rectangular_features, name, n):
    import ai.neural as module
    from tests.ml.test_observation_features import expected_channels
    game, state = rectangular_game
    model = Mock(); model.predict.return_value = (0,None)
    monkeypatch.setattr(module.PPO, "load", Mock(return_value=model))
    ai = getattr(module,name)("blue", {"doubledCoordinates":False})
    deliver(ai, "parameters", rectangular_features["scenario"])
    deliver(ai, "observation", state)
    actual = model.predict.call_args.args[0]
    base = expected_channels(game,state)
    mover = np.zeros((3,4)); mover[2,0] = 1
    legal = np.zeros((3,4))
    legal[1,0] = legal[1,1] = legal[2,1] = 1
    short = [mover, legal, *base[1:7], *base[7:11]]
    full = [mover, base[0], legal, *base[1:7], *base[7:11]]
    phase = np.full((3,4), .81)
    expected = {"AITwelve":short, "AI13":short+[phase], "AI14":full+[phase],
                "AI18":[mover,*base[:15],phase,base[16]]}[name]
    assert actual.shape == (n,3,4)
    np.testing.assert_allclose(actual, np.stack(expected))


@pytest.mark.parametrize("adapter", ["ai.dl_alpha_beta", "ai.state_eval_gpu"])
def test_portabletorch_import_boundary_characterization(tmp_path, adapter):
    # Run from a disposable cwd, exactly as the repository's callers may do.
    run_python(f'''\nfrom tests.support.imports import server_imports
with server_imports():
    import importlib
    module = importlib.import_module({adapter!r})
    assert not hasattr(module.portabletorch, 'PortableTorch')
    try:
        if {adapter!r} == 'ai.dl_alpha_beta':
            module.AI('blue', {{'debug':False, 'depthLimit':1, 'neuralNet':'missing.pt'}})
        else:
            module.StateEvalGPUAI('blue', {{'neuralNet':'missing.pt', 'partialPly':False}})
    except AttributeError as exc:
        assert str(exc) == "module 'portabletorch' has no attribute 'PortableTorch'"
    else:
        raise AssertionError('expected missing public loader')
''', cwd=tmp_path, timeout=45)


@pytest.mark.parametrize("adapter", ["dl", "gpu", "azero"])
def test_isolated_model_search_adapters(tmp_path, adapter):
    run_python(f"from tests.support.neural_adapters import probe\nprobe({adapter!r})", cwd=tmp_path, timeout=45)
