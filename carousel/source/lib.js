// Shared collage parts: palette, filters, papers, stickers, folk flowers.
const C = {
  ink: '#3a2620', cocoa: '#6b4632', chestnut: '#8a4b33', rose: '#e9b9ad', roseDeep: '#c97c6d',
  butter: '#f3e2a4', dove: '#a8bccb', doveDeep: '#7f98ab', cream: '#f6efdc', sage: '#9fae8c', kraft: '#c9ad86',
};

// seeded random so renders are repeatable
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

const defs = `
<defs>
  <filter id="torn" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="5" seed="3" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="16" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="9" result="g"/>
    <feColorMatrix in="g" type="matrix" values="0 0 0 0 0.25  0 0 0 0 0.17  0 0 0 0 0.1  0 0 0 0.22 -0.06" result="g2"/>
    <feComposite in="g2" in2="d" operator="in" result="g3"/>
    <feMerge result="m"><feMergeNode in="d"/><feMergeNode in="g3"/></feMerge>
    <feDropShadow in="m" dx="3" dy="5" stdDeviation="5" flood-color="#3a2620" flood-opacity="0.28"/>
  </filter>
  <filter id="fiber" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.12" numOctaves="4" seed="21" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="14" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id="tissue" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="4" seed="11" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="12" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feTurbulence type="turbulence" baseFrequency="0.012 0.03" numOctaves="3" seed="5" result="cr"/>
    <feDiffuseLighting in="cr" surfaceScale="2.2" lighting-color="#fff" result="lit"><feDistantLight azimuth="235" elevation="58"/></feDiffuseLighting>
    <feComposite in="lit" in2="d" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="shade"/>
    <feComposite in="shade" in2="d" operator="in" result="shade2"/>
    <feDropShadow in="shade2" dx="2" dy="3" stdDeviation="3" flood-color="#3a2620" flood-opacity="0.18"/>
  </filter>
  <filter id="sticker" x="-25%" y="-25%" width="150%" height="150%">
    <feMorphology in="SourceAlpha" operator="dilate" radius="9" result="dil"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="7" result="n"/>
    <feDisplacementMap in="dil" in2="n" scale="6" result="dil2"/>
    <feFlood flood-color="#fbf7ec"/><feComposite in2="dil2" operator="in" result="white"/>
    <feDropShadow in="white" dx="2" dy="4" stdDeviation="3.5" flood-color="#3a2620" flood-opacity="0.32" result="ws"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="2" result="w"/>
    <feDisplacementMap in="SourceGraphic" in2="w" scale="3" result="wob"/>
    <feMerge><feMergeNode in="ws"/><feMergeNode in="wob"/></feMerge>
  </filter>
  <filter id="pencil" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="1.2" numOctaves="1" seed="4" result="g"/>
    <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -0.55 1.12" result="ga"/>
    <feComposite in="SourceGraphic" in2="ga" operator="in"/>
  </filter>
  <filter id="inkprint">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="8" result="g"/>
    <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.1 1.15" result="ga"/>
    <feComposite in="SourceGraphic" in2="ga" operator="in"/>
  </filter>
  <filter id="soft"><feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#3a2620" flood-opacity="0.25"/></filter>
  <pattern id="stripesRose" width="46" height="46" patternUnits="userSpaceOnUse" patternTransform="rotate(0)">
    <rect width="46" height="46" fill="${C.rose}"/><rect width="23" height="46" fill="${C.chestnut}"/>
  </pattern>
  <pattern id="stripesBalloon" width="40" height="40" patternUnits="userSpaceOnUse">
    <rect width="40" height="40" fill="${C.butter}"/><rect width="20" height="40" fill="${C.roseDeep}"/>
  </pattern>
  <pattern id="lined" width="40" height="38" patternUnits="userSpaceOnUse">
    <rect width="40" height="38" fill="${C.butter}"/><line x1="0" y1="37" x2="40" y2="37" stroke="${C.doveDeep}" stroke-opacity="0.55" stroke-width="1.6"/>
  </pattern>
  <pattern id="dots" width="34" height="34" patternUnits="userSpaceOnUse">
    <rect width="34" height="34" fill="${C.dove}"/><circle cx="17" cy="17" r="2.4" fill="${C.cream}" fill-opacity="0.7"/>
  </pattern>
</defs>`;

