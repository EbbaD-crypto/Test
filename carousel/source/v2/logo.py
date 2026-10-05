import sys; sys.path.insert(0,'.')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
F = lambda n, s: ImageFont.truetype(f'fonts/{n}.ttf', s)
def logo_mask(S=4):
    W, H = 520 * S, 300 * S
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6*S, 6*S, W-6*S, H-6*S], radius=14*S, outline=255, width=3*S)
    d.rounded_rectangle([16*S, 16*S, W-16*S, H-16*S], radius=9*S, outline=255, width=1*S)
    def c(t, f, y):
        d.text(((W - d.textlength(t, font=f)) / 2, y), t, font=f, fill=255)
    c('THE', F('LibreCaslonText', 26*S), 38*S)
    big = F('LibreCaslonText', 66*S)
    c('Little', F('LibreCaslonText-Italic', 66*S), 68*S)
    c('ARCHIVE', F('LibreCaslonText', 50*S), 152*S)
    d.line([(150*S, 226*S), (370*S, 226*S)], fill=255, width=1*S)
    c('LETTERS IN CERAMIC  ·  Nº', F('CourierPrime', 17*S), 238*S)
    return np.array(im, np.float32) / 255
def logo_rgba(width, color=(0x3a, 0x2c, 0x25), seed=0):
    m = logo_mask(); rng = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rng.normal(0, 1, m.shape).astype(np.float32), (0, 0), 3)
    m = m * np.clip(0.88 + 0.12 * n / n.std(), 0.6, 1)  # light stamp ink, still crisp
    h = int(m.shape[0] * width / m.shape[1])
    a = cv2.resize(m, (width, h), interpolation=cv2.INTER_AREA)
    rgb = np.ones((h, width, 3), np.float32) * np.array(color, np.float32) / 255
    return np.dstack([rgb, a])
if __name__ == '__main__':
    r = logo_rgba(1040)
    paper = np.ones(r.shape[:2] + (3,), np.float32) * np.array([0.957, 0.925, 0.847])
    out = paper * (1 - r[..., 3:]) + r[..., :3] * r[..., 3:]
    cv2.imwrite('/home/user/Test/brand/logo_the_little_archive.png', (out[..., ::-1] * 255).astype(np.uint8))
    t = np.dstack([r[..., :3], r[..., 3:]]); cv2.imwrite('/home/user/Test/brand/logo_the_little_archive_transparent.png', (np.dstack([t[..., 2::-1], t[..., 3:]]) * 255).astype(np.uint8))
