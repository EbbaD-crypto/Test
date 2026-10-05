"""Stop-motion pop-on version: things simply appear. No slides, no shake, no film flicker. Cut-out travel symbols."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2, subprocess
import build3 as B
from build3 import L, render, save, finish, W
from cutsym import cut_symbol
# (symbol, width, dx, dy, rot) relative to centre; designed to sit on empty corners of the card
SYMS = {
    'sc_cover':   [('balloon', 200, 330, 330, 6), ('globe', 210, -330, -400, -7)],
    'sc_alessio': [('train', 280, -300, -480, -5)],
    'sc_august':  [('suitcase', 250, 250, 300, 6), ('plane', 250, -300, 560, -10)],
    'sc_amir':    [('compass', 220, 250, 330, 8), ('map', 200, -340, 470, -6)],
    'sc_atlas':   [('globe', 230, 260, 340, -6), ('balloon', 170, -360, -420, 5)],
    'sc_arthur':  [('sailboat', 250, 250, 330, 5), ('compass', 170, -360, -440, -8)],
}
cache = {}
import comp
from comp import torn, noise
CREAM, CHEST, RED, BUTTER = '#f4ead2', '#6b4a35', '#7d2a25', '#eedfaa'
def torn_strip(w, h, color, seed):
    rng = np.random.default_rng(seed)
    pad = 24; m = np.zeros((h + 2 * pad, w + 2 * pad), np.float32); m[pad:pad + h, pad:pad + w] = 1
    inner = torn(m, 5, 1.8, seed); outer = torn(cv2.dilate(m, np.ones((6, 6), np.uint8)), 6, 2.2, seed + 3)
    kind = 'kraft' if color in (CHEST, RED) else 'cream'
    t = comp.paper(kind, m.shape[0], m.shape[1], color, seed)
    fib = np.clip(outer - inner, 0, 1)[..., None]
    rgb = t * inner[..., None] + np.clip(t * 0.4 + 0.6, 0, 1) * fib
    return rgb.astype(np.float32), np.clip(inner + fib[..., 0] * 0.85, 0, 1).astype(np.float32)
# (color, w, h, dx, dy, rot) – laid under everything
STRIPS = {
    'sc_cover':   [(CHEST, 420, 120, -330, 560, -4), (RED, 90, 300, 440, -170, 3), (BUTTER, 360, 110, 320, 470, 5)],
    'sc_alessio': [(BUTTER, 760, 150, 40, -470, -2), (RED, 100, 520, -470, 120, 2)],
    'sc_august':  [(CHEST, 880, 160, -120, 560, -2), (BUTTER, 160, 700, 470, 0, 1), (RED, 280, 70, -380, -560, -6)],
    'sc_amir':    [(BUTTER, 330, 900, 400, 120, 2), (CHEST, 680, 120, -220, 590, 3)],
    'sc_atlas':   [(RED, 120, 760, -470, 160, -2), (BUTTER, 700, 130, 120, -590, 3), (CHEST, 260, 90, -380, -570, -5)],
    'sc_arthur':  [(CHEST, 300, 560, 430, -230, 3), (BUTTER, 600, 130, -220, 600, -3), (RED, 90, 330, -470, -420, -4)],
}
def warm(bg):
    c = comp.hexc(CREAM)
    g = bg.mean(-1, keepdims=True)
    bg = bg * 0.82 + g * 0.18                 # soften pinks/greys
    return np.clip(bg * 0.8 + c * g * 0.25, 0, 1).astype(np.float32)
def sym(name, w, seed):
    k = (name, w, seed)
    if k not in cache: cache[k] = cut_symbol(name, w, seed)
    return cache[k]
def scene(fn, H):
    bg, layers, ex = fn(H)
    bg = warm(bg)
    for i, (col, w, h, dx, dy, r) in enumerate(STRIPS.get(fn.__name__, [])[::-1]):
        rgb, a = torn_strip(w, h, col, i * 7 + len(fn.__name__))
        layers.insert(0, L(rgb, a, dx, dy * (1 if H < 1500 else 1.3), r, g=0, frm=(0, 0)))
    g = max(l.g for l in layers) + 1
    for i, (n, w, dx, dy, r) in enumerate(SYMS.get(fn.__name__, [])):
        rgb, a = sym(n, w, i + len(fn.__name__))
        layers.append(L(rgb, a, dx, dy * (1 if H < 1500 else 1.25), r, g=g + i, frm=(0, 0)))
    return bg, layers, ex
def end_scene(H):
    from logo import logo_rgba
    from aged import type_in
    bg = B.scan(B.R + 'rivet_papper_1.jpg', H, 1.0)
    k_rgb, k_a = B.mat('kuvert_rosett.png', 1.3); lg = logo_rgba(560, seed=3)
    p_rgb, p_a = sym('plane', 260, 3)
    def ex(cv, H):
        type_in(cv.img, 'a little archive of names', 'CourierPrime-Italic', 34, W // 2, H // 2 + 560, seed=2)
        type_in(cv.img, 'save for later', 'CourierPrime', 26, W // 2, H - 200, seed=5)
    return bg, [L(lg[..., :3], lg[..., 3], 0, -520, 0, g=0, frm=(0, 0), op=0.92, ink=True),
                L(k_rgb, k_a, 0, 160, 0, g=1, frm=(0, 0)),
                L(p_rgb, p_a, 300, -200, -12, g=2, frm=(0, 0))], ex
FNS = [B.sc_cover, B.sc_alessio, B.sc_august, B.sc_amir, B.sc_atlas, B.sc_arthur]
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if mode in ('all', 'carousel'):
        for i, fn in enumerate(FNS):
            bg, layers, ex = scene(fn, 1350)
            save(finish(render(bg, layers, 99, 0, 1350, ex), i), f'/home/user/Test/carousel/{B.NAMES_OUT[i]}.png'); print('ok', i, flush=True)
    if mode in ('all', 'reel'):
        H, FPS = 1920, 12          # stop motion: 12 fps, every state simply appears
        proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '21', '-preset', 'slow', '-r', '24', '-movflags', '+faststart',
            '/home/user/Test/carousel/reel_5_boy_names.mp4'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        n = 0
        for fn in FNS + [end_scene]:
            bg, layers, ex = scene(fn, H) if fn is not end_scene else end_scene(H)
            G = max(l.g for l in layers)
            for g in range(G + 1):
                img = finish(render(bg, layers, g, 0.0, H, ex), g)   # layer simply appears
                hold = 5 if g < G else (20 if fn is not end_scene else 30)
                b = (np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes()
                for _ in range(hold): proc.stdin.write(b); n += 1
        proc.stdin.close(); proc.wait(); print('reel s', n / FPS)