// irregular quad paper; points = [[x,y]...]
const paper = (pts, fill, extra = '', filter = 'torn') => {
  const P = pts.map(p => p.join(',')).join(' ');
  const edge = filter === 'torn' ? `<g filter="url(#fiber)"><polygon points="${P}" fill="#fbf6e9" stroke="#fbf6e9" stroke-width="9" stroke-linejoin="round"/></g>` : '';
  return `<g filter="url(#soft)">${edge}</g><g filter="url(#${filter})"><polygon points="${P}" fill="${fill}" ${extra}/></g>`;
};

// ---------- sticker illustrations (drawn around 0,0, ~200px box) ----------
const S = { stroke: C.ink, sw: 3.2 };
const st = (body, x, y, s = 1, r = 0) =>
  `<g transform="translate(${x},${y}) rotate(${r}) scale(${s})"><g filter="url(#sticker)"><g filter="url(#pencil)" stroke="${S.stroke}" stroke-width="${S.sw}" stroke-linecap="round" stroke-linejoin="round">${body}</g></g></g>`;

const globe = () => `
  <path d="M-78 70 Q0 128 78 70" fill="none" stroke-width="5"/>
  <path d="M0 98 L0 128 M-42 132 L42 132" fill="none" stroke-width="7"/>
  <path d="M-92 -10 A92 92 0 0 1 60 -78" fill="none" stroke="${C.chestnut}" stroke-width="6"/>
  <circle cx="0" cy="0" r="80" fill="${C.dove}"/>
  <path d="M-52 -46 q18 -16 36 -6 q10 14 -4 24 q-6 18 -24 14 q-14 6 -18 -10 q-8 -12 10 -22z" fill="${C.sage}"/>
  <path d="M10 -18 q24 -10 40 6 q14 18 2 34 q-4 24 -22 30 q-14 -8 -12 -26 q-14 -12 -8 -44z" fill="${C.butter}"/>
  <path d="M-46 36 q14 -6 22 6 q2 14 -12 18 q-14 -6 -10 -24z" fill="${C.rose}"/>
  <ellipse cx="0" cy="0" rx="34" ry="80" fill="none" stroke-width="2"/>
  <path d="M-80 0 H80 M-70 -38 H70 M-70 38 H70" fill="none" stroke-width="2"/>
  <circle cx="0" cy="0" r="80" fill="none"/>`;

const train = () => `
  <path d="M-110 40 H120" stroke-width="4"/>
  <rect x="-96" y="-28" width="120" height="58" rx="14" fill="${C.chestnut}"/>
  <path d="M-96 -6 H24" stroke="${C.butter}" stroke-width="5"/>
  <rect x="24" y="-68" width="70" height="98" rx="6" fill="${C.rose}"/>
  <path d="M16 -74 H102" stroke-width="7"/>
  <rect x="40" y="-52" width="38" height="30" rx="4" fill="${C.butter}"/>
  <path d="M-70 -28 V-62 H-48 V-28" fill="${C.cocoa}"/>
  <path d="M-76 -64 H-42" stroke-width="6"/>
  <path d="M-30 -28 q8 -22 26 0" fill="${C.butter}"/>
  <path d="M-96 26 L-118 40 L-96 40z" fill="${C.cocoa}"/>
  <circle cx="-66" cy="40" r="17" fill="${C.cocoa}"/><circle cx="-66" cy="40" r="5" fill="${C.cream}"/>
  <circle cx="-16" cy="40" r="17" fill="${C.cocoa}"/><circle cx="-16" cy="40" r="5" fill="${C.cream}"/>
  <circle cx="56" cy="38" r="22" fill="${C.cocoa}"/><circle cx="56" cy="38" r="6" fill="${C.cream}"/>
  <path d="M-66 40 H56" stroke-width="4"/>
  <path d="M-64 -84 q-10 -18 8 -26 q6 -20 28 -12 q20 -12 32 6 q20 2 14 22 q-8 14 -26 8 q-14 14 -30 2 q-20 6 -26 0z" fill="${C.cream}"/>`;

