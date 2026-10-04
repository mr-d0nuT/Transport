const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf8');

// Añadir controles de configuración al inicio del results o en el topbar
const settingsHtml = `
            <div id="routingOptions" style="padding: 10px; background: var(--bg-hover); border-radius: 12px; margin-bottom: 12px; display: flex; gap: 10px; overflow-x: auto;">
                <button onclick="toggleRoutingProfile()" id="btnProfile" style="padding: 8px 12px; border-radius: 20px; border: 1px solid var(--border); background: var(--bg); white-space: nowrap;">🏃 Perfil: Normal</button>
                <button onclick="toggleWeatherRouting()" id="btnWeather" style="padding: 8px 12px; border-radius: 20px; border: 1px solid var(--border); background: var(--bg); white-space: nowrap;">☀️ Ruta A Cubierto: Off</button>
            </div>
`;

html = html.replace('<div id="results">', settingsHtml + '\n            <div id="results">');

fs.writeFileSync('index.html', html);
