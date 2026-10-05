"""Small real tensors; training helpers receive one batch only."""
import pytest
from tests.support.s16 import probe

pytestmark = [pytest.mark.ml, pytest.mark.integration]


@pytest.mark.parametrize('path', ['portabletorch/cnn.py', 'dlalphabeta.py',
    'ai/A5b_M3/cnn.py', 'ai/A5b_LX3/cnn.py', 'ai/pass-v-pass-g3/cnn.py'])
def test_architecture_residual_shapes_configuration_and_training(tmp_path, path):
    probe(f"m = load('architecture', {path!r})\n" + '''
x = torch.ones(2,2,5,5)
block = m.HexBlock(2,2)
with torch.no_grad():
    for p in block.parameters(): p.zero_()
torch.testing.assert_close(block(x), x)
block.residual = False
torch.testing.assert_close(block(x), torch.zeros_like(x))
if hasattr(m, 'AtlatlDataset'):
    ds = m.AtlatlDataset([[1,2],[3,4]], [5,6])
    assert len(ds)==2 and ds[1][0].dtype==torch.float32
    torch.testing.assert_close(ds[1][0], torch.tensor([3.,4.]))
    hidden=[8]
    model=m.CNN(2, mlp_hiddens=hidden)
    assert hidden==[3200,8]  # characterization: constructor mutates caller list
    other=m.CNN(2, mlp_hiddens=[8])
else:
    model=m.CNN(2, mlp_layers=1, mlp_size=8)
    other=m.CNN(2, mlp_layers=1, mlp_size=8)
assert list(model.state_dict())==list(other.state_dict())
y=model(x)
assert y.shape==(2,1) and torch.isfinite(y).all()
if hasattr(m, 'train'):
    data=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, torch.zeros(2,1)), batch_size=2)
    optimizer=torch.optim.SGD(model.parameters(), lr=.001)
    with pytest.raises(NameError, match="device"):
        m.train(data,model,torch.nn.MSELoss(),optimizer)
    m.device=torch.device('cpu')  # explicitly configured helper behavior
    before=[p.detach().clone() for p in model.parameters()]
    losses=[]
    def loss(a,b):
        value=torch.nn.functional.mse_loss(a,b); losses.append(value.item()); return value
    gradients=[]
    handles=[p.register_hook(lambda g: gradients.append(torch.isfinite(g).all().item())) for p in model.parameters()]
    m.train(data,model,loss,optimizer)
    for h in handles: h.remove()
    assert np.isfinite(losses).all() and gradients and all(gradients)
    assert any(not torch.equal(a,b) for a,b in zip(before,model.parameters()))
''', tmp_path, torch=True)


def test_simple_model_forward(tmp_path):
    probe("m=load('model','portabletorch/model.py'); y=m.Model()(torch.ones(3,2)); assert y.shape==(3,1) and torch.isfinite(y).all()", tmp_path, torch=True)
