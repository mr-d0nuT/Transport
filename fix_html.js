const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf8');

// Remove the injected bottomSheet opening tags
html = html.replace(/\s*<div id="bottomSheet" class="bottom-sheet">\s*<div class="sheet-drag-handle"><\/div>\s*<div class="sheet-content">/, '');

// Remove the injected closing tags at the very end
html = html.replace(/\s*<\/div>\s*<\/div>\s*<\/body>\s*<\/html>/, '\n</body>\n</html>');

// Insert a drag handle at the top of <main>
html = html.replace('<main>', '<main id="bottomSheet" class="bottom-sheet">\n        <div class="sheet-drag-handle"></div>\n        <div class="sheet-content">');

// Close sheet-content right before </main>
html = html.replace('</main>', '</div>\n    </main>');

fs.writeFileSync('index.html', html);
