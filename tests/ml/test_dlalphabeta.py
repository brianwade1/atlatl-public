"""CPU-only depth-limited search in a fresh bounded interpreter."""

import pytest
from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.ml, pytest.mark.unit]


def test_neural_search_terminal_cutoff_depth_sign_and_pruning(tmp_path):
    result = run_python('''
import torch
from unittest.mock import Mock
from tests.support.imports import server_imports
from tests.support.doubles import FiniteGame
from tests.support.isolation import isolated_rng
with server_imports(), isolated_rng(torch_module=torch):
    import dlalphabeta as module
    game = FiniteGame()
    model = Mock(return_value=torch.tensor([[11.0]]))
    def observation(game, state):
        return torch.tensor([float(len(state))])
    # Feature construction is a separate S15 contract; retain real Torch inference.
    module.observation = observation
    assert module._state_value(game, ("left", "low"), 0, model, -99, 99) == 3
    model.assert_not_called()
    assert module._state_value(game, (), 0, model, -99, 99).item() == 11
    torch.testing.assert_close(model.call_args.args[0], torch.tensor([[0.]]))
    model.reset_mock()
    # dlab depth=1 evaluates children AND their children (two actions).
    action, value, pairs = module.dlab(game, (), 1, model)
    assert (action, value) == ("left", 3)
    assert pairs == [("left", 3), ("right", -2)]
    model.assert_not_called()
    assert module.dlab(game, ("right",), 1, model)[:2] == ("low", -2)
    for depth in [0, -1]:
        try:
            module.dlab(game, (), depth, model)
        except ValueError as exc:
            assert str(exc) == 'depth_limit is less than 1, no actions to consider'
        else:
            raise AssertionError('invalid depth accepted')
    try:
        module.dlab(game, ("left", "low"), 1, model)
    except ValueError as exc:
        assert str(exc) == 'Starting state is already terminal, no actions to consider'
    else:
        raise AssertionError('terminal root accepted')
    transition = Mock(wraps=game.transition)
    game.transition = transition
    assert module._state_value(game, ("left",), 1, model, 4, 99) == 3
    assert transition.call_count == 1  # red prunes high after low <= alpha
    transition.reset_mock()
    assert module._state_value(game, (), 2, model, -99, 2) == 3
    assert transition.call_count == 3  # blue prunes right after left >= beta
    print('neural search verified')
''', cwd=tmp_path, timeout=60)
    assert "neural search verified" in result.stdout
