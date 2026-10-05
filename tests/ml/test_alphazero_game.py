"""5x5 adapter contracts, all interior directions and current-state defect."""
import pytest
from tests.support.s16 import probe

pytestmark = [pytest.mark.ml, pytest.mark.unit]

SETUP = '''
from alphazero_game import AtlatlGame
b=board()
AtlatlGame.registry={'tiny': {'gen':lambda:copy.deepcopy(b['param']), 'max_score':100, 'all_units_move_one':True}}
g=AtlatlGame('tiny')
'''


def test_board_masks_transition_canonical_score_and_symmetry(tmp_path):
    probe(SETUP + '''
assert g.getBoardSize()==(5,5) and g.getActionSize()==151
initial=g.getInitBoard()
assert initial['param']==b['param']
assert g.atlatlActionToVectorIndex({'type':'pass'},b)==150
assert g.vectorIndexActionToAtlatl(150,b)=={'type':'pass'}
assert g.vectorIndexActionToAtlatl(0,b) is None
edge=copy.deepcopy(b); edge['state']['units']=[make_unit(hex='hex-0-0')]
assert any(g.vectorIndexActionToAtlatl(i,edge) is None for i in range(6))
valid=g.getValidMoves(b)
assert len(valid)==151 and valid[150]==1 and set(valid)<={0,1}
with patch.object(g.game,'transition',return_value={'sentinel':True}) as transition:
    result=g.getNextState(b,150)
    transition.assert_called_once_with(b['state'],{'type':'pass'})
    assert result['param'] is b['param'] and result['state']=={'sentinel':True}
assert g.getScore(b)==25 and not g.getIsTerminal(b) and g.getPlayerOnMove(b)==1
assert g.getCanonicalForm(b) is b
b['state']['status'].update(onMove='red',cityOwner={'hex-2-2':'blue','hex-3-2':'red','hex-0-0':'neutral'})
before=copy.deepcopy(b); canonical=g.getCanonicalForm(b)
assert b==before and canonical['state']['status']['score']==-25
assert canonical['state']['status']['cityOwner']=={'hex-2-2':'red','hex-3-2':'blue','hex-0-0':'neutral'}
assert canonical['state']['units'][0]['faction']=='red' and canonical['param']['units'][0]['faction']=='red'
assert g.getPlayerOnMove(b)==-1
pi=[0]*151; pi[150]=1
sym=g.getSymmetries(b,pi)
assert len(sym)==1 and sym[0][0].shape==(16,5,5) and sym[0][1] is pi
g.game_spec['all_units_move_one']=False
assert g.getActionSize()==451 and g.atlatlActionToVectorIndex({'type':'pass'},b)==150
assert g.vectorIndexActionToAtlatl(450,b) is None  # advertised wider mode retains 151 conversion
''', tmp_path)


@pytest.mark.parametrize('col', [1,2])
@pytest.mark.parametrize('direction', range(6))
@pytest.mark.parametrize('occupied', [False,True])
def test_move_fire_round_trip_both_parities(tmp_path,col,direction,occupied):
    probe(SETUP + f"col={col}; direction={direction}; occupied={occupied}\n" + '''
b['state']['units']=[make_unit(hex=f'hex-{col}-2')]
index=col*30+12+direction
action=g.vectorIndexActionToAtlatl(index,b)
assert action['type']=='move'
destination=action['destination']
if occupied:
    b['state']['units'].append(make_unit(faction='red',hex=destination))
    action=g.vectorIndexActionToAtlatl(index,b)
    assert action=={'type':'fire','source':'blue A','target':'red A'}
assert g.atlatlActionToVectorIndex(action,b)==index
''', tmp_path)


def test_features_order_helpers_and_stale_parameter_characterization(tmp_path):
    probe('''
import alphazero_observation as o
b=board(); b['state']['units'][0].update(hex='hex-0-0',currentStrength=40)
features=o.nnetObservation(b)
assert features.shape==(16,5,5)
assert features[2,2,2]==1 and features[2,0,0]==0  # currently reads param units
import map,unit
md=map.MapData(); ud=unit.UnitData()
map.fromPortable(b['param']['map'],md); unit.fromPortable(b['state']['units'],ud,md)
current=o.make_observation(b['param'],b['state'],md,ud)
assert current[2,0,0]==.4 and current[2,2,2]==0
assert current[0,0,0]==1 and current[4,0,0]==1
assert current[1].sum()>0 and current[1,0,0]==0
assert np.all(current[8]==1) and np.all(current[9:14]==0)
assert np.allclose(current[14],.9**3) and np.all(current[15]==.025)
u=ud.units()[0]
assert o.moverFeatureFactory(u)(u)==1
assert o.moverFeatureFactory(object())(u)==0
assert o.unitTypeFeatureFactory('armor')(u)==0
assert o.strengthUnitFeature(u,'red')==0
u.ineffective=True; assert o.canMoveFeature(u)==0 and o.blueUnitFeature(u)==0
b['state']['status']['onMove']='red'
red=o.make_observation(b['param'],b['state'],md,ud)
assert np.array_equal(red[2],current[3])
assert np.all(red[15]==.025)  # red score is not negated
''', tmp_path)


def test_all_channels_literal_terrain_types_ownership_and_legal_targets(tmp_path):
    probe('''
import alphazero_observation as o, map, unit
units=[make_unit(hex='hex-0-0',strength=40),
       make_unit('B',hex='hex-1-1',unit_type='mechinf',can_move=False),
       make_unit('C',faction='red',hex='hex-3-3',unit_type='armor',strength=70,can_move=False),
       make_unit('D',faction='red',hex='hex-4-4',unit_type='artillery',can_move=False)]
param=make_scenario(make_map(rows=5,cols=5,terrain_overrides={(1,0):'water',(2,0):'rough',(3,0):'urban'}),units,max_phases=6)
state=make_state(units,phase=2,score=-125,city_owner={'hex-3-0':'blue','hex-2-0':'red'})
md=map.MapData(); ud=unit.UnitData(); map.fromPortable(param['map'],md); unit.fromPortable(units,ud,md)
x=o.make_observation(param,state,md,ud)
expected=np.zeros((16,5,5))
expected[0,0,0]=1
# Literal neighbors of even-column corner; water destination is unavailable.
expected[1,1,0]=1
expected[2,0,0]=.4; expected[2,1,1]=1
expected[3,3,3]=.7; expected[3,4,4]=1
for channel,row,col in [(4,0,0),(5,1,1),(6,3,3),(7,4,4)]: expected[channel,row,col]=1
expected[8]=1; expected[8,0,1:4]=0
expected[9,0,1]=1; expected[10,0,2]=1; expected[11,0,3]=1
expected[12,0,3]=1; expected[13,0,2]=1
expected[14]=.9**3; expected[15]=-.125
np.testing.assert_allclose(x,expected)
state['status']['onMove']='red'
red=o.make_observation(param,state,md,ud)
np.testing.assert_array_equal(red[[2,3,12,13]],x[[3,2,13,12]])
''',tmp_path)
