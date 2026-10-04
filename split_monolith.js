const fs = require('fs');
let html = fs.readFileSync('index.html', 'utf8');

// 1. Extract CSS
const styleRegex = /<style>([\s\S]*?)<\/style>/;
const styleMatch = html.match(styleRegex);
if (styleMatch) {
    fs.writeFileSync('styles.css', styleMatch[1].trim());
    html = html.replace(styleMatch[0], '<link rel="stylesheet" href="styles.css">');
}

// 2. Extract JS (but only the main massive script tag, leave small inline ones if any, wait, there's only one main script)
// Actually, let's find the script tag that contains "const APP_ID ="
const scriptRegex = /<script>([\s\S]*?const APP_ID =[\s\S]*?)<\/script>/;
const scriptMatch = html.match(scriptRegex);
if (scriptMatch) {
    fs.writeFileSync('app.js', scriptMatch[1].trim());
    html = html.replace(scriptMatch[0], '<script src="app.js"></script>');
}

fs.writeFileSync('index.html', html);
console.log("Monolith decoupled.");
