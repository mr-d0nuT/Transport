const fs = require('fs');
let sw = fs.readFileSync('sw.js', 'utf8');

sw = sw.replace(/transport-bcn-v89/, 'transport-bcn-v90');
sw = sw.replace(
    /const SHELL = \['\.\/', '\.\/index\.html', '\.\/styles\.css', '\.\/app\.js', '\.\/icon-192\.png', '\.\/favicon-64\.png', '\.\/manifest\.webmanifest', '\.\/assets\/mark-donut\.png'\];/,
    "const SHELL = ['./', './index.html', './styles.css', './app.js', './worker.js', './db.js', './icon-192.png', './favicon-64.png', './manifest.webmanifest', './assets/mark-donut.png'];"
);

fs.writeFileSync('sw.js', sw);
