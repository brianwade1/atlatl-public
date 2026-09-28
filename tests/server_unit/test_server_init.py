"""Initialization and import-time gating in bounded fresh interpreters."""

from textwrap import dedent

import pytest

from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.core, pytest.mark.unit, pytest.mark.protocol]


@pytest.fixture
def probe(tmp_path):
    def run(body):
        source = "from tests.support.server_init_boundary import arguments, initialization_boundary\n"
        source += "with initialization_boundary() as p:\n"
        source += "\n".join("    " + line for line in dedent(body).strip().splitlines())
        return run_python(source, cwd=tmp_path, timeout=10)
    return run


@pytest.mark.parametrize("scenario", ["tiny", "sample.scn", "folder with spaces/λ.SCN"])
@pytest.mark.parametrize("sides", ["none", "blue", "red", "both"])
def test_init_resolution_clients_options_and_registration(probe, scenario, sides):
    probe(f'''
        args = arguments(scenario={scenario!r}, blueAI={"test" if sides in ("blue", "both") else None!r},
                         redAI={"other" if sides in ("red", "both") else None!r},
                         scenarioSeed=17, scenarioCycle=3, openSocket=True, v=True,
                         blueReplay="blue.log", redReplay="red.log", logActions=True, nReps=1)
        p.module.init(args)
        assert [ai.role for ai in p.instances] == {(["blue", "red"] if sides == "both" else [] if sides == "none" else [sides])!r}
        assert p.module.server.clients == [ai.process for ai in p.instances]
        assert p.module.server.options == dict(open_socket=True, verbose=True, blue_log="blue.log",
                                               red_log="red.log", log_actions=True, n_reps=1)
        assert p.current.server is p.module.server
        p.module.server.run.assert_called_once_with()
        assert p.events == ["run"]
        p.dispenser_factory.assert_called_once_with(p.generator)
        if {scenario!r} == "tiny":
            p.constructor.assert_called_once_with(size=2, scenarioSeed=17, scenarioCycle=3)
            p.file_factory.assert_not_called()
        else:
            p.file_factory.assert_called_once_with({scenario!r})
            p.constructor.assert_not_called()
    ''')


@pytest.mark.parametrize("shared", [False, True])
def test_both_ai_constructor_options_and_shared_model(probe, shared):
    probe(f'''
        p.module.init(arguments(blueAI="test", redAI="other", blueNeuralNet="blue.zip",
            redNeuralNet={"shared" if shared else "red.zip"!r}, blueDepthLimit="2", redDepthLimit="3",
            blueSearch="minimax", redSearch="alpha-beta", blueSubAIs="one,two", redSubAIs="three"))
        blue, red = p.instances
        assert blue.options == dict(neuralNet="blue.zip", depthLimit="2", search="minimax", subAIs="one,two")
        expected = dict(neuralNet={"shared" if shared else "red.zip"!r}, depthLimit="3", search="alpha-beta", subAIs="three")
        assert {{key: value for key, value in red.options.items() if key != "neuralNetObj"}} == expected
        if {shared!r}:
            blue.getNeuralNet.assert_called_once_with()
            assert p.registry["other"][1]["neuralNetObj"] is p.model
        else:
            blue.getNeuralNet.assert_not_called()
            assert "neuralNetObj" not in red.options
    ''')


@pytest.mark.parametrize("seed, cycle", [(None, None), (0, 0), (1, 2)])
def test_generator_zero_options_characterization(probe, seed, cycle):
    probe(f'''
        p.module.init(arguments(scenarioSeed={seed!r}, scenarioCycle={cycle!r}))
        assert p.constructor.call_args.kwargs == {({"size": 2, **({"scenarioSeed": seed} if seed else {}), **({"scenarioCycle": cycle} if cycle else {})})!r}
    ''')


def test_repeated_initialization_registry_leak_characterization(probe):
    probe('''
        p.module.init(arguments(blueAI="test", blueNeuralNet="old.zip", blueDepthLimit="4",
                               blueSearch="old", blueSubAIs="old-ai", scenarioSeed=9, scenarioCycle=2))
        first = p.module.server
        p.module.init(arguments(redAI="test", scenarioSeed=0, scenarioCycle=0))
        assert p.module.server is not first and p.current.server is p.module.server
        assert p.instances[1].options == dict(neuralNet="old.zip", depthLimit="4", search="old", subAIs="old-ai")
        assert p.registry["test"][1] == p.instances[1].options
        assert p.constructor.call_args.kwargs == dict(size=2, scenarioSeed=9, scenarioCycle=2)
        assert p.events == ["run", "run"]
        first.run.assert_called_once_with()
        p.module.server.run.assert_called_once_with()
    ''')


