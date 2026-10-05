"""Pen sketch + soft watercolour wash on a scrap of cream paper, cut out with scissors (same look as v4 symbols).
Reads ill/<name>_line.png + ill/<name>_fill.png (from symbols.js), writes sym/<name>.png (RGBA)."""
import os, sys, numpy as np, cv2
D = os.path.dirname(os.path.abspath(__file__))

def rd(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    return cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255

def noise(h, w, sigma, rng):
    n = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), sigma)
    return (n - n.mean()) / (n.std() + 1e-6)

def wobble(img, amp, scale, rng):
    h, w = img.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(img, gx + amp * noise(h, w, scale, rng), gy + amp * noise(h, w, scale, rng), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

PAPER = cv2.cvtColor(cv2.imread(f'{D}/../v4/paper.png'), cv2.COLOR_BGR2RGB).astype(np.float32) / 255

def scrap(h, w, rng):
    y, x = rng.integers(0, PAPER.shape[0] - h), rng.integers(0, PAPER.shape[1] - w)
    p = PAPER[y:y + h, x:x + w]
    detail = p.mean(-1, keepdims=True) / p.mean()
    return np.clip(np.array([0.955, 0.925, 0.87], np.float32) * detail ** 1.6, 0, 1)

def scissor(mask, pad, rng):
    m8 = (mask > 0.2).astype(np.uint8)
    m8 = cv2.dilate(m8, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1)))
    m8 = (wobble(m8.astype(np.float32), pad * 0.35, 24, rng) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(m8)
    for c in cs: cv2.fillPoly(out, [cv2.approxPolyDP(c, pad * 0.55, True)], 1)
    return cv2.GaussianBlur(out.astype(np.float32), (0, 0), 0.7)

def make(name, width, seed):
    rng = np.random.default_rng(seed)
    l = rd(f'{D}/ill/{name}_line.png')[..., 3]; f = rd(f'{D}/ill/{name}_fill.png')
    s = width / l.shape[1]; sz = (int(width), int(round(l.shape[0] * s)))
    l = cv2.resize(l, sz, interpolation=cv2.INTER_AREA); f = cv2.resize(f, sz, interpolation=cv2.INTER_AREA)
    pad = int(width * 0.09); l = np.pad(l, pad); f = np.pad(f, ((pad, pad), (pad, pad), (0, 0)))
    h, w = l.shape
    img = scrap(h, w, rng)
    # watercolour: muted, soft-edged, blotchy, pooled pigment at the rim, a little off-register
    fa = cv2.GaussianBlur(wobble(f[..., 3], 3, 16, rng), (0, 0), 1.8)
    fa = fa * 0.85                                                # even wash, no blotches
    rim = np.clip(fa - cv2.GaussianBlur(fa, (0, 0), 5), 0, 1) * 1.6
    fc = cv2.GaussianBlur(f[..., :3], (0, 0), 2)
    fc = fc * 0.62 + fc.mean(-1, keepdims=True) * 0.38           # desaturate
    fc = fc * 0.75 + np.array([0.95, 0.92, 0.86]) * 0.25          # milky, pastel
    sh = (int(rng.integers(2, 5)), int(rng.integers(-4, -1)))
    fc, fa, rim = np.roll(fc, sh, (0, 1)), np.roll(fa, sh, (0, 1)), np.roll(rim, sh, (0, 1))
    A = np.clip(fa * 0.8 + rim * 0.25, 0, 1)[..., None]
    img = img * (1 - A) + img * fc / 0.93 * A
    # pen: two loose passes, broken here and there, uneven pressure
    l1 = wobble(l, 1.1, 7, rng); l2 = wobble(np.roll(l, (1, 2), (0, 1)), 1.8, 5, rng) * 0.5
    la = np.clip(np.maximum(l1, l2) * 1.5, 0, 1)
    la *= (noise(h, w, 3.5, rng) > -0.75) * np.clip(0.72 + 0.3 * noise(h, w, 1.2, rng), 0.35, 1)
    la = cv2.GaussianBlur(la, (0, 0), 0.5)[..., None]
    img = img * (1 - la * 0.88) + np.array([0.22, 0.18, 0.16]) * la * 0.88
    # cut out; slightly toasted grey edge like a scanned scrap
    m = scissor(np.maximum(l, f[..., 3]), int(pad * 0.55), rng)
    d = cv2.distanceTransform((m > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    e = np.exp(-d / 2.2)[..., None] * 0.28 + np.exp(-d / 14)[..., None] * 0.06
    img = img * (1 - e) + img * np.array([0.62, 0.6, 0.58]) * e
    ys, xs = np.where(m > 0.05)
    out = np.dstack([np.clip(img, 0, 1), m])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    os.makedirs(f'{D}/sym', exist_ok=True)
    cv2.imwrite(f'{D}/sym/{name}.png', cv2.cvtColor((out * 255).astype(np.uint8), cv2.COLOR_RGBA2BGRA))

if __name__ == '__main__':
    names = sys.argv[1:] or sorted({f.rsplit('_', 1)[0] for f in os.listdir(f'{D}/ill')})
    for i, n in enumerate(names): make(n, 380, 11 + i)
    print('symbols cut:', len(names))