const compass = () => {
  let ticks = '';
  for (let i = 0; i < 16; i++) { const a = i * Math.PI / 8, r1 = i % 4 ? 64 : 58; ticks += `<path d="M${(Math.cos(a)*r1).toFixed(1)} ${(Math.sin(a)*r1).toFixed(1)} L${(Math.cos(a)*72).toFixed(1)} ${(Math.sin(a)*72).toFixed(1)}" stroke-width="2.4"/>`; }
  return `
  <circle cx="0" cy="-96" r="12" fill="none" stroke-width="5"/>
  <rect x="-12" y="-90" width="24" height="12" rx="3" fill="${C.butter}"/>
  <circle cx="0" cy="0" r="84" fill="${C.butter}"/>
  <circle cx="0" cy="0" r="72" fill="${C.cream}"/>${ticks}
  <path d="M0 -58 L13 0 L0 58 L-13 0z" fill="${C.cream}"/>
  <path d="M0 -58 L13 0 L-13 0z" fill="${C.roseDeep}"/>
  <path d="M0 58 L13 0 L-13 0z" fill="${C.dove}"/>
  <path d="M-46 0 L0 -9 L46 0 L0 9z" fill="${C.cream}" stroke-width="2"/>
  <circle cx="0" cy="0" r="6" fill="${C.ink}"/>
  <text x="0" y="-36" text-anchor="middle" font-family="Cormorant Garamond" font-size="22" font-weight="500" fill="${C.ink}" stroke="none">N</text>`;
};

const balloon = () => `
  <path d="M-58 40 L-22 104 M58 40 L22 104 M-20 40 L-12 104 M20 40 L12 104" stroke-width="2.4"/>
  <path d="M0 -112 C76 -112 96 -40 60 20 C44 46 24 58 18 66 H-18 C-24 58 -44 46 -60 20 C-96 -40 -76 -112 0 -112z" fill="url(#stripesBalloon)"/>
  <path d="M0 -112 C-30 -80 -30 20 -18 66 M0 -112 C30 -80 30 20 18 66" fill="none" stroke-width="2.4"/>
  <path d="M-80 -30 Q0 -6 80 -30" fill="none" stroke="${C.chestnut}" stroke-width="7"/>
  <rect x="-22" y="102" width="44" height="34" rx="5" fill="${C.cocoa}"/>
  <path d="M-22 116 H22" stroke="${C.butter}" stroke-width="2.4"/>`;

const stamp = (label = 'POSTE', value = '5') => {
  // perforated edge
  let d = ''; const w = 150, h = 180; const r = 7, step = 18;
  for (let x = -w/2; x <= w/2; x += step) d += `<circle cx="${x}" cy="${-h/2}" r="${r}"/><circle cx="${x}" cy="${h/2}" r="${r}"/>`;
  for (let y = -h/2; y <= h/2; y += step) d += `<circle cx="${-w/2}" cy="${y}" r="${r}"/><circle cx="${w/2}" cy="${y}" r="${r}"/>`;
  return `
  <mask id="perf"><rect x="-90" y="-110" width="180" height="220" fill="#fff"/><g fill="#000">${d}</g></mask>
  <rect x="${-w/2}" y="${-h/2}" width="${w}" height="${h}" fill="${C.cream}" stroke="none" mask="url(#perf)"/>
  <rect x="-58" y="-72" width="116" height="122" fill="${C.dove}" stroke-width="2.4"/>
  <path d="M-58 20 q22 -18 40 -4 q20 -26 40 -10 q18 -8 36 4 V50 H-58z" fill="${C.sage}" stroke-width="2.4"/>
  <path d="M-34 -30 l52 -8 l14 -12 q6 0 4 6 l-10 14 l18 18 l-6 2 l-22 -12 l-10 6 l4 12 l-4 2 l-10 -12 l-30 -4z" fill="${C.cream}" stroke-width="2.4"/>
  <text x="-50" y="76" font-family="Special Elite" font-size="17" fill="${C.ink}" stroke="none">${label}</text>
  <text x="50" y="76" text-anchor="end" font-family="Special Elite" font-size="20" fill="${C.chestnut}" stroke="none">${value}</text>`;
};

