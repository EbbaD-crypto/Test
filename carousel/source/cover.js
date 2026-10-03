const L = require('./lib'); const { C } = L;
const body = `
<image href="paper.jpg" x="-60" y="-80" width="1200" height="1680" preserveAspectRatio="xMidYMid slice"/>
${L.paper([[58,170],[688,92],[750,800],[112,866]], 'url(#dots)', '', 'torn')}
${L.paper([[28,930],[548,862],[602,1290],[72,1338]], 'url(#lined)')}
<line x1="104" y1="880" x2="118" y2="1316" stroke="${C.roseDeep}" stroke-width="2" opacity="0.7"/>
${L.paper([[420,176],[1000,108],[1042,622],[478,702]], C.rose, 'fill-opacity="0.86"', 'tissue')}
<g transform="rotate(-3 730 400)" fill="${C.ink}">
  <text x="735" y="300" text-anchor="middle" font-family="La Belle Aurore" font-size="120">5</text>
  <text x="735" y="410" text-anchor="middle" font-family="Homemade Apple" font-size="46">Boy Names</text>
  <text x="735" y="490" text-anchor="middle" font-family="Homemade Apple" font-size="46">for Little</text>
  <text x="735" y="575" text-anchor="middle" font-family="Homemade Apple" font-size="46">Globetrotters</text>
</g>
<g transform="rotate(4 845 760)"><g filter="url(#soft)"><rect x="730" y="730" width="230" height="58" fill="${C.butter}"/></g>
<text x="845" y="768" text-anchor="middle" font-family="Special Elite" font-size="22" fill="${C.cocoa}">TRAVEL EDITION · Nº 01</text></g>
${L.postmark(700, 840, -8)}
${L.tape(450, 190, 130, -38)}
${L.tape(1010, 600, 120, -40, '#a8bccb')}
${L.tape(300, 880, 110, 6, '#e9b9ad')}
${L.airmail(320, 690, -6)}
${L.initial('A', 330, 1185, 560)}
${L.st(L.compass(), 175, 205, 0.9, -12)}
${L.st(L.balloon(), 975, 205, 0.62, 10)}
${L.st(L.globe(), 860, 970, 0.95, 8)}
${L.st(L.train(), 760, 1200, 0.9, -4)}
${L.st(L.stamp('POSTE', '5'), 610, 760, 0.62, -9)}
${L.st(L.star(), 120, 760, 0.7, 12)}
${L.st(L.star(C.dove), 1010, 1100, 0.5, -10)}
${L.st(L.heart(), 560, 120, 0.6, -14)}
${L.st(L.heart(C.chestnut), 990, 1290, 0.0001, 0)}
${L.st(L.arrow(), 975, 1290, 0.75, -4)}
`;
require('fs').writeFileSync('cover.html', L.page(body));
