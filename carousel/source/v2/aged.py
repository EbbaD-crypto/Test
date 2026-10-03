"""Aged scanned paper, flatbed-flat placement, typewriter type debossed into paper."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
from comp import text_mask, inked, rotate_rgba, noise

def age(rgb, a, seed=0, amount=1.0):
    """yellow + darken toward edges, foxing spots, mottled stains, slightly faded"""
    rng = np.random.default_rng(seed)
    h, w = a.shape
    d = cv2.distanceTransform((a > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    edge = np.exp(-d / 28)[..., None]                       # dirty, toasted edges
    tone = np.array([0.80, 0.68, 0.50], np.float32)          # old-paper brown
    out = rgb * (1 - 0.32 * amount * edge) + rgb * tone * 0.32 * amount * edge
    mott = noise(h, w, 45, rng) * 0.6 + noise(h, w, 12, rng) * 0.4  # uneven yellowing
    out = out * (1 - 0.05 * amount * np.clip(mott, -1, 2)[..., None] * (1 - tone))
    # foxing: small rusty dots and a few faint rings
    fox = np.zeros((h, w), np.float32)
    for _ in range(int(14 * amount * (h * w) / 4e5) + 3):
        x, y = rng.integers(0, w), rng.integers(0, h); r = rng.uniform(1.5, 6)
        cv2.circle(fox, (int(x), int(y)), int(r), float(rng.uniform(0.25, 0.7)), -1)
    for _ in range(2):
        x, y = rng.integers(0, w), rng.integers(0, h); r = int(rng.uniform(40, 110))
        cv2.circle(fox, (int(x), int(y)), r, 0.06, int(rng.uniform(2, 5)))
    fox = cv2.GaussianBlur(fox, (0, 0), 2.2)[..., None]
    out = out * (1 - fox * (1 - np.array([0.62, 0.45, 0.28])))
    # faded, slightly desaturated
    g = out.mean(-1, keepdims=True); out = out * 0.88 + g * 0.12
    return np.clip(out, 0, 1)

def flatplace(cv, rgb, a, x, y, rot):
    """lying flat on a scanner glass: only a hairline contact shadow"""
    r2, a2 = rotate_rgba(rgb, a, rot)
    cv.put(r2, a2, int(x - (a2.shape[1] - rgb.shape[1]) / 2), int(y - (a2.shape[0] - rgb.shape[0]) / 2),
           shadow=0.18, sdx=1, sdy=1, sblur=1.2)

def type_in(rgb, text, font, size, cx, cy, color='#2f2622', seed=0, depth=1.0, ink=0.9, align='c'):
    """typewriter strike: per-letter ink density, slight baseline drift, pressed into the paper"""
    m = text_mask(text, font, size, 0, jitter=0.35, rot_j=0.3, seed=seed, ink_var=0.18)
    ys, xs = np.where(m > 0.05)
    m = np.pad(m, 12)[ys.min() + 4:ys.max() + 20, xs.min() + 4:xs.max() + 20]
    r = inked(m, color, seed, 0.6, 0.22, fade=0.18, wob=0)
    A = r[..., 3]
    h, w = A.shape
    x0 = int(cx - w / 2) if align == 'c' else int(cx); y0 = int(cy - h / 2)
    reg = rgb[y0:y0 + h, x0:x0 + w].copy()
    # deboss: height = -blur(mask); light from top-left
    sm = cv2.GaussianBlur(m, (0, 0), max(1.0, size / 45))
    gx = cv2.Sobel(sm, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(sm, cv2.CV_32F, 0, 1, ksize=3)
    shade = np.clip((gx + gy) * 0.55 * depth, -0.35, 0.35)[..., None]
    reg = reg * (1 - np.clip(shade, 0, None)) + (1 - reg) * np.clip(-shade, 0, None) * 0.6
    # ink sits in the impression, paper texture shows through
    lum = reg.mean(-1, keepdims=True)
    pig = r[..., :3] * np.clip(lum / 0.85, 0.75, 1.05)
    Ai = (A * ink)[..., None]
    rgb[y0:y0 + h, x0:x0 + w] = reg * (1 - Ai) + pig * Ai

def type_para(rgb, text, font, size, cx, top, maxw, lh, **kw):
    from comp import lines_wrap
    for i, l in enumerate(lines_wrap(text, font, size, maxw)):
        type_in(rgb, l, font, size, cx, top + i * lh, seed=kw.pop('seed', 0) + i if False else i + 31, **kw)
