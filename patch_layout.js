const fs = require('fs');
let css = fs.readFileSync('styles.css', 'utf8');

// Fix map-hint-pill stretching
css = css.replace(
    /.map-hint-pill { position: fixed !important; z-index: 50 !important; top: 20px !important; left: 50% !important; transform: translateX\(-50%\) !important; }/,
    '.map-hint-pill { position: fixed !important; z-index: 50 !important; top: 20px !important; bottom: auto !important; left: 50% !important; transform: translateX(-50%) !important; }'
);

// Fix bottom-sheet centering (add right: 0 so margin: 0 auto works)
css = css.replace(
    /position: fixed; bottom: 0; left: 0; width: 100%; height: 60vh;/,
    'position: fixed; bottom: 0; left: 0; right: 0; width: 100%; height: 60vh;'
);

fs.writeFileSync('styles.css', css);
