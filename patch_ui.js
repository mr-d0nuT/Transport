const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf8');

// 1. Extract the map and its buttons
const mapWrapRegex = /<div class="map-wrap">\s*<div id="map"><\/div>\s*(<button class="map-fab"[\s\S]*?<\/button>)\s*(<button class="map-fab ar"[\s\S]*?<\/button>)\s*(<button id="tripRecenter"[\s\S]*?<\/button>)\s*(<div class="map-hint-pill"[\s\S]*?<\/div>)\s*<\/div>/;
const match = html.match(mapWrapRegex);

if (match) {
    const mapHtml = `
    <div id="map"></div>
    ${match[1]}
    ${match[2]}
    ${match[3]}
    ${match[4]}
    `;
    
    // Remove the original map-wrap
    html = html.replace(match[0], '');
    
    // Insert map HTML at the very top of body
    html = html.replace('<body>', '<body>\n' + mapHtml + '\n    <div id="bottomSheet" class="bottom-sheet">\n        <div class="sheet-drag-handle"></div>\n        <div class="sheet-content">');
    
    // Close bottom sheet
    html = html.replace('</body>', '        </div>\n    </div>\n</body>');
    
    const newCss = `
        /* --- NUEVO LAYOUT INMERSIVO --- */
        body { overflow: hidden; background: var(--bg); }
        #map { position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important; z-index: 1 !important; border-radius: 0 !important; }
        
        .map-fab { position: fixed !important; z-index: 50 !important; top: 20px !important; right: 20px !important; }
        .map-fab.ar { top: 70px !important; }
        #tripRecenter { position: fixed !important; z-index: 50 !important; top: 120px !important; right: 20px !important; }
        .map-hint-pill { position: fixed !important; z-index: 50 !important; top: 20px !important; left: 50% !important; transform: translateX(-50%) !important; }

        .bottom-sheet {
            position: fixed; bottom: 0; left: 0; width: 100%; height: 60vh;
            background: var(--bg); z-index: 100;
            border-radius: 24px 24px 0 0;
            box-shadow: 0 -10px 40px rgba(0,0,0,0.2);
            display: flex; flex-direction: column;
            transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
            transform: translateY(0);
        }
        .sheet-drag-handle {
            width: 40px; height: 5px; background: var(--text-soft); border-radius: 3px; margin: 12px auto; opacity: 0.5;
        }
        .sheet-content {
            flex: 1; overflow-y: auto; padding: 0; -webkit-overflow-scrolling: touch;
        }
        main { padding: 0 14px 50px; max-width: 660px; margin: 0 auto; }
        .topbar { position: sticky; top: 0; z-index: 50; border-radius: 0; margin-bottom: 0; }
`;

    html = html.replace('</style>', newCss + '\n    </style>');
    
    fs.writeFileSync('index.html', html);
    console.log("Success");
} else {
    console.log("Regex failed");
}
