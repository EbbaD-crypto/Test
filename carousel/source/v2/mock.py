import sys; sys.path.insert(0, '.')
import cv2, numpy as np
from comp import *
IMG = '../../images'

def cutout_asset(i):
    im = cv2.imread(f'{IMG}/{i}.jpg'); h, w = im.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for s in [(0,0),(w-1,0),(0,h-1),(w-1,h-1),(w//2,0),(w//2,h-1),(0,h//2),(w-1,h//2)]:
        if im[s[1], s[0]].min() > 235:
            cv2.floodFill(im.copy(), mask, s, 0, (14,)*3, (14,)*3, cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8) | 8)
    bg = (mask[1:-1, 1:-1] > 0) | (im.min(-1) > 247)
    a = cv2.GaussianBlur(cv2.erode((~bg).astype(np.uint8) * 255, np.ones((3,3), np.uint8)), (0,0), 0.8).astype(np.float32) / 255
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255, a

def scaled(i, width):
    rgb, a = cutout_asset(i); s = width / rgb.shape[1]
    sz = (int(width), int(rgb.shape[0] * s))
    return cv2.resize(rgb, sz, interpolation=cv2.INTER_AREA), cv2.resize(a, sz, interpolation=cv2.INTER_AREA)

def ink_local(rgb, text, font, size, cx, cy, color, seed=0, typewriter=False, bleed=0.5, grain=0.25, op=0.92):
    m = text_mask(text, font, size, 0, *( (0.8, 1.0) if typewriter else (0, 0) ), seed=seed, ink_var=0.2 if typewriter else 0)
    ys, xs = np.where(m > 0.05); m = np.pad(m, 10)[ys.min()+4:ys.max()+16, xs.min()+4:xs.max()+16]
    r = inked(m, color, seed, bleed, grain, wob=0); A = r[..., 3:] * op
    h, w = A.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    reg = rgb[y0:y0+h, x0:x0+w]
    pig = r[..., :3] * np.clip(reg.mean(-1, keepdims=True) / 0.85, 0.7, 1.05)
    rgb[y0:y0+h, x0:x0+w] = reg * (1 - A) + pig * A

def para_local(rgb, text, font, size, cx, top, maxw, lh, color, seed=0, **kw):
    for i, l in enumerate(lines_wrap(text, font, size, maxw)):
        ink_local(rgb, l, font, size, cx, top + i * lh, color, seed + i, **kw)

def place(cv, rgb, a, x, y, rot, shadow=0.35):
    r2, a2 = rotate_rgba(rgb, a, rot)
    cv.put(r2, a2, int(x - (a2.shape[1] - rgb.shape[1]) / 2), int(y - (a2.shape[0] - rgb.shape[0]) / 2), shadow=shadow, sdx=4, sdy=8, sblur=10)

def background():
    p = rd('../../images/3.jpg')[60:1180, 420:1840]
    p = np.rot90(p).copy()
    p = cv2.resize(p, (1080, int(p.shape[0] * 1080 / p.shape[1])), interpolation=cv2.INTER_AREA)
    return p[:1350].copy()

INK, BR, PEN = '#3a2c25', '#5a4334', '#4a4744'

def atlas():
    cv = Canvas(background())
    d_rgb, d_a = scaled(1, 700); place(cv, d_rgb, d_a, 30, 70, -4)
    f_rgb, f_a = scaled(2, 690)
    ink_local(f_rgb, 'Nº 4 / 5', 'SpecialElite', 30, 470, 110, BR, 1, typewriter=True)
    ink_local(f_rgb, 'Atlas', 'IMFellEnglish', 150, 345, 420, INK, 2, bleed=0.6, grain=0.2)
    ink_local(f_rgb, 'English:  [ˈætləs]', 'Gentium-Italic', 36, 345, 540, BR, 3, bleed=0.4, grain=0.15)
    f_rgb[598:600, 305:385] = f_rgb[598:600, 305:385] * 0.75
    ink_local(f_rgb, 'A name from Greek mythology,', 'SpecialElite', 24, 345, 650, BR, 4, typewriter=True)
    ink_local(f_rgb, 'possibly meaning “to endure.”', 'SpecialElite', 24, 345, 686, BR, 5, typewriter=True)
    para_local(f_rgb, 'Someone with the courage to meet the unfamiliar and the tenderness to understand it.',
               'HomemadeApple', 25, 345, 790, 520, 56, PEN, 6, bleed=0.4, grain=0.45, op=0.8)
    place(cv, f_rgb, f_a, 290, 300, 3.5)
    postmark(cv, 190, 1160, 'ATHENS', '21.V.26', rot=-12, color='#4b3f3a', seed=7)
    save(finish(cv.img, 4), 'v3/mock_atlas.png')

def cover():
    cv = Canvas(background())
    d_rgb, d_a = scaled(1, 760); place(cv, d_rgb, d_a, 200, 90, 3)
    n_rgb, n_a = scaled(5, 600)
    ink_local(n_rgb, '5', 'IMFellEnglish', 120, 300, 120, INK, 1, bleed=0.6, grain=0.2)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        ink_local(n_rgb, l, 'IMFellEnglish-Italic', 56, 300, 225 + i * 64, INK, 2 + i, bleed=0.55, grain=0.2)
    ink_local(n_rgb, 'a little archive of names', 'SpecialElite', 22, 300, 640, BR, 9, typewriter=True)
    place(cv, n_rgb, n_a, 150, 330, -5)
    postmark(cv, 880, 1190, 'PARIS', '2026', rot=10, color='#4b3f3a', seed=3)
    write(cv, 'swipe  →', 'HomemadeApple', 24, 900, 1290, PEN, rot=-3, seed=5, grain=0.4)
    save(finish(cv.img, 0), 'v3/mock_cover.png')

if __name__ == "__main__": cover(); atlas()
