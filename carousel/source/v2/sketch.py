import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
from comp import rd, wobble, noise, rotate_rgba
def sketch(img, name, cx, cy, width, rot=0, seed=0, wash=0.5, ink=(0.24, 0.19, 0.16)):
    """pen-and-ink + light watercolour wash drawn straight onto the paper"""
    rng = np.random.default_rng(seed)
    l = rd(f'ill/{name}_line.png')[..., 3]; f = rd(f'ill/{name}_fill.png')
    s = width / l.shape[1]; sz = (int(width), int(l.shape[0] * s))
    l = cv2.resize(l, sz, interpolation=cv2.INTER_AREA); f = cv2.resize(f, sz, interpolation=cv2.INTER_AREA)
    pad = 20; l = np.pad(l, pad); f = np.pad(f, ((pad, pad), (pad, pad), (0, 0)))
    h, w = l.shape
    # two slightly offset pen passes, uneven pressure
    l1 = wobble(l, 1.2, 8, rng); l2 = wobble(l, 1.8, 6, rng) * 0.45
    la = np.clip(np.maximum(l1, l2) * 1.4, 0, 1) * np.clip(0.75 + 0.35 * noise(h, w, 1.5, rng), 0.3, 1)
    # watercolour wash: soft, offset from the lines, blotchy, doesn't fill perfectly
    fa = wobble(f[..., 3], 4, 18, rng)
    fa = cv2.GaussianBlur(fa, (0, 0), 1.5) * np.clip(0.6 + 0.5 * noise(h, w, 10, rng), 0, 1) * wash
    fc = f[..., :3]; fc = fc * 0.75 + fc.mean(-1, keepdims=True) * 0.25
    fc = np.roll(fc, (3, -2), (0, 1)); fa = np.roll(fa, (3, -2), (0, 1))
    if rot:
        fc, fa = rotate_rgba(fc, fa, rot); _, la = rotate_rgba(np.zeros_like(fc[:la.shape[0], :la.shape[1]]) if False else np.zeros(l.shape + (3,), np.float32), la, rot)
        h, w = la.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    H, W = img.shape[:2]
    sx, sy = max(0, -x0), max(0, -y0); ex, ey = min(w, W - x0), min(h, H - y0)
    fc, fa, la = fc[sy:ey, sx:ex], fa[sy:ey, sx:ex], la[sy:ey, sx:ex]
    x0, y0 = x0 + sx, y0 + sy; h, w = la.shape
    reg = img[y0:y0 + h, x0:x0 + w]
    reg = reg * (1 - fa[..., None]) + reg * fc * fa[..., None] / np.maximum(reg.mean(-1, keepdims=True), 0.5) * 0.9 + 0 * reg
    reg = reg * (1 - la[..., None]) + np.array(ink, np.float32) * reg ** 0.3 * la[..., None]
    img[y0:y0 + h, x0:x0 + w] = np.clip(reg, 0, 1)
