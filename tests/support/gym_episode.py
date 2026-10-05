"""Owned real Gym/engine/function-transport episode; no source changes or casts."""

from copy import deepcopy
import asyncio
import random
import signal
import warnings

from tests.support.builders import make_map, make_scenario, make_unit
from tests.support.imports import server_imports


def probe(role, mode):
    with server_imports():
        import numpy as np
        import gym_interface
        import server
        import scenario_gen_reg
        units = [make_unit(hex="hex-0-0"), make_unit(faction="red", hex="hex-3-2")]
        scenario = make_scenario(make_map(terrain_overrides={(3,2):"urban"}), units, max_phases=4,
                                 city_score=10 if mode == "signed" else 0)
        # Register a recording generator to prove reset(seed) does not reseed it.
        calls = []
        draws = []
        random.seed(1729)
        def factory(**kwargs):
            calls.append(dict(kwargs))
            def generate():
                calls.append("generate")
                draws.append(random.random())
                return deepcopy(scenario)
            return generate
        scenario_gen_reg.scenario_generator_registry["s15-fixture"] = (factory, {})
        old_signal = signal.getsignal(signal.SIGINT)
        env = None
        try:
            env = gym_interface.GymEnvironment(role=role, scenario="s15-fixture", scenarioSeed=1729,
                                               ai="gym18" if mode == "signed" else "gym")
            loop = server.server.message_server.loop
            errors = []
            loop.set_exception_handler(lambda loop, ctx: errors.append(str(ctx.get("exception",ctx["message"]))))
            if mode in ("gymnasium", "sb3"):
                if mode == "gymnasium":
                    from gymnasium.utils.env_checker import check_env
                else:
                    from stable_baselines3.common.env_checker import check_env
                with warnings.catch_warnings(record=True):
                    try:
                        check_env(env)
                    except AssertionError as exc:
                        if mode == "gymnasium":
                            assert str(exc) == "The first element returned by `env.reset()` is not within the observation space."
                        else:
                            assert "cannot cast" in str(exc) and "float32" in str(exc) and "float64" in str(exc)
                        actual, _ = env.reset()
                        assert actual.dtype == np.float64
                        assert actual.shape == env.observation_space.shape
                        assert actual.min() >= 0 and actual.max() <= 1
                        assert not env.observation_space.contains(actual)
                        print("K45: exact dtype contract violation")
                return
            for episode in range(2):
                obs, info = env.reset(seed=83)
                assert info == {} and obs.shape == env.observation_space.shape
                assert obs.dtype == np.float64
                assert not env.observation_space.contains(obs)
                if mode == "episode":
                    expected = np.zeros((3,3,4))
                    expected[0,0,0] = int(role == "blue")
                    expected[0,2,3] = int(role == "red")
                    expected[1,0,0] = expected[2,2,3] = 1
                    np.testing.assert_array_equal(obs, expected)
                for step in range(8):
                    obs, reward, terminated, truncated, info = env.step(0)
                    assert obs.shape == env.observation_space.shape and obs.dtype == np.float64
                    assert not truncated and isinstance(terminated, bool)
                    assert np.isfinite(obs).all()
                    if mode == "episode":
                        assert info == {"score":0}
                        assert reward == (25 if terminated else 0)
                    if terminated:
                        break
                else:
                    raise AssertionError("episode exceeded eight steps")
                assert terminated
                if mode == "signed":
                    assert info["score"] < 0
                    assert (obs[17] == info["score"] / 1000).all()
                    if (obs[17] < env.observation_space.low[17]).all():
                        print("K46: negative score outside Box")
                    else:
                        # A corrected space must reach strict XPASS, not fail
                        # while asserting the old defect's lower bound.
                        assert (obs >= env.observation_space.low).all()
                        assert (obs <= env.observation_space.high).all()
            assert calls[0] == {"scenarioSeed":1729}
            assert all(item == "generate" for item in calls[1:])
            assert len(calls) >= 4
            independent_rng = random.Random(1729)
            assert draws == [independent_rng.random() for _ in draws]
            assert len(set(draws)) == len(draws)  # repeated Gym seeds did not restart generator RNG
            assert not errors
        finally:
            if env is not None:
                env.close()
            gs = getattr(server, "server", None)
            if gs is not None:
                loop = gs.message_server.loop
                tasks = asyncio.all_tasks(loop)
                for task in tasks:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
                for name in ("blue_logfile", "red_logfile"):
                    handle = getattr(gs, name, None)
                    if handle is not None and not handle.closed:
                        handle.close()
                assert not asyncio.all_tasks(loop)
                loop.close()
                asyncio.set_event_loop(None)
            signal.signal(signal.SIGINT, old_signal)
