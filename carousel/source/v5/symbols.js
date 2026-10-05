// Theme symbols, drawn as simple SVG (fills + ink lines). Rendered to ill/<name>_fill.png and ill/<name>_line.png,
// then turned into pen + watercolour cut-outs by symbols.py (same look as the v4 travel symbols).
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs');
const L = require('../lib'); const { C } = L;
const D = __dirname;
const T = { terra: '#b8664a', olive: '#8f9a6e', lemon: '#efd77a', sea: '#9db5c6', straw: '#d9bf8a', grape: '#8c6f86' };

// a star with rounded tips, centred on 0,0
const star = (ro, ri, n = 5) => {
  let d = ''; for (let i = 0; i < n * 2; i++) { const r = i % 2 ? ri : ro, a = -Math.PI / 2 + i * Math.PI / n;
    d += `${i ? 'L' : 'M'}${(r * Math.cos(a)).toFixed(1)} ${(r * Math.sin(a)).toFixed(1)} `; } return d + 'z';
};
// leaf along an angle from a stem point
const leaf = (x, y, len, w, deg, fill) => `<g transform="translate(${x},${y}) rotate(${deg})">
  <path d="M0 0 C${len * 0.3} ${-w} ${len * 0.75} ${-w} ${len} 0 C${len * 0.75} ${w} ${len * 0.3} ${w} 0 0z" fill="${fill}"/>
  <path d="M2 0 H${len * 0.85}" stroke-width="1.5"/></g>`;

