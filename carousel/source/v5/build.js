// Carousels in the clean Milk Honey style (v4), with theme symbols per post.
// Content from content/namnkaruseller_A-Z.pdf, in publishing order. Usage: node build.js [postNo ...]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs');
const D = __dirname, ROOT = D + '/../../../', OUT = ROOT + 'carousel/';
const b64 = f => fs.readFileSync(f).toString('base64');
const F = D + '/../fonts/';
const LATIN = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD';
const EXT = 'U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF';
const face = (n, f, r) => `@font-face{font-family:${n};src:url(data:font/woff2;base64,${b64(F + f)});unicode-range:${r}}`;
const FONTS = `@font-face{font-family:MH;src:url(data:font/otf;base64,${b64(ROOT + 'brand/fonts/MilkHoney.otf')})}` +
  face('Caslon', 'Caslon.woff2', LATIN) + face('Caslon', 'Caslon-ext.woff2', EXT) +
  face('CaslonI', 'CaslonI.woff2', LATIN) + face('CaslonI', 'CaslonI-ext.woff2', EXT) +
  face('Gent', 'Gent.woff2', LATIN) + face('Gent', 'Gent-ext.woff2', EXT);
const sym = n => `data:image/png;base64,${b64(D + '/sym/' + n + '.png')}`;
const PAPER = `data:image/png;base64,${b64(D + '/../v4/paper.png')}`;

// [name, pronunciation (as in the PDF), origin, story phrase, symbol, tilt]
const POSTS = {
  1: { dir: '01_V_boy_italian_villa', kind: 'Boy', sub: 'for an Italian Villa', cover: [['villa', -4, 250], ['lemons', 8, 200]], names: [
    ['Valerio', 'Italian [vah-LEH-ryoh]', 'Italian form of the Roman family name Valerius, from Latin <i>valeo</i>, to be strong.', 'Someone who holds courage and compassion close together.', 'cypress', -5],
    ['Vincent', 'French [van-SAHN]', 'From Latin Vincentius, based on <i>vinco</i>, to conquer.', 'Someone who celebrates other people’s growth as warmly as their own.', 'moka', 5],
    ['Viktor', 'German [VIK-tor]', 'A form of Latin <i>Victor</i>, victor or conqueror, used in many European languages.', 'Someone whose determination leaves room for fairness, patience and kindness.', 'olive', -6],
    ['Valentino', 'Italian [vah-lehn-TEE-noh]', 'Italian form of Valentinus, from Latin <i>Valens</i>, strong, vigorous or healthy.', 'Someone whose warmth is expressive and whose affection is wholehearted.', 'lemontree', 4],
    ['Viggo', 'Swedish [VIG-go]', 'Short form of names containing Old Norse <i>vig</i>, war or battle.', 'Someone who is spirited enough to be brave and thoughtful enough to be gentle.', 'grapes', -4],
  ]},
  2: { dir: '02_A_girl_villa_by_the_sea', kind: 'Girl', sub: 'for a Villa by the Sea', cover: [['gulls', -6, 210], ['parasol', 7, 210]], names: [
    ['Alma', 'Spanish [AL-ma]', 'Probably Latin <i>almus</i>, meaning nourishing. The Spanish word <i>alma</i> means soul, an additional association.', 'Someone whose warmth stays with you long after you have said goodbye.', 'hat', -5],
    ['Amara', 'English approximation [ah-MAR-ah]', 'In Igbo, Amara means grace. This is the Igbo origin; other traditions use the same spelling.', 'Someone who makes being loved feel simple, generous and without conditions.', 'shell', 6],
    ['Alba', 'Italian [AL-ba]', 'Italian and Spanish <i>alba</i> means dawn; this can inspire the name. Older Latin and Germanic origins also exist.', 'Someone who sees each new beginning as a reason to hope.', 'dawn', -4],
    ['Astrid', 'Swedish [AS-strid]', 'From Old Norse <i>Ástríðr</i>, combining a word for god with a word for beautiful or beloved.', 'Someone who trusts their own path while making room for yours.', 'starfish', 8],
    ['Adèle', 'French [ah-DEL]', 'French form of Adela, from the Germanic element <i>adal</i>, meaning noble.', 'Someone whose gentle heart gives even the smallest feelings a place to belong.', 'sailboat', -5],
  ]},
  3: { dir: '03_B_boy_countryside', kind: 'Boy', sub: 'for a Childhood in the Countryside', cover: [['barn', -4, 250], ['wheat', 6, 170]], names: [
    ['Bruno', 'Italian [BROO-no]', 'Germanic name with disputed roots: brown is one possibility; armour or protection is another.', 'Someone whose strength is gentle and whose affection is wholehearted.', 'wellies', -5],
    ['Benjamin', 'English [BEN-juh-min]', 'Hebrew name combining son and right hand; the latter can also refer to the south.', 'Someone who offers reassurance without making anyone feel small.', 'apple', 6],
    ['Basil', 'English [BAZ-uhl]', 'From Greek Basileios, based on <i>basileus</i>, king; its sense is royal.', 'Someone whose imagination is bold and whose heart is generous.', 'basil', -6],
    ['Björn', 'Swedish [BYURN (ö-sound)]', 'Scandinavian name from Old Norse <i>bjǫrn</i>, meaning bear.', 'Someone who is brave enough to be tender and steady enough to be trusted.', 'bear', 5],
    ['Bodhi', 'English [BOH-dee]', 'From Sanskrit <i>bodhi</i>, awakening or enlightenment, a central concept in Buddhism.', 'Someone who pays attention with patience, curiosity and an open heart.', 'bodhileaf', -4],
  ]},
};

