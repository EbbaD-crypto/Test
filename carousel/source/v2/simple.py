"""Simple & captivating: torn colour sheet + big plain name card + one cut-out symbol."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2, subprocess
import comp
from comp import Canvas, rotate_rgba, paper, noise, lines_wrap, save, finish
from aged import type_in, age
from cutsym import cut_symbol
from build4 import torn_strip
from archive import NAMES
from logo import logo_rgba
import build3 as B
W = 1080
CREAM, CHEST, RED, BUTTER, DOVE, ROSE = '#f4ead2', '#6b4a35', '#7d2a25', '#eedfaa', '#a9bccb', '#e2b4a6'
def desk(H): return B.scan('src/crumple.jpg', H, 0.3) * np.array([0.80, 0.72, 0.60], np.float32)
def card_base(w, h, tone, seed):
    c = paper('cream', h, w, tone, 80 + seed).astype(np.float32)
    a = np.ones((h, w), np.float32); a[:2] = a[-2:] = 0; a[:, :2] = a[:, -2:] = 0
    return age(c, a, 90 + seed, 0.55), a
def name_card(n, t, tone):
    name, lang, ipa, origin, meaning = t[:5]
    w, h = 780, 1000; c, a = card_base(w, h, tone, n); cx = w // 2
    type_in(c, f'Nº {n} / 5', 'CourierPrime', 30, w - 120, 64, seed=n)
    type_in(c, name, 'IMFellEnglishSC', 150 if len(name) <= 6 else 132, cx, 270, seed=2 + n, depth=1.2)
    type_in(c, f'{lang}  {ipa}', 'Gentium-Italic', 46, cx, 385, seed=3 + n)
    c[450:452, cx - 60:cx + 60] *= 0.6
    y = 520
    for i, l in enumerate(lines_wrap(' '.join(origin), 'CourierPrime', 30, 640)):
        type_in(c, l, 'CourierPrime', 30, cx, y, seed=10 + n + i); y += 46
    y += 40
    for i, l in enumerate(lines_wrap(meaning, 'CourierPrime-Italic', 33, 640)):
        type_in(c, l, 'CourierPrime-Italic', 33, cx, y + i * 52, seed=40 + n + i)
    return c, a
def cover_card():
    w, h = 780, 1000; c, a = card_base(w, h, '#f6f0e2', 0); cx = w // 2
    type_in(c, '5', 'IMFellEnglishSC', 200, cx, 230, seed=1, depth=1.2)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        type_in(c, l, 'IMFellEnglishSC', 86, cx, 420 + i * 105, seed=2 + i)
    type_in(c, 'a little archive of names', 'CourierPrime-Italic', 32, cx, 820, seed=9)
    return c, a
def end_card():
    w, h = 780, 1000; c, a = card_base(w, h, '#f6f0e2', 9); cx = w // 2
    lg = logo_rgba(560, seed=3); A = lg[..., 3:] * 0.92; y0, x0 = 260, (w - 560) // 2
    reg = c[y0:y0 + A.shape[0], x0:x0 + A.shape[1]]; c[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = reg * (1 - A) + lg[..., :3] * reg ** 0.3 * A
    type_in(c, 'a little archive of names', 'CourierPrime-Italic', 34, cx, 680, seed=2)
    type_in(c, 'letters in ceramic', 'CourierPrime', 30, cx, 740, seed=4)
    return c, a
# scene = (sheet colour, card, symbol, symbol rot)
def scenes():
    out = [(CHEST, cover_card(), 'balloon', -6)]
    cfg = [(BUTTER, '#f6f0e2', 'train'), (RED, '#efe5d0', 'suitcase'), (DOVE, '#f6f0e2', 'compass'),
           (CHEST, '#efe5d0', 'globe'), (ROSE, '#f6f0e2', 'sailboat')]
    for i, (sc, tone, sym) in enumerate(cfg):
        out.append((sc, name_card(i + 1, NAMES[i], tone), sym, [5, -6, 7, -5, 6][i]))
    out.append((BUTTER, end_card(), 'plane', -8))
    return out
def items(H, sc_col, card, sym, srot, k):
    """returns ordered list of (rgb, a, cx, cy) pieces, as they are laid down"""
    sh_rgb, sh_a = torn_strip(900, 1180 if H < 1500 else 1560, sc_col, 11 + k)
    sh_rgb, sh_a = rotate_rgba(sh_rgb, sh_a, [-2, 1.5, -1, 2, -1.5, 1, -2][k])
    c_rgb, c_a = card
    s = 1.0 if H < 1500 else 1.12
    if s != 1: c_rgb = cv2.resize(c_rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA); c_a = cv2.resize(c_a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    c_rgb, c_a = rotate_rgba(c_rgb, c_a, [1, -1.2, 0.8, -0.6, 1.1, -0.9, 0.5][k])
    y_rgb, y_a = cut_symbol(sym, 250, k)
    y_rgb, y_a = rotate_rgba(y_rgb, y_a, srot)
    cy = (1350 if H < 1500 else H) / 2
    return [(sh_rgb, sh_a, W / 2, cy), (c_rgb, c_a, W / 2, cy), (y_rgb, y_a, W / 2 + 330, cy + c_a.shape[0] / 2 - 90)]
def compose(H, base, pieces, offsets=None):
    comp.W, comp.H = W, H
    cv = Canvas(base.copy())
    for i, (rgb, a, cx, cy) in enumerate(pieces):
        dx, dy = (offsets or {}).get(i, (0, 0))
        cv.put(rgb, a, int(cx + dx - a.shape[1] / 2), int(cy + dy - a.shape[0] / 2), shadow=0.2, sdx=2, sdy=3, sblur=2)
    return cv.img
if __name__ == '__main__':
    SC = scenes()
    # carousel
    D = desk(1350)
    for k, sc in enumerate(SC[:6]):
        img = compose(1350, D, items(1350, *sc, k))
        type_in(img, 'swipe >' if k < 5 else 'save for later', 'CourierPrime', 26, 140, 1318, seed=k)
        save(finish(img, k), f'/home/user/Test/carousel/{B.NAMES_OUT[k]}.png')
    print('carousel ok', flush=True)
    # reel: lay down (pop on), hold, clear away off-frame in jerky steps
    H, FPS = 1920, 12; D = desk(H)
    proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '21', '-preset', 'slow', '-r', '24', '-movflags', '+faststart',
        '/home/user/Test/carousel/reel_5_boy_names.mp4'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = [0]
    def out(img, hold):
        b = (np.clip(finish(img, n[0] % 7), 0, 1) * 255).astype(np.uint8).tobytes()
        for _ in range(hold): proc.stdin.write(b); n[0] += 1
    out(D, 4)
    for k, sc in enumerate(SC):
        P = items(H, *sc, k); last = k == len(SC) - 1
        for i in range(1, 4): out(compose(H, D, P[:i]), 3 if i < 3 else (36 if k else 30))
        if last: break
        # clear: symbol + card leave together (towards right / down), then the sheet (towards left)
        out(compose(H, D, P, {1: (380, 140), 2: (520, 160)}), 2)
        out(compose(H, D, P[:1]), 2)
        out(compose(H, D, P[:1], {0: (-560, -120)}), 2)
        out(D, 2)
    proc.stdin.close(); proc.wait(); print('reel s', n[0] / FPS)
