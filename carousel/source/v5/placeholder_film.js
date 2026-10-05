// PLACEHOLDER footage until real (licensed) clips are added: a softly painted, moving Italian coast.
// Writes clips/_placeholder_villa.mp4 (720x900, 24 fps). Usage: node placeholder_film.js
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), { execSync } = require('child_process');
const D = __dirname, W = 720, H = 900, FPS = 24, SEC = 7;
const page = `<html><body style="margin:0"><canvas id=c width=${W} height=${H}></canvas><script>
const c = document.getElementById('c'), g = c.getContext('2d');
let s = 7; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
const glints = Array.from({ length: 140 }, () => [rnd() * ${W}, 560 + rnd() * 340, 8 + rnd() * 30, rnd() * 6.28]);
window.draw = t => {
  let gr = g.createLinearGradient(0, 0, 0, 560); gr.addColorStop(0, '#e9d8c6'); gr.addColorStop(0.6, '#f3e2cf'); gr.addColorStop(1, '#f6e6d2');
  g.fillStyle = gr; g.fillRect(0, 0, ${W}, ${H});
  g.fillStyle = 'rgba(255,236,200,.8)'; g.beginPath(); g.arc(520, 330, 46, 0, 7); g.fill();          // low sun
  g.fillStyle = 'rgba(255,240,215,.25)'; g.beginPath(); g.arc(520, 330, 110, 0, 7); g.fill();
  g.fillStyle = '#c9b8a6'; g.beginPath(); g.moveTo(0, 520); g.bezierCurveTo(160, 470, 300, 500, 420, 545); g.lineTo(420, 560); g.lineTo(0, 560); g.fill(); // far cape
  gr = g.createLinearGradient(0, 560, 0, ${H}); gr.addColorStop(0, '#b9c6c8'); gr.addColorStop(1, '#8fa6ad');
  g.fillStyle = gr; g.fillRect(0, 560, ${W}, ${H - 560});                                             // sea
  for (const [x, y, l, p] of glints) { const a = 0.18 + 0.18 * Math.sin(t * 2.2 + p);
    g.strokeStyle = 'rgba(255,245,230,' + a + ')'; g.lineWidth = 2; const dx = Math.sin(t * 0.8 + p) * 6;
    g.beginPath(); g.moveTo(x + dx, y); g.lineTo(x + dx + l * (y - 520) / 300, y); g.stroke(); }
  const bx = 120 + t * 14, by = 610 + Math.sin(t * 1.5) * 2;                                          // drifting boat
  g.fillStyle = '#7a6a60'; g.fillRect(bx - 22, by, 44, 6); g.fillStyle = '#f7efe4';
  g.beginPath(); g.moveTo(bx, by - 46); g.lineTo(bx + 20, by - 2); g.lineTo(bx, by - 2); g.fill();
  g.fillStyle = '#9a8a6a'; g.beginPath(); g.moveTo(${W}, 430); g.bezierCurveTo(640, 450, 560, 560, 500, ${H}); g.lineTo(${W}, ${H}); g.fill(); // hillside
  g.fillStyle = '#f2e6d4'; g.fillRect(600, 420, 120, 90); g.fillStyle = '#b8664a';
  g.beginPath(); g.moveTo(590, 422); g.lineTo(660, 392); g.lineTo(730, 422); g.fill();                 // villa
  g.fillStyle = '#9db0b8'; for (const x of [618, 650, 682]) g.fillRect(x, 445, 14, 22);
  g.fillStyle = '#5f6a46'; for (const [x, h] of [[575, 150], [548, 110]]) { const sw = Math.sin(t * 1.2 + x) * 3;
    g.beginPath(); g.moveTo(x - 14, 530); g.quadraticCurveTo(x - 18, 530 - h * 0.6, x + sw, 530 - h); g.quadraticCurveTo(x + 18, 530 - h * 0.6, x + 14, 530); g.fill(); }
};</script></body></html>`;
(async () => {
  const fdir = D + '/frames_film'; fs.rmSync(fdir, { recursive: true, force: true }); fs.mkdirSync(fdir);
  const b = await chromium.launch(); const p = await b.newPage(); await p.setViewportSize({ width: W, height: H }); await p.setContent(page);
  for (let i = 0; i < FPS * SEC; i++) { await p.evaluate(t => draw(t), i / FPS);
    await p.locator('canvas').screenshot({ path: `${fdir}/f${String(i).padStart(4, '0')}.png` }); }
  await b.close(); fs.mkdirSync(D + '/clips', { recursive: true });
  execSync(`ffmpeg -v error -y -framerate ${FPS} -i ${fdir}/f%04d.png -vf "gblur=sigma=1.2,format=yuv420p" -c:v libx264 -crf 18 ${D}/clips/_placeholder_villa.mp4`);
  fs.rmSync(fdir, { recursive: true, force: true }); console.log('placeholder film done');
})();
