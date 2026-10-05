"""Real NumPy/SciPy computations with disposable data files."""
import pytest
from tests.support.s16 import probe

pytestmark=[pytest.mark.scripts,pytest.mark.integration]


def test_statistics_import_means_sem_paired_comparisons_and_invalid_data(tmp_path):
    result=probe(r'''
Path('pass-agg.data').write_text('1\n2\n3\n')
m=load('statistics_script','stats.py')
assert m.compute_mean('pass-agg')==2
assert m.compute_sem('pass-agg')==pytest.approx(1/np.sqrt(3))
assert m.compute_mean('absent')==m.compute_sem('absent')=='unknown'
Path('other.data').write_text('0\n0\n0\n')
m.ttest('pass-agg.data','other.data')
Path('short.data').write_text('1\n')
with pytest.raises(ValueError,match='same number'): m.ttest('short.data','other.data')
with pytest.warns(RuntimeWarning): assert np.isnan(m.compute_sem('short'))
Path('empty.data').write_text('')
with pytest.warns(RuntimeWarning): assert np.isnan(m.compute_mean('empty'))
Path('bad.data').write_text('hello')
with pytest.raises(ValueError): m.compute_mean('bad')
with patch.object(m,'ttest') as spy:
    m.ttests()
    assert [call.args for call in spy.call_args_list]==[
        ('pass-agg.data','pass-agg-pseudo-q-fixed.data'),
        ('pass-agg.data','pass-agg-state-fixed.data'),
        ('pass-agg-state-fixed.data','pass-agg-pseudo-q-fixed.data'),
        ('pass-agg-state-greedy.data','pass-agg-pseudo-q-greedy.data'),
        ('stomp-scoring-greedy.data','stomp-pp.data'),
        ('stomp.data','stomp-scoring-full.data'),
        ('pass-agg-fp.data','pass-agg-state.data')]
m.means()
''',tmp_path)
    assert 'pass-agg 2.0+-' in result.stdout and 'unknown+-unknown' in result.stdout
    assert 'pass-agg.data ? other.data' in result.stdout
    import re
    p_value=float(re.search(r'p: ([0-9.eE+-]+)',result.stdout).group(1))
    assert p_value==pytest.approx(.07417990022744853)
