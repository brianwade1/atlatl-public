"""S02 CPU fixture preflight; no trained model, GPU or training required."""

import pytest

from tests.support.process_helpers import run_python

pytestmark = [pytest.mark.ml, pytest.mark.integration]


def test_cpu_model_numeric_oracle_and_torch_restoration(tmp_path):
    result = run_python('''
import torch
from tests.support.builders import load_fixture
from tests.support.imports import TESTS_DIR, SERVER_DIR, explicit_module
from tests.support.isolation import isolated_rng, preserve_globals
data = load_fixture('models/numeric.json')
before = torch.get_rng_state().clone()
settings = (torch.are_deterministic_algorithms_enabled(),
            torch.is_deterministic_algorithms_warn_only_enabled(), torch.get_num_threads())
try:
    with isolated_rng(torch_module=torch):
        torch.rand(3)
        with explicit_module('tiny_cpu', TESTS_DIR / 'fixtures/models/tiny_cpu.py') as module:
            model = module.TinyCPU()
            actual = model(torch.tensor(data['input']))
            torch.testing.assert_close(actual, torch.tensor(data['output']))
            assert actual.device.type == 'cpu'
        raise RuntimeError('deliberate')
except RuntimeError as exc:
    assert str(exc) == 'deliberate'
torch.testing.assert_close(torch.get_rng_state(), before, rtol=0, atol=0)
assert settings == (torch.are_deterministic_algorithms_enabled(),
                    torch.is_deterministic_algorithms_warn_only_enabled(), torch.get_num_threads())
with explicit_module('portable_fixture', SERVER_DIR / 'portabletorch/portabletorch.py') as module:
    initial = module.PortableTorch.cnt
    with preserve_globals((module.PortableTorch, 'cnt')):
        module.PortableTorch.cnt += 1
    assert module.PortableTorch.cnt == initial
print('CPU fixture verified')
''', cwd=tmp_path, timeout=60)
    assert "CPU fixture verified" in result.stdout
