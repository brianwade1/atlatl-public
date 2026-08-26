export var SVGUtil = {};

import {SVGCreateView} from './svg-create-view.js';
import { Style } from './style.js';

(function() {
    
    SVGUtil.svgNS = 'http://www.w3.org/2000/svg';
    
    SVGUtil.recreateMysvg = function() {
        var svg = document.getElementById('mysvg');
        if (svg)  svg.remove();
        svg = makeSvgElement();
        document.body.appendChild(svg);
        return svg;
    }

    SVGUtil.vbZoomedWidth = 100;
    SVGUtil.vbZoomedHeight = 40;

    function setViewBox(vbox, bounds) {
        vbox.x = bounds.x;
        vbox.y = bounds.y;
        vbox.width = bounds.width;
        vbox.height = bounds.height;
    }

    SVGUtil.ViewBoxControl = function() {
        this.viewBoxZoomedIn = true;
        this.fittedViewBox = null;
    };

    SVGUtil.ViewBoxControl.prototype.fitToContent = function(svg) {
        const bbox = svg.getBBox();
        if (!bbox.width || !bbox.height)
            return;

        const padding = 1;
        this.fittedViewBox = {
            x: bbox.x - padding,
            y: bbox.y - padding,
            width: bbox.width + 2 * padding,
            height: bbox.height + 2 * padding
        };

        setViewBox(svg.viewBox.baseVal, this.fittedViewBox);
        svg.style.aspectRatio = `${this.fittedViewBox.width} / ${this.fittedViewBox.height}`;
        svg.style.height = "auto";
        svg.style.display = "block";
        this.viewBoxZoomedIn = false;
    };

    SVGUtil.ViewBoxControl.prototype.toggleZoom = function(svg, evt) {
        const vbox = svg.viewBox.baseVal;
        if (this.viewBoxZoomedIn) {
            // Zoom out
            if (this.fittedViewBox) {
                setViewBox(vbox, this.fittedViewBox);
            }
            else {
                const bbox = svg.getBBox();
                const bbw = bbox.width + bbox.x;
                const bbh = bbox.height + bbox.y;
                if (vbox.width < bbw || vbox.height < bbh) {
                    const c = Math.max(bbw/vbox.width, bbh/vbox.height);
                    vbox.x = 0;
                    vbox.y = 0;
                    vbox.width *= c;
                    vbox.height *= c;
                }
            }
            this.viewBoxZoomedIn = false;
            return;
        }

        // Zoom in centered on mouse
        const bb = svg.getBoundingClientRect();
        const x_frac = (evt.x - bb.x)/bb.width;
        const y_frac = (evt.y - bb.y)/bb.height;
        const xc_vb = vbox.x + x_frac * vbox.width;
        const yc_vb = vbox.y + y_frac * vbox.height;
        if (this.fittedViewBox) {
            const scale = Math.min(
                1,
                SVGUtil.vbZoomedWidth / this.fittedViewBox.width,
                SVGUtil.vbZoomedHeight / this.fittedViewBox.height
            );
            const zoomedWidth = this.fittedViewBox.width * scale;
            const zoomedHeight = this.fittedViewBox.height * scale;
            const maxX = this.fittedViewBox.x + this.fittedViewBox.width - zoomedWidth;
            const maxY = this.fittedViewBox.y + this.fittedViewBox.height - zoomedHeight;
            vbox.x = Math.max(this.fittedViewBox.x, Math.min(xc_vb - zoomedWidth/2, maxX));
            vbox.y = Math.max(this.fittedViewBox.y, Math.min(yc_vb - zoomedHeight/2, maxY));
            vbox.width = zoomedWidth;
            vbox.height = zoomedHeight;
        }
        else {
            vbox.x = xc_vb - SVGUtil.vbZoomedWidth/2;
            vbox.y = yc_vb - SVGUtil.vbZoomedHeight/2;
            vbox.width = SVGUtil.vbZoomedWidth;
            vbox.height = SVGUtil.vbZoomedHeight;
        }
        this.viewBoxZoomedIn = true;
    };

    function makeSvgElement() {
        let svg = document.createElementNS(SVGCreateView.svgNS, 'svg');
        svg.setAttributeNS(null, 'preserveAspectRatio', 'xMidYMid meet');
        svg.setAttributeNS(null, 'viewBox', '0 0 '+SVGUtil.vbZoomedWidth+' '+SVGUtil.vbZoomedHeight);
        svg.setAttributeNS(null, 'id', 'mysvg');
        svg.setAttributeNS(null, 'style', 'border:1px gray solid;');
        svg.setAttributeNS(null, 'width', '100%');
        return svg;
    }
    SVGUtil.makeSvgElement = makeSvgElement;
    
    SVGUtil.gridToSVG = function(x_grid, y_grid, x_hex_margin, y_hex_margin, hex_width) {
        // Convert grid coords (fine square grid that contains all hex verts) to svg coords
        let x_spacing = hex_width/4;
        let y_spacing = hex_width*Math.sqrt(3)/4;
        let x_svg = x_hex_margin + x_grid * x_spacing;
        let y_svg = y_hex_margin + y_grid * y_spacing;
        return {x:x_svg, y:y_svg};
    }
    
    SVGUtil.VerticalCenteredLayout = function(par, topmid) {
        this.group = document.createElementNS(SVGCreateView.svgNS, 'g');
        this.group.setAttributeNS(null, 'style', 'pointer-events:none;');
        this.topmid = topmid; //anchor
        this.offset = 0;
        par.appendChild(this.group);
    }
    
    SVGUtil.VerticalCenteredLayout.prototype = {
        addBigSpace : function() { this.addInvisibleBox(2); },
        addSmallSpace : function() { this.addInvisibleBox(0.5); },
        addInvisibleBox : function(height) {
            let width = 2;
            let x = this.topmid.x - width/2;
            let y = this.topmid.y + this.offset;
            this.add(SVGUtil.makeRect(x,y,width,height,"transparent","transparent")); 
        },
        add : function(elem, originAtBottom) {
            this.group.appendChild(elem);
            var bb = elem.getBBox()
            // Place so bbox starts at offset
            let x = this.topmid.x-bb.width/2;
            let y = this.topmid.y+this.offset;
            if (originAtBottom)
                y += bb.height;
            elem.setAttributeNS(null, 'transform', `translate(${x} ${y})`);
            this.offset += bb.height;
        },
        drawFrame : function() {
            let [xm,ym] = [0.2,0.2];
            let bb = this.group.getBBox();
            this.group.appendChild( SVGUtil.makeRect(bb.x-xm,bb.y-ym,bb.width+2*xm,bb.height+2*ym,'transparent') );
        }
    };
    
    SVGUtil.makeLabel = function(txt) {
        var label = document.createElementNS(SVGCreateView.svgNS, 'text');
        label.setAttributeNS(null, 'style', 'font: 1px sans-serif;');
        label.setAttributeNS(null, 'stroke', 'black');
        label.setAttributeNS(null, 'stroke-width', '0');
        var textNode = document.createTextNode(txt);
        label.appendChild(textNode);
        return label;
    }
    
    SVGUtil.makeRect = function(x,y,width,height,fill,stroke) {
        if (typeof(stroke)==="undefined")  stroke="black";
        let element = document.createElementNS(SVGCreateView.svgNS, 'rect');
        element.setAttributeNS(null, 'x', x);
        element.setAttributeNS(null, 'y', y);
        element.setAttributeNS(null, 'width', width);
        element.setAttributeNS(null, 'height', height);
        element.setAttributeNS(null, 'stroke', stroke);
        element.setAttributeNS(null, 'fill', fill);
        element.setAttributeNS(null, 'stroke-width', '0.1');
        return element;
    }
    
    SVGUtil.makeLineInRect = function(x,y,width,height,lineStyle) {
        let group = document.createElementNS(SVGCreateView.svgNS, 'g');
        let rect = SVGUtil.makeRect(x,y,width,height,"transparent","black");
        let line = document.createElementNS(SVGCreateView.svgNS, 'path');
        let [xa, ya, xb, yb] = [x, y+height/2, x+width, y+height/2];
        line.setAttributeNS(null, 'd', 'M '+xa+" "+ya+" L "+xb+" "+yb);
        line.setAttributeNS(null, 'stroke', lineStyle.color);
        line.setAttributeNS(null, 'stroke-width', lineStyle.width);
        group.appendChild(line);
        group.appendChild(rect);
        return group;
    }  
    
    SVGUtil.makeRectInRect = function(x,y,width,height,fill) {
        let group = document.createElementNS(SVGCreateView.svgNS, 'g');
        let rect = SVGUtil.makeRect(x,y,width,height,"transparent","black");
        let innerRect = SVGUtil.makeRect(x+width/3,y+height/3,width/3,height/3,fill,"transparent");
        group.appendChild(innerRect);
        group.appendChild(rect);
        return group;
    }  
    
    SVGUtil.makePath = function(path) {
        let param = SVGCreateView.param;
        let svg = SVGCreateView.svg;
        let elem = document.createElementNS(SVGCreateView.svgNS, 'path');
        elem.setAttributeNS(null, 'id', path.id);
        const {x:xa,y:ya} = SVGUtil.gridToSVG(path.hexA.x_grid, path.hexA.y_grid, param.x_hex_margin, param.y_hex_margin, param.width);
        const {x:xb,y:yb} = SVGUtil.gridToSVG(path.hexB.x_grid, path.hexB.y_grid, param.x_hex_margin, param.y_hex_margin, param.width);
        elem.setAttributeNS(null, 'd', 'M '+xa+" "+ya+" L "+xb+" "+yb);
        elem.setAttributeNS(null, 'stroke', Style.terrainPathIndex[path.type].color);
        //elem.setAttributeNS(null, 'fill', 'transparent');
        elem.setAttributeNS(null, 'stroke-linecap', 'round');
        elem.setAttributeNS(null, 'stroke-width', Style.terrainPathIndex[path.type].width);
        svg.appendChild(elem);
        SVGCreateView.pathIndex[path.id] = elem;
    }
    
    SVGUtil.removePath = function(path) {
        let elem = SVGCreateView.pathIndex[path.id];
        if (elem)
            elem.remove();
    }
    
    SVGUtil.setFill = function(elem, value) {
        elem.setAttributeNS(null, 'fill', value);
    };
    
    SVGUtil.setPathStyle = function(elem, style) {
        elem.setAttributeNS(null, 'stroke', style.color);
        elem.setAttributeNS(null, 'stroke-width', style.width);
    };
    
    function applySvgMatrix( mat, vec ) {
        return { x: mat.a*vec.x+mat.c*vec.y+mat.e*1, y: mat.b*vec.x+mat.d*vec.y+mat.f*1 };
    }

    function applyMatrixToBBox( mat, bbox ) {
        let raw_ul = {x: bbox.x, y: bbox.y};
        let raw_ur = {x: bbox.x + bbox.width, y: bbox.y};
        let raw_ll = {x: bbox.x, y: bbox.y + bbox.height};
        let raw_lr = {x: bbox.x + bbox.width, y: bbox.y + bbox.height};
        
        let ul = applySvgMatrix( mat, raw_ul );
        let ur = applySvgMatrix( mat, raw_ur );
        let ll = applySvgMatrix( mat, raw_ll );
        let lr = applySvgMatrix( mat, raw_lr );
        return { x: ul.x, y: ul.y, width: ur.x-ul.x, height: ll.y-ul.y }   
    }

    SVGUtil.getTransformedBBox = function( element ) {
        // First path is needed if the element is transformed, and fails otherwise
        if (element.transform.baseVal.length)
            return applyMatrixToBBox(element.transform.baseVal.consolidate().matrix, element.getBBox());
        return element.getBBox();
    }
    
}())
