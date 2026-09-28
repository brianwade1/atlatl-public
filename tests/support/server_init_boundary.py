"""Subprocess-only initialization collaborators; no real AI/model/loop startup."""

from contextlib import contextmanager
from copy import deepcopy
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
import sys

from tests.support.imports import import_server, server_imports


def arguments(**overrides):
    values = dict(blueAI=None, redAI=None, blueNeuralNet=None, redNeuralNet=None,
                  blueDepthLimit=None, redDepthLimit=None, blueSearch=None,
                  redSearch=None, blueSubAIs=None, redSubAIs=None,
                  scenario="tiny", scenarioSeed=None, scenarioCycle=None,
                  openSocket=False, v=False, redReplay=None, blueReplay=None,
                  logActions=False, nReps=0)
    values.update(overrides)
    return SimpleNamespace(**values)


@contextmanager
def initialization_boundary():
    instances = []
    events = []
    model = object()

    class AI:
        def __init__(self, role, options):
            self.role, self.options = role, deepcopy(options)
            self.process = Mock(name=f"{role}.process")
            self.getNeuralNet = Mock(return_value=model)
            instances.append(self)

    registry = ModuleType("airegistry")
    aliases = ["test", "other", "gym", "gymx2", "gym12", "gym13", "gym14", "gym16", "gym18", "multigym"]
    registry.ai_registry = {name: (AI, {}) for name in aliases}
    with server_imports(), patch.dict(sys.modules, {"airegistry": registry}):
        module = import_server("server")
        scenario_generator = Mock(name="scenario-generator")
        constructor = Mock(return_value=scenario_generator)
        file_factory = Mock(return_value=scenario_generator)
        dispenser = Mock(name="dispenser")
        dispenser_factory = Mock(return_value=dispenser)
        current = import_server("current_game_access")

        class Server:
            def __init__(self, actual_dispenser, clients, **options):
                assert actual_dispenser is dispenser
                self.clients, self.options = clients, options
                self.run = Mock(side_effect=self.running)

            def running(self):
                assert current.server is self  # Registration must precede run.
                events.append("run")

        with patch.object(module, "GameServer", Server), \
             patch.object(module, "scenario_generator_registry", {"tiny": (constructor, {"size": 2})}), \
             patch.object(module.scenario, "from_file_factory", file_factory), \
             patch.object(module.game_dispenser, "ScenarioGeneratorGameDispenser", dispenser_factory):
            yield SimpleNamespace(module=module, instances=instances, events=events,
                                  constructor=constructor, file_factory=file_factory,
                                  generator=scenario_generator, dispenser_factory=dispenser_factory,
                                  registry=registry.ai_registry, current=current, model=model)


def check_neural_gate(environment, argv, expected, import_launcher):
    """Execute real registry/launcher gating; AI modules are import boundaries.

    Enumerate actual imports, providing inert modules with named constructors.
    Record import statements, not sys.modules presence (stubs are preinstalled).
    This tests gating only and deliberately makes no Torch-free import claim.
    """
    import ast
    import builtins
    import os
    from tests.support.imports import SERVER_DIR

    class AIModule(ModuleType):
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError(name)
            return type(name, (), {})

    imports = [alias.name for node in ast.walk(ast.parse((SERVER_DIR / "airegistry.py").read_text()))
               if isinstance(node, ast.Import) for alias in node.names if alias.name.startswith("ai.")]
    package = ModuleType("ai")
    package.__path__ = []
    modules = {"ai": package}
    for name in imports:
        module = AIModule(name)
        modules[name] = module
        setattr(package, name.split(".")[1], module)
    attempted = []
    original_import = builtins.__import__

    def recording_import(name, *args, **kwargs):
        if name.startswith("ai."):
            attempted.append(name)
        return original_import(name, *args, **kwargs)

    if environment is None:
        os.environ.pop("ATLATL_NEURAL", None)
    else:
        os.environ["ATLATL_NEURAL"] = environment
    sys.argv = ["server.py", *argv]
    with server_imports(), patch.dict(sys.modules, modules), patch.object(builtins, "__import__", recording_import):
        if import_launcher:
            import_server("server")
        registry = import_server("airegistry")
        assert registry.IMPORT_NEURAL is expected
        neural_names = {"neural", "cnn", "hex12", "hex13", "hex14", "hex14dqn", "hex18dqn",
                        "mando-fun-lab3", "alphazero", "dlalphabeta", "state-eval-gpu",
                        "state-eval-gpu-pp", "pascal", "ibarra-m3", "ibarra-lx3"}
        assert neural_names.intersection(registry.ai_registry) == (neural_names if expected else set())
        optional = {"ai.neural", "ai.azero", "ai.dl_alpha_beta", "ai.state_eval_gpu"}
        assert optional.intersection(attempted) == (optional if expected else set())
        assert "ai.multigym_ai" in attempted
        assert "passive" in registry.ai_registry and "gym18" in registry.ai_registry
