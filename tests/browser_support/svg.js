// Real SVG/model modules; helpers only arrange inputs and serialize native geometry.
import {Map as GameMap} from '/browser/map.js';
import {Unit} from '/browser/unit.js';
import {SVGUtil} from '/browser/svg-util.js';
import {SVGCreateView} from '/browser/svg-create-view.js';
import {SVGMapView} from '/browser/svg-map-view.js';
import {SVGSetupMarker} from '/browser/svg-setup-marker.js';
import {SVGCityMarker} from '/browser/svg-city-marker.js';
import {SVGUnitSymbol} from '/browser/svg-unit-symbol.js';
import {SVGGui} from '/browser/svg-gui.js';
import {MapEditorPalette} from '/browser/svg-map-editor-palette.js';
import {MapEditorControl} from '/browser/map-editor-control.js';
import {UnitPlacementControl} from '/browser/unit-placement-control.js';
import {HumanPlayerControl} from '/browser/human-player-control.js';
Object.assign(window, {GameMap, Unit, SVGUtil, SVGCreateView, SVGMapView,
    SVGSetupMarker, SVGCityMarker, SVGUnitSymbol, SVGGui, MapEditorPalette,
    MapEditorControl, UnitPlacementControl, HumanPlayerControl});
window.param = {width: 8, x_hex_margin: 10, y_hex_margin: 4,
    x_palette_margin: 1, y_palette_margin: 1, palette_width: 4};
window.box = b => [b.x, b.y, b.width, b.height];
window.attrs = e => Object.fromEntries([...e.attributes].map(a => [a.name,a.value]));
window.root = () => {
    SVGCreateView.param = param;
    SVGCreateView.svg = SVGUtil.recreateMysvg();
    return SVGCreateView.svg;
};
window.drawMap = (rows=2, cols=2) => {
    GameMap.createHexGrid(rows, cols);
    root();
    SVGMapView.add(param, SVGCreateView.svg, () => {}, () => {});
};
window.makeUnit = (overrides={}) => {
    const u = new Unit.Unit({uniqueId:'blue Alpha', longName:'Alpha', name:'A',
        faction:'blue', type:'infantry', echelon:'regiment',
        currentStrength:73, fullStrength:100, ...overrides});
    Unit.units.push(u);
    u.setHex(GameMap.hexes[0]);
    SVGUnitSymbol.create(u, e => window.unitClick = e.currentTarget.id);
    return u;
};
