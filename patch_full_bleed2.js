const fs = require('fs');
let css = fs.readFileSync('styles.css', 'utf8');

const fullBleedCSS = `
/* --- TARJETAS FULL-BLEED (Color de línea de fondo) --- */
.bus-card {
    position: relative;
    overflow: hidden;
    z-index: 1;
}

.bus-card::after {
    content: '';
    position: absolute;
    inset: 0;
    /* color-mix para mezclar el color de la línea con transparente al 90% */
    background: color-mix(in srgb, var(--line, var(--primary)) 12%, transparent);
    z-index: -1;
    pointer-events: none; /* Que no bloquee clicks */
}

/* El contenido debe ir encima del pseudo-elemento */
.bus-card-content, .bus-card-top, .bus-card-bottom {
    position: relative;
    z-index: 1;
}
`;

css += '\n' + fullBleedCSS;
fs.writeFileSync('styles.css', css);
