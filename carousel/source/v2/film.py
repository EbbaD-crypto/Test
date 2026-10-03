"""Reel as one continuous film: camera glides over an archive desk from scene to scene."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
from archive import *
from comp import Canvas, rotate_rgba, noise
from logo import logo_rgba
W, H, FPS = 1080, 1920, 24
SW, SH = 1080, 1350
NS = 7
XS = [0, 520, 60, 560, 20, 500, 260]
POS = [(XS[k], 320 + k * 1450) for k in range(NS)]
DW, DH = 1700, POS[-1][1] + SH + 400
# --- desk: mirrored tiles of the old album paper, toned down
bg = background()
from comp import paper
desk = paper('cream', DH, DW, '#b9a184', 21).astype(np.float32)
desk *= (0.95 + 0.05 * noise(DH, DW, 200, np.random.default_rng(2)))[..., None]
D0 = desk.copy(); D = desk.copy()
def el(cv, rgb, a, cx, cy, rot=0, lift=0.0, scale=1.0):
    if scale != 1:
        rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA); a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    r2, a2 = rotate_rgba(rgb, a, rot)
    cv.put(r2, a2, int(cx - a2.shape[1] / 2), int(cy - a2.shape[0] / 2),
           shadow=0.18 + 0.22 * lift, sdx=int(1 + 16 * lift), sdy=int(1 + 24 * lift), sblur=1.2 + 12 * lift)
def scene_base(k): x, y = POS[k]; return D0[y:y + SH, x:x + SW].copy()
def commit(k, img): x, y = POS[k]; D[y:y + SH, x:x + SW] = img
DIV = scaled(1, 760); NOTE = scaled(5, 620); FOLD = None
def aged(asset, seed): rgb, a = asset; return age(rgb.copy(), a, seed), a
# ---------------- scenes: each returns list of (image, hold_frames)
def s_cover():
    cv = Canvas(scene_base(0))
    el(cv, *aged(DIV, 1), 560, 600, 3)
    n_rgb, n_a = aged(NOTE, 2)
    type_in(n_rgb, '5', 'IMFellEnglishSC', 120, 310, 130, seed=1, depth=1.2)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        type_in(n_rgb, l, 'IMFellEnglishSC', 54, 310, 245 + i * 64, seed=2 + i, depth=1.1)
    type_in(n_rgb, 'a little archive of names', 'CourierPrime-Italic', 24, 310, 660, seed=9)
    el(cv, n_rgb, n_a, 470, 720, -5)
    sketch(cv.img, 'globe', 880, 1120, 220, 6, seed=3)
    stamp_logo(cv, 900, 150, 260, 6, seed=0)
    return [(cv.img, 30)]
def s_pull(k, n, t, color=None):
    """card pulled out of the folder in tugs"""
    card = make_card(n, *t[:5], color=color); front = decorate_front(make_front(n), n)
    out = []
    for p, w in zip([0, 40, 95, 120, 190, 250, 265, 330, 380], [0, 0.6, -0.4, 0.3, -0.5, 0.4, 0, -0.2, 0]):
        cv = Canvas(scene_base(k))
        el(cv, *aged(DIV, 10 + n), 400, 520, -4)
        rgb, a = folder_unit(front, card, p, n)
        el(cv, rgb, a, 560, 760, 2 + w)
        out.append((cv.img, 2 if p else 10))
    return out
def s_lift(k, n, t, color):
    """kraft divider lying on the card is lifted and put aside"""
    card = make_card(n, *t[:5], color=color)
    d_rgb, d_a = aged(DIV, 30 + n)
    out = []
    for p in [0, 0, 0.08, 0.2, 0.36, 0.55, 0.72, 0.86, 0.95, 1.0]:
        cv = Canvas(scene_base(k))
        sketch(cv.img, 'compass', 170, 1180, 190, -8, seed=n)
        el(cv, card, CARD_A, 520, 660, -2)
        lift = np.sin(np.pi * min(p, 1)) * 0.9
        el(cv, d_rgb, d_a, 500 + 560 * p, 640 - 380 * p, 4 + 24 * p, lift=lift, scale=1 + 0.04 * lift)
        out.append((cv.img, 2 if 0 < p < 1 else 10))
    return out
def s_slide(k, n, t, color):
    """grey notebook lying on the card is pushed aside"""
    card = make_card(n, *t[:5], color=color)
    nb_rgb, nb_a = aged(NOTE, 40 + n)
    out = []
    for p in [0, 0, 0.1, 0.24, 0.42, 0.6, 0.76, 0.9, 1.0]:
        cv = Canvas(scene_base(k))
        el(cv, card, CARD_A, 560, 650, 1.5)
        el(cv, nb_rgb, nb_a, 560 - 520 * p, 640 + 330 * p, -3 - 10 * p, lift=0.12 * np.sin(np.pi * p))
        stamp_logo(cv, 880, 1230, 230, 4, seed=n)
        out.append((cv.img, 2 if 0 < p < 1 else 10))
    return out
def s_turn(k, n, t, color):
    """a page lying on the card is lifted at its right edge and turned over to the left"""
    card = make_card(n, *t[:5], color=color)
    pg = bg[40:1250, 80:960].astype(np.float32)
    pg = cv2.resize(pg, (640, 880)); pa = np.ones(pg.shape[:2], np.float32)
    pa[:, :3] = 0; pa[:, -3:] = 0; pa[:3] = 0; pa[-3:] = 0
    pg = age(pg, pa, 60 + n, 1.0)
    type_in(pg, 'Nº 5', 'CourierPrime', 34, 320, 120, seed=n)
    sketch(pg, 'train', 320, 520, 300, -3, seed=n)
    back = age(np.ones_like(pg) * np.array([0.86, 0.80, 0.68], np.float32), pa, 70 + n, 1.0)
    out = []
    left = 220
    for th in [0, 0, 0.12, 0.3, 0.5, 0.7, 0.86, 1.0]:
        cv = Canvas(scene_base(k))
        el(cv, card, CARD_A, 540, 660, -1.5)
        c = np.cos(np.pi * th); lift = np.sin(np.pi * th)
        src = pg if c > 0 else back[:, ::-1]
        w = max(int(640 * abs(c)), 4)
        im = cv2.resize(src, (w, 880)); am = cv2.resize(pa, (w, 880))
        im = im * (1 - 0.25 * lift)
        x = left if c > 0 else left - w
        cv.put(im, am, x, 660 - 440 - int(20 * lift), shadow=0.18 + 0.25 * lift, sdx=int(1 + 20 * lift), sdy=int(1 + 18 * lift), sblur=1.2 + 10 * lift)
        out.append((cv.img, 2 if 0 < th < 1 else 10))
    return out
def s_end(k):
    cv = Canvas(scene_base(k))
    pg = bg[40:1250, 80:960].astype(np.float32); pg = cv2.resize(pg, (700, 900))
    pa = np.ones(pg.shape[:2], np.float32); pa[:3] = pa[-3:] = 0; pa[:, :3] = pa[:, -3:] = 0
    pg = age(pg, pa, 91, 1.0)
    from comp import rot_rgba4
    r = logo_rgba(520, seed=4); A = r[..., 3:] * 0.9; y0, x0 = 200, 90
    reg = pg[y0:y0 + A.shape[0], x0:x0 + A.shape[1]]; pg[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = reg * (1 - A) + r[..., :3] * reg ** 0.3 * A
    type_in(pg, 'a little archive of names', 'CourierPrime-Italic', 30, 350, 600, seed=2)
    type_in(pg, 'save for later', 'CourierPrime', 26, 350, 780, seed=3)
    el(cv, pg, pa, 540, 680, 1.5)
    return [(cv.img, 40)]
N = NAMES
scenes = [s_cover(),
          s_pull(1, 1, N[0]),
          s_lift(2, 2, N[1], '#f1dfa0'),
          s_slide(3, 3, N[2], '#e7b6a8'),
          s_pull(4, 4, N[3], '#c8d3bf'),
          s_turn(5, 5, N[4], '#a9bccb'),
          s_end(6)]
print('scenes rendered', flush=True)
for k, sc in enumerate(scenes): commit(k, sc[0][0])
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', '/home/user/Test/carousel/reel_5_boy_names.mp4'],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
yy, xx = np.mgrid[0:H, 0:W]; VIG = (1 - 0.10 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None].astype(np.float32)
fr = np.random.default_rng(11); count = [0]
def cam(k): x, y = POS[k]; return x + SW / 2, y + SH / 2
def crop(cx, cy):
    x0 = int(round(cx - W / 2)); y0 = int(round(cy - H / 2))
    x0 = min(max(x0, 0), DW - W); y0 = min(max(y0, 0), DH - H)
    return D[y0:y0 + H, x0:x0 + W]
def write(img, jit=True):
    if count[0] % 2 == 0: write.j = fr.normal(0, 1.2, 2) if jit else (0, 0); write.g = 1 + fr.normal(0, 0.015)
    out = cv2.warpAffine(img, np.float32([[1, 0, write.j[0]], [0, 1, write.j[1]]]), (W, H), borderMode=cv2.BORDER_REFLECT) * write.g * VIG
    proc.stdin.write((np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes()); count[0] += 1
write.j = (0, 0); write.g = 1
for k, sc in enumerate(scenes):
    cx, cy = cam(k)
    for img, hold in sc:
        commit(k, img)
        f = crop(cx, cy).copy()
        for _ in range(hold): write(f)
    for _ in range(int(FPS * (1.3 if 0 < k < NS - 1 else 0.6))): write(f)
    if k < NS - 1:   # camera dolly to next scene, smooth with a little motion blur
        nx, ny = cam(k + 1); nf = int(FPS * 1.1)
        for i in range(1, nf + 1):
            acc = 0
            for sub in (-0.3, -0.15, 0, 0.15, 0.3):
                u = min(max((i + sub) / nf, 0), 1); e = u * u * (3 - 2 * u)
                px = cx + (nx - cx) * e + 60 * np.sin(np.pi * e) * (1 if k % 2 else -1)
                acc = acc + crop(px, cy + (ny - cy) * e)
            write(acc / 5, jit=False)
proc.stdin.close(); proc.wait(); print(count[0] / FPS)
