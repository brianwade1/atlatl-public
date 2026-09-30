"""S11 page boundaries and small engine-compatible creation inputs."""

from contextlib import contextmanager
import json

from tests.support.browser_helpers import checked_page
from tests.support.builders import make_map, make_scenario, make_unit
from tests.support.isolation import KnownDefect


def creation_map():
    return make_map(3, 3, setup_overrides={
        (0, 0): 'setup-type-blue', (0, 1): 'setup-type-blue',
        (2, 1): 'setup-type-red', (2, 2): 'setup-type-red'})


def oob():
    return [dict(make_unit(name=name, faction=faction, strength=strength, hex=None),
                 uniqueId=f'{faction} {name}', name=name, echelon='regiment',
                 fullStrength=100, homeOrgId='HQ', taskOrgId='TF')
            for name, faction, strength in [('Alpha', 'blue', 73), ('Bravo', 'red', 91)]]


def scenario():
    units = oob()
    units[0]['hex'], units[1]['hex'] = 'hex-0-0', 'hex-2-2'
    result = make_scenario(creation_map(), units, max_phases=8, city_score=12,
                           loss_penalty=-3)
    result['map']['fogOfWar'] = True
    return result


@contextmanager
def creation_page(page, base_url, name, *, expected_errors=(), clipboard=True,
                  defect_error=None):
    # Replace only prompt and deprecated clipboard APIs, not page logic.
    page.add_init_script('''window.promptInputs=[]; window.promptCalls=[];
        window.prompt=(...args)=>{
            window.promptCalls.push(args);
            if(!window.promptInputs.length) throw Error('Unexpected prompt');
            return window.promptInputs.shift();
        };''')
    if clipboard:
        page.add_init_script('''window.copies=[];
            document.execCommand=command=>{
                if(command!=='copy') throw Error('Unexpected execCommand');
                const el=document.activeElement;
                if(el.tagName!=='TEXTAREA') throw Error('Copy without selected textarea');
                window.copies.push(el.value); return true;
            };''')
    matched = []

    def match_error(error):
        if defect_error and str(error) == defect_error[1]:
            matched.append(str(error))

    page.on('pageerror', match_error)
    try:
        with checked_page(page, expected_page_errors=matched if defect_error else expected_errors):
            page.goto(f'{base_url}/browser/{name}.html')
            page.wait_for_function("typeof window.copy === 'function'")
            page.evaluate("() => import('/tests/browser_support/svg.js')")
            yield page
        if matched:
            assert matched == [defect_error[1]], 'Expected exactly one defect error'
            raise KnownDefect(f'{defect_error[0]}: {matched[0]}')
    finally:
        page.remove_listener('pageerror', match_error)


def hex_content(data):
    # K01 already has dedicated identity tests; compare geographic content here.
    return [{k:v for k,v in h.items() if k != 'edges'} for h in data['hexes']]


def prompt_load(page, control, value):
    page.evaluate('(value)=>window.promptInputs.push(value)',
                  json.dumps(value) if value is not None else None)
    page.locator('#' + control).click()
    assert page.evaluate('window.promptInputs.length') == 0


def copy_json(page):
    page.locator('#copy').click()
    assert page.locator('textarea').count() == 0
    return json.loads(page.evaluate('window.copies.at(-1)'))


def event(page, element_id, kind='mousedown', **kwargs):
    page.locator(f'[id="{element_id}"]').dispatch_event(kind, kwargs)


def assert_fitted(page):
    assert page.evaluate('''() => {
        const s=document.getElementById('mysvg'), v=s.viewBox.baseVal, b=s.getBBox();
        return v.width>0 && v.height>0 && v.x<=b.x && v.y<=b.y &&
            v.x+v.width>=b.x+b.width && v.y+v.height>=b.y+b.height;
    }''')
