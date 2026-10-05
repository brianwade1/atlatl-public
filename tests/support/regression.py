"""Test-local daily runner: independent artifacts and deterministic reverse order."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def command(suite, label, *, reverse=False, coverage=False):
    output = ROOT / 'tests/.artifacts' / label
    args = [sys.executable, '-B', '-m', 'pytest']
    if suite == 'full':
        args.append('tests')
    args += ['-q', '--durations=15', f'--basetemp={ROOT / "tests/.tmp" / label}',
             f'--output={output / "playwright"}',
             f'--junitxml={output / "results.xml"}']
    if reverse:
        args.append('--reverse-order')
    if coverage:
        args += ['--cov', f'--cov-config={ROOT / "tests/coverage.ini"}',
                 f'--cov-report=json:{output / "python.json"}',
                 f'--cov-report=html:{output / "html"}', '--cov-report=term',
                 f'--js-coverage-dir={output / "javascript"}']
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='1729',
               ATLATL_COVERAGE_ROOT=str(ROOT),
               COVERAGE_FILE=str(output / '.coverage'))
    return args, env, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=['core', 'full'])
    parser.add_argument('--repeat', action='store_true', help='normal, normal, reverse')
    parser.add_argument('--coverage', action='store_true')
    options = parser.parse_args()
    for index in range(3 if options.repeat else 1):
        label = f'{options.suite}-{index + 1}'
        args, env, output = command(options.suite, label, reverse=index == 2,
                                    coverage=options.coverage)
        output.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(args, cwd=ROOT, env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