const css = `${FONTS}
*{margin:0;box-sizing:border-box} body{width:1080px;height:1350px;background:#f7f1ec url(${PAPER}) center/cover;color:#3b2f2a;font-family:Caslon;overflow:hidden;position:relative}
.wrap{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 120px}
.top{position:absolute;top:80px;left:0;right:0;text-align:center;font-family:CaslonI;font-size:30px;letter-spacing:1px;color:#8a7468}
.no{position:absolute;top:80px;right:90px;font-size:26px;color:#8a7468;letter-spacing:2px}
.name{font-family:MH;font-size:210px;line-height:1;margin-bottom:28px;white-space:nowrap}
.ipa{font-family:Gent;font-size:42px;color:#5a4a42;margin-bottom:46px}
.rule{width:70px;height:2px;background:#c9b6a8;margin-bottom:46px}
.org,.mean,.cs{text-wrap:balance}
.org{font-size:34px;line-height:1.5;color:#4a3d36;max-width:780px;margin-bottom:34px}
.mean{font-family:CaslonI;font-size:40px;line-height:1.45;color:#3b2f2a;max-width:780px}
.sym{position:absolute;width:auto;height:auto;max-width:210px;max-height:190px;bottom:120px;right:100px}
.dia{position:relative;display:inline-block}
.dia i{position:absolute;display:block;background:radial-gradient(circle at 40% 35%,#6a4632 0,#4e3326 60%,rgba(78,51,38,.0) 100%);opacity:.9}
.uml i{width:.15em;height:.15em;border-radius:50%;top:.05em}
.uml i:first-child{left:22%} .uml i:last-child{right:22%}
.grave i{width:.11em;height:.24em;border-radius:.06em;top:-.03em;left:40%;transform:rotate(-38deg);background:linear-gradient(#6a4632,#4e3326)}
.swipe{position:absolute;bottom:56px;left:0;right:0;text-align:center;font-family:CaslonI;font-size:28px;color:#8a7468}
.big5{font-family:MH;font-size:420px;line-height:.9}
.ct{font-family:MH;font-size:120px;line-height:1.05;margin-top:20px;white-space:nowrap}
.cs{font-family:CaslonI;font-size:56px;margin-top:40px;color:#4a3d36;max-width:820px;line-height:1.25}`;
// Milk Honey has no accented glyphs (ö draws as O), so diacritics are added by hand above the letter
const MARKS = { 'ö': ['O', 'uml', 2], 'ä': ['A', 'uml', 2], 'ü': ['U', 'uml', 2], 'è': ['E', 'grave', 1], 'é': ['E', 'acute', 1] };
const mh = t => [...t].map(c => { const k = MARKS[c.toLowerCase()];
  return k ? `<span class="dia ${k[1]}">${k[0]}${'<i></i>'.repeat(k[2])}</span>` : c; }).join('');
const html = body => `<html><head><meta charset=utf-8><style>${css}</style></head><body>${body}</body></html>`;

const nameHTML = (p, i) => { const [n, ipa, o, m, s, r] = p.names[i]; return html(`
 <div class=top>a little archive of names</div><div class=no>Nº ${i + 1} / 5</div>
 <div class=wrap><div class=name>${mh(n)}</div><div class=ipa>${ipa}</div><div class=rule></div>
 <div class=org>${o}</div><div class=mean>${m}</div></div>
 <img class=sym src="${sym(s)}" style="transform:rotate(${r}deg)">
 <div class=swipe>${i < 4 ? 'swipe →' : 'save for later'}</div>`); };
const coverHTML = p => { const [[s1, r1, w1], [s2, r2, w2]] = p.cover; return html(`
 <div class=wrap><div class=big5>5</div><div class=ct>${p.kind} Names</div><div class=cs>${p.sub}</div></div>
 <img class=sym src="${sym(s1)}" style="transform:rotate(${r1}deg);top:130px;left:100px;bottom:auto;right:auto;max-width:${w1}px">
 <img class=sym src="${sym(s2)}" style="transform:rotate(${r2}deg);right:100px;bottom:140px;max-width:${w2}px">
 <div class=swipe>a little archive of names</div>`); };

(async () => {
  const which = process.argv.slice(2).map(Number); const b = await chromium.launch(); const pg = await b.newPage();
  await pg.setViewportSize({ width: 1080, height: 1350 });
  const shot = async (h, file) => { await pg.setContent(h);
    await pg.evaluate(async () => { await document.fonts.load('80px MH'); await document.fonts.ready;
      // long names: shrink until they fit the text column
      for (const el of document.querySelectorAll('.name,.ct')) { let s = parseFloat(getComputedStyle(el).fontSize);
        while (el.scrollWidth > 860 && s > 60) el.style.fontSize = (s -= 4) + 'px'; } });
    await pg.waitForTimeout(100); await pg.screenshot({ path: file }); };
  for (const [no, p] of Object.entries(POSTS)) { if (which.length && !which.includes(+no)) continue;
    const dir = OUT + p.dir + '/'; fs.mkdirSync(dir, { recursive: true });
    await shot(coverHTML(p), dir + '01_omslag.png');
    for (let i = 0; i < 5; i++) await shot(nameHTML(p, i), dir + `0${i + 2}_${p.names[i][0]}.png`);
    console.log('built', p.dir); }
  await b.close();
})();
