import sys; sys.path.insert(0,'.')
import numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont
F = lambda n, s: ImageFont.truetype(f'fonts/{n}.ttf', s)
def ring_text(im, text, font, cx, cy, r, start_deg, span_deg, top=True):
    d = ImageDraw.Draw(im); n = len(text)
    widths = [font.getlength(c) for c in text]; total = sum(widths)
    ang = start_deg - span_deg / 2 if top else start_deg + span_deg / 2
    for ch, w in zip(text, widths):
        step = span_deg * w / total
        a = ang + (step / 2 if top else -step / 2)
        g = Image.new('L', (int(w) + 40, font.size + 40), 0); ImageDraw.Draw(g).text((20, 10), ch, font=font, fill=255)
        rot = -(a + 90) if top else -(a - 90)
        g = g.rotate(rot, resample=Image.BICUBIC, expand=True)
        x = cx + r * math.cos(math.radians(a)); y = cy + r * math.sin(math.radians(a))
        im.paste(255, (int(x - g.width / 2), int(y - g.height / 2)), g)
        ang += step if top else -step
def logo_mask(S=4, size=600):
    D = size * S; im = Image.new('L', (D, D), 0); d = ImageDraw.Draw(im); c = D / 2
    for r, wdt in [(0.485, 5), (0.455, 2), (0.30, 2)]:
        R = D * r; d.ellipse([c - R, c - R, c + R, c + R], outline=255, width=wdt * S)
    ring_text(im, 'THE LITTLE ARCHIVE', F('IMFellEnglishSC', 46 * S), c, c, D * 0.378, -90, 196, top=True)
    ring_text(im, 'LETTERS IN CERAMIC', F('CourierPrime', 28 * S), c, c, D * 0.392, 90, 118, top=False)
    for a in (166, 14):   # little dots between the texts
        x = c + D * 0.385 * math.cos(math.radians(a)); y = c + D * 0.385 * math.sin(math.radians(a))
        d.ellipse([x - 6 * S, y - 6 * S, x + 6 * S, y + 6 * S], fill=255)
    # four-petal flower from the pattern paper
    p = 34 * S
    for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
        px, py = c + dx * p * 0.95, c + dy * p * 0.95
        w, h = (p * 0.55, p * 0.9) if dx == 0 else (p * 0.9, p * 0.55)
        d.ellipse([px - w, py - h, px + w, py + h], fill=255)
    f = F('IMFellEnglishSC', 34 * S); t = 'Nº'
    d.text((c - f.getlength(t) / 2, c + D * 0.155), t, font=f, fill=255)
    return np.array(im, np.float32) / 255
def logo_rgba(width, color=(0x2a, 0x22, 0x1e), seed=0):
    m = logo_mask(); rng = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rng.normal(0, 1, m.shape).astype(np.float32), (0, 0), 3)
    m = m * np.clip(0.9 + 0.1 * n / n.std(), 0.6, 1)
    a = cv2.resize(m, (width, width), interpolation=cv2.INTER_AREA)
    return np.dstack([np.ones((width, width, 3), np.float32) * np.array(color, np.float32) / 255, a])
if __name__ == '__main__':
    r = logo_rgba(1000)
    paper = np.ones((1000, 1000, 3), np.float32) * np.array([0.957, 0.925, 0.847])
    out = paper * (1 - r[..., 3:]) + r[..., :3] * r[..., 3:]
    cv2.imwrite('/home/user/Test/brand/logo_rund.png', (out[..., ::-1] * 255).astype(np.uint8))
    cv2.imwrite('/home/user/Test/brand/logo_rund_transparent.png', (np.dstack([r[..., 2::-1], r[..., 3:]]) * 255).astype(np.uint8))
