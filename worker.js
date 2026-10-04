// worker.js - Procesamiento en 2º plano para cálculos pesados y JSONs
self.onmessage = async function(e) {
    const { id, type, data } = e.data;
    
    if (type === 'HAVERSINE') {
        // Mueve el cálculo pesado del algoritmo Haversine fuera del hilo principal
        const { lat, lon, points } = data;
        const R = 6371e3; // Radio de la Tierra en metros
        const phi1 = lat * Math.PI / 180;
        const cosPhi1 = Math.cos(phi1);
        
        const distances = new Float64Array(points.length);
        for (let i = 0; i < points.length; i++) {
            const pt = points[i];
            const phi2 = pt.lat * Math.PI / 180;
            const deltaPhi = (pt.lat - lat) * Math.PI / 180;
            const deltaLambda = (pt.lon - lon) * Math.PI / 180;
            const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
                      cosPhi1 * Math.cos(phi2) *
                      Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
            distances[i] = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        }
        self.postMessage({ id, results: distances });
    }
    else if (type === 'FETCH_SHARD') {
        // Carga de JSONs masivos en el hilo secundario para liberar memoria principal
        try {
            const response = await fetch(`./tmb-sched/${data.name}.json`);
            const json = await response.json();
            self.postMessage({ id, results: json });
        } catch (err) {
            self.postMessage({ id, error: true });
        }
    }
};
