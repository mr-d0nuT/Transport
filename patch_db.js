const fs = require('fs');
let app = fs.readFileSync('app.js', 'utf8');

app = app.replace(
    /try \{ cached = JSON\.parse\(localStorage\.getItem\(CACHE_KEY\)\); \} catch \{\}/g,
    'try { cached = await window.DB.getJSON(CACHE_KEY); } catch {}'
);

app = app.replace(
    /localStorage\.setItem\(CACHE_KEY, JSON\.stringify\(\{ t: Date\.now\(\), s \}\)\);/g,
    'window.DB.setJSON(CACHE_KEY, { t: Date.now(), s });'
);

app = app.replace(
    /localStorage\.setItem\(CACHE_KEY, JSON\.stringify\(\{ t: Date\.now\(\), codes \}\)\);/g,
    'window.DB.setJSON(CACHE_KEY, { t: Date.now(), codes });'
);

app = app.replace(
    /try \{ cached = JSON\.parse\(localStorage\.getItem\(CACHE_KEY\)\); \} catch \{\}/g,
    'try { cached = await window.DB.getJSON(CACHE_KEY); } catch {}'
);

fs.writeFileSync('app.js', app);
