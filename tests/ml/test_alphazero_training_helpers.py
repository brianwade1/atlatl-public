"""Bounded Coach orchestration and real Torch losses/checkpoints."""
import pytest
from tests.support.s16 import probe

pytestmark = [pytest.mark.ml, pytest.mark.unit]


@pytest.mark.parametrize('wins,accepted', [((4,0,0),False),((0,0,4),False),((1,3,0),True)])
@pytest.mark.parametrize('skip', [False,True])
def test_coach_history_thresholds_checkpoints_and_example_roundtrip(tmp_path,wins,accepted,skip):
    probe(f"wins={wins!r}; accepted={accepted}; skip={skip}\n" + '''
import Coach as module
from utils import dotdict
class Net:
    def __init__(self,g): self.save_checkpoint=Mock(); self.load_checkpoint=Mock(); self.train=Mock()
g=Mock(); net=Net(g)
args=dotdict(numIters=1,numEps=1,maxlenOfQueue=2,numItersForTrainExamplesHistory=1,checkpoint='checkpoints',arenaCompare=4,updateThreshold=.6,load_folder_file=('checkpoints','checkpoint_0.pth.tar'))
c=module.Coach(g,net,args)
c.trainExamplesHistory=[['old']]; c.skipFirstSelfPlay=skip
c.executeEpisode=Mock(return_value=[1,2,3])
with patch.object(module,'Arena') as arena:
    arena.return_value.playGames.return_value=wins
    c.learn()
assert len(c.trainExamplesHistory)==1
assert net.train.call_args.args[0]==(['old'] if skip else [2,3]) or sorted(net.train.call_args.args[0])==[2,3]
assert c.executeEpisode.call_count==(0 if skip else 1)
saved=[call.kwargs['filename'] for call in net.save_checkpoint.call_args_list]
assert saved==(['temp.pth.tar','checkpoint_1.pth.tar','best.pth.tar'] if accepted else ['temp.pth.tar'])
assert net.load_checkpoint.call_count==(0 if accepted else 1)
assert c.getCheckpointFile(12)=='checkpoint_12.pth.tar'
c.trainExamplesHistory=[]; c.loadTrainExamples()
assert c.skipFirstSelfPlay and len(c.trainExamplesHistory)==1
c.args.load_folder_file=('absent','none')
with patch('builtins.input',return_value='y'): c.loadTrainExamples()
with patch('builtins.input',return_value='n'), pytest.raises(SystemExit): c.loadTrainExamples()
''',tmp_path)


def test_episode_heuristic_adjustment_and_utils(tmp_path):
    probe('''
from Coach import Coach
from utils import dotdict,AverageMeter
g=Mock(); g.getInitBoard.return_value={'param':{},'state':{'step':0}}
g.getCanonicalForm.side_effect=lambda b:b
g.getSymmetries.side_effect=lambda b,p:[(b['state']['step'],p)]
g.getNextState.side_effect=lambda b,a:{'param':{},'state':{'step':b['state']['step']+1}}
g.getIsTerminal.side_effect=lambda b:b['state']['step']==2
g.getScore.return_value=10
class Net:
    def __init__(self,g): pass
args=dotdict(tempThreshold=2,blueAI='b',redAI='r',heuristicEvalFn=lambda p,s,b,r:2+s['step'])
c=Coach(g,Net(g),args); c.mcts=Mock(); c.mcts.getActionProb.return_value=[1,0]
examples=c.executeEpisode()
assert examples==[(0,[1,0],8),(1,[1,0],7)]
assert [x.kwargs['temp'] for x in c.mcts.getActionProb.call_args_list]==[1,0]
meter=AverageMeter(); assert (meter.count,meter.avg)==(0,0)
meter.update(2,3); meter.update(6)
assert (meter.val,meter.sum,meter.count,meter.avg)==(6,12,4,3)
assert repr(meter)=='3.00e+00' and AverageMeter().sum==0
d=dotdict(a=3); assert pickle.loads(pickle.dumps(d)).a==3
with pytest.raises(KeyError): d.absent
''',tmp_path)


def test_network_losses_predict_checkpoints_and_real_forward(tmp_path):
    probe('''
import alphazero_nnet as m
m.args.cuda=False
w=m.NNetWrapper.__new__(m.NNetWrapper)
targets=torch.tensor([[1.,0.],[.5,.5]])
logs=torch.log(torch.tensor([[.25,.75],[.5,.5]]))
assert w.loss_pi(targets,logs).item()==pytest.approx((np.log(4)+np.log(2))/2)
assert w.loss_v(torch.tensor([1.,3.]),torch.tensor([[2.],[1.]])).item()==2.5
class Tiny(torch.nn.Module):
    def __init__(self): super().__init__(); self.bias=torch.nn.Parameter(torch.tensor(2.))
    def forward(self,x): return torch.log_softmax(torch.stack([self.bias,self.bias])[None],1),self.bias.reshape(1,1)
w.nnet=Tiny()
with patch.object(m,'nnetObservation',return_value=np.zeros((16,5,5))):
    policy,value=w.predict({})
assert np.allclose(policy,[.5,.5]) and value[0]==2 and not w.nnet.training
w.save_checkpoint('checkpoint','tiny.pt')
with torch.no_grad(): w.nnet.bias.fill_(9)
w.load_checkpoint('checkpoint','tiny.pt'); assert w.nnet.bias.item()==2
with pytest.raises(TypeError,match='exceptions must derive'): w.load_checkpoint('checkpoint','absent')
from alphazero_atlatl_nnet import AtlatlNNet
g=Mock(); g.getBoardSize.return_value=(5,5); g.getActionSize.return_value=151; g.getInitBoard.side_effect=board
model=AtlatlNNet(g,SimpleNamespace()).eval()
x=torch.ones(2,16,5,5)
with torch.no_grad():
    pi,v=model(x); pi2,v2=model(x)
assert pi.shape==(2,151) and v.shape==(2,1)
assert torch.isfinite(v).all() and torch.allclose(pi.exp().sum(1),torch.ones(2))
assert not torch.equal(pi,pi2)  # forced dropout remains active in eval
''',tmp_path,torch=True)