def test_same_alias_cross_faction_option_leak_characterization(probe):
    probe('''
        p.module.init(arguments(blueAI="test", redAI="test", blueDepthLimit="7"))
        assert [ai.options for ai in p.instances] == [{"depthLimit": "7"}, {"depthLimit": "7"}]
    ''')


@pytest.mark.parametrize("role", ["blue", "red"])
@pytest.mark.parametrize("alias", ["gym", "gymx2", "gym12", "gym13", "gym14", "gym16", "gym18", "multigym"])
def test_gym_surrogate_selection_characterization(probe, role, alias):
    recognized = role == "blue" or alias in ("gym", "gymx2", "multigym")
    probe(f'''
        p.module.init(arguments(**{{{role + "AI"!r}: {alias!r}}}))
        assert len(p.instances) == 1
        if {recognized!r}:
            assert p.module.getGymAI() is p.instances[0]
        else:
            try:
                p.module.getGymAI()
            except NameError as error:
                assert str(error) == "name 'gym_ai' is not defined"
            else:
                raise AssertionError("Red variant unexpectedly registered; review K07")
    ''')


def test_gym_last_recognized_role_and_stale_binding_characterization(probe):
    probe('''
        p.module.init(arguments(blueAI="gym", redAI="gymx2"))
        previous = p.instances[1]
        assert p.module.getGymAI() is previous
        p.module.init(arguments(blueAI="test"))
        assert p.module.getGymAI() is previous
    ''')


@pytest.mark.parametrize("options, exception, message", [
    ({"blueAI": "missing"}, "KeyError", "missing"),
    ({"redAI": "missing"}, "Exception", "redAI with name missing not found in AI registry"),
    ({"scenario": "missing"}, "KeyError", "missing"),
    ({"redAI": "test", "redNeuralNet": "shared"}, "UnboundLocalError", "blue_ai"),
])
def test_invalid_initialization_characterization(probe, options, exception, message):
    probe(f'''
        try:
            p.module.init(arguments(**{options!r}))
        except {exception} as error:
            assert {message!r} in str(error)
        else:
            raise AssertionError("Expected {exception}")
        assert p.events == [] and not hasattr(p.module, "server")
    ''')


def test_gym_accessors_reset_and_submit_before_resume(probe):
    probe('''
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        events = []
        dimensions = {"width": 2, "height": 3}
        p.module.server = SimpleNamespace(game=SimpleNamespace(mapData=SimpleNamespace(
            getDimensions=Mock(return_value=dimensions))))
        assert p.module.mapDimensionBackdoor() is dimensions
        p.module.server.game.mapData.getDimensions.assert_called_once_with()
        p.module.gym_ai = SimpleNamespace(
            sendToServer=lambda message: events.append(("send", message)),
            observation=lambda: events.append("observation") or {"fresh": True})
        loop = SimpleNamespace(run_forever=lambda: events.append("resume"))
        with patch.object(p.module.asyncio, "get_event_loop", return_value=loop):
            message = {"type": "action", "action": {"type": "pass"}}
            p.module.addMessageRunLoop(message)
            assert events == [("send", message), "resume"]
            events.clear()
            assert p.module.reset() == {"fresh": True}
            assert events == [("send", {"type": "next-game-request"}), "resume", "observation"]
    ''')


@pytest.mark.parametrize("environment, argv, expected, launcher", [
    (None, [], False, False), ("0", [], False, False), ("1", [], True, False),
    ("true", [], False, False), ("0", ["--blueAI", "neural"], False, False),
    ("0", ["--blueAI", "passive"], False, True),
    ("1", ["--redAI", "passive"], True, True),
    ("0", ["--blueAI", "neural"], True, True),
    ("0", ["--redAI", "hex18dqn"], True, True),
    ("0", ["--blueNeuralNet", "test.zip"], True, True),
    ("0", ["--redNeuralNet", "shared"], True, True),
    ("0", ["--blueNeuralNet=test.zip"], False, True),
], ids=["unset", "disabled", "enabled", "exact-env-value", "registry-ignores-argv",
        "passive", "env-retained", "blue-neural", "red-neural", "blue-model", "red-model", "equals-form-characterization"])
def test_neural_import_gating(tmp_path, environment, argv, expected, launcher):
    run_python(f'''
from tests.support.server_init_boundary import check_neural_gate
check_neural_gate({environment!r}, {argv!r}, {expected!r}, {launcher!r})
''', cwd=tmp_path, timeout=10)
