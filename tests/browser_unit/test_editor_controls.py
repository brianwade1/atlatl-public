"""S11 exported editor handlers on attached, real SVG elements."""
import pytest

from tests.support.creation_pages import event
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


@pytest.fixture
def editor(svg_page):
    svg_page.evaluate('''() => {
        GameMap.createHexGrid(3,2); SVGCreateView.createMapEditorView(param);
        MapEditorControl.fitMapToContent(SVGCreateView.svg);
    }''')
    return svg_page


@pytest.mark.parametrize('terrain,color', [('clear','white'), ('water','powderblue'),
    ('marsh','palegreen'), ('rough','wheat'), ('urban','lightgray'), ('unused','gray')])
def test_fill_drag_and_mouseup(editor, terrain, color):
    event(editor, 'fill-type-' + terrain)
    event(editor, 'hex-0-0')
    event(editor, 'hex-0-1', 'mouseover')
    event(editor, 'mysvg', 'mouseup')
    event(editor, 'hex-0-2', 'mouseover')
    assert editor.evaluate('''() => ['hex-0-0','hex-0-1','hex-0-2'].map(id=>
        [GameMap.hexIndex[id].terrain,document.getElementById(id).getAttribute('fill')])''') == [
            [terrain, color], [terrain, color], ['clear', 'white']]


@pytest.mark.parametrize('name,color,width', [('normal','black','0.1'),
    ('stream','blue','0.3'), ('river','blue','0.5')])
def test_edge_palette_and_drag(editor, name, color, width):
    result = editor.evaluate('''name => {
        const c=MapEditorControl, edge=GameMap.edges[0], el=document.getElementById(edge.id);
        c.paletteEdgeMouseDown.call(document.getElementById('edge-type-'+name),{});
        c.svgMouseDownHandler.call(SVGCreateView.svg,{}); c.edgeMouseOver.call(el,{});
        c.svgMouseUpHandler({});
        return [edge.type,el.getAttribute('stroke'),el.getAttribute('stroke-width')];
    }''', name)
    assert result == [name, color, width]


def test_setup_replace_erase_and_drag(editor):
    for faction in ['blue', 'red', 'erase']:
        event(editor, 'setup-type-' + faction)
        event(editor, 'hex-0-0')
        event(editor, 'hex-0-1', 'mouseover')
        event(editor, 'mysvg', 'mouseup')
        assert editor.evaluate('''() => ['hex-0-0','hex-0-1'].map(id=>[
            GameMap.hexIndex[id].setup, SVGSetupMarker.setupMarkerIndex[id]?.getAttribute('fill')??null])''') == (
                [[None, None]] * 2 if faction == 'erase' else [[f'setup-type-{faction}', faction]] * 2)


def test_path_segments_replace_erase_and_mouseup(editor):
    for palette, expected in [('edge-type-road','road'), ('edge-type-path','path'), ('path-type-erase',None)]:
        editor.evaluate('window.previousPaths=[...document.querySelectorAll("[id^=path-hex-]")]')
        event(editor, palette)
        event(editor, 'hex-0-0')
        event(editor, 'hex-0-1', 'mouseover')
        event(editor, 'hex-0-1', 'mouseover')  # no self segment
        event(editor, 'hex-0-2', 'mouseover')
        event(editor, 'mysvg', 'mouseup')
        event(editor, 'hex-1-2', 'mouseover')
        result = editor.evaluate('''() => Object.values(GameMap.pathIndex).map(p=>
            [p.type,document.getElementById(p.id).getAttribute('stroke'),
                document.getElementById(p.id).getAttribute('stroke-width')])''')
        assert result == ([[expected, 'black' if expected=='road' else 'gray', '0.2']] * 2 if expected else [])
        assert editor.evaluate('window.previousPaths.every(e=>!e.isConnected)')
        assert editor.locator('[id^="path-hex-"]').count() == (2 if expected else 0)
    # Mouse-up must clear the remembered endpoint as well as dragging.
    event(editor, 'edge-type-road')
    event(editor, 'hex-1-0')
    assert editor.evaluate('Object.keys(GameMap.pathIndex).length') == 0


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K10: path palette uses edge IDs')
def test_path_palette_identity_independent_of_path_model(editor):
    ids = editor.locator('[id$="-road"], [id$="-path"]').evaluate_all('(els)=>els.map(e=>e.id)')
    if ids == ['edge-type-road', 'edge-type-path']:
        raise KnownDefect('K10: palette emits edge category IDs before any Map.addPath call')
    assert ids == ['path-type-road', 'path-type-path']


def test_shift_zoom_ends_drag_and_normal_click_resumes(editor):
    event(editor, 'fill-type-water')
    event(editor, 'hex-0-0')
    before = editor.locator('#mysvg').get_attribute('viewBox')
    event(editor, 'hex-0-1', shiftKey=True, clientX=400, clientY=300)
    assert editor.locator('#mysvg').get_attribute('viewBox') != before
    event(editor, 'hex-0-2', 'mouseover', shiftKey=True)
    assert editor.evaluate("GameMap.hexIndex['hex-0-1'].terrain") == 'clear'
    assert editor.evaluate("GameMap.hexIndex['hex-0-2'].terrain") == 'clear'
    event(editor, 'hex-0-1', shiftKey=True, clientX=400, clientY=300)
    assert editor.locator('#mysvg').get_attribute('viewBox') == before
    event(editor, 'hex-0-1')
    assert editor.evaluate("GameMap.hexIndex['hex-0-1'].terrain") == 'water'
