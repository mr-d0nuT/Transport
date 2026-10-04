const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

const visCode = `
/* --- AHORRO DE BATERÍA (Page Visibility) --- */
let wasWatchingGPS = false;
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pausar auto-refresco
        if (window._refreshInterval) clearInterval(window._refreshInterval);
        
        // Pausar GPS si no estamos en medio de una ruta activa
        if (!activeTrip && watchId) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
            wasWatchingGPS = true;
        }
    } else {
        // Reanudar auto-refresco si hay parada seleccionada
        if (currentStop) {
            fetchArrivals(currentStop, true);
        }
        
        // Reanudar GPS
        if (wasWatchingGPS) {
            watchPosition();
            wasWatchingGPS = false;
        }
    }
});
`;

app += '\n' + visCode;
fs.writeFileSync('app.js', app);
