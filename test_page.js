const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch({headless: "new"});
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
    
    // Server the file locally
    const { exec } = require('child_process');
    const server = exec('npx http-server -p 8081');
    
    await new Promise(r => setTimeout(r, 2000));
    
    await page.goto('http://127.0.0.1:8081');
    await new Promise(r => setTimeout(r, 5000));
    
    await browser.close();
    server.kill();
})();
