"""Zara Home calm: brushed aluminium table, cream papers, pencil symbol, lots of air."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2, subprocess
import comp
from comp import Canvas, rotate_rgba, save, noise
from aged import type_in
from cutsym import cut_symbol
import simple as S
import build3 as B
W = 1080
def aluminium(H, seed=1):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (H, W)).astype(np.float32)
    streak = cv2.GaussianBlur(n, (0, 0), sigmaX=60, sigmaY=0.6) * 6     # brushed lines
    fine = cv2.GaussianBlur(n, (0, 0), sigmaX=8, sigmaY=0.4) * 1.2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    light = 0.80 + 0.07 * np.exp(-(((xx - W * 0.3) / (W * 0.9)) ** 2 + ((yy - H * 0.2) / (H * 0.9)) ** 2))   # soft window light
    v = light + 0.012 * streak + 0.008 * fine
    return np.clip(np.dstack([v * 0.985, v * 0.99, v]), 0, 1).astype(np.float32)
def finish_cool(img):
    h, w = img.shape[:2]
    g = noise(h, w, 0.7, np.random.default_rng(3)) * 0.008
    return np.clip(cv2.GaussianBlur(img + g[..., None], (0, 0), 0.5), 0, 1)
def put(cv, rgb, a, cx, cy):
    # natural soft shadow, light from upper left
    cv.put(rgb, a, int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2), shadow=0.22, sdx=10, sdy=14, sblur=14)
def items(H, card, sym, k, scale):
    c_rgb, c_a = card
    c_rgb = cv2.resize(c_rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA); c_a = cv2.resize(c_a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    cw, ch = c_a.shape[1], c_a.shape[0]
    c_rgb, c_a = rotate_rgba(c_rgb, c_a, [0, 0.8, -0.6, 0.5, -0.7, 0.6, 0][k])
    y_rgb, y_a = cut_symbol(sym, 170, k, tone='#f7f3ea', wash=0.0)
    g = y_rgb.mean(-1, keepdims=True); y_rgb = y_rgb * 0.4 + g * 0.6           # graphite only
    y_rgb, y_a = rotate_rgba(y_rgb, y_a, [-5, 6, -4, 5, -6, 4, -3][k])
    cy = H / 2 - 20
    return [(c_rgb, c_a, W / 2, cy), (y_rgb, y_a, W / 2 + cw / 2 - 30, cy + ch / 2 - 40)]
def compose(H, base, P, off=None):
    comp.W, comp.H = W, H; cv = Canvas(base.copy())
    for i, (rgb, a, cx, cy) in enumerate(P):
        dx, dy = (off or {}).get(i, (0, 0)); put(cv, rgb, a, cx + dx, cy + dy)
    return cv.img
SC = S.scenes()   # (colour, card, sym, rot) – colour ignored now
if __name__ == '__main__':
    A = aluminium(1350)
    for k, (_, card, sym, _) in enumerate(SC[:6]):
        img = compose(1350, A, items(1350, card, sym, k, 0.86))
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
    for k, (_, card, sym, _) in enumerate(SC):
        P = items(H, card, sym, k, 1.0); last = k == len(SC) - 1
        out(compose(H, A, P[:1]), 6)
        out(compose(H, A, P), 36 if not last else 36)
        if last: break
        out(compose(H, A, P, {0: (460, 90), 1: (520, 100)}), 2)
        out(A, 4)
    proc.stdin.close(); proc.wait(); print('reel s', n[0] / FPS)
