"""S11 placement selection, exchange and unconstrained editor occupancy."""
import pytest

pytestmark = [pytest.mark.browser, pytest.mark.unit]


@pytest.mark.parametrize('action,positions', [
    ('empty',['hex-0-2','hex-0-1']), ('exchange',['hex-0-1','hex-0-0']),
    ('same',['hex-0-0','hex-0-1']), ('occupied',['hex-0-1','hex-0-1'])])
def test_selection_move_exchange_and_end(svg_page, action, positions):
    r = svg_page.evaluate('''action => {
        drawMap(3,1); const a=makeUnit(), b=makeUnit({uniqueId:'red Bravo',faction:'red'});
        b.setHex(GameMap.hexIndex['hex-0-1']); SVGUnitSymbol.moveSymbolToHex(b.uniqueId,b.hex);
        const c=UnitPlacementControl, symbol=u=>SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole;
        const before=[symbol(a).getAttribute('transform'),symbol(b).getAttribute('transform')];
        c.unitMouseDownHandler.call(symbol(a),{});
        const selected=SVGCreateView.svg.children.length;
        if(action==='exchange') c.unitMouseDownHandler.call(symbol(b),{});
        else if(action==='same') c.unitMouseDownHandler.call(symbol(a),{});
        else c.hexMouseDownHandler.call(document.getElementById(action==='empty'?'hex-0-2':'hex-0-1'),{});
        const ended=SVGCreateView.svg.children.length;
        c.hexMouseDownHandler.call(document.getElementById('hex-0-0'),{});
        return {positions:[a.hex.id,b.hex.id], before,
            after:[symbol(a).getAttribute('transform'),symbol(b).getAttribute('transform')],
            selection:[selected,ended], occupancy:Object.fromEntries(Object.entries(Unit.occupancy)
                .map(([k,v])=>[k,v.map(u=>u.uniqueId)]))};
    }''', action)
    assert r['positions'] == positions
    assert r['selection'][0] == r['selection'][1] + 1
    for hex_id in ['hex-0-0','hex-0-1','hex-0-2']:
        assert sorted(r['occupancy'].get(hex_id, [])) == sorted(
            uid for uid, pos in zip(['blue Alpha','red Bravo'], positions) if pos == hex_id)
    if action == 'exchange':
        assert r['after'] == r['before'][::-1]
    elif action == 'same':
        assert r['after'] == r['before']
    else:
        assert r['after'][0] != r['before'][0]
        assert r['after'][1] == r['before'][1]
        if action == 'occupied':
            assert r['after'][0] == r['after'][1]


def test_shift_does_not_select_or_move_and_preserves_pending_selection(svg_page):
    assert svg_page.evaluate('''() => {
        drawMap(2,1); const u=makeUnit(), c=UnitPlacementControl;
        const s=SVGUnitSymbol.unitSymbolIndex[u.uniqueId].whole, h=document.getElementById('hex-0-1');
        c.unitMouseDownHandler.call(s,{shiftKey:true}); c.hexMouseDownHandler.call(h,{});
        const first=u.hex.id;
        c.unitMouseDownHandler.call(s,{}); c.hexMouseDownHandler.call(h,{shiftKey:true});
        const second=u.hex.id; c.hexMouseDownHandler.call(h,{});
        return [first,second,u.hex.id];
    }''') == ['hex-0-0','hex-0-0','hex-0-1']
