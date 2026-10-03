const L = require('./lib'); const { C } = L;
const fo = (x, y, w, h, html) => `<foreignObject x="${x}" y="${y}" width="${w}" height="${h}"><div xmlns="http://www.w3.org/1999/xhtml" style="width:${w}px;height:${h}px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">${html}</div></foreignObject>`;

function flourish(cx, y, w, cols) {
  const x0 = cx - w / 2;
  const d = `M${x0} ${y} C${x0 + w*0.2} ${y - 30}, ${x0 + w*0.3} ${y + 30}, ${cx} ${y} S${x0 + w*0.8} ${y - 30}, ${x0 + w} ${y}`;
  return `<g filter="url(#pencil)" stroke="${C.ink}" stroke-width="2">
    <path d="${d}" fill="none" stroke="${C.sage}" stroke-width="8" stroke-linecap="round"/><path d="${d}" fill="none" stroke-linecap="round"/>
    ${L.leaf(x0 + w*0.12, y - 8, 0.75, 210)}${L.leaf(x0 + w*0.3, y + 10, 0.75, 20)}${L.leaf(x0 + w*0.68, y - 10, 0.75, 200)}${L.leaf(x0 + w*0.86, y + 8, 0.75, 30)}
    ${L.flower(x0, y, 0.75, 6, cols[0], C.butter)}${L.tulip(cx, y - 2, 0.8, cols[1])}${L.flower(x0 + w, y, 0.75, 5, cols[2], C.cream)}
    ${L.flower(x0 + w*0.22, y - 20, 0.42, 5, C.butter, C.roseDeep)}${L.flower(x0 + w*0.78, y + 18, 0.42, 5, C.butter, C.roseDeep)}
  </g>`;
}

function slide(n, d) {
  const size = Math.min(170, 760 / (0.74 * d.name.length));
  const nameFill = d.nameFill;
  const body = `
<image href="paper.jpg" x="${d.flip ? 1140 : -60}" y="-80" width="1200" height="1680" preserveAspectRatio="xMidYMid slice" ${d.flip ? 'transform="scale(-1,1)"' : ''}/>
${L.paper(d.back, d.backFill)}
${L.paper([[86,176],[994,124],[1014,704],[112,748]], d.card, '', d.cardFilter || 'torn')}
${d.extraTop || ''}
<g transform="rotate(-3 550 440)">
  <g filter="url(#soft)">
    <text x="558" y="${470 + 8}" text-anchor="middle" font-family="Rye" font-size="${size}" fill="${C.cocoa}">${d.name}</text>
    <text x="550" y="470" text-anchor="middle" font-family="Rye" font-size="${size}" fill="${nameFill}" stroke="${C.ink}" stroke-width="4" paint-order="stroke">${d.name}</text>
  </g>
  <text x="550" y="${556 + (d.drop||0)}" text-anchor="middle" font-family="Gentium" font-style="italic" font-size="38" fill="${C.ink}">${d.lang}: ${d.ipa}</text>
  ${flourish(550, 630 + (d.drop||0), 420, d.flo)}
</g>
${L.paper([[150,772],[934,806],[914,1252],[128,1222]], d.note, '', 'torn')}
${d.noteLine ? `<line x1="210" y1="790" x2="190" y2="1232" stroke="${C.roseDeep}" stroke-width="2" opacity="0.7"/>` : ''}
${L.tape(170, 790, 120, -30, d.tape1)}${L.tape(900, 1236, 120, -28, d.tape2)}
<g transform="rotate(1.8 530 1010)">
${fo(210, 820, 650, 390, `
  <div style="font-family:'Special Elite';font-size:27px;line-height:1.45;color:${C.cocoa};margin-bottom:26px">${d.origin}</div>
  <div style="width:70px;height:2px;background:${C.roseDeep};opacity:.6;margin-bottom:26px"></div>
  <div style="font-family:'Homemade Apple';font-size:28px;line-height:1.75;color:${C.ink}">${d.meaning}</div>`)}
</g>
<g transform="rotate(-6 150 110)" filter="url(#soft)"><rect x="80" y="82" width="150" height="56" fill="${C.butter}"/>
<text x="155" y="120" text-anchor="middle" font-family="Special Elite" font-size="26" fill="${C.cocoa}">Nº ${n} / 5</text></g>
${d.stickers}
${n < 5 ? L.st(L.arrow(), 975, 1290, 0.75, -4) : L.st(`<path d="M-90 -40 Q60 -60 100 -6 Q50 34 -80 30 Q-110 0 -90 -40z" fill="#d8d5cd" stroke="none"/><text x="4" y="4" text-anchor="middle" font-family="Homemade Apple" font-size="26" fill="${C.ink}" stroke="none">save ♡</text>`, 960, 1288, 0.85, -4)}
`;
  return L.page(body);
}

