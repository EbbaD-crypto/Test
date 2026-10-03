"""Wes Anderson-style reel: centred symmetric tableaux, one paper world per scene, whip-pans."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
import comp
from archive import *
from comp import Canvas, rotate_rgba, noise, torn, rot_rgba4
from logo import logo_rgba
W, H, FPS = 1080, 1920, 24
comp.W, comp.H = W, H
R = '/home/user/Test/brand/referenser/'
def scan(path, x0f=0.5, flip=False):
    im = cv2.imread(path)[..., ::-1].astype(np.float32) / 255
    if flip: im = im[:, ::-1]
    h, w = im.shape[:2]; tw = int(h * W / H)
    if tw <= w: x0 = int((w - tw) * x0f); im = im[:, x0:x0 + tw]
    else: th = int(w * H / W); im = im[(h - th) // 2:(h - th) // 2 + th]
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
BG = {
    'pattern': scan(R + 'monster_blomkors.jpg'),
    'land':    scan(R + 'rivet_papper_2.jpg', 0.5),
    'confetti': scan(R + 'rivet_papper_3_konfetti.jpg', 0.5),
    'collage': scan(R + 'rivet_papper_1.jpg', 0.0),
    'pink':    scan(R + 'rivet_papper_1.jpg', 1.0),
    'kraft':   scan('src/crumple.jpg'),
}
def place(cv, rgb, a, cx, cy, rot=0.0, lift=0.0, scale=1.0):
    if scale != 1: rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA); a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    if rot: rgb, a = rotate_rgba(rgb, a, rot)
    cv.put(rgb, a, int(round(cx - a.shape[1] / 2)), int(round(cy - a.shape[0] / 2)),
           shadow=0.16 + 0.22 * lift, sdx=int(1 + 14 * lift), sdy=int(1 + 22 * lift), sblur=1.2 + 10 * lift)
def title(cv, text, y=150, size=40):
    type_in(cv.img, text, 'IMFellEnglishSC', size, W // 2, y, seed=len(text))
CHAP = ['One', 'Two', 'Three', 'Four', 'Five']
# confetti: torn pink scraps cut from the pink scan
PINK = BG['pink']
def scrap(seed):
    r = np.random.default_rng(seed); s = int(r.uniform(38, 62))
    m = np.zeros((s + 24, s + 24), np.float32); m[12:12 + s, 12:12 + int(s * r.uniform(0.75, 1.2)) if 12 + int(s * 1.2) < s + 24 else s + 12] = 1
    inner = torn(m, 2.5, 1.2, seed); outer = torn(cv2.dilate(m, np.ones((5, 5), np.uint8)), 3, 1.6, seed + 1)
    y, x = r.integers(150, 1000), r.integers(560, 980)
    t = PINK[y:y + m.shape[0], x:x + m.shape[1]] * 1.04
    rgb = t * inner[..., None] + np.array([0.97, 0.94, 0.92]) * np.clip(outer - inner, 0, 1)[..., None]
    return np.clip(rgb, 0, 1).astype(np.float32), np.clip(np.maximum(inner, (outer - inner) * 0.85), 0, 1).astype(np.float32)
SCRAPS = [scrap(i) for i in range(40)]
# --------------- scenes (each: list of (frame, hold))
def sc_cover():
    out = []
    nb, na = scaled(5, 760); nb = age(nb, na, 2)
    type_in(nb, '5', 'IMFellEnglishSC', 150, 380, 150, seed=1, depth=1.2)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        type_in(nb, l, 'IMFellEnglishSC', 66, 380, 290 + i * 78, seed=2 + i)
    type_in(nb, 'a little archive of names', 'CourierPrime-Italic', 28, 380, 800, seed=9)
    for d in [1.0, 0.5, 0.18, 0.0]:
        cv = Canvas(BG['pattern']); place(cv, nb, na, W / 2, H / 2 + 40 + d * 1300, lift=0.3 * d)
        stamp_logo(cv, W / 2, 230, 300, 0, seed=0); out.append((cv.img.copy(), 2 if d else 30))
    return out
def sc_pull(n, bgk, color=None, chap=True):
    t = NAMES[n - 1]; card = make_card(n, *t[:5], color=color); front = decorate_front(make_front(n), n)
    out = []
    for p in [0, 60, 140, 175, 260, 330, 350, 400]:
        cv = Canvas(BG[bgk]); title(cv, f'Chapter {CHAP[n-1]}')
        rgb, a = folder_unit(front, card, p, n)
        place(cv, rgb, a, W / 2, H / 2 + 120, scale=1.12)
        out.append((cv.img.copy(), 2 if p else 8))
    out[-1] = (out[-1][0], 34); return out
def sc_confetti(n, bgk, color):
    t = NAMES[n - 1]; card = make_card(n, *t[:5], color=color)
    r = np.random.default_rng(n); drops = []
    while len(drops) < 24:
        x, y = r.uniform(60, 1020), r.uniform(330, 1800)
        inside = 190 < x < 890 and 470 < y < 1470
        corner = inside and (y > 1380 or (x > 820 and y < 560))
        if inside and not corner: continue
        drops.append((x, y, r.uniform(-40, 40), r.integers(0, 40)))
    out = []
    for step in range(7):
        cv = Canvas(BG[bgk]); title(cv, f'Chapter {CHAP[n-1]}')
        place(cv, card, CARD_A, W / 2, H / 2 + 60, scale=1.2)
        for i, (x, y, rr, si) in enumerate(drops):
            k = i * 6 // len(drops)
            if k < step:
                place(cv, *SCRAPS[si], x, y, rr)
            elif k == step:
                place(cv, *SCRAPS[si], x, y - 140, rr + 20, lift=0.6)
        out.append((cv.img.copy(), 2 if step else 8))
    out[-1] = (out[-1][0], 34); return out
def sc_lift(n, bgk, color):
    t = NAMES[n - 1]; card = make_card(n, *t[:5], color=color)
    d_rgb, d_a = scaled(1, 820); d_rgb = age(d_rgb, d_a, 30 + n)
    out = []
    for p in [0, 0.12, 0.3, 0.55, 0.8, 1.0]:
        cv = Canvas(BG[bgk]); title(cv, f'Chapter {CHAP[n-1]}')
        place(cv, card, CARD_A, W / 2, H / 2 + 60, scale=1.2)
        lift = np.sin(np.pi * p) * 0.9
        if p < 1: place(cv, d_rgb, d_a, W / 2 + 900 * p, H / 2 + 60 - 300 * p, 30 * p, lift=lift, scale=1 + 0.05 * lift)
        out.append((cv.img.copy(), 2 if 0 < p < 1 else 8))
    out[-1] = (out[-1][0], 34); return out
def sc_stamp(n, bgk, color):
    t = NAMES[n - 1]; card = make_card(n, *t[:5], color=color)
    out = []
    for d in [1.0, 0.45, 0.12, 0.0]:
        cv = Canvas(BG[bgk]); title(cv, f'Chapter {CHAP[n-1]}')
        place(cv, card, CARD_A, W / 2, H / 2 + 60 - d * 1400, scale=1.2, lift=0.3 * d); out.append((cv.img.copy(), 2))
    base = cv.img.copy()
    lg = logo_rgba(330, seed=n)
    for sc_, op, shake in [(1.25, 0.0, 0), (1.06, 0.95, 14), (1.0, 0.9, -6), (1.0, 0.9, 0)]:
        c = base.copy()
        if op:
            r4 = cv2.resize(lg, None, fx=sc_, fy=sc_); r4 = rot_rgba4(r4, -4); r4[..., 3] *= op
            cv = Canvas(c); cv.ink(r4, int(W / 2 + 120 - r4.shape[1] / 2), int(H / 2 + 520 - r4.shape[0] / 2)); c = cv.img
        if shake: c = cv2.warpAffine(c, np.float32([[1, 0, 0], [0, 1, shake]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        out.append((c, 2))
    out[-1] = (out[-1][0], 34); return out
def sc_end():
    cv = Canvas(BG['pink'])
    lg = logo_rgba(620, seed=3); cv.ink(lg, int(W / 2 - lg.shape[1] / 2), int(H / 2 - 260))
    type_in(cv.img, 'a little archive of names', 'CourierPrime-Italic', 34, W // 2, H // 2 + 200, seed=2)
    type_in(cv.img, 'letters in ceramic', 'CourierPrime', 28, W // 2, H // 2 + 260, seed=4)
    type_in(cv.img, 'save for later', 'CourierPrime', 26, W // 2, H - 220, seed=5)
    return [(cv.img.copy(), 48)]
scenes = [sc_cover(),
          sc_pull(1, 'land'),
          sc_confetti(2, 'confetti', '#f1dfa0'),
          sc_lift(3, 'collage', '#a9bccb'),
          sc_pull(4, 'kraft', '#c8d3bf'),
          sc_stamp(5, 'pattern', '#e7b6a8'),
          sc_end()]
print('scenes ok', flush=True)
# --------------- whip pans
def mblur(img, length, horiz):
    L = max(int(length), 1)
    if L < 3: return img
    k = np.zeros((L, L), np.float32)
    if horiz: k[L // 2, :] = 1 / L
    else: k[:, L // 2] = 1 / L
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)
def whip(A, B, d, n=6):
    """A exits, B enters; d in 'L','R','U','D'. very fast with heavy blur"""
    horiz = d in 'LR'
    strip = np.concatenate([A, B], 1 if horiz else 0)
    if d in 'RD': strip = np.concatenate([B, A], 1 if horiz else 0)
    size = W if horiz else H
    out = []; prev = 0
    for i in range(1, n + 1):
        u = i / n; e = u ** 2 * (3 - 2 * u)
        off = int(size * e) if d in 'LU' else int(size * (1 - e))
        v = abs(off - prev) if i > 1 else size / n; prev = off
        f = strip[:, off:off + W] if horiz else strip[off:off + H]
        out.append(mblur(f, min(v * 1.6, 320), horiz))
    return out
DIRS = ['L', 'U', 'R', 'D', 'L', 'U']
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', '-movflags', '+faststart', '/home/user/Test/carousel/reel_5_boy_names.mp4'],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
fr = np.random.default_rng(5); cnt = [0]
yy, xx = np.mgrid[0:H, 0:W]; VIG = (1 - 0.12 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None].astype(np.float32)
GR = [cv2.GaussianBlur(fr.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.8)[..., None] for _ in range(6)]
def emit(img, steady=False):
    if cnt[0] % 2 == 0:
        emit.j = (0, 0) if steady else fr.normal(0, 1.4, 2); emit.g = 1 + fr.normal(0, 0.02)
    o = cv2.warpAffine(img, np.float32([[1, 0, emit.j[0]], [0, 1, emit.j[1]]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    o = o * emit.g * VIG + GR[cnt[0] % 6] * 0.022          # film grain changes every frame
    proc.stdin.write((np.clip(o, 0, 1) * 255).astype(np.uint8).tobytes()); cnt[0] += 1
emit.j = (0, 0); emit.g = 1
for k, sc in enumerate(scenes):
    for img, hold in sc:
        for _ in range(hold): emit(img)
    if k < len(scenes) - 1:
        if k == 3:     # one hard snap cut for rhythm
            continue
        for f in whip(sc[-1][0], scenes[k + 1][0][0], DIRS[k]): emit(f, steady=True)
proc.stdin.close(); proc.wait(); print(cnt[0] / FPS)
