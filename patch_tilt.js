const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf8');

const tiltScript = `
        /* --- TILT-TO-AR --- */
        let arActive = false;
        if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', function(event) {
                if (!event.beta) return;
                // beta goes from -180 to 180. 90 is vertical, 0 is flat.
                const tilt = event.beta; 
                
                if (tilt > 70 && tilt < 110 && !arActive) {
                    arActive = true;
                    if (typeof openAR === 'function') openAR();
                } else if (tilt < 40 && tilt > -40 && arActive) {
                    arActive = false;
                    if (typeof closeAR === 'function') closeAR();
                }
            });
        }
`;

html = html.replace('function openAR() {', tiltScript + '\n        function openAR() {');
fs.writeFileSync('index.html', html);
