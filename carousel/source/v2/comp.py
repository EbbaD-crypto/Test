"""Collage toolkit: real paper scans, scissor-cut stickers, torn paper, inked type."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from pencil import pencilize, noise, wobble, tooth

D = __import__('os').path.dirname(__file__) or '.'
F = lambda n: f'{D}/fonts/{n}.ttf'
W, H = 1080, 1350

def rd(p):  # read as float RGB(A) 0..1
    im = cv2.imread(f'{D}/{p}', cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4: im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
    else: im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return im.astype(np.float32) / 255

def save(img, p):
    cv2.imwrite(p, cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))

def hexc(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255

PAL = dict(ink='#3a2a24', cocoa='#6e4a36', chestnut='#8c4a34', rose='#e7b6a8', roseDeep='#c98272',
           butter='#f1dfa0', dove='#a9bccb', doveDeep='#7d95a8', cream='#f4ecd8', sage='#a3ae8c', blush='#efc9bf')

# ---------------- textures ----------------
_names = rd('base_names.png'); _d13 = rd('src/d13.png'); _crum = rd('src/crumple.jpg'); _cov = rd('base_cover.png')
TEX = {
    'cream': _names[440:860, 380:960],
    'cream2': _names[1120:1340, 360:1000],
    'pink': _d13[650:800, 330:520],
    'kraft': _crum[0:200, 0:1179],
    'kraft2': _d13[150:290, 330:980],
    'tracing': _cov[500:860, 500:880],
}

def grow(tex, h, w, seed=0):
    """make a larger texture by mirrored tiling with random offsets (keeps real scan grain)"""
    rng = np.random.default_rng(seed)
    th, tw = tex.shape[:2]
    t = np.concatenate([tex, tex[:, ::-1]], 1); t = np.concatenate([t, t[::-1]], 0)
    reps = (h // t.shape[0] + 2, w // t.shape[1] + 2, 1)
    big = np.tile(t, reps)
    oy, ox = rng.integers(0, th), rng.integers(0, tw)
    return big[oy:oy + h, ox:ox + w].copy()

def tint(tex, color, strength=1.0, keep=0.9):
    """recolor a paper scan, keeping its fibres and grain"""
    lum = tex.mean(-1, keepdims=True)
    base = cv2.GaussianBlur(lum, (0, 0), 25)[..., None] if lum.ndim == 2 else cv2.GaussianBlur(lum[..., 0], (0, 0), 25)[..., None]
    detail = lum / np.maximum(base, 1e-3)
    low = cv2.GaussianBlur(lum[..., 0], (0, 0), 60)[..., None] / max(lum.mean(), 1e-3)  # gentle mottling
    out = hexc(color) * (detail ** keep) * (0.92 + 0.08 * low)
    return np.clip(tex * (1 - strength) + out * strength, 0, 1)

def paper(kind, h, w, color=None, seed=0):
    t = grow(TEX[kind], h, w, seed)
    return tint(t, color) if color else t

def stripes(h, w, c1, c2, period=54, seed=0, angle=0):
    """printed stripe paper: uneven ink edges on a real paper scan"""
    t = paper('cream', h, w, None, seed)
    gx = np.arange(w)[None, :].repeat(h, 0).astype(np.float32)
    edge = noise(h, w, 2, np.random.default_rng(seed)) * 0.7 + noise(h, w, 40, np.random.default_rng(seed + 1)) * 1.2
    m = (((gx + edge) % period) < period / 2).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 0.8)
    a = tint(t, c1); b = tint(t, c2)
    ink = np.clip(0.88 + 0.12 * noise(h, w, 1.2, np.random.default_rng(seed + 3)), 0, 1)[..., None]
    return a * (1 - m[..., None]) + b * m[..., None] * ink + a * m[..., None] * (1 - ink)

# ---------------- masks ----------------
def poly_mask(h, w, pts):
    m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.int32(pts)], 255); return m.astype(np.float32) / 255

def torn(mask, amp=7, fine=2.5, seed=0):
    rng = np.random.default_rng(seed)
    m = wobble(mask, amp, 9, rng)
    m = wobble(m, fine, 1.6, rng)
    return np.clip((m - 0.5) * 6 + 0.5, 0, 1)

def scissor(mask, pad=10, eps=2.2, seed=0):
    """sticker outline: dilate then approximate with straight scissor cuts"""
    m8 = (mask > 0.3).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1))
    m8 = cv2.dilate(m8, k)
    m8 = (wobble(m8.astype(np.float32), pad * 0.25, 20, np.random.default_rng(seed)) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(m8)
    for c in cs:
        a = cv2.approxPolyDP(c, eps * pad / 6, True)
        cv2.fillPoly(out, [a], 1)
    return cv2.GaussianBlur(out.astype(np.float32), (0, 0), 0.6)

# ---------------- layer ops ----------------
class Canvas:
    def __init__(self, base): self.img = base.copy()
    def put(self, rgb, alpha, x, y, shadow=0.32, sdx=3, sdy=5, sblur=5, blend='normal'):
        h, w = alpha.shape
        X0, Y0 = max(x, 0), max(y, 0); X1, Y1 = min(x + w, W), min(y + h, H)
        if X1 <= X0 or Y1 <= Y0: return
        sx, sy = X0 - x, Y0 - y
        A = alpha[sy:sy + Y1 - Y0, sx:sx + X1 - X0][..., None]
        C = rgb[sy:sy + Y1 - Y0, sx:sx + X1 - X0]
        if shadow:
            pad = 30
            sm = np.zeros((h + 2 * pad, w + 2 * pad), np.float32); sm[pad:pad + h, pad:pad + w] = alpha
            sm = cv2.GaussianBlur(sm, (0, 0), sblur) * shadow
            self._mul(1 - sm, x - pad + sdx, y - pad + sdy, warm=True)
            sm2 = cv2.GaussianBlur(np.pad(alpha, pad), (0, 0), 1.2) * shadow * 0.6  # tight contact shadow
            self._mul(1 - sm2, x - pad + 1, y - pad + 1, warm=True)
        reg = self.img[Y0:Y1, X0:X1]
        if blend == 'multiply': C = reg * C
        self.img[Y0:Y1, X0:X1] = reg * (1 - A) + C * A
    def _mul(self, m, x, y, warm=False):
        h, w = m.shape
        X0, Y0 = max(x, 0), max(y, 0); X1, Y1 = min(x + w, W), min(y + h, H)
        if X1 <= X0 or Y1 <= Y0: return
        M = m[Y0 - y:Y1 - y, X0 - x:X1 - x][..., None]
        tintc = np.array([0.93, 0.88, 0.84], np.float32) if warm else 1
        self.img[Y0:Y1, X0:X1] *= M + (1 - M) * tintc * 0.0
    def ink(self, rgba, x, y):
        """pigment that sits *in* the paper: multiply-ish so grain shows through"""
        h, w = rgba.shape[:2]
        X0, Y0 = max(x, 0), max(y, 0); X1, Y1 = min(x + w, W), min(y + h, H)
        reg = self.img[Y0:Y1, X0:X1]
        R = rgba[Y0 - y:Y1 - y, X0 - x:X1 - x]
        A = R[..., 3:]
        paper_lum = reg.mean(-1, keepdims=True)
        pig = R[..., :3] * np.clip(paper_lum / 0.86, 0.75, 1.08)
        self.img[Y0:Y1, X0:X1] = reg * (1 - A) + pig * A

def rotate_rgba(rgb, a, deg):
    h, w = a.shape
    d = int(np.hypot(h, w)) + 4
    pad_y, pad_x = (d - h) // 2, (d - w) // 2
    rgb2 = np.zeros((d, d, 3), np.float32); a2 = np.zeros((d, d), np.float32)
    rgb2[pad_y:pad_y + h, pad_x:pad_x + w] = rgb; a2[pad_y:pad_y + h, pad_x:pad_x + w] = a
    M = cv2.getRotationMatrix2D((d / 2, d / 2), deg, 1)
    # premultiply to avoid dark fringes
    pm = cv2.warpAffine(rgb2 * a2[..., None], M, (d, d), flags=cv2.INTER_CUBIC)
    a3 = np.clip(cv2.warpAffine(a2, M, (d, d), flags=cv2.INTER_CUBIC), 0, 1)
    return pm / np.maximum(a3[..., None], 1e-4), a3

def piece(cv, kind, pts, color=None, seed=0, edge='torn', fiber=True, shadow=0.3, alpha_mul=1.0, tex=None, amp=4):
    """a torn / cut paper piece at absolute polygon pts"""
    pts = np.float32(pts); x0, y0 = pts.min(0).astype(int) - 30; x1, y1 = pts.max(0).astype(int) + 30
    h, w = y1 - y0, x1 - x0
    m = poly_mask(h, w, pts - [x0, y0])
    t = tex if tex is not None else paper(kind, h, w, color, seed)
    if edge == 'torn':
        inner = torn(m, amp, 1.8, seed)
        if fiber:
            outer = torn(cv2.dilate(m, np.ones((4, 4), np.uint8)), 5, 1.6, seed + 5)
            fib = np.clip(outer - inner, 0, 1)
            fcol = np.clip(t * 0.55 + 0.42, 0, 1) * (0.92 + 0.08 * noise(h, w, 0.8, np.random.default_rng(seed))[..., None])
            rgb = t * inner[..., None] + fcol * fib[..., None]
            a = np.clip(inner + fib * 0.8, 0, 1)
        else: rgb, a = t, inner
    else:
        a = scissor(m, 2, 1.2, seed) if edge == 'cut' else m
        rgb = t
    cv.put(rgb, a * alpha_mul, int(x0), int(y0), shadow=shadow)

# ---------------- illustrations as stickers ----------------
_ill_cache = {}
def drawing(name, seed=0):
    key = (name, seed)
    if key not in _ill_cache:
        f = rd(f'ill/{name}_fill.png'); l = rd(f'ill/{name}_line.png')
        _ill_cache[key] = pencilize((f * 255).astype(np.uint8), (l * 255).astype(np.uint8), seed=seed)
    return _ill_cache[key]

def sticker(cv, name, cx, cy, width, rot=0, seed=0, border=True, shadow=0.34):
    o = drawing(name, seed)  # 3x resolution
    scale = width / o.shape[1]
    pad = 40
    o = np.pad(o, ((pad, pad), (pad, pad), (0, 0)))
    h, w = o.shape[:2]
    if border:
        sm = scissor(o[..., 3], pad=int(30), eps=3.0, seed=seed)
        sp = paper('cream', h, w, '#f6f1e6', seed + 11)
        sp = sp * (0.97 + 0.03 * noise(h, w, 1, np.random.default_rng(seed))[..., None])
        pig = o[..., :3] * np.clip(sp.mean(-1, keepdims=True) / 0.9, 0.8, 1.05)
        rgb = sp * (1 - o[..., 3:]) + pig * o[..., 3:]
        a = np.maximum(sm, o[..., 3])
    else:
        rgb, a = o[..., :3], o[..., 3]
    nh, nw = int(h * scale), int(w * scale)
    rgb = cv2.resize(rgb * a[..., None], (nw, nh), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA)
    rgb = rgb / np.maximum(a[..., None], 1e-4)
    rgb, a = rotate_rgba(rgb, a, rot)
    if border: cv.put(rgb, a, int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2), shadow=shadow, sdx=2, sdy=4, sblur=4)
    else: cv.ink(np.dstack([rgb, a]), int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2))

def cutout(cv, src, box, cx, cy, scale=1.0, rot=0, thresh=None, shadow=0.3):
    """lift an existing real sticker from a scan using GrabCut"""
    img = (rd(src)[..., :3] * 255).astype(np.uint8)
    x0, y0, x1, y1 = box
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.grabCut(bgr, mask, (x0, y0, x1 - x0, y1 - y0), np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 1, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = (lab == 1 + np.argmax(stats[1:, 4])).astype(np.uint8)
    m = cv2.erode(m, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.7)[y0:y1, x0:x1]
    rgb = img[y0:y1, x0:x1].astype(np.float32) / 255
    if scale != 1:
        nh, nw = int(a.shape[0] * scale), int(a.shape[1] * scale)
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA); a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA)
    rgb, a = rotate_rgba(rgb, a, rot)
    cv.put(rgb, a, int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2), shadow=shadow, sdx=2, sdy=3, sblur=3)

# ---------------- type ----------------
def _font(name, size): return ImageFont.truetype(F(name), size)

def text_mask(text, font, size, spacing=0, jitter=0.0, rot_j=0.0, seed=0, ink_var=0.0):
    """render text char by char with typewriter-like misalignment; returns float alpha"""
    rng = np.random.default_rng(seed)
    f = _font(font, size)
    asc, desc = f.getmetrics()
    wsum = int(sum(f.getlength(c) + spacing for c in text)) + 60
    hh = asc + desc + 40
    canvas = np.zeros((hh, wsum), np.float32)
    x = 20.0
    MAC = {'ō': 'o', 'ī': 'ı', 'ā': 'a', 'ē': 'e', 'ū': 'u'}
    for ch in text:
        base = MAC.get(ch, ch)
        cw = f.getlength(base)
        if ch != ' ':
            g = Image.new('L', (int(cw) + 30, hh), 0)
            gd = ImageDraw.Draw(g); gd.text((15, 20), base, font=f, fill=255)
            if ch in MAC:
                bb = gd.textbbox((15, 20), base, font=f)
                yy = bb[1] - max(2, size // 9); gd.line([(bb[0] + 1, yy), (bb[2] - 1, yy)], fill=255, width=max(2, size // 12))
            ga = np.array(g, np.float32) / 255
            if rot_j:
                M = cv2.getRotationMatrix2D((ga.shape[1] / 2, hh / 2), rng.normal(0, rot_j), 1)
                ga = cv2.warpAffine(ga, M, (ga.shape[1], hh))
            dy = int(round(rng.normal(0, jitter)))
            dens = 1 - abs(rng.normal(0, ink_var)) if ink_var else 1
            gx0 = int(x) - 15
            sl = canvas[max(dy, 0):hh + min(dy, 0), max(gx0, 0):gx0 + ga.shape[1]]
            src = ga[max(-dy, 0):hh - max(dy, 0), max(-gx0, 0):max(-gx0, 0) + sl.shape[1]]
            canvas[max(dy, 0):hh + min(dy, 0), max(gx0, 0):gx0 + ga.shape[1]] = np.maximum(sl, src[:sl.shape[0], :sl.shape[1]] * dens)
        x += cw + spacing
    return canvas

def inked(alpha, color, seed=0, bleed=0.6, grain=0.25, fade=0.0, wob=0.8):
    rng = np.random.default_rng(seed)
    h, w = alpha.shape
    a = cv2.GaussianBlur(alpha, (0, 0), bleed) if bleed else alpha
    if wob: a = wobble(a, wob, 3, rng)
    g = np.clip(1 - grain * np.abs(noise(h, w, 0.8, rng)) - fade * np.clip(noise(h, w, 25, rng), 0, 1), 0, 1)
    a = np.clip(a * 1.15, 0, 1) * g
    return np.dstack([np.broadcast_to(hexc(color), (h, w, 3)), a])

def rot_rgba4(rgba, deg):
    rgb, a = rotate_rgba(rgba[..., :3], rgba[..., 3], deg); return np.dstack([rgb, a])

def write(cv, text, font, size, cx, cy, color=PAL['ink'], rot=0, anchor='c', seed=0, typewriter=False, bleed=0.6, grain=0.25, spacing=0, fade=0.0):
    if typewriter:
        m = text_mask(text, font, size, spacing, jitter=0.9, rot_j=1.2, seed=seed, ink_var=0.22)
    else:
        m = text_mask(text, font, size, spacing, seed=seed)
    ys, xs = np.where(m > 0.05)
    if len(xs) == 0: return
    m = m[max(ys.min() - 10, 0):ys.max() + 10, max(xs.min() - 10, 0):xs.max() + 10]
    r = rot_rgba4(inked(m, color, seed, bleed, grain, fade), rot)
    x = int(cx - r.shape[1] / 2) if anchor == 'c' else int(cx)
    cv.ink(r, x, int(cy - r.shape[0] / 2))

def lines_wrap(text, font, size, maxw):
    f = _font(font, size); out = []; cur = ''
    for wd in text.split():
        t = (cur + ' ' + wd).strip()
        if f.getlength(t) > maxw and cur: out.append(cur); cur = wd
        else: cur = t
    out.append(cur); return out

def paragraph(cv, text, font, size, cx, top, maxw, lh, color=PAL['ink'], rot=0, seed=0, typewriter=False, **kw):
    ls = lines_wrap(text, font, size, maxw)
    rr = np.deg2rad(rot)
    for i, l in enumerate(ls):
        dy = i * lh
        write(cv, l, font, size, cx - np.sin(rr) * dy, top + np.cos(rr) * dy, color, rot, seed=seed + i, typewriter=typewriter, **kw)
    return top + len(ls) * lh

# ---------------- cut-paper letters ----------------
def cut_word(cv, word, font, size, cx, base_y, papers, seed=0, track=-4, rot_amp=4, shadow=0.38):
    rng = np.random.default_rng(seed)
    f = _font(font, size)
    widths = [f.getlength(c) for c in word]
    total = sum(widths) + track * (len(word) - 1)
    x = cx - total / 2
    for i, ch in enumerate(word):
        g = Image.new('L', (int(widths[i]) + 80, int(size * 1.5)), 0)
        ImageDraw.Draw(g).text((40, 20), ch, font=f, fill=255)
        ga = np.array(g, np.float32) / 255
        m = scissor(ga, pad=3, eps=1.6, seed=seed + i)
        h, w = m.shape
        kind, color = papers[i % len(papers)]
        if kind == 'stripes': t = stripes(h, w, color[0], color[1], 26, seed + i)
        else: t = paper(kind, h, w, color, seed + i * 7)
        rgb, a = rotate_rgba(t, m, rng.normal(0, rot_amp))
        dy = rng.normal(0, size * 0.02)
        cv.put(rgb, a, int(x - 40 - (a.shape[1] - w) / 2), int(base_y - size * 0.95 - 20 + dy - (a.shape[0] - h) / 2), shadow=shadow, sdx=3, sdy=5, sblur=4)
        x += widths[i] + track

def tape(cv, cx, cy, w, h, rot, color='#efe3c0', seed=0, alpha=0.62):
    """masking/washi tape with torn short ends"""
    t = paper('cream2', h + 20, w + 20, color, seed)
    m = np.zeros((h + 20, w + 20), np.float32); m[10:10 + h, 10:10 + w] = 1
    rng = np.random.default_rng(seed)
    # zig-zag torn ends
    for side in (10, 10 + w):
        for yy in range(10, 10 + h):
            d = int(abs(rng.normal(0, 2.5)) + 2 * np.sin(yy * 0.9))
            if side == 10: m[yy, 10:10 + d] = 0
            else: m[yy, side - d:side] = 0
    m = cv2.GaussianBlur(m, (0, 0), 0.6)
    rgb, a = rotate_rgba(t, m * alpha, rot)
    cv.put(rgb, a, int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2), shadow=0.08, sdx=1, sdy=1, sblur=2)

# ---------------- finishing ----------------
def finish(img, seed=0):
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    g = noise(h, w, 0.7, rng) * 0.012 + noise(h, w, 2, rng) * 0.008
    img = img + g[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - 0.07 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    img = img * v[..., None]
    # slight warm, faded scan response
    img = img * np.array([1.0, 0.985, 0.955]) + np.array([0.012, 0.01, 0.005])
    img = np.clip(img, 0, 1) ** 1.03
    # mild optical softness of a flatbed scan
    soft = cv2.GaussianBlur(img, (0, 0), 0.55)
    return np.clip(soft, 0, 1)

def stamp(cv, cx, cy, w, h, ill, ink, label, value, rot=0, seed=0):
    """perforated postage stamp, single-ink print of an illustration"""
    rng = np.random.default_rng(seed)
    S = 3; W3, H3 = w * S, h * S; P = 14 * S
    m = np.zeros((H3 + 2 * P, W3 + 2 * P), np.float32); m[P:P + H3, P:P + W3] = 1
    r = int(5.5 * S); step = 15 * S
    for x in range(P, P + W3 + 1, step):
        cv2.circle(m, (x, P), r, 0, -1); cv2.circle(m, (x, P + H3), r, 0, -1)
    for y in range(P, P + H3 + 1, step):
        cv2.circle(m, (P, y), r, 0, -1); cv2.circle(m, (P + W3, y), r, 0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    hh, ww = m.shape
    pp = paper('cream', hh, ww, '#f3ecdb', seed)
    inkc = hexc(ink)
    # printed frame + flat tint plate
    plate = np.zeros((hh, ww), np.float32)
    fx0, fy0, fx1, fy1 = P + 10 * S, P + 10 * S, P + W3 - 10 * S, P + H3 - 28 * S
    cv2.rectangle(plate, (fx0, fy0), (fx1, fy1), 0.42, -1)
    cv2.rectangle(plate, (fx0, fy0), (fx1, fy1), 1, 2 * S)
    cv2.rectangle(plate, (fx0 - 4 * S, fy0 - 4 * S), (fx1 + 4 * S, P + H3 - 8 * S), 1, S)
    # illustration line work printed in the same ink
    l = rd(f'ill/{ill}_line.png')[..., 3]; f_ = rd(f'ill/{ill}_fill.png')
    lum = 1 - f_[..., :3].mean(-1)
    ia = np.maximum(l, f_[..., 3] * (0.25 + 0.5 * lum))
    bw, bh = fx1 - fx0 - 12 * S, fy1 - fy0 - 12 * S
    sc = min(bw / ia.shape[1], bh / ia.shape[0])
    ia = cv2.resize(ia, (int(ia.shape[1] * sc), int(ia.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    oy = fy0 + (fy1 - fy0 - ia.shape[0]) // 2; ox = fx0 + (fx1 - fx0 - ia.shape[1]) // 2
    plate[oy:oy + ia.shape[0], ox:ox + ia.shape[1]] = np.maximum(plate[oy:oy + ia.shape[0], ox:ox + ia.shape[1]], ia)
    # lettering
    pil = Image.new('L', (ww, hh), 0); d = ImageDraw.Draw(pil)
    fnt = _font('IMFellEnglishSC', 13 * S); d.text((fx0, P + H3 - 25 * S), label, font=fnt, fill=255)
    fv = _font('IMFellEnglish', 20 * S); d.text((fx1 - fv.getlength(value), P + H3 - 30 * S), value, font=fv, fill=255)
    plate = np.maximum(plate, np.array(pil, np.float32) / 255)
    plate = plate * np.clip(0.8 + 0.25 * noise(hh, ww, 1.0, rng), 0, 1)  # uneven ink on paper
    plate = wobble(plate, 1.0, 6, rng)
    k = np.clip(plate * 1.1, 0, 1)[..., None]
    rgb = pp * (1 - k) + (inkc ** 1.25 * pp) * k
    rgb = cv2.resize(rgb, (ww // S, hh // S), interpolation=cv2.INTER_AREA); a = cv2.resize(m, (ww // S, hh // S), interpolation=cv2.INTER_AREA)
    rgb, a = rotate_rgba(rgb, a, rot)
    cv.put(rgb, a, int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2), shadow=0.3, sdx=2, sdy=3, sblur=3)

def postmark(cv, cx, cy, city, date, rot=0, color='#3b3330', seed=0, r=62):
    rng = np.random.default_rng(seed)
    S = 3; size = (r * 2 + 260) * S
    pil = Image.new('L', (size, r * 2 * S + 40 * S), 0); d = ImageDraw.Draw(pil)
    c = (r * S + 20 * S, r * S + 20 * S)
    d.ellipse([c[0] - r * S, c[1] - r * S, c[0] + r * S, c[1] + r * S], outline=255, width=3 * S)
    d.ellipse([c[0] - (r - 22) * S, c[1] - (r - 22) * S, c[0] + (r - 22) * S, c[1] + (r - 22) * S], outline=255, width=2 * S)
    f = _font('IMFellEnglishSC', 15 * S)
    d.text((c[0] - f.getlength(city) / 2, c[1] - 28 * S), city, font=f, fill=255)
    fd = _font('SpecialElite', 15 * S)
    d.text((c[0] - fd.getlength(date) / 2, c[1] + 0 * S), date, font=fd, fill=255)
    for i in range(5):
        y0 = c[1] - 34 * S + i * 17 * S
        pts = [(c[0] + (r + 8) * S + t * S, y0 + 6 * S * np.sin(t / 14)) for t in range(0, 230, 3)]
        d.line(pts, fill=255, width=3 * S)
    a = np.array(pil, np.float32) / 255
    h, w = a.shape
    a = a * np.clip(0.78 + 0.35 * noise(h, w, 2.0, rng) + 0.25 * noise(h, w, 30, rng), 0, 1)   # patchy ink
    a = cv2.resize(a, (w // S, h // S), interpolation=cv2.INTER_AREA) * 0.85
    r4 = rot_rgba4(np.dstack([np.broadcast_to(hexc(color), a.shape + (3,)), a]), rot)
    cv.ink(r4, int(cx - r4.shape[1] / 2), int(cy - r4.shape[0] / 2))
