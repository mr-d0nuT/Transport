const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');
let css = fs.readFileSync('styles.css', 'utf8');

// Append CSS for HUD
css += `
/* --- HUD A LA CARRERA --- */
#hudLayer {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: 9999; display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    color: white; opacity: 0; pointer-events: none;
    transition: opacity 0.5s ease;
    backdrop-filter: blur(10px);
}
#hudLayer.active { opacity: 1; pointer-events: auto; }
#hudLine { font-size: 8rem; font-weight: 900; line-height: 1; margin: 0; }
#hudTime { font-size: 15rem; font-weight: 900; line-height: 1; margin: 0; }
#hudUnit { font-size: 3rem; font-weight: bold; }
`;
fs.writeFileSync('styles.css', css);

// Append JS for HUD and DeviceMotion
const hudJs = `
/* --- HUD A LA CARRERA (Acelerómetro) --- */
let hudEnabled = true;
let isRunning = false;
let runTimeout = null;

if (window.DeviceMotionEvent) {
    window.addEventListener('devicemotion', event => {
        if (!hudEnabled || !window._departures || window._departures.length === 0) return;
        
        const acc = event.acceleration;
        if (!acc) return;
        const totalAcc = Math.abs(acc.x) + Math.abs(acc.y) + Math.abs(acc.z);
        
        // Si el usuario agita el móvil o va corriendo (aceleración brusca > 15m/s2)
        if (totalAcc > 15) {
            if (!isRunning) {
                isRunning = true;
                showHUD();
            }
            clearTimeout(runTimeout);
            runTimeout = setTimeout(() => {
                isRunning = false;
                hideHUD();
            }, 3000); // 3 segundos sin correr para ocultarlo
        }
    });
}

function showHUD() {
    let hud = document.getElementById('hudLayer');
    if (!hud) {
        hud = document.createElement('div');
        hud.id = 'hudLayer';
        hud.innerHTML = '<div id="hudLine"></div><div id="hudTime"></div><div id="hudUnit">min</div>';
        document.body.appendChild(hud);
    }
    
    // Obtener la línea más inminente que el usuario está esperando
    const nextDep = window._departures[0];
    if (!nextDep) return;
    
    const min = nextDep.mins > 0 ? nextDep.mins : 0;
    const col = nextDep.color.startsWith('#') ? nextDep.color : '#' + nextDep.color;
    
    hud.style.backgroundColor = col + 'E6'; // 90% opacity
    document.getElementById('hudLine').innerText = nextDep.line || '';
    document.getElementById('hudTime').innerText = min;
    
    hud.classList.add('active');
}

function hideHUD() {
    const hud = document.getElementById('hudLayer');
    if (hud) hud.classList.remove('active');
}
`;
app += '\\n' + hudJs;
fs.writeFileSync('app.js', app);
