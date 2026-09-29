"""S10 native SVG utility geometry and viewport contracts."""

import math

import pytest

from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.browser, pytest.mark.unit]


@pytest.mark.parametrize('args,expected', [
    ([0, 0, 0, 0, 4], [0, 0]),
    ([2, 2, 0, 0, 4], [2, 2 * math.sqrt(3)]),
    ([-2, 3, 10, 5, 8], [6, 5 + 6 * math.sqrt(3)]),
    ([4, -2, 1, 2, 2], [3, 2 - math.sqrt(3)]),
])
def test_grid_to_svg(svg_page, args, expected):
    assert svg_page.evaluate('a => Object.values(SVGUtil.gridToSVG(...a))', args) == pytest.approx(expected)


def test_roots_primitives_and_styles(svg_page):
    r = svg_page.evaluate('''() => {
        const detached = SVGUtil.makeSvgElement(), a = root(), b = root();
        const rect = SVGUtil.makeRect(1,2,3,4,'blue'); b.append(rect);
        const before = attrs(rect); SVGUtil.setFill(rect,'red');
        SVGUtil.setPathStyle(rect,{color:'green',width:0.7});
        const label = SVGUtil.makeLabel('<Alpha & Beta>'); b.append(label);
        const line = SVGUtil.makeLineInRect(1,2,6,4,{color:'blue',width:0.3});
        const inner = SVGUtil.makeRectInRect(0,0,6,9,'red'); b.append(line,inner);
        return {root:attrs(b), detached:detached.isConnected, old:a.isConnected,
            count:document.querySelectorAll('#mysvg').length,
            ns:[b,rect,label,line,inner].map(e=>e.namespaceURI), before,
            after:attrs(rect), label:label.textContent, labelChildren:label.children.length,
            line:[...line.children].map(attrs), inner:[...inner.children].map(attrs)};
    }''')
    assert r['detached'] is False and r['old'] is False and r['count'] == 1
    assert r['ns'] == ['http://www.w3.org/2000/svg'] * 5
    assert r['root'] == dict(preserveAspectRatio='xMidYMid meet', viewBox='0 0 100 40',
                             id='mysvg', style='border:1px gray solid;', width='100%')
    assert r['before'] == {'x':'1','y':'2','width':'3','height':'4','stroke':'black',
                           'fill':'blue','stroke-width':'0.1'}
    assert r['after'] == dict(r['before'], fill='red', stroke='green', **{'stroke-width':'0.7'})
    assert r['label'] == '<Alpha & Beta>' and r['labelChildren'] == 0
    assert r['line'][0] == {'d':'M 1 4 L 7 4','stroke':'blue','stroke-width':'0.3'}
    assert r['line'][1]['fill'] == 'transparent'
    assert r['inner'][0] == {'x':'2','y':'3','width':'2','height':'3','fill':'red',
                             'stroke':'transparent','stroke-width':'0.1'}


def test_attached_vertical_layout_and_frame(svg_page):
    r = svg_page.evaluate('''() => {
        const layout = new SVGUtil.VerticalCenteredLayout(root(),{x:0,y:0});
        const a=SVGUtil.makeRect(0,0,4,2,'red'); layout.add(a);
        layout.addSmallSpace(); layout.addBigSpace();
        const b=SVGUtil.makeRect(0,0,2,3,'blue'); layout.add(b);
        const label=SVGUtil.makeLabel('Label'); layout.add(label,true);
        const content=box(layout.group.getBBox()); layout.drawFrame();
        return {offset:layout.offset, a:box(SVGUtil.getTransformedBBox(a)),
            b:box(SVGUtil.getTransformedBBox(b)), label:box(SVGUtil.getTransformedBBox(label)),
            content, frame:box(layout.group.lastChild.getBBox()),
            order:[...layout.group.children].map(e=>e.tagName)};
    }''')
    assert r['a'] == pytest.approx([-2, 0, 4, 2])
    assert r['b'] == pytest.approx([-1, 4.5, 2, 3])
    assert r['order'] == ['rect', 'rect', 'rect', 'rect', 'text', 'rect']
    assert r['label'][0] + r['label'][2] / 2 == pytest.approx(0, abs=.05)
    assert r['label'][1] >= 7.5 - .1
    assert r['offset'] > 7.5
    x, y, w, h = r['content']
    assert r['frame'] == pytest.approx([x-.2, y-.2, w+.4, h+.4], abs=1e-5)


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K23: layout spaces apply anchor/offset twice')
def test_layout_spaces_stay_centered_at_nonzero_anchor(svg_page):
    actual = svg_page.evaluate('''() => {
        const layout=new SVGUtil.VerticalCenteredLayout(root(),{x:10,y:5});
        layout.add(SVGUtil.makeRect(0,0,4,2,'red'));
        layout.addSmallSpace(); layout.addBigSpace();
        return [...layout.group.children].map(e=>box(SVGUtil.getTransformedBBox(e)));
    }''')
    if actual == [[8,5,4,2],[18,14,2,.5],[18,15,2,2]]:
        raise KnownDefect('K23: invisible spacer coordinates and translation both include anchor/offset')
    assert actual == [[8,5,4,2],[9,7,2,.5],[9,7.5,2,2]]


