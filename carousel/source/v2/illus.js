const L = require('../lib'); const { C } = L;
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const wreath = () => {
  const vine = `<path d="M-150 190 C-215 60 -190 -120 -60 -195 C40 -235 150 -190 185 -90 C215 0 190 120 140 195" fill="none" stroke="${C.sage}" stroke-width="9"/>
    <path d="M-150 190 C-215 60 -190 -120 -60 -195 C40 -235 150 -190 185 -90 C215 0 190 120 140 195" fill="none"/>`;
  const lv = [[-185,120,200],[-200,30,170],[-190,-60,215],[-150,-140,230],[-90,-190,250],[20,-222,-15],[100,-205,10],[160,-150,40],[195,-40,-20],[200,60,20],[175,150,60],[-170,170,160]];
  const fl = [L.flower(-195,-10,1.0,6,C.rose,C.butter,0), L.flower(-120,-178,0.9,5,C.butter,C.roseDeep,10), L.tulip(60,-214,0.95,C.roseDeep,15),
    L.flower(182,-110,0.95,8,C.dove,C.cream,0), L.flower(196,100,0.8,5,C.rose,C.chestnut,0), L.tulip(-160,190,0.85,C.dove,-160), L.flower(150,200,0.75,6,C.butter,C.roseDeep,0),
    L.flower(-30,-226,0.55,5,C.dove,C.butter,0), L.flower(-200,80,0.55,5,C.butter,C.chestnut,0)];
  return vine + lv.map(([x,y,r])=>L.leaf(x,y,0.95,r)).join('') + fl.join('') +
    [[-60,232],[-20,240],[20,240],[60,232]].map(([x,y])=>`<circle cx="${x}" cy="${y}" r="7" fill="${C.roseDeep}"/>`).join('');
};
const items = {
  wreath: [wreath(), 480, 540],
  globe: [L.globe(), 300, 330], train: [L.train(), 300, 260], compass: [L.compass(), 260, 300], balloon: [L.balloon(), 230, 300],
  suitcase: [L.suitcase(), 260, 200], lemons: [L.lemons(), 260, 180], crown: [L.crown(), 230, 180], map: [L.map(), 260, 220],
  sailboat: [L.sailboat(), 280, 230], bear: [L.bear(), 200, 240], plane: [L.plane(), 300, 220],
};
const page = (body, w, h, mode) => `<!doctype html><html><head><link rel="stylesheet" href="../fonts-local.css"><style>
html,body{margin:0;background:transparent} ${mode === 'fill' ? '*{stroke:none !important}' : '*{fill:none !important} text{fill:#3a2620 !important}'}</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="${w*3}" height="${h*3}" viewBox="${-w/2} ${-h/2} ${w} ${h}">${L.defs}
<g stroke="${C.ink}" stroke-width="${mode==='fill'?3.2:1.7}" stroke-linecap="round" stroke-linejoin="round">${mode==='fill'?body:body.replace(/stroke-width="([\d.]+)"/g,(m,v)=>`stroke-width="${(v*0.5).toFixed(2)}"`)}</g></svg></body></html>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  for (const [k, [body, w, h]] of Object.entries(items)) for (const mode of ['fill', 'line']) {
    await p.setViewportSize({ width: w*3, height: h*3 });
    require('fs').writeFileSync(__dirname + '/ill/tmp.html', page(body, w, h, mode));
    await p.goto('file://' + __dirname + '/ill/tmp.html'); await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: `${__dirname}/ill/${k}_${mode}.png`, omitBackground: true });
  }
  await b.close();
})();
