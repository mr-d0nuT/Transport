const fs = require('fs');
let css = fs.readFileSync('styles.css', 'utf8');

// Fix bottom-sheet centering robustly
css = css.replace(
    /position: fixed; bottom: 0; left: 0; right: 0; width: auto; height: 60vh;/,
    'position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; height: 60vh;'
);

fs.writeFileSync('styles.css', css);
