import pytest
from tests.support.s16 import probe

pytestmark=[pytest.mark.scripts,pytest.mark.integration]


@pytest.mark.parametrize('case',['valid','missing','key'])
def test_archive_script(tmp_path,case):
    source="import runpy\n"
    if case=='valid': source+="np.savez('evaluations.npz',results=[[1,3],[2,6]],timesteps=[10,20])\n"
    if case=='key': source+="np.savez('evaluations.npz',timesteps=[10,20])\n"
    if case=='valid':
        result=probe(source+"runpy.run_path(str(SERVER_DIR/'read_log.py'))",tmp_path)
        assert 'results' in result.stdout and 'timesteps' in result.stdout
        assert result.stdout.splitlines()[-2:]==['2.0','4.0']
    else:
        probe(source+f"with pytest.raises({'FileNotFoundError' if case=='missing' else 'KeyError'}): runpy.run_path(str(SERVER_DIR/'read_log.py'))",tmp_path)
