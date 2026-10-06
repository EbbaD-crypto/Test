// Cover on a scanned paper photo (two torn cream cards): title printed on the tilted upper card, one symbol on the lower card.
// Usage: node paper_cover.js [postNo ...]  -> carousel/<post dir>/01_omslag_papper.png
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs');
const { POSTS, html, sym, fit, OUT } = require('./build');
const D = __dirname;
const BG = `data:image/jpeg;base64,${fs.readFileSync(D + '/../../../brand/referenser/papper/rivna_kort_kram.jpg').toString('base64')}`;
// photo is 1414x2000; show a 4:5 slice (y 120..1887) scaled to 1080 wide
const css = `body{background:#efe4cc url(${BG}) 0 -${Math.round(120 * 1080 / 1414)}px / 1080px auto no-repeat}
 .ink{mix-blend-mode:multiply}
 .card{position:absolute;left:150px;top:300px;width:820px;transform:rotate(-15deg);text-align:center}
 .card .big5{font-size:300px} .card .ct{font-size:104px;margin-top:6px;display:inline-block} .card .cs{font-size:50px;margin:30px auto 0;max-width:640px}
 .low{position:absolute;bottom:92px;left:0;right:0;text-align:center;font-family:CaslonI;font-size:28px;color:#7d6a5c}
 .s{position:absolute;max-width:250px;max-height:200px;mix-blend-mode:multiply}`;
const page = p => html(`<style>${css}</style>
 <div class="card ink"><div class=big5>5</div><div class=ct>${p.kind} Names</div><div class=cs>${p.sub}</div></div>
 <img class="s" src="${sym(p.cover[0][0])}" style="left:150px;bottom:150px;transform:rotate(-3deg)">
 <div class="low ink" style="left:360px">a little archive of names</div>`);
(async () => {
  const which = process.argv.slice(2).map(Number); const b = await chromium.launch(); const pg = await b.newPage();
  await pg.setViewportSize({ width: 1080, height: 1350 });
  for (const [no, p] of Object.entries(POSTS)) { if (which.length && !which.includes(+no)) continue;
    await pg.setContent(page(p)); await fit(pg); await pg.waitForTimeout(100);
    await pg.screenshot({ path: `${OUT}${p.dir}/01_omslag_papper.png` }); console.log('paper cover', p.dir); }
  await b.close();
})();
