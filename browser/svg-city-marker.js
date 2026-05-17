export var SVGCityMarker = {};

import {SVGCreateView} from './svg-create-view.js';
import {SVGUtil} from './svg-util.js';
import {Map} from './map.js';

(function() {
    
    var _size = 0.5;
    
    SVGCityMarker.cityMarkerGroup = null;
    SVGCityMarker.cityMarkerIndex = {};
    SVGCityMarker.param = null;
    SVGCityMarker.styleIndex = {"city-owner-blue":"#ababe0", "city-owner-red":"#e0abab"};

    SVGCityMarker.init = function(param) {
        SVGCityMarker.cityMarkerGroup = document.createElementNS(SVGCreateView.svgNS, 'g');
        SVGCreateView.svg.appendChild( SVGCityMarker.cityMarkerGroup );
        SVGCityMarker.param = param;
    } 

    SVGCityMarker.addMarkers = function(hex) {
        let blueMarker = addMarker(hex,"city-owner-blue");
        let redMarker = addMarker(hex,"city-owner-red");
        SVGCityMarker.cityMarkerIndex[ hex.id ] = {blue:blueMarker, red:redMarker};
    }
    
    const addMarker = function(hex, owner) {
        let param = SVGCityMarker.param;
        let position = SVGUtil.gridToSVG(hex.x_grid, hex.y_grid, param.x_hex_margin, param.y_hex_margin, param.width);
        let x = position.x;
        let y = position.y;
        let elem = document.createElementNS(SVGCreateView.svgNS, 'circle');
        elem.setAttributeNS(null, 'cx', x);
        elem.setAttributeNS(null, 'cy', y);
        elem.setAttributeNS(null, 'r', _size);
        elem.setAttributeNS(null, 'stroke', "transparent");
        elem.setAttributeNS(null, 'fill', SVGCityMarker.styleIndex[owner]);
        elem.setAttributeNS(null, 'stroke-width', 0);
        elem.setAttributeNS(null, 'pointer-events', "none");
        elem.setAttributeNS(null, 'visibility', "hidden");
        SVGCityMarker.cityMarkerGroup.appendChild(elem);
        return elem;
    }

    SVGCityMarker.setVisible = function(value, hex, owner) {
        let marker = SVGCityMarker.cityMarkerIndex[hex.id][owner]
        let vis = "hidden";
        if (value)
            vis = "visible";
        marker.setAttributeNS(null, 'visibility', vis);
    }
    
}())