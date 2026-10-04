const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

// Modify pasoMs to respect the routing profile
const originalPasoMs = `        function pasoMs() {
            const m = pasoDatos().m;
            if (m.length < 3) return 1.25;
            const orden = [...m].sort((a, b) => a - b);
            return Math.min(1.9, Math.max(0.5, orden[Math.floor(orden.length / 2)]));
        }`;

const newPasoMs = `        function pasoMs() {
            let speed = 1.25; // 1.25 m/s por defecto
            const m = pasoDatos().m;
            if (m.length >= 3) {
                const orden = [...m].sort((a, b) => a - b);
                speed = Math.min(1.9, Math.max(0.5, orden[Math.floor(orden.length / 2)]));
            }
            
            // Ajustar según el perfil seleccionado
            if (window._routingProfile === 'atleta') return Math.max(speed, 1.8); // 1.8 m/s = muy rápido
            if (window._routingProfile === 'relajado') return Math.min(speed, 0.8); // 0.8 m/s = relajado
            return speed;
        }`;

app = app.replace(originalPasoMs, newPasoMs);

fs.writeFileSync('app.js', app);