const items = {
  // ---- 01 Italian villa ----
  villa: [`
    <path d="M-130 96 H130" stroke-width="4"/>
    <path d="M-112 -28 L0 -76 L112 -28z" fill="${T.terra}"/>
    <rect x="-98" y="-28" width="196" height="124" fill="${C.butter}"/>
    <path d="M-104 -28 H104" stroke-width="5"/>
    <path d="M-20 96 V40 a20 20 0 0 1 40 0 V96z" fill="${T.olive}"/>
    <rect x="-76" y="-8" width="30" height="38" fill="${C.dove}"/><path d="M-61 -8 V30"/>
    <rect x="46" y="-8" width="30" height="38" fill="${C.dove}"/><path d="M61 -8 V30"/>
    <rect x="-76" y="50" width="30" height="34" fill="${C.dove}"/><path d="M-61 50 V84"/>
    <rect x="46" y="50" width="30" height="34" fill="${C.dove}"/><path d="M61 50 V84"/>
    <rect x="-16" y="-14" width="32" height="30" rx="15" fill="${C.dove}"/>
    <path d="M-140 96 C-160 40 -150 -10 -136 -40 C-122 -10 -114 40 -132 96z" fill="${T.olive}"/>`, 300, 210],
  lemons: [L.lemons(), 230, 160],
  cypress: [`
    <path d="M-90 112 H90" stroke-width="4"/>
    <path d="M-28 112 C-66 40 -56 -70 -28 -130 C0 -70 10 40 -28 112z" fill="${T.olive}"/>
    <path d="M-28 -110 V112" stroke-width="1.5"/>
    <path d="M34 112 C6 60 14 -20 34 -66 C54 -20 62 60 34 112z" fill="${C.sage}"/>
    <path d="M34 -50 V112" stroke-width="1.5"/>`, 200, 260],
  moka: [`
    <path d="M-50 100 L-40 22 H40 L50 100z" fill="${C.dove}"/>
    <path d="M-40 22 L-46 10 H46 L40 22z" fill="${C.cocoa}"/>
    <path d="M-46 10 L-36 -66 H36 L46 10z" fill="${C.dove}"/>
    <path d="M-38 -66 L-28 -82 H28 L38 -66z" fill="${C.dove}"/>
    <circle cx="0" cy="-90" r="8" fill="${C.cocoa}"/>
    <path d="M-36 -62 L-66 -74 L-44 -50z" fill="${C.dove}"/>
    <path d="M42 -56 C84 -56 88 -4 46 0" fill="none" stroke="${C.cocoa}" stroke-width="12"/>
    <path d="M-24 30 V92 M0 30 V94 M24 30 V92 M-20 0 V-60 M0 0 V-62 M20 0 V-60" stroke-width="1.5"/>
`, 200, 220],
  olive: [`
    <path d="M-110 60 C-50 30 20 -10 110 -60" fill="none" stroke="${C.cocoa}" stroke-width="5"/>
    ${leaf(-80, 45, 60, 12, -70, T.olive)}${leaf(-60, 35, 62, 12, 40, C.sage)}${leaf(-20, 14, 66, 12, -80, C.sage)}
    ${leaf(0, 2, 64, 12, 30, T.olive)}${leaf(40, -18, 60, 12, -75, T.olive)}${leaf(60, -30, 58, 12, 25, C.sage)}
    ${leaf(95, -52, 50, 11, -30, T.olive)}
    <ellipse cx="-34" cy="44" rx="13" ry="17" fill="#5f6a46" transform="rotate(-20 -34 44)"/>
    <ellipse cx="22" cy="22" rx="12" ry="16" fill="#5f6a46" transform="rotate(-20 22 22)"/>
    <ellipse cx="70" cy="-10" rx="12" ry="16" fill="#6e5a6a" transform="rotate(-20 70 -10)"/>`, 260, 200],
  lemontree: [`
    <path d="M-50 60 L-40 120 H40 L50 60z" fill="${T.terra}"/>
    <rect x="-58" y="50" width="116" height="16" rx="3" fill="${T.terra}"/>
    <path d="M0 50 V-10 M0 10 L-22 -16 M0 0 L20 -22" fill="none" stroke="${C.cocoa}" stroke-width="6"/>
    <circle cx="0" cy="-60" r="68" fill="${T.olive}"/>
    <circle cx="-30" cy="-70" r="11" fill="${T.lemon}"/><circle cx="24" cy="-88" r="11" fill="${T.lemon}"/>
    <circle cx="34" cy="-40" r="11" fill="${T.lemon}"/><circle cx="-14" cy="-30" r="11" fill="${T.lemon}"/>
    <circle cx="-44" cy="-100" r="10" fill="${T.lemon}"/>`, 180, 260],
  grapes: [`
    <path d="M0 -84 C4 -100 18 -112 34 -116" fill="none" stroke="${C.cocoa}" stroke-width="5"/>
    ${leaf(6, -92, 70, 26, -20, T.olive)}
    ${[[-30,-62],[0,-64],[30,-60],[-44,-34],[-15,-36],[15,-34],[44,-32],[-30,-6],[0,-8],[30,-6],[-15,20],[15,20],[0,46]]
      .map(([x, y]) => `<circle cx="${x}" cy="${y}" r="16" fill="${T.grape}"/>`).join('')}`, 200, 220],
  // ---- 02 villa by the sea ----
  parasol: [`
    <path d="M-120 112 q30 -10 60 0 t60 0 t60 0 t60 0" fill="none" stroke-width="3"/>
    <path d="M8 -70 L-14 112" stroke="${C.cocoa}" stroke-width="6"/>
    ${[-110, -55, 0, 55].map((x, i) => `<path d="M8 -74 L${x} -6 Q${x + 27} 14 ${x + 55} -6z" fill="${i % 2 ? C.cream : C.roseDeep}"/>`).join('')}
    <path d="M-110 -6 Q-60 -110 8 -76 Q76 -110 110 -6" fill="none"/>
    <circle cx="8" cy="-80" r="6" fill="${C.cocoa}"/>`, 260, 240],
  gulls: [`
    <path d="M-60 -16 q20 -24 40 0 q20 -24 40 0" fill="none" stroke-width="5"/>
    <path d="M6 14 q16 -20 32 0 q16 -20 32 0" fill="none" stroke-width="4"/>
    <path d="M-36 34 q12 -14 24 0 q12 -14 24 0" fill="none" stroke-width="3"/>`, 170, 110],
  hat: [`
    <ellipse cx="0" cy="30" rx="130" ry="40" fill="${T.straw}"/>
    <path d="M-62 26 C-64 -60 64 -60 62 26z" fill="${T.straw}"/>
    <path d="M-63 0 C-30 12 30 12 63 0 L62 22 C30 34 -30 34 -62 22z" fill="${C.roseDeep}"/>
    <path d="M40 18 l26 -18 l4 30z M40 18 l30 22 l-26 12z" fill="${C.roseDeep}"/>
    <path d="M-100 34 q100 30 200 0 M-40 -30 q40 -10 80 0" fill="none" stroke-width="1.5"/>`, 290, 170],
  shell: [`
    <path d="M-16 84 L-96 -6 Q-86 -84 0 -92 Q86 -84 96 -6 L16 84z" fill="${C.rose}"/>
    ${[-80, -54, -27, 0, 27, 54, 80].map(x => `<path d="M0 82 L${x} ${-70 - (80 - Math.abs(x)) * 0.25 + (Math.abs(x) > 70 ? 40 : 0)}" stroke-width="1.8"/>`).join('')}
    <path d="M-30 84 L-38 104 H38 L30 84z" fill="${C.roseDeep}"/>`, 220, 220],
  dawn: [`
    <path d="M-80 20 A80 80 0 0 1 80 20z" fill="${T.lemon}"/>
    ${[-160, -135, -110, -90, -70, -45, -20].map(a => { const r = a * Math.PI / 180;
      return `<path d="M${(96 * Math.cos(r)).toFixed(0)} ${(20 + 96 * Math.sin(r)).toFixed(0)} L${(124 * Math.cos(r)).toFixed(0)} ${(20 + 124 * Math.sin(r)).toFixed(0)}" stroke-width="4"/>`; }).join('')}
    <rect x="-130" y="20" width="260" height="70" fill="${T.sea}"/>
    <path d="M-130 20 H130 M-110 46 q14 -10 28 0 t28 0 M10 62 q14 -10 28 0 t28 0 M-60 78 q14 -10 28 0" fill="none" stroke-width="2"/>`, 280, 230],
  starfish: [`<path d="${star(100, 40)}" fill="${C.roseDeep}" stroke-linejoin="round"/>
    ${[[0,-60],[0,-30],[52,-18],[28,-8],[34,46],[18,22],[-34,46],[-18,22],[-52,-18],[-28,-8],[0,0]]
      .map(([x, y]) => `<circle cx="${x}" cy="${y}" r="4.5" fill="${C.cream}"/>`).join('')}`, 230, 220],
  sailboat: [L.sailboat(), 260, 230],
  // ---- 03 countryside ----
  barn: [`
    <path d="M-130 100 H130" stroke-width="4"/>
    <path d="M-90 100 V-10 L-60 -60 H60 L90 -10 V100z" fill="${T.terra}"/>
    <path d="M-100 -4 L-62 -66 H62 L100 -4" fill="none" stroke-width="7"/>
    <rect x="-38" y="20" width="76" height="80" fill="${C.cream}"/>
    <path d="M-38 20 L38 100 M38 20 L-38 100" stroke-width="3"/>
    <rect x="-18" y="-40" width="36" height="34" fill="${C.cream}"/>
    <path d="M-18 -40 L18 -6 M18 -40 L-18 -6" stroke-width="2"/>
    <path d="M110 100 V20 a16 16 0 0 1 0 0" fill="none"/>
    <rect x="96" y="-20" width="34" height="120" rx="4" fill="${C.dove}"/><path d="M96 -20 Q113 -50 130 -20" fill="${C.dove}"/>`, 280, 220],
  wheat: [`
    ${[-30, -15, 0, 15, 30].map((a, i) => { const r = (a - 90) * Math.PI / 180, x = 150 * Math.cos(r), y = 70 + 150 * Math.sin(r);
      const ears = [0.55, 0.65, 0.75, 0.85, 0.95].map(t => { const ex = x * t, ey = 70 + (y - 70) * t;
        return `<ellipse cx="${(ex - 7).toFixed(0)}" cy="${ey.toFixed(0)}" rx="5" ry="10" fill="${C.butter}" transform="rotate(${a - 25} ${(ex - 7).toFixed(0)} ${ey.toFixed(0)})"/>` +
               `<ellipse cx="${(ex + 7).toFixed(0)}" cy="${ey.toFixed(0)}" rx="5" ry="10" fill="${T.straw}" transform="rotate(${a + 25} ${(ex + 7).toFixed(0)} ${ey.toFixed(0)})"/>`; }).join('');
      return `<path d="M${(-a * 0.6).toFixed(0)} 120 L0 70 L${x.toFixed(0)} ${y.toFixed(0)}" fill="none" stroke="${T.straw}" stroke-width="3"/>${ears}`; }).join('')}
    <path d="M-22 64 Q0 80 22 64 L22 80 Q0 96 -22 80z" fill="${C.roseDeep}"/>`, 220, 280],
  wellies: [`
    <path d="M-80 -70 H-30 V40 C-30 46 -20 50 -6 54 C10 58 12 80 0 84 H-82 Q-90 84 -90 74 L-84 -70z" fill="${T.olive}"/>
    <path d="M-84 -60 H-30" stroke-width="5"/><path d="M-90 74 H0" stroke-width="3"/>
    <g transform="translate(96 10)"><path d="M-80 -70 H-30 V40 C-30 46 -20 50 -6 54 C10 58 12 80 0 84 H-82 Q-90 84 -90 74 L-84 -70z" fill="${C.sage}"/>
    <path d="M-84 -60 H-30" stroke-width="5"/><path d="M-90 74 H0" stroke-width="3"/></g>`, 230, 200],
  apple: [`
    <path d="M0 -40 C-30 -70 -96 -60 -92 10 C-88 70 -40 104 0 86 C40 104 88 70 92 10 C96 -60 30 -70 0 -40z" fill="${C.roseDeep}"/>
    <path d="M0 -40 C-2 -60 4 -80 14 -94" fill="none" stroke="${C.cocoa}" stroke-width="6"/>
    ${leaf(10, -76, 64, 18, -30, T.olive)}
    <path d="M-52 -20 q-12 20 -6 44" fill="none" stroke="${C.cream}" stroke-width="6"/>`, 210, 210],
  basil: [`
    <path d="M0 120 C-4 60 4 0 0 -110" fill="none" stroke="${T.olive}" stroke-width="5"/>
    ${[[0,-100,0],[0,-60,1],[0,-10,2],[0,44,3]].map(([x, y, i]) => {
      const len = 46 + i * 10, w = 18 + i * 4; return leaf(x, y, len, w, -150 + i * 4, C.sage) + leaf(x, y, len, w, -30 - i * 4, T.olive); }).join('')}
    ${leaf(0, -110, 34, 12, -90, C.sage)}`, 230, 260],
  bear: [L.bear(), 200, 240],
  bodhileaf: [`
    <path d="M0 110 C-8 80 -24 60 -60 30 C-110 -10 -100 -90 -44 -96 C-20 -98 -6 -86 0 -72 C6 -86 20 -98 44 -96 C100 -90 110 -10 60 30 C24 60 8 80 0 110z" fill="${T.olive}"/>
    <path d="M0 -72 V100" stroke="${C.cocoa}" stroke-width="3"/>
    ${[-50, -20, 10, 40].map(y => { const r = 70 - (y + 50) * 0.55; return `<path d="M0 ${y} Q${-r * 0.5} ${y - 6} ${-r} ${y - 28} M0 ${y} Q${r * 0.5} ${y - 6} ${r} ${y - 28}" stroke-width="1.6"/>`; }).join('')}`, 230, 230],
};

const page = (body, w, h, mode) => `<!doctype html><html><head><style>
html,body{margin:0;background:transparent} ${mode === 'fill' ? '*{stroke:none !important}' : '*{fill:none !important}'}</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="${w*3}" height="${h*3}" viewBox="${-w/2} ${-h/2} ${w} ${h}">
<g stroke="${C.ink}" stroke-width="${mode==='fill'?3.2:1.7}" stroke-linecap="round" stroke-linejoin="round" fill="none">${mode==='fill'?body:body.replace(/stroke-width="([\d.]+)"/g,(m,v)=>`stroke-width="${Math.max(1.3, v*0.5).toFixed(2)}"`)}</g></svg></body></html>`;

(async () => {
  fs.mkdirSync(D + '/ill', { recursive: true });
  const only = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  for (const [k, [body, w, h]] of Object.entries(items)) {
    if (only.length && !only.includes(k)) continue;
    for (const mode of ['fill', 'line']) {
      await p.setViewportSize({ width: w * 3, height: h * 3 });
      await p.setContent(page(body, w, h, mode));
      await p.screenshot({ path: `${D}/ill/${k}_${mode}.png`, omitBackground: true });
    }
  }
  await b.close(); console.log('symbols drawn');
})();
