const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf8');

html = html.replace(/let loadedShapes = null;[\s\S]*?(?=\/\* ===================== 14\. MAPA Y RENDER ===================== \*\/)/, '');
// Wait, loadedShapes is at 1442, initMap is at 1570... 
// Better use line numbers!
