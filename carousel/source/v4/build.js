// New clean style: Milk Honey names, warm off-white paper, lots of air. Carousel (1080x1350) + stop-motion reel (1080x1920).
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path'), { execSync, spawn } = require('child_process');
const D = __dirname, OUT = '/home/user/Test/carousel/';
const b64 = f => fs.readFileSync(f).toString('base64');
const font = (n, f, t) => `@font-face{font-family:${n};src:url(data:font/${t};base64,${b64(f)})}`;
const FONTS = font('MH', '/home/user/Test/brand/fonts/MilkHoney.otf', 'otf') + font('Caslon', D + '/../fonts/LibreCaslonText.ttf', 'ttf') +
  font('CaslonI', D + '/../fonts/LibreCaslonText-Italic.ttf', 'ttf') + font('Gent', D + '/../fonts/Gentium-Italic.ttf', 'ttf');
const img = f => `data:image/png;base64,${b64(D + '/' + f)}`;
const N = [
 ['Alessio','Italian','[aˈlɛssjo]','From Greek <i>alexō</i>, meaning “to defend or help.”','Someone whose quiet strength makes others feel safe enough to be themselves.','train',-6],
 ['August','English','[ˈɔːɡəst]','From Latin <i>Augustus</i>, meaning “venerable” or “exalted.”','Someone who sees the good in others and gives it room to grow.','suitcase',5],
 ['Amir','Arabic','[ʔaˈmiːr]','From Arabic <i>amīr</i>, meaning “prince” or “commander.”','Someone who makes others feel they belong, wherever they come from.','compass',-4],
 ['Atlas','English','[ˈætləs]','A name from Greek mythology, possibly meaning “to endure.”','Someone with the courage to meet the unfamiliar and the tenderness to understand it.','globe',6],
 ['Arthur','British English','[ˈɑːθə]','A name of debated origin, possibly connected with the Celtic word for “bear.”','Someone who notices what others feel, even when they cannot find the words.','sailboat',-5],
];
const css = (H) => `${FONTS}
*{margin:0;box-sizing:border-box} body{width:1080px;height:${H}px;background:#f7f1ec url(${img('paper.png')}) center/cover;color:#3b2f2a;font-family:Caslon;overflow:hidden;position:relative}
.wrap{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 120px}
.top{position:absolute;top:${H>1500?230:80}px;left:0;right:0;text-align:center;font-family:CaslonI;font-size:30px;letter-spacing:1px;color:#8a7468}
.no{position:absolute;top:${H>1500?230:80}px;right:90px;font-size:26px;color:#8a7468;letter-spacing:2px}
.name{font-family:MH;font-size:210px;line-height:1;margin-bottom:28px}
.ipa{font-family:Gent;font-size:44px;color:#5a4a42;margin-bottom:46px}
.rule{width:70px;height:2px;background:#c9b6a8;margin-bottom:46px}
.org,.mean,.cs{text-wrap:balance}
.org{font-size:34px;line-height:1.5;color:#4a3d36;max-width:760px;margin-bottom:34px}
.mean{font-family:CaslonI;font-size:40px;line-height:1.45;color:#3b2f2a;max-width:780px}
.sym{position:absolute;width:190px;bottom:${H>1500?300:120}px;right:110px}
.swipe{position:absolute;bottom:${H>1500?230:56}px;left:0;right:0;text-align:center;font-family:CaslonI;font-size:28px;color:#8a7468}
.big5{font-family:MH;font-size:420px;line-height:.9}
.ct{font-family:MH;font-size:120px;line-height:1.05;margin-top:20px}
.cs{font-family:CaslonI;font-size:56px;margin-top:40px;color:#4a3d36}
.h{visibility:hidden}`;
const nameHTML = (i, H, step) => { const [n,l,ipa,o,m,s,r]=N[i]; const v=k=>step>=k?'':'h';
 return `<html><head><meta charset=utf-8><style>${css(H)}</style></head><body>
 <div class="top ${v(1)}">a little archive of names</div><div class="no ${v(1)}">Nº ${i+1} / 5</div>
 <div class=wrap><div class="name ${v(1)}">${n}</div><div class="ipa ${v(2)}">${l} ${ipa}</div><div class="rule ${v(2)}"></div>
 <div class="org ${v(3)}">${o}</div><div class="mean ${v(3)}">${m}</div></div>
 <img class="sym ${v(4)}" src="${img(s+'.png')}" style="transform:rotate(${r}deg)">
 <div class="swipe ${v(4)}">${i<4?'swipe →':'save for later'}</div></body></html>`; };
