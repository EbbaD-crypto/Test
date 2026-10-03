const { chromium } = require('/opt/node-tools/node_modules/playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
 for (const f of process.argv.slice(2)) { await p.goto('file://' + __dirname + '/' + f + '.html'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
 await p.screenshot({ path: f + '.png' }); } await b.close(); })();
