"""Execute original examples with recording external training boundaries."""
import pytest
from tests.support.s16 import probe

pytestmark=[pytest.mark.scripts,pytest.mark.unit]


@pytest.mark.parametrize('name,steps,algorithm',[
    ('train_cnn_sbl3',1000,'DQN'),('train_mlp_sbl3',4000,'PPO'),
    ('train_multigym',3000,'DQN'),('train_viz_demo',400,'PPO')])
def test_training_wiring_and_retrieved_features(tmp_path,name,steps,algorithm):
    probe(f"name={name!r}; steps={steps}; algorithm={algorithm!r}\n"+'''
import runpy,os,types
import stable_baselines3 as sb
import stable_baselines3.common.evaluation as evaluation
import stable_baselines3.common.callbacks as callbacks
import gymnasium as gym
env=Mock(); env.reset.return_value=(np.zeros((2,5,5)),{})
env.step.return_value=(np.zeros((2,5,5)),1.,True,False,{'score':1})
model=Mock(); model.get_env.return_value=env; model.predict.return_value=(0,None)
construct=Mock(return_value=model); callback=Mock(); evaluate=Mock(return_value=(1,0))
boundary=types.ModuleType('gym_interface'); boundary.GymEnvironment=Mock(return_value=env)
multi=types.ModuleType('multigym'); multi.GymEnvironment=boundary.GymEnvironment
original_chdir=os.chdir
def chdir(path):
    assert Path(path).resolve()==SERVER_DIR
    # Keep the unchanged script's remaining relative outputs test-local.
with patch.dict(sys.modules,{'gym_interface':boundary,'multigym':multi}), patch.object(os,'chdir',side_effect=chdir), patch.object(sb,algorithm,construct), patch.object(evaluation,'evaluate_policy',evaluate), patch.object(callbacks,'EvalCallback',callback):
    ns=runpy.run_path(str(SERVER_DIR/'sbl3'/f'{name}.py'))
assert construct.call_count==1 and model.learn.call_args.kwargs['total_timesteps']==steps
assert boundary.GymEnvironment.call_args.kwargs['saveReplay'] is False
model.save.assert_called_once_with('model_save' if algorithm=='DQN' else 'ppo_save')
assert evaluate.call_args.kwargs['n_eval_episodes']==10
if callback.called:
    for key in ['best_model_save_path','log_path']:
        if key in callback.call_args.kwargs:
            assert (Path.cwd()/callback.call_args.kwargs[key]).resolve().is_relative_to(Path.cwd())
if 'MyCNN' in ns:
    space=gym.spaces.Box(0,1,shape=(2,5,5),dtype=np.float32)
    cnn=ns['MyCNN'](space,features_dim=8)
    output=cnn(torch.ones(2,2,5,5))
    assert output.shape==(2,8) and torch.isfinite(output).all()
''',tmp_path,torch=True)


def test_gym_main_unconfigured_import_failure(tmp_path):
    probe('''
import runpy
with pytest.raises(AttributeError,match="GymEnvironment"):
    runpy.run_path(str(SERVER_DIR/'gym_main.py'))
''',tmp_path)


@pytest.mark.parametrize('name',['simple_demo.py','cnn_demo.py','testdir/read_demo.py'])
def test_portable_examples_absolute_paths_intercepted(tmp_path,name):
    probe(f"name={name!r}\n"+'''
import runpy,types
boundary=types.ModuleType('portabletorch')
portable=Mock(); boundary.PortableTorch=Mock(return_value=portable)
boundary.PortableTorch.load.return_value=portable
model=types.ModuleType('model'); model.Model=Mock()
cnn=types.ModuleType('cnn'); cnn.CNN=Mock()
with patch.dict(sys.modules,{'portabletorch':boundary,'model':model,'cnn':cnn}), patch.object(sys,'argv',['demo']):
    runpy.run_path(str(SERVER_DIR/'portabletorch'/name))
portable.print.assert_called_once_with(); portable.test.assert_called_once_with()
if name=='testdir/read_demo.py':
    assert boundary.PortableTorch.load.call_args.args[0].endswith('simple')
else:
    assert portable.save.call_count==1
    assert boundary.PortableTorch.call_args.kwargs['dependence_paths']==[]
# save/load are intercepted because these scripts derive absolute source-directory outputs.
''',tmp_path)
