import pytest
from tests.support.s16 import probe

pytestmark=[pytest.mark.ml,pytest.mark.unit]


@pytest.mark.parametrize('load_model',[False,True])
def test_main_orchestration_without_logging_or_training(tmp_path,load_model):
    probe(f"load_model={load_model}\n"+'''
import types
colored=types.ModuleType('coloredlogs'); colored.install=Mock()
with patch.dict(sys.modules,{'coloredlogs':colored}):
    m=load('az_main','azg/alphazero_main.py')
m.args.load_model=load_model
with patch.object(m,'Game') as game, patch.object(m,'nn') as net, patch.object(m,'Coach') as coach:
    game.__name__='Game'; net.__name__='Network'
    m.main()
    game.assert_called_once_with(m.args.scenario_name)
    net.assert_called_once_with(game.return_value)
    coach.assert_called_once_with(game.return_value,net.return_value,m.args)
    coach.return_value.learn.assert_called_once_with()
    assert net.return_value.load_checkpoint.call_count==int(load_model)
    assert coach.return_value.loadTrainExamples.call_count==int(load_model)
colored.install.assert_called_once_with(level='DEBUG')
''',tmp_path)


def test_play_and_score_real_short_game_and_both_act_failure(tmp_path):
    probe('''
import util,game,airegistry
class Agent:
    def __init__(self,role,options): self.role=role
    def process(self,message):
        data=json.loads(message)
        if data['type']=='observation' and data['observation']['status']['onMove']==self.role:
            return json.dumps({'action':{'type':'pass'}})
b=board(); b['param']['score']['maxPhases']=2
airegistry.ai_registry['controlled']=(Agent,{})
state=game.Game(b['param']).initial_state()
assert util.playAndScore(b['param'],state,'controlled','controlled')==0
class Both(Agent):
    def process(self,message):
        if json.loads(message)['type']=='observation': return json.dumps({'action':{'type':'pass'}})
airegistry.ai_registry['both']=(Both,{})
with pytest.raises(TypeError,match='exceptions must derive'):
    util.playAndScore(b['param'],state,'both','both')
''',tmp_path)


def test_neither_agent_progress_deadline(tmp_path):
    probe('''
import util,game,airegistry,threading
class Agent:
    def __init__(self,*args): pass
    def process(self,message): return None
airegistry.ai_registry['none']=(Agent,{})
b=board(); state=game.Game(b['param']).initial_state()
class Deadline(Exception): pass
# A finite observation boundary detects repeated unchanged state without hanging the runner.
original=util.Game
class Guarded(original):
    calls=0
    def observation(self,state,role):
        self.calls+=1
        if self.calls>20: raise Deadline('no progress after ten iterations')
        return super().observation(state,role)
util.Game=Guarded
with pytest.raises(Deadline,match='no progress'):
    util.playAndScore(b['param'],state,'none','none')
''',tmp_path)
