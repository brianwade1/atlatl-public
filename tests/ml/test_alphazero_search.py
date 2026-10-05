"""Finite trees expose faction-sensitive backups and Arena selection."""
import pytest
from tests.support.s16 import probe

pytestmark = [pytest.mark.ml, pytest.mark.unit]

TREE = '''
class Tree:
    def getInitBoard(self): return 0
    def getCanonicalForm(self,b): return b
    def stringRepresentation(self,b): return str(b)
    def getIsTerminal(self,b): return b==2
    def getScore(self,b): return 7 if b==2 else 0
    def getActionSize(self): return 3
    def getValidMoves(self,b): return np.array([1,0,1])
    def getNextState(self,b,a): assert a in [0,2]; return b+1
    def getPlayerOnMove(self,b): return -1 if b==2 else 1
'''


@pytest.mark.parametrize('prior', [[.2,.7,.1], [0,1,0]])
def test_mcts_mask_fallback_visits_temperature_and_value_sign(tmp_path, prior):
    probe(TREE + f"prior={prior!r}\n" + '''
from MCTS import MCTS
g=Tree(); net=Mock(); net.predict.side_effect=lambda b:(np.array(prior,dtype=float), 3.)
args=SimpleNamespace(numMCTSSims=12, cpuct=1., heuristicEvalFn=None)
m=MCTS(g,net,args)
assert m.search(0)==3
assert m.Ps['0'][1]==0 and m.Ps['0'].sum()==pytest.approx(1)
assert m.search(2)==7
probs=m.getActionProb(0)
assert sum(probs)==pytest.approx(1) and probs[1]==0
assert m.Ns['0']==12
assert sum(v for (s,a),v in m.Nsa.items() if s=='0')==12
assert all(v==-7 for (s,a),v in m.Qsa.items() if s=='1')
one=m.getActionProb(0,temp=0)
assert sum(one)==1 and one[1]==0 and set(one)<={0,1}
before=m.Ns['0']; m.search(0); assert m.Ns['0']==before+1
''', tmp_path)


def test_arena_score_invalid_actions_odd_counts_and_selection_characterization(tmp_path):
    probe(TREE + '''
from Arena import Arena
g=Tree(); first=Mock(return_value=0); second=Mock(return_value=2)
a=Arena(first,second,g)
assert a.playGame()==7
assert first.call_count==2 and second.call_count==0
g.getPlayerOnMove=lambda b: 1 if b==0 else -1
first.reset_mock(); a.playGame()
assert first.call_count==2 and second.call_count==0  # current player never updated
with pytest.raises(AssertionError): Arena(lambda b:1,second,g).playGame()
assert a.playGames(3)==(1,1,0)  # drops odd remainder, leaves players swapped
assert a.player1 is second
a.playGame=Mock(side_effect=[0,-2,0,2])
assert a.playGames(4)==(0,2,2)
''', tmp_path)
