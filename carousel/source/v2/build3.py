"""The Little Archive – carousel + reel built from licensed materials. Centred, Wes-style scenes."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
import comp
from archive import make_card, CARD_A, NAMES
from aged import type_in, age
from comp import Canvas, rotate_rgba, save, finish
from logo import logo_rgba
from comp import rot_rgba4
R = '/home/user/Test/brand/referenser/'; M = R + 'material/'
W = 1080
def scan(path, H, x0f=0.5, flip=False):
    im = cv2.imread(path)[..., ::-1].astype(np.float32) / 255
    if flip: im = im[:, ::-1]
    h, w = im.shape[:2]; tw = int(h * W / H)
    if tw <= w: x0 = int((w - tw) * x0f); im = im[:, x0:x0 + tw]
    else: th = int(w * H / W); y0 = (h - th) // 2; im = im[y0:y0 + th]
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
def mat(name, s=1.0):
    im = cv2.imread(M + name, cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    rgb = im[..., 2::-1].copy(); a = im[..., 3].copy() if im.shape[2] == 4 else np.ones(im.shape[:2], np.float32)
    if s != 1:
        rgb = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC); a = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        rgb = np.clip(rgb + 0.35 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.2)), 0, 1)   # gentle re-sharpen
    return rgb, np.clip(a, 0, 1)
class L:  # layer
    def __init__(s, rgb, a, dx, dy, rot=0, g=0, frm=(0, -1500), op=1.0, ink=False):
        s.rgb, s.a, s.dx, s.dy, s.rot, s.g, s.frm, s.op, s.ink = rgb, a, dx, dy, rot, g, frm, op, ink
def render(bg, layers, step, d, H, extra=None):
    comp.W, comp.H = W, H
    cv = Canvas(bg.copy())
    cx, cy = W / 2, H / 2
    for l in layers:
        if l.g > step: continue
        dd = d if l.g == step else 0.0
        x = cx + l.dx + l.frm[0] * dd; y = cy + l.dy + l.frm[1] * dd
        rgb, a = (rotate_rgba(l.rgb, l.a, l.rot + 6 * dd) if (l.rot or dd) else (l.rgb, l.a))
        if l.ink:
            r4 = np.dstack([rgb, a * l.op]); cv.ink(r4, int(x - a.shape[1] / 2), int(y - a.shape[0] / 2))
        else:
            lift = 0.5 * dd
            cv.put(rgb, a * l.op, int(round(x - a.shape[1] / 2)), int(round(y - a.shape[0] / 2)),
                   shadow=0.16 + 0.22 * lift, sdx=int(1 + 12 * lift), sdy=int(1 + 18 * lift), sblur=1.2 + 9 * lift)
    if extra: extra(cv, H)
    return cv.img
def card(n, color, s=1.0):
    c = make_card(n, *NAMES[n - 1][:5], color=color); a = CARD_A.copy()
    if s != 1: c = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_AREA); a = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return c, a
CH = ['One', 'Two', 'Three', 'Four', 'Five']
def chapter(n):
    def f(cv, H):
        type_in(cv.img, f'Chapter {CH[n - 1]}', 'IMFellEnglishSC', 40, W // 2, 95 if H < 1500 else 250, seed=n)
        type_in(cv.img, 'swipe >' if n < 5 else 'save for later', 'CourierPrime', 24, W - 130, H - 60 if H < 1500 else H - 230, seed=n + 1)
    return f
# ---------------- scenes
def sc_cover(H):
    bg = scan(R + 'monster_blomkors.jpg', H)
    b_rgb, b_a = mat('brevbunt_lacksigill.png', 1.45)
    t = make_card(0, '', '', '', [], '', color='#f4ecd8') if False else None
    tc = age(cv2.resize(comp.paper('cream', 300, 640, '#f3ead6', 4), (640, 300)), np.ones((300, 640), np.float32), 3, 0.6)
    ta = np.ones((300, 640), np.float32); ta[:2] = ta[-2:] = 0; ta[:, :2] = ta[:, -2:] = 0
    type_in(tc, '5 Boy Names', 'IMFellEnglishSC', 64, 320, 95, seed=1)
    type_in(tc, 'for Little Globetrotters', 'IMFellEnglishSC', 40, 320, 170, seed=2)
    type_in(tc, 'a little archive of names', 'CourierPrime-Italic', 24, 320, 238, seed=3)
    tp_rgb, tp_a = mat('tejp_kraft_2.png', 0.38)
    lg = logo_rgba(260, seed=0)
    layers = [L(b_rgb, b_a, 0, 150, 0, g=0, frm=(0, 1400)),
              L(tc, ta, 0, -330, 0, g=1, frm=(0, -1200)),
              L(tp_rgb, tp_a, -330, -470, -40, g=2, frm=(-500, -300)),
              L(tp_rgb[:, ::-1].copy(), tp_a[:, ::-1].copy(), 330, -470, 40, g=2, frm=(500, -300)),
              L(lg[..., :3], lg[..., 3], 0, 520 if H < 1500 else 640, 0, g=3, frm=(0, 0), op=0.9, ink=True)]
    def ex(cv, H): type_in(cv.img, 'swipe >', 'CourierPrime', 24, W - 130, H - 60 if H < 1500 else H - 230, seed=9)
    return bg, layers, ex
def sc_alessio(H):
    n = 1; bg = scan(R + 'rivet_papper_2.jpg', H)
    s = 1.75; e_rgb, e_a = mat('kuvert_kraft_no_name.png', s)
    # fill in the envelope form
    type_in(e_rgb, '1', 'CourierPrime', 30, int(118 * s), int(343 * s), seed=1)
    type_in(e_rgb, 'Little Globetrotter', 'CourierPrime', 24, int(410 * s), int(343 * s), seed=2)
    type_in(e_rgb, 'ALESSIO', 'CourierPrime-Bold', 34, int(255 * s), int(378 * s), seed=3)
    type_in(e_rgb, 'Italian', 'CourierPrime', 26, int(150 * s), int(410 * s), seed=4)
    cut = int(214 * s)
    f_a = e_a.copy(); f_a[:cut] = 0
    c_rgb, c_a = card(n, 'white-lines', 1.0)
    ey = 200 if H < 1500 else 300
    layers = [L(e_rgb, e_a, 0, ey, 0, g=0, frm=(0, 1500)),
              L(c_rgb, c_a, 0, ey - 220, 0, g=1, frm=(0, 640)),
              L(e_rgb, f_a, 0, ey, 0, g=0, frm=(0, 1500))]
    return bg, layers, chapter(n)
def sc_august(H):
    n = 2; bg = scan(R + 'rivet_papper_3_konfetti.jpg', H)
    c_rgb, c_a = card(n, 'beige', 1.12)
    t_rgb, t_a = mat('tejp_kraft_1.png', 0.42)
    sp_rgb, sp_a = mat('spets.png', 1.0); sp_rgb = np.concatenate([sp_rgb, sp_rgb], 1); sp_a = np.concatenate([sp_a, sp_a], 1)
    sp_rgb, sp_a = sp_rgb[220:], sp_a[220:]
    layers = [L(c_rgb, c_a, 0, -20, 0, g=0, frm=(0, -1500)),
              L(t_rgb, t_a, -350, -500, -42, g=1, frm=(-400, -400)),
              L(t_rgb[:, ::-1].copy(), t_a[:, ::-1].copy(), 335, 380, -42, g=1, frm=(400, 400))]
    return bg, layers, chapter(n)
def sc_amir(H):
    n = 3; bg = scan(R + 'rivet_papper_1.jpg', H, 0.15)
    c_rgb, c_a = card(n, 'white-grid', 1.12)
    ts_rgb, ts_a = mat('silkespapper_vit_3.png', 1.35)
    st_rgb, st_a = mat('frimarke_rott.png', 0.42)
    type_in(st_rgb, 'A', 'IMFellEnglishSC', 120, st_rgb.shape[1] // 2, st_rgb.shape[0] // 2 + 6, color='#f4ecd8', seed=3)
    layers = [L(c_rgb, c_a, 0, -40, 0, g=0, frm=(0, 1500)),
              L(ts_rgb, ts_a, -170, 380, -8, g=1, frm=(-900, 300), op=0.72),
              L(st_rgb, st_a, -320, -480, -7, g=2, frm=(-500, -500))]
    return bg, layers, chapter(n)
def sc_atlas(H):
    n = 4; bg = scan('src/crumple.jpg', H)
    k_rgb, k_a = mat('rivet_kvitto.png', 1.3)
    c_rgb, c_a = card(n, 'beige-lines', 1.12)
    x_rgb, x_a = mat('tejp_kryss_vit.png', 0.42)
    layers = [L(k_rgb, k_a, 170, 330, 8, g=0, frm=(1200, 200)),
              L(c_rgb, c_a, -20, -40, 0, g=1, frm=(0, -1500)),
              L(x_rgb, x_a, 0, -470, 0, g=2, frm=(0, -500), op=0.9)]
    return bg, layers, chapter(n)
def sc_arthur(H):
    n = 5; bg = scan(R + 'rivet_papper_1.jpg', H, 1.0)
    b_rgb, b_a = mat('linjerat_block_kraft.png', 1.45)
    c_rgb, c_a = card(n, 'white', 1.1)
    t_rgb, t_a = mat('tejp_brun.png', 0.42)
    layers = [L(b_rgb, b_a, -60, 60, -7, g=0, frm=(-1200, 0)),
              L(c_rgb, c_a, 20, -30, 0, g=1, frm=(0, 1500)),
              L(t_rgb, t_a, -320, -470, 45, g=2, frm=(-500, -500))]
    return bg, layers, chapter(n)
SCENES = [sc_cover, sc_alessio, sc_august, sc_amir, sc_atlas, sc_arthur]
NAMES_OUT = ['01_omslag', '02_Alessio', '03_August', '04_Amir', '05_Atlas', '06_Arthur']
def frames_of(scene, H):
    bg, layers, ex = scene(H)
    G = max(l.g for l in layers); out = []
    for g in range(G + 1):
        for d in [1.0, 0.45, 0.12, 0.0]:
            out.append((render(bg, layers, g, d, H, ex), 2 if d else (6 if g < G else 34)))
    return out
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if mode in ('all', 'reel'):
        H = 1920; FPS = 24
        def end_scene(H):
            bg = scan(R + 'rivet_papper_1.jpg', H, 1.0)
            k_rgb, k_a = mat('kuvert_rosett.png', 1.3)
            lg = logo_rgba(560, seed=3)
            def ex(cv, H):
                type_in(cv.img, 'a little archive of names', 'CourierPrime-Italic', 34, W // 2, H // 2 + 560, seed=2)
                type_in(cv.img, 'save for later', 'CourierPrime', 26, W // 2, H - 200, seed=5)
            return bg, [L(lg[..., :3], lg[..., 3], 0, -520, 0, g=0, frm=(0, 0), op=0.92, ink=True),
                        L(k_rgb, k_a, 0, 160, 0, g=1, frm=(0, 1500))], ex
        seqs = [frames_of(sc, H) for sc in SCENES + [end_scene]]
        print('reel scenes ok', flush=True)
        def mblur(img, length, horiz):
            Lk = max(int(length), 1)
            if Lk < 3: return img
            k = np.zeros((Lk, Lk), np.float32)
            if horiz: k[Lk // 2, :] = 1 / Lk
            else: k[:, Lk // 2] = 1 / Lk
            return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)
        def whip(A, B, d, n=6):
            horiz = d in 'LR'; strip = np.concatenate([A, B] if d in 'LU' else [B, A], 1 if horiz else 0)
            size = W if horiz else H; out = []; prev = None
            for i in range(1, n + 1):
                u = i / n; e = u * u * (3 - 2 * u)
                off = int(size * e) if d in 'LU' else int(size * (1 - e))
                v = size / n if prev is None else abs(off - prev); prev = off
                f = strip[:, off:off + W] if horiz else strip[off:off + H]
                out.append(mblur(f, min(v * 1.6, 320), horiz))
            return out
        DIRS = ['L', 'U', 'R', 'D', 'L', 'U']
        proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '22', '-preset', 'slow', '-movflags', '+faststart', '/home/user/Test/carousel/reel_5_boy_names.mp4'],
            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        fr = np.random.default_rng(5); cnt = [0]
        yy, xx = np.mgrid[0:H, 0:W]; VIG = (1 - 0.12 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None].astype(np.float32)
        GR = [cv2.GaussianBlur(fr.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.8)[..., None] for _ in range(6)]
        st = {'j': (0, 0), 'g': 1}
        def emit(img, steady=False):
            if cnt[0] % 2 == 0: st['j'] = (0, 0) if steady else fr.normal(0, 1.4, 2); st['g'] = 1 + fr.normal(0, 0.02)
            o = cv2.warpAffine(img, np.float32([[1, 0, st['j'][0]], [0, 1, st['j'][1]]]), (W, H), borderMode=cv2.BORDER_REFLECT)
            o = o * st['g'] * VIG + GR[cnt[0] % 6] * 0.022
            proc.stdin.write((np.clip(o, 0, 1) * 255).astype(np.uint8).tobytes()); cnt[0] += 1
        for k, sq in enumerate(seqs):
            for img, hold in sq:
                for _ in range(hold): emit(img)
            if k < len(seqs) - 1 and k != 3:
                for f in whip(sq[-1][0], seqs[k + 1][0][0], DIRS[k]): emit(f, steady=True)
        proc.stdin.close(); proc.wait(); print('reel', cnt[0] / FPS)
    if mode in ('all', 'carousel'):
        for i, sc in enumerate(SCENES):
            bg, layers, ex = sc(1350)
            img = render(bg, layers, 99, 0, 1350, ex)
            save(finish(img, i), f'/home/user/Test/carousel/{NAMES_OUT[i]}.png'); print('ok', NAMES_OUT[i], flush=True)
