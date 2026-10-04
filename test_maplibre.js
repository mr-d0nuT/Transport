const assert = require('assert');

let logs = [];
const consoleWarn = console.warn;
console.warn = (...args) => logs.push(args.join(' '));

const gl = {
    getSource: () => false,
    addSource: (id, obj) => { console.log('Source added'); },
    addLayer: (layer, before) => { console.log('Layer added before:', before); },
    getStyle: () => ({ layers: [{id: 'water'}, {id: 'place_label'}] })
};

const loadedShapes = {
    "test_dir": { c: "FF0000", t: 2, p: [[41,2], [41.1, 2.1]], o: 3 }
};

async function loadBackgroundTransitGL(gl) {
    try {
        const features = Object.values(loadedShapes).filter(l => l.p && l.p.length > 0).map(line => {
            return {
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: line.p.map(pt => [pt[1], pt[0]])
                },
                properties: {
                    color: '#' + line.c,
                    offset: line.o || 0,
                    isBus: line.t === '3' || line.t === 3
                }
            };
        });
        
        if (gl.getSource('transit-shapes')) return;

        gl.addSource('transit-shapes', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: features }
        });
        
        gl.addLayer({
            id: 'transit-lines',
            type: 'line',
            source: 'transit-shapes',
            layout: {
                'line-join': 'round',
                'line-cap': 'round'
            },
            paint: {
                'line-color': ['get', 'color'],
                'line-width': ['case', ['get', 'isBus'], 2.5, 4.0],
                'line-offset': ['case', ['get', 'isBus'], 1.5, ['get', 'offset']],
                'line-opacity': [
                    'case',
                    ['get', 'isBus'],
                    ['interpolate', ['linear'], ['zoom'], 12, 0, 13, 0.6], 
                    1.0
                ]
            }
        }, gl.getStyle().layers.find(l => l.id.includes('label')) ? gl.getStyle().layers.find(l => l.id.includes('label')).id : undefined); 
    } catch (e) { console.warn('Error loading shapes in WebGL', e.message); }
}

loadBackgroundTransitGL(gl).then(() => {
    console.log("Logs:", logs);
});
