let loadedShapes = null;
let currentZoomBus = false;

async function loadBackgroundTransit() {
    try {
        const res = await fetch('shapes.json');
        loadedShapes = await res.json();
        drawBackgroundTransit();
        map.on('zoomend', drawBackgroundTransit);
    } catch (e) {
        console.warn('No se pudieron cargar las líneas', e);
    }
}

function drawBackgroundTransit() {
    if (!loadedShapes) return;
    const showBus = map.getZoom() >= 13;
    if (showBus === currentZoomBus && backgroundTransitLayer.getLayers().length > 0) return; // Ya dibujado
    
    backgroundTransitLayer.clearLayers();
    currentZoomBus = showBus;
    
    Object.values(loadedShapes).forEach(line => {
        if (!line.p || line.p.length === 0) return;
        // line.t == 3 es Bus. Si no es bus, o si es bus y el zoom es >= 13, lo dibujamos.
        // Espera, en shapes.json metí "t"? ¡Aún no!
        // Necesito añadir "t": rtype a build_shapes.py!
