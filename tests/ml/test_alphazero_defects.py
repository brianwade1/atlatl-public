"""Desired contracts; only verified wrong signatures become strict xfails."""
import pytest
from tests.support.s16 import defect_probe
from tests.support.isolation import KnownDefect

pytestmark=[pytest.mark.ml,pytest.mark.unit]


@pytest.mark.xfail(strict=True,raises=KnownDefect,reason='K48: AlphaZero observation uses initial units')
def test_observation_uses_current_state(tmp_path):
    defect_probe('''
import alphazero_observation as o
b=board(); b['state']['units'][0].update(hex='hex-0-0',currentStrength=40)
x=o.nnetObservation(b)
if x[2,2,2]==1 and x[2,0,0]==0: print('S16_MATCHED_DEFECT')
else: assert x[2,0,0]==.4 and x[2,2,2]==0
''',tmp_path)


@pytest.mark.xfail(strict=True,raises=KnownDefect,reason='K49: Arena never updates current player')
def test_arena_uses_faction_on_move(tmp_path):
    defect_probe('''
from Arena import Arena
g=Mock(); g.getInitBoard.return_value=0; g.getCanonicalForm.side_effect=lambda b:b
g.getIsTerminal.side_effect=lambda b:b==2; g.getNextState.side_effect=lambda b,a:b+1
g.getPlayerOnMove.side_effect=lambda b:1 if b==0 else -1
g.getValidMoves.return_value=[1]; g.getScore.return_value=7
p1=Mock(return_value=0); p2=Mock(return_value=0)
assert Arena(p1,p2,g).playGame()==7
if (p1.call_count,p2.call_count)==(2,0): print('S16_MATCHED_DEFECT')
else: assert (p1.call_count,p2.call_count)==(1,1)
''',tmp_path)


@pytest.mark.xfail(strict=True,raises=KnownDefect,reason='K50: CNN mutates caller hidden-layer configuration')
def test_hidden_configuration_preserved(tmp_path):
    defect_probe('''
m=load('dlalphabeta','dlalphabeta.py'); hidden=[8]; m.CNN(2,mlp_hiddens=hidden)
if hidden==[3200,8]: print('S16_MATCHED_DEFECT')
else: assert hidden==[8]
''',tmp_path,torch=True)


@pytest.mark.xfail(strict=True,raises=KnownDefect,reason='K51: Coach episode targets ignore faction changes')
def test_episode_targets_follow_acting_faction(tmp_path):
    defect_probe('''
from Coach import Coach
from utils import dotdict
g=Mock(); g.getInitBoard.return_value={'param':{},'state':{'step':0,'status':{'onMove':'blue'}}}
g.getCanonicalForm.side_effect=lambda b:b
g.getPlayerOnMove.side_effect=lambda b:1 if b['state']['step']==0 else -1
g.getSymmetries.side_effect=lambda b,p:[(b['state']['step'],p)]
g.getNextState.side_effect=lambda b,a:{'param':{},'state':{'step':b['state']['step']+1,'status':{'onMove':'red'}}}
g.getIsTerminal.side_effect=lambda b:b['state']['step']==2
g.getScore.return_value=10
class Net:
    def __init__(self,g): pass
c=Coach(g,Net(g),dotdict(tempThreshold=2,blueAI='b',redAI='r',heuristicEvalFn=None))
c.mcts=Mock(); c.mcts.getActionProb.return_value=[1,0]
values=[x[2] for x in c.executeEpisode()]
if values==[10,10]: print('S16_MATCHED_DEFECT')
else: assert values==[10,-10]
''',tmp_path)