const suitcase = () => `
  <path d="M-30 -62 V-80 H30 V-62" fill="none" stroke-width="7"/>
  <rect x="-100" y="-62" width="200" height="132" rx="16" fill="${C.cocoa}"/>
  <path d="M-60 -62 V70 M60 -62 V70" stroke="${C.butter}" stroke-width="10"/>
  <path d="M-60 -62 V70 M60 -62 V70" stroke-width="2"/>
  <rect x="-30" y="-30" width="54" height="34" rx="4" fill="${C.rose}" transform="rotate(-8)"/>
  <circle cx="-14" cy="-14" r="6" fill="${C.cream}" stroke-width="2"/>
  <ellipse cx="38" cy="30" rx="22" ry="14" fill="${C.dove}" transform="rotate(12 38 30)"/>`;

const star = (fill = C.butter) => `<path d="M0 -40 L11 -12 L40 -12 L17 6 L26 36 L0 18 L-26 36 L-17 6 L-40 -12 L-11 -12z" fill="${fill}"/>`;
const heart = (fill = C.rose) => `<path d="M0 34 C-50 0 -44 -40 -14 -36 C-4 -34 0 -24 0 -20 C0 -24 4 -34 14 -36 C44 -40 50 0 0 34z" fill="${fill}"/>`;

const arrow = () => `
  <path d="M-80 -40 Q60 -60 90 -6 Q40 30 -70 30 Q-100 0 -80 -40z" fill="#d8d5cd" stroke="none"/>
  <path d="M-56 4 Q0 26 54 -6 M36 -20 L56 -6 L40 12" fill="none" stroke-width="3"/>`;

// ---------- folk flowers ----------
function flower(x, y, s, petals, fill, center, rot = 0) {
  let p = '';
  for (let i = 0; i < petals; i++) {
    const a = (360 / petals) * i;
    p += `<ellipse cx="0" cy="-22" rx="13" ry="22" transform="rotate(${a})" fill="${fill}"/>`;
  }
  return `<g transform="translate(${x},${y}) rotate(${rot}) scale(${s})">${p}<circle r="10" fill="${center}"/><circle r="4" fill="${C.ink}" stroke="none"/></g>`;
}
function tulip(x, y, s, fill, rot = 0) {
  return `<g transform="translate(${x},${y}) rotate(${rot}) scale(${s})">
    <path d="M0 0 C-30 -6 -34 -46 -22 -58 L-10 -40 L0 -62 L10 -40 L22 -58 C34 -46 30 -6 0 0z" fill="${fill}"/>
    <path d="M0 -6 V-40" stroke="${C.cream}" stroke-width="3"/></g>`;
}
function leaf(x, y, s, rot, fill = C.sage) {
  return `<g transform="translate(${x},${y}) rotate(${rot}) scale(${s})"><path d="M0 0 C12 -16 34 -18 46 0 C34 18 12 16 0 0z" fill="${fill}"/><path d="M4 0 H40" stroke-width="1.8"/></g>`;
}
function dotRow(x, y, n, gap, fill) {
  let o = ''; for (let i = 0; i < n; i++) o += `<circle cx="${x + i * gap}" cy="${y}" r="5" fill="${fill}"/>`; return o;
}

