"""Selection adapters and league routing with recording external collaborators."""

import json
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from tests.support.builders import make_scenario, make_state
from tests.support.isolation import KnownDefect
from tests.ml.test_gym_surrogate import deliver, ready

pytestmark = [pytest.mark.ml, pytest.mark.unit]


@pytest.fixture
def multi(ml_registry, monkeypatch):
    import ai.multigym_ai as module
    agents = []
    def constructor(role, kwargs):
        agent = SimpleNamespace(process=Mock(return_value=json.dumps({"type":"action", "action":{"type":"pass"}})))
        agents.append((role, kwargs, agent))
        return agent
    monkeypatch.setitem(module.airegistry.ai_registry, "s15-agent", (constructor, {"depth":2}))
    return module, agents


@pytest.mark.parametrize("role", ["blue", "red"])
def test_subagents_forwarding_selection_and_duplicate_setup(multi, role):
    module, agents = multi
    ai = module.AI(role, {"mode":"training", "subAIs": '["s15-agent"]'})
    ai.setSubAIs(["s15-agent"])
    assert len(ai.subAIs) == 2  # second call appends rather than replaces
    scenario = make_scenario(); state = make_state(scenario["units"], on_move=role)
    ready(ai, scenario, state)
    for registered_role, options, agent in agents:
        assert registered_role == role and options == {"depth":2}
        assert json.loads(agent.process.call_args.args[0]) == {"type":"parameters", "parameters":scenario}
        assert agent.process.call_args.args[1] is None
    assert ai.actionMessageDiscrete(1) == {"type":"action", "action":{"type":"pass"}}
    agents[1][2].process.assert_called_with(ai.last_obs_msg)
    assert agents[0][2].process.call_count == 1  # unselected observations aren't forwarded
    assert ai.observation().shape == (17,3,4)
    assert ai.getNFeatures() == 3  # metadata characterization; wrapper hardcodes 17
    assert ai.action_result()[1:] == (0, False, {"score":0})
    with pytest.raises(IndexError, match="list index out of range"):
        ai.actionMessageDiscrete(2)
    with pytest.raises(TypeError, match="list indices must be integers"):
        ai.actionMessageDiscrete(.5)
    agents[1][2].process.return_value = None
    with pytest.raises(TypeError, match="JSON object must be str"):
        ai.actionMessageDiscrete(-1)


@pytest.mark.parametrize("dqn", [False, True])
def test_production_prediction_and_terminal(multi, monkeypatch, dqn):
    module, agents = multi
    model = Mock(); model.predict.return_value = (0, None)
    loader = Mock(return_value=model)
    monkeypatch.setattr(module.DQN if dqn else module.PPO, "load", loader)
    ai = module.AI("blue", {"mode":"production", "subAIs": '["s15-agent"]', "neuralNet":"fixture.zip", "dqn":dqn})
    loader.assert_called_once_with("fixture.zip")
    scenario = make_scenario(); state = make_state(scenario["units"])
    deliver(ai, "parameters", scenario)
    assert deliver(ai, "observation", state) == {"type":"action", "action":{"type":"pass"}}
    assert model.predict.call_args.args[0].shape == (17,3,4)
    state["status"]["isTerminal"] = True
    assert deliver(ai, "observation", state) is None
    assert model.predict.call_count == 1
    ai.reset()
    assert len(ai.subAIs) == 1 and ai.response_fn is None


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K47: multigym state tensor stays at initial state")
def test_multigym_observation_tracks_current_state(multi):
    module, _ = multi
    ai = module.AI("blue", {"mode":"training", "subAIs":"[]"})
    scenario = make_scenario(); state = make_state(scenario["units"])
    ready(ai, scenario, state)
    before = ai.observation().clone()
    state["units"][0].update(currentStrength=40, hex="hex-1-0")
    state["status"]["score"] = 12
    deliver(ai, "observation", state)
    actual = ai.observation()
    if (actual == before).all() and ai.unitData.unitIndex["blue A"].currentStrength == 40 and ai.last_score == 12:
        raise KnownDefect("K47: updated local units but unchanged initial tensor")
    assert actual[1,0,1] == pytest.approx(.4)
    assert actual[16,0,0] == pytest.approx(.012)


def test_league_selection_forwarding_and_noop_close(engine_imports, monkeypatch):
    import league_env
    envs = [SimpleNamespace(action_space=object(), observation_space=object(), metadata={"name":i}, reward_range=(-i,i),
                            reset=Mock(return_value=(i, {})), step=Mock(return_value=(i,1,False,False,{})), close=Mock(), render=Mock()) for i in range(2)]
    choose = Mock(side_effect=[[envs[1]], [envs[0]]])
    monkeypatch.setattr(league_env.random, "choices", choose)
    league = league_env.LeagueEnvironment(envs, [.2,.8])
    for field in ("action_space", "observation_space", "metadata", "reward_range"):
        assert getattr(league, field) is getattr(envs[0], field)
    with pytest.raises(AttributeError, match="has no attribute 'env'"):
        league.step(0)
    assert league.reset() == (1,{})
    choose.assert_called_with(envs, [.2,.8])
    assert league.step(7) == (1,1,False,False,{})
    envs[1].step.assert_called_once_with(7)
    assert league.reset() == (0,{})
    assert league.close() is league.render() is None
    for env in envs:
        env.close.assert_not_called(); env.render.assert_not_called()


def test_league_empty_and_mismatched_weights(engine_imports):
    from league_env import LeagueEnvironment
    with pytest.raises(IndexError, match="list index out of range"):
        LeagueEnvironment([], [])
    env = SimpleNamespace(action_space=1, observation_space=2, metadata={}, reward_range=(0,1))
    for weights, message in [([1,2], "number of weights"), ([0], "Total of weights must be greater than zero")]:
        league = LeagueEnvironment([env], weights)
        with pytest.raises(ValueError, match=message):
            league.reset()
