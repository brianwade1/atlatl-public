"""Real CPU persistence of test-owned source and weights."""
import pytest
from tests.support.s16 import probe

pytestmark = [pytest.mark.ml, pytest.mark.integration]


def test_save_load_metadata_predictions_cpu_and_distinct_modules(tmp_path):
    probe('''
p = load('portabletorch', 'portabletorch/portabletorch.py')
source = TESTS_DIR / 'fixtures/models/tiny_cpu.py'
m = p.import_from_path('tiny', source)
dep = Path('dependency.txt'); dep.write_text('test dependency')
portable = p.PortableTorch(m.TinyCPU(), 'TinyCPU', str(source), [str(dep)], input_shape=[2], output_shape=[2], comment='tiny')
portable.save('first')
info = json.loads(Path('first/info.json').read_text())
assert info == portable.info
assert Path('first/tiny_cpu.py').read_bytes() == source.read_bytes()
assert Path('first/dependency.txt').read_text() == 'test dependency'
original_load = torch.load
with patch.object(torch.cuda, 'is_available', return_value=False), patch.object(torch, 'load', wraps=original_load) as spy:
    restored = p.PortableTorch.load('first')
    assert str(spy.call_args.kwargs['map_location']) == 'cpu'
assert not restored.model.training
torch.testing.assert_close(restored.model(torch.tensor([0.,3.])), torch.tensor([1.,7.]))
for key, value in portable.model.state_dict().items():
    torch.testing.assert_close(restored.model.state_dict()[key], value)
with torch.no_grad(): portable.model.bias.fill_(4)
portable.save('second')
second = p.PortableTorch.load('second')
assert type(second.model) is not type(restored.model)
torch.testing.assert_close(second.model(torch.tensor([0.])), torch.tensor([4.]))
torch.testing.assert_close(restored.model(torch.tensor([0.])), torch.tensor([1.]))
restored.save('first')  # same-file source copying is supported
restored.print(); restored.test()
''', tmp_path, torch=True)


@pytest.mark.parametrize('damage,exception', [
    ('metadata', 'FileNotFoundError'), ('json', 'json.JSONDecodeError'),
    ('source', 'UnboundLocalError'), ('weights', 'UnboundLocalError'),
    ('class', 'AttributeError'), ('incompatible', 'RuntimeError')])
def test_load_failure_characterizations(tmp_path, damage, exception):
    probe('''
p = load('portabletorch', 'portabletorch/portabletorch.py')
source = TESTS_DIR / 'fixtures/models/tiny_cpu.py'
m = p.import_from_path('tiny', source)
p.PortableTorch(m.TinyCPU(), 'TinyCPU', str(source)).save('saved')
''' + {
        'metadata': "Path('saved/info.json').unlink()",
        'json': "Path('saved/info.json').write_text('{')",
        'source': "Path('saved/tiny_cpu.py').unlink()",
        'weights': "Path('saved/model.pt').unlink()",
        'class': "info=json.loads(Path('saved/info.json').read_text()); info['model_class_name']='Absent'; Path('saved/info.json').write_text(json.dumps(info))",
        'incompatible': "torch.save({'wrong':torch.zeros(1)}, 'saved/model.pt')",
    }[damage] + f"\nwith pytest.raises({exception}): p.PortableTorch.load('saved')\n", tmp_path, torch=True)