// Ornamental circus/folklore initial with vines and flowers.
// cx = centre x, base = baseline y, size = font size
function initial(letter, cx, base, size, opts = {}) {
  const font = opts.font || 'Rye';
  const fill = opts.fill || 'url(#stripesRose)';
  const t = (dx, dy, f, extra = '') => `<text x="${cx + dx}" y="${base + dy}" text-anchor="middle" font-family="${font}" font-size="${size}" fill="${f}" ${extra}>${letter}</text>`;
  const h = size * 0.74; const top = base - h; const w = size * 0.8;
  // vine curling around the letter
  const vine = `<path d="M${cx - w*0.62} ${base + 10} C${cx - w*0.9} ${base - h*0.4}, ${cx - w*0.55} ${top - 10}, ${cx - w*0.1} ${top - 26}
     C${cx + w*0.3} ${top - 40}, ${cx + w*0.7} ${top + 10}, ${cx + w*0.66} ${base - h*0.5}
     C${cx + w*0.64} ${base - h*0.15}, ${cx + w*0.86} ${base}, ${cx + w*0.74} ${base + 24}" fill="none" stroke="${C.sage}" stroke-width="10" stroke-linecap="round"/>
     <path d="M${cx - w*0.62} ${base + 10} C${cx - w*0.9} ${base - h*0.4}, ${cx - w*0.55} ${top - 10}, ${cx - w*0.1} ${top - 26}
     C${cx + w*0.3} ${top - 40}, ${cx + w*0.7} ${top + 10}, ${cx + w*0.66} ${base - h*0.5}
     C${cx + w*0.64} ${base - h*0.15}, ${cx + w*0.86} ${base}, ${cx + w*0.74} ${base + 24}" fill="none" stroke="${C.ink}" stroke-width="2" stroke-linecap="round"/>`;
  const L = [
    leaf(cx - w*0.78, base - h*0.2, 1, 200), leaf(cx - w*0.8, base - h*0.5, 0.9, 160),
    leaf(cx - w*0.55, top + 4, 0.9, 230), leaf(cx + w*0.12, top - 36, 0.9, -20),
    leaf(cx + w*0.6, top + 30, 0.9, 30), leaf(cx + w*0.66, base - h*0.32, 0.9, -10),
    leaf(cx + w*0.74, base - h*0.08, 0.8, 40), leaf(cx - w*0.88, base - h*0.82, 0.8, 250),
    leaf(cx + w*0.42, top - 30, 0.8, 200), leaf(cx - w*0.5, base + 8, 0.8, 150), leaf(cx + w*0.56, base - h*0.6, 0.8, 120),
  ].join('');
  const F = [
    flower(cx - w*0.72, base - h*0.68, 1.15, 6, C.rose, C.butter, 10),
    flower(cx - w*0.04, top - 30, 1.0, 5, C.butter, C.roseDeep, 0),
    tulip(cx + w*0.52, top - 4, 1.0, C.roseDeep, 25),
    flower(cx + w*0.7, base - h*0.42, 0.9, 8, C.dove, C.cream, 0),
    flower(cx - w*0.66, base + 4, 0.85, 5, C.chestnut, C.butter, 20),
    tulip(cx + w*0.78, base + 20, 0.85, C.rose, 160),
    flower(cx - w*0.3, top - 6, 0.6, 5, C.dove, C.butter, 0),
    flower(cx + w*0.3, top - 34, 0.7, 6, C.rose, C.chestnut, 15),
    flower(cx - w*0.86, base - h*0.3, 0.7, 5, C.butter, C.roseDeep, 0),
    tulip(cx - w*0.8, base - h*0.05, 0.8, C.dove, -150),
    flower(cx + w*0.62, base - h*0.72, 0.6, 5, C.butter, C.chestnut, 0),
  ].join('');
  const berries = dotRow(cx - w*0.34, base + 34, 5, 34, C.roseDeep) + dotRow(cx - w*0.17, base + 60, 3, 34, C.butter);
  return `<g>
    <g filter="url(#soft)">${t(10, 10, C.cocoa)}${t(0, 0, fill, `stroke="${C.ink}" stroke-width="5" paint-order="stroke"`)}</g>
    <g filter="url(#pencil)" stroke="${C.ink}" stroke-width="2">${vine}${L}${F}${berries}</g>
  </g>`;
}

const page = (body) => `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="fonts-local.css">
<style>html,body{margin:0;background:#fff} svg{display:block}</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="1350" viewBox="0 0 1080 1350">${defs}${body}</svg></body></html>`;

