"""Cards made from the user's own scanned papers; symbols step into frame in stop motion."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2, subprocess
import comp
from comp import Canvas, rotate_rgba, save, lines_wrap
from aged import type_in
from cutsym import cut_symbol
from archive import NAMES
from logo import logo_rgba
import build3 as B
from alu import aluminium, finish_cool, put
W = 1080
def real_paper(name, width, flip=False):
    rgb, a = B.mat(name, 1.0)
    if flip: rgb, a = rgb[:, ::-1].copy(), a[:, ::-1].copy()
    s = width / rgb.shape[1]
    rgb = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4); a = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
    rgb = np.clip(rgb + 0.4 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.5)), 0, 1)
    return rgb.astype(np.float32), np.clip(a, 0, 1).astype(np.float32)
INK = '#2e2a28'
def name_card(n, t, mat, flip):
    name, lang, ipa, origin, meaning = t[:5]
    c, a = real_paper(mat, 760, flip); w = c.shape[1]; cx = w // 2
    type_in(c, f'Nº {n} / 5', 'CourierPrime', 24, w - 110, 52, color=INK, seed=n)
    type_in(c, name, 'IMFellEnglishSC', 112 if len(name) <= 6 else 98, cx, 170, color=INK, seed=2 + n, depth=1.2)
    type_in(c, f'{lang}  {ipa}', 'Gentium-Italic', 36, cx, 255, color=INK, seed=3 + n)
    y = 330
    for i, l in enumerate(lines_wrap(' '.join(origin), 'CourierPrime', 24, 600)):
        type_in(c, l, 'CourierPrime', 24, cx, y, color=INK, seed=10 + n + i); y += 36
    y += 24
    for i, l in enumerate(lines_wrap(meaning, 'CourierPrime-Italic', 26, 600)):
        type_in(c, l, 'CourierPrime-Italic', 26, cx, y + i * 40, color=INK, seed=40 + n + i)
    return c, a
def cover():
    c, a = real_paper('pergament_skrynkligt.png', 760); cx = c.shape[1] // 2
    type_in(c, '5 Boy Names', 'IMFellEnglishSC', 92, cx, 150, color=INK, seed=1)
    type_in(c, 'for Little Globetrotters', 'IMFellEnglishSC', 54, cx, 250, color=INK, seed=2)
    type_in(c, 'a little archive of names', 'CourierPrime-Italic', 28, cx, 380, color=INK, seed=3)
    return c, a
def endc():
    c, a = real_paper('papper_veck.png', 760); w = c.shape[1]
    lg = logo_rgba(460, seed=3); A = lg[..., 3:] * 0.9; y0, x0 = 120, (w - 460) // 2
    reg = c[y0:y0 + A.shape[0], x0:x0 + A.shape[1]]; c[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = reg * (1 - A) + lg[..., :3] * reg ** 0.3 * A
    type_in(c, 'a little archive of names', 'CourierPrime-Italic', 30, w // 2, 470, color=INK, seed=2)
    return c, a
CFG = [('papper_veck.png', False, 'train'), ('rutpapper_hal.png', False, 'suitcase'), ('pergament_skrynkligt.png', True, 'compass'),
       ('skrynkligt_kraft.png', False, 'globe'), ('papper_veck.png', True, 'sailboat')]
SC = [(cover(), 'balloon')] + [(name_card(i + 1, NAMES[i], m, f), s) for i, (m, f, s) in enumerate(CFG)] + [(endc(), 'plane')]
ROT = [0, 1.0, -0.8, 0.7, -0.9, 0.8, 0]
def pieces(H, k):
    (c, a), sym = SC[k]
    cw, ch = a.shape[1], a.shape[0]
    c2, a2 = rotate_rgba(c, a, ROT[k])
    y, ya = cut_symbol(sym, 170, k, tone='#f7f3ea', wash=0.0)
    g = y.mean(-1, keepdims=True); y = y * 0.4 + g * 0.6
    y, ya = rotate_rgba(y, ya, [-5, 6, -4, 5, -6, 4, -3][k])
    cy = H / 2 - 30
    return [(c2, a2, W / 2, cy), (y, ya, W / 2 + cw / 2 - 40, cy + ch / 2 + 30)]
def compose(H, base, P, off=None, upto=None):
    comp.W, comp.H = W, H; cv = Canvas(base.copy())
    for i, (rgb, a, cx, cy) in enumerate(P[:upto]):
        dx, dy = (off or {}).get(i, (0, 0)); put(cv, rgb, a, cx + dx, cy + dy)
    return cv.img
if __name__ == '__main__':
    A = aluminium(1350)
    for k in range(6):
        img = compose(1350, A, pieces(1350, k))
        type_in(img, 'swipe >' if k < 5 else 'save for later', 'CourierPrime', 24, W // 2, 1300, color='#55585c', seed=k)
        save(finish_cool(img), f'/home/user/Test/carousel/{B.NAMES_OUT[k]}.png')
    print('carousel ok', flush=True)
    H, FPS = 1920, 12; A = aluminium(H)
    proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'slow', '-r', '24', '-movflags', '+faststart',
        '/home/user/Test/carousel/reel_5_boy_names.mp4'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = [0]
    def out(img, hold):
        b = (finish_cool(img) * 255).astype(np.uint8).tobytes()
        for _ in range(hold): proc.stdin.write(b); n[0] += 1
    out(A, 6)
    for k in range(len(SC)):
        P = pieces(H, k); last = k == len(SC) - 1
        out(compose(H, A, P, upto=1), 8)                       # card is simply there
        for dx, dy, r in [(620, 90, 0), (380, 50, 0), (170, 20, 0), (40, 4, 0)]:   # symbol steps in from the right
            out(compose(H, A, P, {1: (dx, dy)}), 2)
        out(compose(H, A, P), 34)
        if last: break
        for dx in (300, 760):                                   # everything steps out to the right
            out(compose(H, A, P, {0: (dx, 40), 1: (dx + 60, 50)}), 2)
        out(A, 3)
    proc.stdin.close(); proc.wait(); print('reel s', n[0] / FPS)
