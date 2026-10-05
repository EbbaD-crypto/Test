// Reel 1080x1920: a cut-out postcard on the paper where the film plays, then the names in stop motion, then the postcard again.
// Film per post: clips/<post dir>.mp4 (licensed footage), otherwise clips/_placeholder_villa.mp4.
// Usage: node reel.js [postNo ...]
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), { execSync } = require('child_process');
const { POSTS, html, mh, sym, nameHTML, fit, OUT } = require('./build');
const D = __dirname, H = 1920, FPS = 24;
const run = c => execSync(c, { stdio: ['ignore', 'ignore', 'inherit'] });

// postcard with a window (.win) where the film shows through; step reveals title / caption
const cardCSS = `.card{position:absolute;left:170px;top:600px;width:740px;padding:26px 26px 0;background:#fbf7f0;transform:rotate(-2deg);
  box-shadow:0 0 0 1px rgba(90,70,55,.12),0 2px 3px rgba(90,70,55,.10)}
 .win{width:688px;height:860px;background:#8a7a6c;box-shadow:0 0 0 3px #8a7a6c}
 .cap{height:112px;display:flex;align-items:center;justify-content:space-between;padding:0 6px;font-family:CaslonI;font-size:34px;color:#6b5a50}
 .cap img{height:84px;transform:rotate(6deg)}
 .tt{position:absolute;top:250px;left:0;right:0;text-align:center}
 .tt .ct{font-size:118px;margin:0;display:inline-block} .tt .cs{margin-top:22px;font-size:54px;margin-left:auto;margin-right:auto}`;
const cardHTML = (p, step, end = false) => { const v = k => step >= k ? '' : 'h'; return html(`<style>${cardCSS}</style>
 <div class="tt">${end ? `<div class="ct ${v(2)}" style="font-size:96px">Save for later</div><div class="cs ${v(2)}">a little archive of names</div>`
   : `<div class="ct ${v(2)}">5 ${p.kind} Names</div><div class="cs ${v(3)}">${p.sub}</div>`}</div>
 <div class="card ${v(1)}"><div class=win></div><div class=cap><span>${p.place}</span><img src="${sym(p.cover[1][0])}"></div></div>`, H); };

(async () => {
  const which = process.argv.slice(2).map(Number); const b = await chromium.launch(); const pg = await b.newPage();
  await pg.setViewportSize({ width: 1080, height: H });
  const tmp = D + '/frames'; fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp);
  const shot = async (h, file) => { await pg.setContent(h); await fit(pg); await pg.waitForTimeout(80); await pg.screenshot({ path: file }); };
  for (const [no, p] of Object.entries(POSTS)) { if (which.length && !which.includes(+no)) continue;
    const film = fs.existsSync(`${D}/clips/${p.dir}.mp4`) ? `${D}/clips/${p.dir}.mp4` : `${D}/clips/_placeholder_villa.mp4`;
    const segs = [];
    // postcard segment: film under a paper layer with the window punched out; layers pop on at hard cuts
    const cardSeg = async (name, steps, filmStart, end) => {
      const imgs = [];
      for (const [k, step] of steps.entries()) { const f = `${tmp}/${name}_${k}.png`; await shot(cardHTML(p, step[0], end), f); imgs.push(f); }
      // window mask (white = paper layer, black = film shows through)
      const mask = `${tmp}/${name}_mask.png`; await pg.setContent(cardHTML(p, 1, end).replace('</body>',
        '<style>body{background:#fff !important}*{visibility:hidden}.win{visibility:visible;background:#000 !important;box-shadow:none !important}</style></body>'));
      await pg.screenshot({ path: mask });
      await pg.setContent(cardHTML(p, 1, end)); const r = await pg.evaluate(() => { const b = document.querySelector('.win').getBoundingClientRect();
        return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
      const total = steps.reduce((a, s) => a + s[1], 0); let t = 0;
      const ins = imgs.map(f => `-loop 1 -t ${total} -i ${f}`).join(' ') + ` -loop 1 -t ${total} -i ${mask}`;
      let fc = `[0:v]trim=start=${filmStart}:duration=${total},setpts=PTS-STARTPTS,scale=760:-2,rotate=-2*PI/180:c=black,` +
        `eq=saturation=0.86:gamma=1.03,colorbalance=rs=.04:bs=-.04,noise=alls=7:allf=t,fps=${FPS}[film];` +
        `color=c=#f7f1ec:s=1080x${H}:r=${FPS}:d=${total}[bg];[bg][film]overlay=x=${Math.round(r.x)}-w/2:y=${Math.round(r.y)}-h/2:shortest=1[v0];`;
      fc += `[${imgs.length + 1}:v]format=gray,split=${imgs.length}${imgs.map((_, k) => `[m${k}]`).join('')};`;
      imgs.forEach((f, k) => { const s = steps[k][1];
        // step 0 hides the card, so no window is punched out
        fc += steps[k][0] ? `[${k + 1}:v][m${k}]alphamerge[l${k}];` : `[${k + 1}:v]format=rgba[l${k}];[m${k}]nullsink;`;
        fc += `[v${k}][l${k}]overlay=enable='between(t,${t.toFixed(3)},${(t + s - 0.001).toFixed(3)})'[v${k + 1}];`; t += s; });
      const out = `${tmp}/${name}.mp4`;
      run(`ffmpeg -v error -y -stream_loop -1 -i ${film} ${ins} -filter_complex "${fc.slice(0, -1)}" -map "[v${imgs.length}]" -t ${total} -r ${FPS} -pix_fmt yuv420p -c:v libx264 -crf 19 ${out}`);
      segs.push(out); };
    // intro: paper, card, title, subtitle
    await cardSeg('intro', [[0, 4 / 12], [1, 8 / 12], [2, 6 / 12], [3, 30 / 12]], 0, false);
    // names: stop motion, each part simply appears (12 fps, hard cuts)
    let list = '';
    for (let i = 0; i < 5; i++) for (const [st, hold] of [[0, 3], [1, 5], [2, 5], [3, 5], [4, 30]]) {
      const f = `${tmp}/n${i}_${st}.png`; await shot(nameHTML(p, i, H, st), f); list += `file '${f}'\nduration ${(hold / 12).toFixed(4)}\n`; }
    list += `file '${tmp}/n4_4.png'\n`; fs.writeFileSync(`${tmp}/names.txt`, list);
    run(`ffmpeg -v error -y -f concat -safe 0 -i ${tmp}/names.txt -vf "fps=${FPS},format=yuv420p" -c:v libx264 -crf 19 ${tmp}/names.mp4`);
    segs.push(`${tmp}/names.mp4`);
    await cardSeg('end', [[0, 3 / 12], [1, 8 / 12], [2, 30 / 12]], 3.5, true);
    fs.writeFileSync(`${tmp}/all.txt`, segs.map(s => `file '${s}'`).join('\n'));
    const out = `${OUT}${p.dir}/reel_${p.dir}.mp4`;
    run(`ffmpeg -v error -y -f concat -safe 0 -i ${tmp}/all.txt -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p -movflags +faststart ${out}`);
    console.log('reel', out, film.includes('_placeholder') ? '(PLACEHOLDER film)' : '');
  }
  await b.close(); fs.rmSync(tmp, { recursive: true, force: true });
})();
