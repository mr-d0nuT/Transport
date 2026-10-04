const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');
const script = html.match(/<script>(.*?)<\/script>/s)[1];
try {
  new Function(script);
  console.log("Syntax OK");
} catch(e) {
  console.log("SYNTAX ERROR:", e);
}