const slides = [
 { name: 'Alessio', lang: 'Italian', ipa: '[aˈlɛssjo]', nameFill: C.butter, card: 'url(#dots)', back: [[620,40],[1060,70],[1050,560],[640,520]], backFill: C.rose,
   note: 'url(#lined)', noteLine: true, tape1: C.rose, tape2: C.dove, flo: [C.rose, C.roseDeep, C.butter],
   origin: 'From Greek <i>alexō</i>, meaning<br>“to defend or help.”',
   meaning: 'Someone whose quiet strength makes others feel safe enough to be themselves.',
   stickers: L.st(L.lemons(), 930, 180, 0.8, -8) + L.st(L.train(), 150, 1290, 0.75, 4) + L.st(L.stamp('ITALIA', '5'), 990, 830, 0.6, 8) + L.postmark(860, 760, -6, 'FIRENZE · VENEZIA · 2026 ·', 'ROMA') + L.st(L.star(C.butter), 70, 740, 0.55, 10) },
 { name: 'August', lang: 'English', ipa: '[ˈɔːɡəst]', drop: 34, nameFill: 'url(#stripesRose)', card: C.butter, back: [[-20,600],[420,560],[460,1100],[0,1140]], backFill: C.dove,
   note: C.cream, tape1: C.dove, tape2: C.rose, flo: [C.dove, C.roseDeep, C.rose],
   origin: 'From Latin <i>Augustus</i>, meaning<br>“venerable” or “exalted.”',
   meaning: 'Someone who sees the good in others and gives it room to grow.',
   stickers: L.st(L.balloon(), 960, 200, 0.75, 8) + L.st(L.suitcase(), 160, 1260, 0.7, -6) + L.airmail(820, 760, 5) + L.st(L.heart(C.rose), 1000, 1110, 0.6, 12) + L.st(L.star(C.dove), 300, 120, 0.45, -10) },
 { name: 'Amir', lang: 'Arabic', ipa: '[ʔaˈmiːr]', nameFill: C.dove, card: C.rose, cardFilter: 'tissue', back: [[600,700],[1080,660],[1080,1300],[640,1340]], backFill: C.butter,
   note: 'url(#lined)', noteLine: true, tape1: C.butter, tape2: C.dove, flo: [C.butter, C.chestnut, C.dove],
   origin: 'From Arabic <i>amīr</i>, meaning<br>“prince” or “commander.”',
   meaning: 'Someone who makes others feel they belong, wherever they come from.',
   stickers: L.st(L.crown(), 930, 190, 0.7, 10) + L.st(L.compass(), 150, 1250, 0.75, -10) + L.st(L.map(), 970, 870, 0.55, 8) + L.st(L.star(C.butter), 330, 110, 0.5, 6) + L.st(L.star(C.rose), 1010, 1130, 0.45, -10) },
 { name: 'Atlas', lang: 'English', ipa: '[ˈætləs]', nameFill: C.cream, card: C.dove, back: [[-20,40],[460,80],[420,520],[-30,480]], backFill: C.butter,
   note: C.cream, tape1: C.rose, tape2: C.butter, flo: [C.rose, C.roseDeep, C.butter],
   origin: 'A name from Greek mythology,<br>possibly meaning “to endure.”',
   meaning: 'Someone with the courage to meet the unfamiliar and the tenderness to understand it.',
   stickers: L.st(L.globe(), 930, 210, 0.75, 8) + L.st(L.plane(), 200, 1270, 0.6, -10) + L.postmark(840, 770, 8, 'GREECE · HELLAS · 2026 ·', 'ATHENS') + L.st(L.star(C.butter), 1000, 1120, 0.55, 14) + L.st(L.star(C.butter), 330, 120, 0.42, -8) + L.st(L.heart(C.rose), 80, 760, 0.5, -12) },
 { name: 'Arthur', lang: 'British English', ipa: '[ˈɑːθə]', nameFill: C.rose, card: C.cream, back: [[560,30],[1070,60],[1060,640],[600,600]], backFill: C.dove,
   note: 'url(#lined)', noteLine: true, tape1: C.dove, tape2: C.rose, flo: [C.dove, C.roseDeep, C.butter],
   origin: 'A name of debated origin, possibly connected with the Celtic word for “bear.”',
   meaning: 'Someone who notices what others feel, even when they cannot find the words.',
   stickers: L.st(L.bear(), 930, 210, 0.75, 6) + L.st(L.sailboat(), 160, 1270, 0.65, -6) + L.st(L.stamp('LONDON', '5'), 1000, 840, 0.58, 8) + L.st(L.heart(C.rose), 300, 120, 0.5, -10) + L.st(L.star(C.butter), 70, 760, 0.5, 10) },
];
slides.forEach((d, i) => require('fs').writeFileSync(`name${i + 1}.html`, slide(i + 1, d)));
