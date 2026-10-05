"""Wrapper unit boundaries and isolated real Gymnasium checker probes."""

import importlib
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock
import numpy as np
import pytest
from tests.support.isolation import KnownDefect
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.ml]


@pytest.mark.parametrize("module_name", ["gym_interface", "multigym"])
@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("actions19", [False, True])
@pytest.mark.unit
def test_wrapper_args_spaces_reset_step(engine_imports, monkeypatch, module_name, role, actions19):
    obs = np.zeros((3,3,4), dtype=np.float32)
    ai = SimpleNamespace(getNFeatures=Mock(return_value=3), setSubAIs=Mock(),
                         actionMessageDiscrete=Mock(side_effect=[None, {"type":"action", "action":{"type":"pass"}}]),
                         action_result=Mock(return_value=(obs, 7, True, {"score":-3})))
    boundary = SimpleNamespace(init=Mock(), mapDimensionBackdoor=Mock(return_value={"height":3,"width":4}),
                               getGymAI=Mock(return_value=ai), reset=Mock(return_value=obs), addMessageRunLoop=Mock())
    monkeypatch.setitem(sys.modules, "server", boundary)
    module = importlib.import_module(module_name)
    options = {"ai":"gymx2"} if module_name == "gym_interface" else {"subAIs":["pass", "agg", "fog"]}
    env = module.GymEnvironment(role=role, versusAI="opponent", versusNeuralNet="opponent.zip",
                                scenario="fixture.scn", actions19=actions19, scenarioSeed=9, scenarioCycle=2, **options)
    args = boundary.init.call_args.args[0]
    assert getattr(args, role+"AI") == ("gymx2" if module_name == "gym_interface" else "multigym")
    other = "red" if role == "blue" else "blue"
    assert getattr(args, other+"AI") == "opponent"
    assert getattr(args, other+"NeuralNet") == "opponent.zip"
    assert getattr(args, role+"NeuralNet") is None
    assert args.nReps == -1 and not args.exitWhenTerminal and not args.logActions
    assert (args.scenarioSeed, args.scenarioCycle, args.scenario) == (9, 2, "fixture.scn")
    assert module.Args(nReps=22).nReps == -1
    assert env.action_space.n == ((19 if actions19 else 7) if module_name == "gym_interface" else 3)
    assert env.observation_space.shape == ((3,7,4) if module_name == "gym_interface" else (17,3,4))
    assert env.observation_space.dtype == np.float32
    assert (env.observation_space.low == 0).all() and (env.observation_space.high == 1).all()
    if module_name == "multigym":
        ai.setSubAIs.assert_called_once_with(["pass", "agg", "fog"])
        assert json.loads(args.blueSubAIs) == json.loads(args.redSubAIs) == ["pass", "agg", "fog"]
    reset_obs, info = env.reset(seed=17, options={"ignored":True})
    assert reset_obs is obs and info == {}
    first_draw = env.np_random.random()
    env.reset(seed=17)
    assert env.np_random.random() == first_draw
    boundary.reset.assert_called_with()  # seed/options are not forwarded to generator
    assert env.step(0)[1:] == (7, True, False, {"score":-3})
    boundary.addMessageRunLoop.assert_not_called()
    assert env.step(1)[0] is obs
    boundary.addMessageRunLoop.assert_called_once_with({"type":"action", "action":{"type":"pass"}})
    before = boundary.init.call_count
    assert env.close() is env.render() is None
    assert boundary.init.call_count == before


@pytest.mark.integration
@pytest.mark.parametrize("role", ["blue", "red"])
def test_real_tiny_episode(tmp_path, role):
    run_python(f"from tests.support.gym_episode import probe\nprobe({role!r}, 'episode')", cwd=tmp_path, timeout=45)


@pytest.mark.integration
@pytest.mark.parametrize("checker", ["gymnasium", "sb3"])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K45: float64 observations violate float32 Box")
def test_real_library_checker(tmp_path, checker):
    result = run_python(f"from tests.support.gym_episode import probe\nprobe('blue', {checker!r})", cwd=tmp_path, timeout=45)
    if "K45: exact dtype contract violation" in result.stdout:
        raise KnownDefect("K45: real environment checker rejects observation dtype")


@pytest.mark.integration
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K46: signed score cannot fit declared [0,1] Box")
def test_real_signed_score_space(tmp_path):
    result = run_python("from tests.support.gym_episode import probe\nprobe('blue', 'signed')", cwd=tmp_path, timeout=45)
    if "K46: negative score outside Box" in result.stdout:
        raise KnownDefect("K46: negative score channel outside declared space")
