"""Fresh-process adapter probes avoid flat Game/utils/portabletorch collisions."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.builders import make_scenario, make_state
from tests.support.imports import server_imports


def probe(adapter):
    with server_imports():
        import torch
        from tests.support.isolation import isolated_rng
        with isolated_rng(torch_module=torch):
            if adapter == "azero":
                return azero()
            # PortableTorch namespace has no public loader when imported from
            # this cwd. Substitute just that persistence boundary, not inference.
            model = Mock()
            model.to.return_value = model
            load = Mock(return_value=SimpleNamespace(model=model))
            sys.modules["portabletorch"] = SimpleNamespace(PortableTorch=SimpleNamespace(load=load))
            if adapter == "dl":
                import ai.dl_alpha_beta as module
                options = {"debug":False, "depthLimit":"2", "neuralNet":"fixture.pt"}
                ai = module.AI("blue", options)
                load.assert_called_once_with("fixture.pt")
                assert ai.getNeuralNet() is model and ai.depth_limit == 2
                shared = module.AI("red", dict(options, neuralNet="shared", neuralNetObj=model))
                assert shared.getNeuralNet() is model
                scenario = make_scenario()
                assert json.loads(ai.process(json.dumps({"type":"parameters", "parameters":scenario}))) == {"type":"role-request", "role":"blue"}
                assert ai.merit_constant == 300 / 2**.5
                game = object()
                search = Mock(return_value=({"type":"pass"}, 8, []))
                with patch.object(module.current_game_access, "get_current_game", return_value=game), patch.object(module.dlalphabeta, "dlab", search):
                    for agent in [ai, shared]:
                        state = make_state(scenario["units"], on_move=agent.role)
                        assert json.loads(agent.process(json.dumps({"type":"observation", "observation":state}))) == {"type":"action", "action":{"type":"pass"}}
                        search.assert_called_with(game, state, 2, model)
                        state["status"]["isTerminal"] = True
                        assert agent.process(json.dumps({"type":"observation", "observation":state})) is None
                    assert search.call_count == 2
                assert ai.process('{"type":"reset"}') is None
                try:
                    module.AI("blue", {})
                except KeyError as exc:
                    assert exc.args == ("debug",)
                else:
                    raise AssertionError("missing required options accepted")
            else:
                import ai.state_eval_gpu as module
                with patch.object(torch.cuda, "is_available", return_value=False):
                    for role in ["blue", "red"]:
                        ai = module.StateEvalGPUAI(role, {"neuralNet":"fixture.pt", "partialPly":False})
                        assert ai.device == "cpu" and ai.getNeuralNet() is model
                        model.to.assert_called_with("cpu")
                        shared = module.StateEvalGPUAI(role, {"neuralNet":"shared", "neuralNetObj":model, "partialPly":True, "depthLimit":"2"})
                        assert shared.getNeuralNet() is model and shared.depth_limit == 2
                        # Bounded finite tree, deliberately spans two inference batches.
                        class Game:
                            def legal_actions(self, state):
                                return list(range(5)) if state["status"]["onMove"] == role else []
                            def transition(self, state, action):
                                return {"value":action, "status":{"onMove":"red" if role == "blue" else "blue"}}
                        game = Game(); state = {"status":{"onMove":role}}
                        assert [p.actions for p in ai.singleActions(game, state)] == [[i] for i in range(5)]
                        assert ai.singleActions(game, {"status":{"onMove":"other"}}) == []
                        assert ai.allActionSequences(game, state, 0)[0].actions == []
                        ai.batch_size = 3
                        model.reset_mock()
                        model.side_effect = lambda tensor: tensor[:, :1]
                        with patch.object(module.observation, "observation", side_effect=lambda game, st: torch.tensor([float(st["value"])])):
                            assert ai.findBestActions(game, state) == ([4] if role == "blue" else [0])
                        assert [call.args[0].shape for call in model.call_args_list] == [torch.Size([3,1]), torch.Size([2,1])]
                        assert all(call.args[0].device.type == "cpu" for call in model.call_args_list)
                        class TwoActions:
                            def legal_actions(self, state):
                                return [1,2] if state["depth"] < 2 else []
                            def transition(self, state, action):
                                return {"depth":state["depth"]+1, "value":state["value"]*10+action,
                                        "status":{"onMove":role}}
                        tree = TwoActions(); root = {"depth":0,"value":0,"status":{"onMove":role}}
                        paths = ai.allActionSequences(tree,root,remainingDepth=2,dupCheck={})
                        assert [p.actions for p in paths] == [[1,1],[1,2],[2,1],[2,2]]
                        with patch.object(module.observation, "observation", side_effect=lambda game, st: torch.tensor([float(st["value"])])):
                            assert ai.findBestActions(tree,root) == ([2,2] if role == "blue" else [1,1])
                            assert shared.findBestActions(tree,root) == ([2] if role == "blue" else [1])
                        # Unequal action IDs make reversed queue order observable.
                        model.side_effect = lambda tensor: -(tensor[:, :1]-12).abs() if role == "blue" else (tensor[:, :1]-12).abs()
                        with patch.object(module.observation, "observation", side_effect=lambda game, st: torch.tensor([float(st["value"])])):
                            assert ai.findBestActions(tree,root) == [2,1]
                            assert shared.findBestActions(tree,root) == [1]
                    try:
                        module.StateEvalGPUAI("blue", {})
                    except KeyError as exc:
                        assert exc.args == ("neuralNet",)
                    else:
                        raise AssertionError("missing model option accepted")


def azero():
    # Explicit module boundaries avoid importing executable AlphaZero helpers.
    game = Mock(); game.vectorIndexActionToAtlatl.return_value = {"type":"pass"}
    net = Mock(); search = Mock(); search.getActionProb.return_value = [.1,.8,.1]
    game_ctor = Mock(return_value=game); net_ctor = Mock(return_value=net); search_ctor = Mock(return_value=search)
    sys.modules["alphazero_game"] = SimpleNamespace(AtlatlGame=game_ctor)
    sys.modules["alphazero_nnet"] = SimpleNamespace(NNetWrapper=net_ctor)
    sys.modules["alphazero_observation"] = SimpleNamespace(make_observation=Mock(return_value="tensor"))
    sys.modules["azg"] = SimpleNamespace(MCTS=SimpleNamespace(MCTS=search_ctor))
    import ai.azero as module
    for role in ["blue", "red"]:
        ai = module.AIaz(role, {"neuralNet":"fixture-model"})
        net.load_checkpoint.assert_called_with(folder="fixture-model", filename="best.pth.tar")
        net_ctor.assert_called_with(game)
        search_ctor.assert_called_with(game, net, module.AI.args)
        scenario = make_scenario(); state = make_state(scenario["units"], on_move=role)
        assert json.loads(ai.process(json.dumps({"type":"parameters", "parameters":scenario}))) == {"type":"role-request", "role":role}
        assert json.loads(ai.process(json.dumps({"type":"observation", "observation":state}))) == {"type":"action", "action":{"type":"pass"}}
        board = {"param":scenario, "state":state}
        search.getActionProb.assert_called_with(board, temp=1)
        game.vectorIndexActionToAtlatl.assert_called_with(1, board)
        assert ai.observation() == "tensor"
        module.make_observation.assert_called_with(scenario, state, ai.mapData, ai.unitData)
        ai.attempted_moveD[f"{role} A"] = True
        assert ai.moveMessage() == {"type":"action", "action":{"type":"pass"}}
        ai.reset(); assert ai.attempted_moveD == {}
    module.AI("blue", {})
    net.load_checkpoint.assert_called_with(folder="temp", filename="best.pth.tar")