@pytest.mark.parametrize('transform,expected', [('', [1,2,3,4]),
    ('translate(5 7)', [6,9,3,4]), ('scale(2 3)', [2,6,6,12])])
def test_transformed_bbox(svg_page, transform, expected):
    assert svg_page.evaluate('''t => {
        const r=SVGUtil.makeRect(1,2,3,4,'red'); root().append(r);
        if(t) r.setAttribute('transform',t);
        return box(SVGUtil.getTransformedBBox(r));
    }''', transform) == pytest.approx(expected)


@pytest.mark.parametrize('transform,wrong,expected', [
    ('rotate(90)', [-2,1,0,0], [-6,1,4,3]),
    ('skewX(45)', [3,2,3,4], [3,2,7,4]),
])
@pytest.mark.xfail(strict=True, raises=KnownDefect, reason='K22: transformed box omits rotated/skewed corners')
def test_transformed_bbox_encloses_all_corners(svg_page, transform, wrong, expected):
    actual = svg_page.evaluate('''t => {
        const r=SVGUtil.makeRect(1,2,3,4,'red'); root().append(r);
        r.setAttribute('transform',t); return box(SVGUtil.getTransformedBBox(r));
    }''', transform)
    if actual == pytest.approx(wrong, abs=1e-6):
        raise KnownDefect(f'K22: {transform}: {actual}')
    assert actual == pytest.approx(expected)


@pytest.mark.parametrize('size', [(200,80), (80,200), (20,10)])
@pytest.mark.parametrize('fraction', [(x,y) for x in (0,.5,1) for y in (0,.5,1)])
def test_fit_zoom_clamp_restore(svg_page, size, fraction):
    w, h = size
    r = svg_page.evaluate('''({size,fraction}) => {
        const s=root(); s.append(SVGUtil.makeRect(5,7,...size,'red'));
        const c=new SVGUtil.ViewBoxControl(); c.fitToContent(s);
        const fitted=box(s.viewBox.baseVal), stored={...c.fittedViewBox};
        const style=[s.style.aspectRatio,s.style.height,s.style.display];
        const bb=s.getBoundingClientRect();
        c.toggleZoom(s,{x:bb.x+fraction[0]*bb.width,y:bb.y+fraction[1]*bb.height});
        const zoom=box(s.viewBox.baseVal), zoomFlag=c.viewBoxZoomedIn;
        c.toggleZoom(s,{});
        return {fitted,stored,style,zoom,zoomFlag,restored:box(s.viewBox.baseVal),flag:c.viewBoxZoomedIn};
    }''', dict(size=size, fraction=fraction))
    fitted = [4, 6, w+2, h+2]
    assert r['fitted'] == fitted and r['restored'] == fitted
    assert r['stored'] == dict(zip(('x','y','width','height'), fitted))
    assert r['style'] == [f'{w+2} / {h+2}', 'auto', 'block']
    scale = min(1, 100/(w+2), 40/(h+2))
    zw, zh = (w+2)*scale, (h+2)*scale
    x, y = fraction
    assert r['zoom'] == pytest.approx([max(4,min(4+x*(w+2)-zw/2,4+w+2-zw)),
        max(6,min(6+y*(h+2)-zh/2,6+h+2-zh)), zw, zh], abs=2e-5)
    assert r['zoomFlag'] is True and r['flag'] is False


def test_empty_fit_and_legacy_zoom(svg_page):
    r = svg_page.evaluate('''() => {
        const s=root(), c=new SVGUtil.ViewBoxControl(); c.fitToContent(s);
        const empty=[box(s.viewBox.baseVal),c.fittedViewBox,c.viewBoxZoomedIn,s.style.aspectRatio];
        s.append(SVGUtil.makeRect(0,0,200,100,'red')); c.toggleZoom(s,{});
        const out=box(s.viewBox.baseVal), bb=s.getBoundingClientRect();
        c.toggleZoom(s,{x:bb.x+bb.width/2,y:bb.y+bb.height/2});
        return {empty,out,inside:box(s.viewBox.baseVal)};
    }''')
    assert r == dict(empty=[[0,0,100,40], None, True, ''], out=[0,0,250,100], inside=[75,30,100,40])


@pytest.mark.parametrize('rows,cols,expected', [
    (2,5,[9,3+2*math.sqrt(3),34,10*math.sqrt(3)+2]),
    (5,2,[9,3+2*math.sqrt(3),16,22*math.sqrt(3)+2]),
])
def test_fit_rectangular_rendered_map(svg_page, rows, cols, expected):
    actual = svg_page.evaluate('''([rows,cols]) => {
        drawMap(rows,cols); const c=new SVGUtil.ViewBoxControl();
        c.fitToContent(SVGCreateView.svg); return box(SVGCreateView.svg.viewBox.baseVal);
    }''', [rows,cols])
    assert actual == pytest.approx(expected, abs=1e-5)
