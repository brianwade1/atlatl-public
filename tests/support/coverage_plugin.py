"""Opt-in Chromium precise function coverage; original scripts stay unchanged."""

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest


def case_reports(output):
    """Only this collector's hashed case files, never unrelated JSON artifacts."""
    return output.glob('[0-9a-f]' * 64 + '.json')


def pytest_addoption(parser):
    parser.addoption('--reverse-order', action='store_true', help='Reverse collected node IDs')
    parser.addoption('--js-coverage-dir', help='Write Chromium function coverage under tests/.artifacts')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--reverse-order'):
        items.reverse()


def pytest_sessionstart(session):
    destination = session.config.getoption('--js-coverage-dir')
    if destination:
        from tests.support.imports import TESTS_DIR
        output = Path(destination).resolve()
        if not output.is_relative_to(TESTS_DIR / '.artifacts'):
            raise pytest.UsageError('JavaScript coverage must stay under tests/.artifacts')
        output.mkdir(parents=True, exist_ok=True)
        for previous in case_reports(output):
            previous.unlink()
        (output / 'summary.json').unlink(missing_ok=True)


def pytest_sessionfinish(session, exitstatus):
    destination = session.config.getoption('--js-coverage-dir')
    if not destination:
        return
    output = Path(destination).resolve()
    functions = {}
    cases = 0
    for report in case_reports(output):
        data = json.loads(report.read_text(encoding='utf-8'))
        cases += 1
        for script in data['scripts']:
            for function in script['functions']:
                span = function['ranges'][0]
                key = (script['path'], script['source_hash'],
                       span['startOffset'], span['endOffset'])
                functions[key] = functions.get(key, False) or span['count'] > 0
    rows = []
    for path in sorted({key[0] for key in functions}):
        observed = [executed for key, executed in functions.items() if key[0] == path]
        rows.append({'path': path, 'observed_functions': len(observed),
                     'executed_functions': sum(observed)})
    (output / 'summary.json').write_text(json.dumps({
        'browser_cases': cases, 'scripts': rows,
        'limits': 'Loaded V8 function ranges only, including module top level; '
                  'unloaded scripts absent; no statement or branch percentage.',
    }, indent=2), encoding='utf-8')


@pytest.fixture(autouse=True)
def chromium_function_coverage(request, monkeypatch):
    destination = request.config.getoption('--js-coverage-dir')
    if not destination or not request.node.get_closest_marker('browser'):
        yield
        return
    from playwright.sync_api import Browser, BrowserContext, Page
    from tests.support.imports import TESTS_DIR

    output = Path(destination).resolve()
    if not output.is_relative_to(TESTS_DIR / '.artifacts'):
        raise pytest.UsageError('JavaScript coverage must stay under tests/.artifacts')
    browser = request.getfixturevalue('browser')
    if browser.browser_type.name != 'chromium':
        pytest.fail('Precise JavaScript coverage requires Chromium; run other browsers without it')
    sessions = {}
    scripts = []

    def start(page):
        session = page.context.new_cdp_session(page)
        hashes = {}
        session.on('Debugger.scriptParsed',
                   lambda script: hashes.__setitem__(script['scriptId'], script['hash']))
        session.send('Debugger.enable')
        session.send('Profiler.enable')
        session.send('Profiler.startPreciseCoverage', {'callCount': True, 'detailed': False})
        sessions[page] = (session, hashes)

    def stop(page):
        state = sessions.pop(page, None)
        if state is not None:
            session, hashes = state
            for script in session.send('Profiler.takePreciseCoverage')['result']:
                path = urlsplit(script['url']).path
                if (path.startswith('/browser/') and path.endswith(('.js', '.html'))
                        and path != '/browser/replay.js'):
                    script['source_hash'] = hashes[script['scriptId']]
                    scripts.append(script)
            session.send('Profiler.stopPreciseCoverage')
            session.detach()

    new_context, close_context, close_page = Browser.new_context, BrowserContext.close, Page.close

    def create(self, *args, **kwargs):
        context = new_context(self, *args, **kwargs)
        context.on('page', start)
        return context

    def context_close(self, *args, **kwargs):
        for page in self.pages:
            stop(page)
        return close_context(self, *args, **kwargs)

    def page_close(self, *args, **kwargs):
        stop(self)
        return close_page(self, *args, **kwargs)

    monkeypatch.setattr(Browser, 'new_context', create)
    monkeypatch.setattr(BrowserContext, 'close', context_close)
    monkeypatch.setattr(Page, 'close', page_close)
    yield
    for page in list(sessions):
        stop(page)
    rows = []
    for script in scripts:
        path = urlsplit(script['url']).path
        if (path.startswith('/browser/') and path.endswith(('.js', '.html'))
                and path != '/browser/replay.js'):
            rows.append({'path': path, 'source_hash': script['source_hash'],
                         'functions': script['functions']})
    output.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(request.node.nodeid.encode()).hexdigest()
    (output / f'{key}.json').write_text(json.dumps({
        'nodeid': request.node.nodeid, 'scripts': rows,
        'metric': 'V8 function ranges; count > 0 means executed; no branch coverage',
    }, indent=2), encoding='utf-8')