module.exports = { C, rng, defs, paper, st, globe, train, compass, balloon, stamp, suitcase, star, heart, arrow, flower, tulip, leaf, initial, page };
// washi tape strip
module.exports.tape = (x, y, w, r, fill = '#f3e2a4') => `<g transform="translate(${x},${y}) rotate(${r})" filter="url(#fiber)"><rect x="${-w/2}" y="-17" width="${w}" height="34" fill="${fill}" fill-opacity="0.78"/></g>`;
// ink postmark
module.exports.postmark = (x, y, r, txt = 'GLOBETROTTER · 2026 ·', city = 'PARIS') => { const C = module.exports.C; return `<g transform="translate(${x},${y}) rotate(${r})" filter="url(#inkprint)" fill="none" stroke="${C.cocoa}" stroke-opacity="0.75" stroke-width="3">
  <circle r="58"/><circle r="40"/>
  <path id="pm${x}" d="M-49 0 A49 49 0 1 1 49 0 A49 49 0 1 1 -49 0" stroke="none"/>
  <text font-family="Special Elite" font-size="13" fill="${C.cocoa}" fill-opacity="0.8" stroke="none" letter-spacing="1"><textPath href="#pm${x}">${txt}</textPath></text>
  <text y="7" text-anchor="middle" font-family="Special Elite" font-size="20" fill="${C.cocoa}" fill-opacity="0.8" stroke="none">${city}</text>
  ${[0,1,2,3].map(i => `<path d="M64 ${-24 + i*16} q22 -10 44 0 t44 0 t44 0"/>`).join('')}
</g>`; };
// airmail label
module.exports.airmail = (x, y, r) => { const C = module.exports.C; return `<g transform="translate(${x},${y}) rotate(${r})" filter="url(#soft)">
  <rect x="-110" y="-26" width="220" height="52" fill="${C.dove}"/><rect x="-102" y="-18" width="204" height="36" fill="${C.cream}"/>
  <text y="8" text-anchor="middle" font-family="Special Elite" font-size="22" fill="${C.doveDeep}">PAR AVION</text></g>`; };
{ const C = module.exports.C;
module.exports.lemons = () => `
  <path d="M-90 40 C-40 0 20 -10 90 -40" fill="none" stroke="${C.cocoa}" stroke-width="6"/>
  <path d="M-40 14 C-30 -20 0 -34 20 -28 C14 -2 -10 14 -40 14z" fill="${C.sage}"/>
  <path d="M30 -14 C50 -48 80 -50 96 -40 C84 -16 60 -6 30 -14z" fill="${C.sage}"/>
  <path d="M-60 30 C-70 10 -40 -6 -50 14z" fill="${C.sage}"/>
  <ellipse cx="-20" cy="52" rx="36" ry="28" fill="${C.butter}" transform="rotate(-20 -20 52)"/>
  <path d="M-52 66 l-8 6 M12 38 l8 -6" stroke-width="3"/>
  <ellipse cx="44" cy="22" rx="30" ry="23" fill="${C.butter}" transform="rotate(15 44 22)"/>
  <circle cx="-30" cy="44" r="4" fill="${C.cream}" stroke="none"/><circle cx="36" cy="14" r="3.5" fill="${C.cream}" stroke="none"/>`;
module.exports.crown = () => `
  <path d="M-80 40 L-90 -40 L-46 0 L0 -60 L46 0 L90 -40 L80 40z" fill="${C.butter}"/>
  <rect x="-84" y="40" width="168" height="26" rx="4" fill="${C.roseDeep}"/>
  <circle cx="-90" cy="-46" r="9" fill="${C.rose}"/><circle cx="0" cy="-68" r="10" fill="${C.dove}"/><circle cx="90" cy="-46" r="9" fill="${C.rose}"/>
  <circle cx="-44" cy="53" r="6" fill="${C.cream}"/><circle cx="0" cy="53" r="7" fill="${C.dove}"/><circle cx="44" cy="53" r="6" fill="${C.cream}"/>
  <path d="M0 -10 l10 18 l-10 14 l-10 -14z" fill="${C.dove}"/>`;
module.exports.map = () => `
  <path d="M-100 -70 L-34 -90 L34 -70 L100 -90 V70 L34 90 L-34 70 L-100 90z" fill="${C.cream}"/>
  <path d="M-34 -90 V70 M34 -70 V90" stroke-width="2"/>
  <path d="M-100 -70 L-34 -90 V70 L-100 90z" fill="${C.butter}" fill-opacity="0.7"/>
  <path d="M34 -70 L100 -90 V70 L34 90z" fill="${C.dove}" fill-opacity="0.6"/>
  <path d="M-80 50 q20 -30 50 -20 t50 -40 t40 -30" fill="none" stroke="${C.chestnut}" stroke-width="3" stroke-dasharray="7 7"/>
  <path d="M62 -86 c-14 0 -22 10 -22 20 c0 16 22 34 22 34 s22 -18 22 -34 c0 -10 -8 -20 -22 -20z" fill="${C.roseDeep}"/><circle cx="62" cy="-66" r="7" fill="${C.cream}"/>
  <path d="M-80 46 l12 12 m0 -12 l-12 12" stroke="${C.chestnut}" stroke-width="4"/>`;
module.exports.sailboat = () => `
  <path d="M-110 70 q20 -12 40 0 t40 0 t40 0 t40 0 t40 0" fill="none" stroke="${C.doveDeep}" stroke-width="5"/>
  <path d="M-90 30 H90 L64 66 H-64z" fill="${C.chestnut}"/>
  <path d="M-80 44 H80" stroke="${C.butter}" stroke-width="4"/>
  <path d="M0 30 V-100" stroke-width="5"/>
  <path d="M6 -94 L76 16 H6z" fill="${C.cream}"/><path d="M-6 -76 L-64 16 H-6z" fill="${C.rose}"/>
  <path d="M0 -100 L34 -90 L0 -80z" fill="${C.roseDeep}"/>`;
module.exports.bear = () => `
  <circle cx="-46" cy="-62" r="22" fill="${C.cocoa}"/><circle cx="46" cy="-62" r="22" fill="${C.cocoa}"/>
  <circle cx="-46" cy="-62" r="10" fill="${C.rose}"/><circle cx="46" cy="-62" r="10" fill="${C.rose}"/>
  <ellipse cx="0" cy="50" rx="56" ry="54" fill="${C.cocoa}"/>
  <ellipse cx="0" cy="58" rx="30" ry="32" fill="${C.kraft}"/>
  <circle cx="0" cy="-30" r="56" fill="${C.cocoa}"/>
  <ellipse cx="0" cy="-12" rx="24" ry="18" fill="${C.kraft}"/>
  <path d="M-8 -20 h16 l-8 8z" fill="${C.ink}"/>
  <circle cx="-20" cy="-40" r="5" fill="${C.ink}" stroke="none"/><circle cx="20" cy="-40" r="5" fill="${C.ink}" stroke="none"/>
  <path d="M-36 20 L0 34 L36 20 L36 0 L0 14 L-36 0z" fill="${C.dove}"/><path d="M0 14 l-12 26 l12 -6 l12 6z" fill="${C.dove}"/>`;
module.exports.plane = () => `
  <path d="M-110 10 C-60 -6 40 -12 100 -2 C116 2 116 14 100 16 C40 24 -60 22 -110 10z" fill="${C.cream}"/>
  <path d="M-20 0 L-60 -70 L-36 -70 L30 -2z" fill="${C.dove}"/><path d="M-20 18 L-56 80 L-32 80 L30 16z" fill="${C.dove}"/>
  <path d="M-96 6 L-118 -34 L-100 -34 L-74 4z" fill="${C.roseDeep}"/>
  <circle cx="40" cy="6" r="5" fill="${C.dove}"/><circle cx="60" cy="6" r="5" fill="${C.dove}"/><circle cx="80" cy="6" r="5" fill="${C.dove}"/>
  <path d="M-140 40 q-30 6 -60 0" fill="none" stroke-dasharray="8 8"/>`;
}
