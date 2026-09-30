"""S12 real DOM events and narrowly matched controller defects."""
import pytest

from tests.support.live_play import play_page, observe, scenario, sent, down, marks
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


def ready(p, **kwargs):
    p.locator('#blue').click()
    observe(p, **kwargs)


@pytest.mark.parametrize('waiting', [True, False])
def test_waiting_and_exhausted_ignore_selection(play_page, waiting):
    p = play_page
    units = scenario()['units']
    units[0]['canMove'] = waiting
    ready(p, units=units, on_move='red' if waiting else 'blue')
    down(p, 'blue A')
    assert marks(p) == 0
    assert len(sent(p)) == 1


@pytest.mark.parametrize('kind,target,action', [
    ('move','mark hex-0-1',{'type':'move','mover':'blue A','destination':'hex-0-1'}),
    ('fire','mark red A',{'type':'fire','source':'blue A','target':'red A'}),
    ('self','mark hex-0-0',None),
])
def test_selection_marker_actions_once(play_page, kind, target, action):
    p = play_page
    units = scenario()['units']
    if kind == 'fire':
        units[2]['hex'] = 'hex-0-1'
    ready(p, units=units)
    down(p, 'blue A')
    assert marks(p) > 1
    down(p, target)
    assert sent(p)[1:] == ([] if action is None else [{'type':'action','action':action}])
    if kind == 'self':
        assert marks(p) == 0


def test_waiting_marker_and_reset_and_end_phase(play_page):
    p = play_page
    ready(p)
    down(p, 'blue A')
    p.evaluate('Play._on_move=false')
    down(p, 'mark hex-0-1')
    assert len(sent(p)) == 1
    p.evaluate('HumanPlayerControl.resetGuiState(); Play._on_move=true')
    assert marks(p) == 0
    down(p, 'blue A')
    assert marks(p) > 1
    p.locator('#end-move').click()
    assert marks(p) == 0
    assert sent(p)[1:] == [{'type':'action','action':{'type':'pass'}}]
    down(p, 'blue A')
    assert marks(p) > 1


@pytest.mark.parametrize('target,action', [
    ('hex-0-1', {'type':'setup-move','mover':'blue A','destination':'hex-0-1'}),
    ('blue B', {'type':'setup-exchange','mover':'blue A','friendly':'blue B'}),
    ('hex-0-2', None), ('red A', None), ('hex-1-2', None),
])
def test_setup_destinations_and_exchange(play_page, target, action):
    ready(play_page, setup=True)
    down(play_page, 'blue A')
    down(play_page, target)
    assert sent(play_page)[1:] == ([] if action is None else [{'type':'action','action':action}])


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K27: direct hex references undefined moveTargets')
def test_direct_hex_move(play_page):
    p = play_page
    ready(p)
    down(p, 'blue A')
    error = p.evaluate('''() => {try {
        HumanPlayerControl.hexMouseDownHandler.call(document.getElementById('hex-0-1'),new MouseEvent('mousedown'));
        return null;
    } catch(e) {return [e.name,e.message];}}''')
    if error == ['ReferenceError','moveTargets is not defined']:
        assert sent(p)[1:] == []
        raise KnownDefect('K27: direct hex throws ReferenceError before sending')
    assert error is None
    assert sent(p)[1:] == [{'type':'action','action':{'type':'move','mover':'blue A','destination':'hex-0-1'}}]


@pytest.mark.parametrize('probe', ['wrong-faction','terminal'])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K28: selection lacks faction/terminal guard')
def test_ineligible_selection(play_page, probe):
    p = play_page
    ready(p, terminal=probe=='terminal')
    target = 'red A' if probe=='wrong-faction' else 'blue A'
    down(p, target)
    result = p.evaluate('HumanPlayerControl.selectedUnit?.uniqueId')
    assert len(sent(p)) == 1
    if result == target and marks(p) > 0:
        raise KnownDefect('K28: ineligible unit selected and action markers rendered')
    assert marks(p) == 0


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K29: observation clears marks without resetting selection mode')
def test_observation_resets_selection_mode(play_page):
    p = play_page
    ready(p)
    down(p, 'blue A')
    observe(p, phase=2)
    assert marks(p) == 0
    down(p, 'blue B')
    result = p.evaluate('HumanPlayerControl.selectedUnit?.uniqueId')
    if result == 'blue A' and marks(p) == 0:
        raise KnownDefect('K29: next selection ignored after observation')
    assert result == 'blue B' and marks(p) > 0
