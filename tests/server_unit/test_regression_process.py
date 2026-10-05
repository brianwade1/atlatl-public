"""S17 gates: child coverage, independent artifacts, and alternate order."""

import ast
import json
import subprocess
import sys

import pytest

from tests.support.imports import REPO_ROOT
from tests.support.regression import command

pytestmark = [pytest.mark.core]


@pytest.mark.unit
@pytest.mark.parametrize('exitcode', [1, 5], ids=['failure', 'empty-selection'])
def test_daily_runner_stops_and_preserves_nonzero_status(monkeypatch, exitcode):
    from types import SimpleNamespace
    from tests.support import regression
    calls = []
    monkeypatch.setattr(sys, 'argv', ['regression', 'core', '--repeat'])
    def run(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=exitcode)
    monkeypatch.setattr(regression.subprocess, 'run', run)
    assert regression.main() == exitcode
    assert len(calls) == 1


@pytest.mark.unit
def test_browser_report_unions_function_hits_across_pages(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from tests.support.coverage_plugin import pytest_sessionstart, pytest_sessionfinish
    from tests.support import imports
    monkeypatch.setattr(imports, 'TESTS_DIR', tmp_path)
    output = tmp_path / '.artifacts/javascript'
    output.mkdir(parents=True)
    session = SimpleNamespace(config=SimpleNamespace(getoption=lambda option: str(output)))
    unrelated = output / 'notes.json'
    unrelated.write_text('{"preserve": true}', encoding='utf-8')
    old_case = output / ('f' * 64 + '.json')
    old_case.write_text('{}', encoding='utf-8')
    (output / 'summary.json').write_text('{}', encoding='utf-8')
    pytest_sessionstart(session)
    assert not old_case.exists()
    assert not (output / 'summary.json').exists()
    assert unrelated.read_text(encoding='utf-8') == '{"preserve": true}'
    for index, counts in enumerate(([0, 0], [1, 0])):
        functions = [{'ranges': [{'startOffset': start, 'endOffset': start + 9,
                                  'count': count}]}
                     for start, count in zip((10, 30), counts)]
        (output / f'{index:064x}.json').write_text(json.dumps({
            'scripts': [{'path': '/browser/map.js', 'source_hash': 'map-source',
                         'functions': functions},
                        {'path': '/browser/play.html', 'source_hash': f'inline-{index}',
                         'functions': [{'ranges': [{'startOffset': 0, 'endOffset': 20,
                                                   'count': index}]}]}]}),
            encoding='utf-8')
    pytest_sessionfinish(session, 0)
    report = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
    assert report['browser_cases'] == 2
    assert report['scripts'] == [{'path': '/browser/map.js', 'observed_functions': 2,
                                  'executed_functions': 1},
                                 {'path': '/browser/play.html', 'observed_functions': 2,
                                  'executed_functions': 1}]
    assert unrelated.read_text(encoding='utf-8') == '{"preserve": true}'


@pytest.mark.unit
def test_regression_reports_and_workspaces_are_independent():
    first, env, output = command('core', 'core-1', coverage=True)
    second, other_env, other_output = command('full', 'full-3', reverse=True, coverage=True)
    assert 'tests' not in first
    assert 'tests' in second
    assert '--reverse-order' in second
    assert output != other_output
    assert env['COVERAGE_FILE'] != other_env['COVERAGE_FILE']
    assert env['PYTHONHASHSEED'] == other_env['PYTHONHASHSEED'] == '1729'
    assert next(arg for arg in first if arg.startswith('--basetemp=')) != next(
        arg for arg in second if arg.startswith('--basetemp='))
    assert next(arg for arg in first if arg.startswith('--output=')) != next(
        arg for arg in second if arg.startswith('--output='))


@pytest.mark.integration
def test_coverage_measures_child_function_after_working_directory_change(tmp_path):
    # The parent never imports status. A positive score therefore proves the
    # actual function ran in the child, and measured body lines prove tracing.
    config = tmp_path / 'coverage.ini'
    data = tmp_path / '.coverage'
    source = REPO_ROOT / 'server/status.py'
    config.write_text(f'[run]\nbranch = True\npatch = subprocess\n'
                      f'source = {REPO_ROOT / "server"}\ndata_file = {data}\n'
                      '[report]\ninclude_namespace_packages = True\n', encoding='utf-8')
    script = tmp_path / 'parent.py'
    child = (
        'import sys; from types import SimpleNamespace; '
        f'sys.path.insert(0, {str(REPO_ROOT / "server")!r}); '
        'from status import Status; '
        'state = SimpleNamespace(score=0, score_per_red_kill=1); '
        'assert Status.dscoreKill(state, "red", 7) == 7; assert state.score == 7'
    )
    script.write_text(
        'from tests.support.process_helpers import run_python\n'
        f'run_python({child!r}, cwd={str(tmp_path)!r})\n', encoding='utf-8')
    args, env, _ = command('core', 'probe')
    env['PYTHONPATH'] = str(REPO_ROOT)
    env['COVERAGE_FILE'] = str(data)
    for invocation in (
        [sys.executable, '-B', '-m', 'coverage', 'run', f'--rcfile={config}', str(script)],
        [sys.executable, '-B', '-m', 'coverage', 'combine', f'--rcfile={config}', str(tmp_path)],
    ):
        result = subprocess.run(invocation, cwd=tmp_path, env=env, capture_output=True,
                                text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
    import coverage
    assert coverage.Coverage(config_file=str(REPO_ROOT / 'tests/coverage.ini')).get_option(
        'report:include_namespace_packages') is True
    measured = coverage.Coverage(data_file=str(data), config_file=False)
    measured.load()
    lines = measured.get_data().lines(str(source))
    tree = ast.parse(source.read_text(encoding='utf-8'))
    function = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name == 'dscoreKill')
    expected = {node.lineno for node in ast.walk(function)
                if isinstance(node, (ast.Assign, ast.AugAssign, ast.Return))}
    # Else assignment was intentionally not executed by this red-only probe.
    assert function.body[0].body[0].lineno in lines
    assert function.body[-1].lineno in lines
    assert len(expected.intersection(lines)) >= 3
    assert measured.get_data().lines(str(REPO_ROOT / 'server/portabletorch/cnn.py')) == []
