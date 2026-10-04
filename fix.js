const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

// 1. Fix getMetroStations
const oldGetMetro = /const grouped = \{\};[\s\S]*?lon: g\.lon \/ g\.count\n                \}\)\);/m;

const newGetMetro = `                // Agrupar IDs por nombre de estación
                const idsByName = {};
                const linesByName = {};
                data.features.forEach(f => {
                    const name = f.properties.NOM_ESTACIO;
                    if (!idsByName[name]) {
                        idsByName[name] = [];
                        linesByName[name] = new Set();
                    }
                    idsByName[name].push(f.properties.CODI_ESTACIO);
                    if (f.properties.PICTO) linesByName[name].add(f.properties.PICTO);
                });
                
                // Generar los 171 marcadores independientes, pero cada uno lleva TODOS los IDs de su estación
                const s = data.features.map(f => {
                    const name = f.properties.NOM_ESTACIO;
                    return {
                        id: idsByName[name].join(','), // Todos los IDs de esta estación para que imetro los baje todos
                        name: name,
                        lines: Array.from(linesByName[name]).join(' · '), // Muestra L4 · L5 en la UI
                        lat: f.geometry.coordinates[1],
                        lon: f.geometry.coordinates[0],
                        _realId: f.properties.CODI_ESTACIO // Clave única real del andén
                    };
                });`;

app = app.replace(oldGetMetro, newGetMetro);

// Bump cache to v4
app = app.replace(/busbcn_metro_v3/g, 'busbcn_metro_v4');

// 2. Fix stopKey to use _realId
// In app.js there is: `const stopKey = s => \`\${s.type}:\${s.type === 'metro' ? s.id : (s.type === 'tram' ? s.out : s.code)}\`;`
// Let's replace it!
const oldStopKey = /const stopKey = s => `\$\{s\.type\}:\$\{s\.type === 'metro' \? s\.id : \(s\.type === 'tram' \? s\.out : s\.code\)\}`;/;
const newStopKey = "const stopKey = s => `${s.type}:${s.type === 'metro' ? (s._realId || s.id) : (s.type === 'tram' ? s.out : s.code)}`;";

app = app.replace(oldStopKey, newStopKey);

fs.writeFileSync('app.js', app);

let sw = fs.readFileSync('sw.js', 'utf8');
sw = sw.replace(/transport-bcn-v88/, 'transport-bcn-v89');
fs.writeFileSync('sw.js', sw);
