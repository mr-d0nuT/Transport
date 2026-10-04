const fs = require('fs');
let css = fs.readFileSync('styles.css', 'utf8');

const fullBleedCSS = `
/* --- TARJETAS FULL-BLEED (Color de línea de fondo) --- */
.arr-row {
    position: relative;
    overflow: hidden;
    z-index: 1;
    border-radius: 12px;
}

.arr-row::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    /* Utiliza la variable CSS --line-color inyectada dinámicamente en app.js */
    background: color-mix(in srgb, var(--line-color, var(--text-soft)) 15%, transparent);
    z-index: -1;
    pointer-events: none;
}
`;

css += '\n' + fullBleedCSS;
fs.writeFileSync('styles.css', css);

let app = fs.readFileSync('app.js', 'utf8');
// Inject CSS variable --line-color into arr-row based on the line color
app = app.replace(
    /return \`<div class="arr-row"\>/g,
    "return `<div class=\"arr-row\" style=\"--line-color: ${color.startsWith('#') ? color : '#' + color}\">`"
);

fs.writeFileSync('app.js', app);
