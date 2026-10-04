const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

const routingLogic = `
/* --- ROUTING AVANZADO (Fase 2) --- */
window._routingProfile = 'normal'; // 'normal', 'atleta', 'relajado'
window._weatherRouting = false;

window.toggleRoutingProfile = function() {
    const profiles = ['normal', 'atleta', 'relajado'];
    const idx = profiles.indexOf(window._routingProfile);
    window._routingProfile = profiles[(idx + 1) % profiles.length];
    
    const btn = document.getElementById('btnProfile');
    if (window._routingProfile === 'normal') btn.innerText = '🏃 Perfil: Normal';
    if (window._routingProfile === 'atleta') btn.innerText = '⚡ Perfil: Atleta (Transbordos Rápidos)';
    if (window._routingProfile === 'relajado') btn.innerText = '🐢 Perfil: Relajado (Transbordos Lentos)';
    
    replanJourney(); // Recalcular con el nuevo perfil
};

window.toggleWeatherRouting = function() {
    window._weatherRouting = !window._weatherRouting;
    const btn = document.getElementById('btnWeather');
    btn.innerText = window._weatherRouting ? '🌧️ Ruta A Cubierto: On' : '☀️ Ruta A Cubierto: Off';
    if (window._weatherRouting) {
        btn.style.background = '#0078BF';
        btn.style.color = 'white';
    } else {
        btn.style.background = 'var(--bg)';
        btn.style.color = 'inherit';
    }
    replanJourney();
};

function getTransferPenalty() {
    if (window._routingProfile === 'atleta') return 1 * 60000;
    if (window._routingProfile === 'relajado') return 8 * 60000;
    return 4 * 60000;
}

function getWalkSpeed() {
    if (window._routingProfile === 'atleta') return 90; // 90 m/min
    if (window._routingProfile === 'relajado') return 45; // 45 m/min
    return 65; // normal
}

// Hook en A_PIE_MIN y penaSinEscaleras
window.A_PIE_MIN = function(dist) { return Math.ceil(dist / getWalkSpeed()) * 60000; };
window.PENA_CLIMA = function(it) {
    if (!window._weatherRouting) return 0;
    // Si está lloviendo, penalizar caminar fuera de estaciones (y primar el metro)
    let outdoorWalk = 0;
    it.legs.forEach(l => {
        if (!l.transitLeg) outdoorWalk += l.distance;
    });
    return outdoorWalk * 2000; // Penalización inmensa por caminar bajo la lluvia
};
`;

// Inyectar antes de function journeyScore
app = app.replace('function journeyScore(it) {', routingLogic + '\n        function journeyScore(it) {');

// Sustituir la constante del transbordo y añadir PENA_CLIMA
app = app.replace(
    'return it.endTime + Math.max(0, journeyWalkDist(it) - 400) * 1000\n                 + Math.max(0, tramos - 1) * 4 * 60000 + penaSinEscaleras(it);',
    'return it.endTime + Math.max(0, journeyWalkDist(it) - 400) * 1000\n                 + Math.max(0, tramos - 1) * getTransferPenalty() + penaSinEscaleras(it) + window.PENA_CLIMA(it);'
);

// Bicing logic en renderWalkWarning
const bicingLogic = `
            if (minimo > 10) {
                // SUGERENCIA BICING
                document.getElementById('journeyLongWalkMsg').innerHTML = \`
                    <div style="background:#E3312C15; padding:12px; border-radius:12px; border-left:4px solid #E3312C; margin-bottom:12px;">
                        <b>🚲 Sugerencia de Micromovilidad:</b> Tienes más de 10 minutos a pie (\${minimo} min). 
                        <br>Coge un Bicing (estación a 50m) y llegarás en \${Math.round(minimo / 3)} minutos al destino.
                    </div>
                    \` + document.getElementById('journeyLongWalkMsg').innerHTML;
            }
`;
app = app.replace(
    /document\.getElementById\('journeySection'\)\.style\.display = 'block';/,
    "document.getElementById('journeySection').style.display = 'block';\n" + bicingLogic
);

fs.writeFileSync('app.js', app);
