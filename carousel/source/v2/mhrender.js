const { chromium } = require('/opt/node-tools/node_modules/playwright');
const items = JSON.parse(process.argv[2]);
const FONT = 'data:font/otf;base64,' + require('fs').readFileSync('/home/user/Test/brand/fonts/MilkHoney.otf').toString('base64');   // [[text, px, outfile], ...]
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2400, height: 600 } });
  for (const [t, px, out] of items) {
    await p.setContent(`<html><head><style>@font-face{font-family:MH;src:url(${FONT})}
      html,body{margin:0;background:transparent} span{font-family:MH;font-size:${px}px;line-height:1.15;white-space:nowrap;display:inline-block;padding:10px}</style></head>
      <body><span id=s>${t}</span></body></html>`);
    await p.evaluate(async () => { await document.fonts.load('80px MH'); await document.fonts.ready; }); await p.waitForTimeout(200);
    await (await p.$('#s')).screenshot({ path: out, omitBackground: true });
  }
  await b.close();
})();