const coverHTML = (H, step) => { const v=k=>step>=k?'':'h'; return `<html><head><meta charset=utf-8><style>${css(H)}</style></head><body>
 <div class=wrap><div class="big5 ${v(1)}">5</div><div class="ct ${v(1)}">Boy Names</div>
 <div class="cs ${v(2)}">for little globetrotters</div></div>
 <img class="sym ${v(3)}" src="${img('balloon.png')}" style="transform:rotate(6deg);right:110px;bottom:${H>1500?300:150}px;width:170px">
 <img class="sym ${v(3)}" src="${img('plane.png')}" style="transform:rotate(-10deg);top:${H>1500?330:150}px;left:110px;bottom:auto;width:230px">
 <div class="swipe ${v(3)}">a little archive of names</div></body></html>`; };
const endHTML = (H, step) => `<html><head><meta charset=utf-8><style>${css(H)}</style></head><body>
 <div class=wrap><div class="ct" style="font-size:110px">The Little<br>Archive</div><div class="cs ${step>=2?'':'h'}">letters in ceramic</div></div>
 <div class="swipe ${step>=2?'':'h'}">save for later</div></body></html>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const shot = async (html, H, file) => { await p.setViewportSize({ width: 1080, height: H }); await p.setContent(html);
    await p.evaluate(async () => { await document.fonts.load('80px MH'); await document.fonts.ready; }); await p.waitForTimeout(120);
    await p.screenshot({ path: file }); };
  const names = ['01_omslag','02_Alessio','03_August','04_Amir','05_Atlas','06_Arthur'];
  await shot(coverHTML(1350, 9), 1350, OUT + names[0] + '.png');
  for (let i = 0; i < 5; i++) await shot(nameHTML(i, 1350, 9), 1350, OUT + names[i + 1] + '.png');
  // reel: stop motion – each element simply appears; hard cuts
  const fdir = D + '/frames'; fs.rmSync(fdir, { recursive: true, force: true }); fs.mkdirSync(fdir);
  let k = 0; const add = async (html, holdFrames) => { const f = `${fdir}/s${String(k).padStart(3,'0')}.png`; await shot(html, 1920, f);
    fs.appendFileSync(fdir + '/list.txt', `file '${f}'\nduration ${(holdFrames/12).toFixed(4)}\n`); k++; };
  await add(coverHTML(1920, 0), 4);
  for (const s of [1,2,3]) await add(coverHTML(1920, s), s < 3 ? 6 : 24);
  for (let i = 0; i < 5; i++) { await add(nameHTML(i, 1920, 0), 3); for (const s of [1,2,3,4]) await add(nameHTML(i, 1920, s), s < 4 ? 5 : 30); }
  await add(endHTML(1920, 1), 8); await add(endHTML(1920, 2), 36);
  fs.appendFileSync(fdir + '/list.txt', `file '${fdir}/s${String(k-1).padStart(3,'0')}.png'\n`);
  await b.close();
  execSync(`ffmpeg -v error -y -f concat -safe 0 -i ${fdir}/list.txt -vf "fps=24,format=yuv420p" -c:v libx264 -crf 20 -preset slow -movflags +faststart ${OUT}reel_5_boy_names.mp4`);
  console.log('done');
})();
