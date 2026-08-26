export var UnitPlacementControl ={};

import { SVGCreateView } from './svg-create-view.js';
import { Unit } from './unit.js';
import { SVGUnitSymbol } from './svg-unit-symbol.js';
import { Map } from './map.js';
import { SVGUtil } from './svg-util.js';

(function() {

var Mode = {
    SelectUnit : 0,
    PlaceUnit : 1
};

var mode = Mode.SelectUnit;
var selectedUnit = null;

var viewBoxControl = null;

function getViewBoxControl() {
    if (!viewBoxControl)
        viewBoxControl = new SVGUtil.ViewBoxControl();
    return viewBoxControl;
}

function fitMapToContent() {
    getViewBoxControl().fitToContent(SVGCreateView.svg);
}
UnitPlacementControl.fitMapToContent = fitMapToContent;

function hexMouseDownHandler(evt) {
    if (evt.shiftKey)
        return;
    if (mode === Mode.PlaceUnit) {
        let hex = Map.hexIndex[this.id];
        selectedUnit.setHex(hex);
        SVGUnitSymbol.unmarkSelected();
        SVGUnitSymbol.moveSymbolToHex(selectedUnit.uniqueId, hex);
        mode = Mode.SelectUnit;
    }
}
UnitPlacementControl.hexMouseDownHandler = hexMouseDownHandler;

function hexMouseOverHandler(evt) {
}
UnitPlacementControl.hexMouseOverHandler = hexMouseOverHandler;

function edgeMouseOver(evt) {
}
UnitPlacementControl.edgeMouseOver = edgeMouseOver;

function unitMouseDownHandler(evt) {
    if (evt.shiftKey)
        return;
    if (mode === Mode.SelectUnit) {
        selectedUnit = Unit.unitIndex[this.id];
        SVGUnitSymbol.markSelected(this);
        mode = Mode.PlaceUnit;
    }
    else if (mode === Mode.PlaceUnit) {
        SVGUnitSymbol.unmarkSelected();
        // Switch locations
        let switchTarget = Unit.unitIndex[this.id];
        let hex_swap = switchTarget.hex;
        switchTarget.setHex(selectedUnit.hex);
        selectedUnit.setHex(hex_swap);
        SVGUnitSymbol.moveSymbolToHex(selectedUnit.uniqueId, selectedUnit.hex);
        SVGUnitSymbol.moveSymbolToHex(switchTarget.uniqueId, switchTarget.hex);
        mode = Mode.SelectUnit;
    }
}
UnitPlacementControl.unitMouseDownHandler = unitMouseDownHandler;

function svgMouseDownHandler(evt) {
    if (evt.shiftKey)
        getViewBoxControl().toggleZoom(this, evt);
}
UnitPlacementControl.svgMouseDownHandler = svgMouseDownHandler;
}())
