const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

// The HTML for the buttons
const smartToolsHTML = `
                <div class="smart-tools" style="padding: 10px; margin-top: 15px; border-top: 1px solid var(--border); display: flex; gap: 8px;">
                    <button onclick="alert('Alarma Proactiva configurada. Te avisaremos 20 min antes si hay averías.')" style="flex: 1; padding: 10px; border-radius: 8px; border: none; background: #9A3B9520; color: #9A3B95; font-weight: bold;">⏰ Smart Wake-Up</button>
                    <button onclick="alert('Buscando VTC/Taxi disponibles cerca...')" style="flex: 1; padding: 10px; border-radius: 8px; border: none; background: #F7A30E20; color: #F7A30E; font-weight: bold;">🚕 VTC / Taxi (Respaldo)</button>
                </div>
`;

// Insert it at the end of the journey-detail
app = app.replace(
    /<div class="jcard-detail" style="display: \${parcial \? 'block' : 'none'};">\\n' \+ journeyStepsHTML\(it\)/,
    `<div class="jcard-detail" style="display: \${parcial ? 'block' : 'none'};">\n' + journeyStepsHTML(it) + '` + smartToolsHTML.replace(/\n/g, '') + "'"
);

fs.writeFileSync('app.js', app);
