import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
from bird import *
from logo import logo_rgba
from aged import age, flatplace, type_in, type_para
from sketch import sketch
def stamp_logo(cv, cx, cy, width, rot, seed=0):
    r = rot_rgba4(logo_rgba(width, seed=seed), rot); r[..., 3] *= 0.9
    cv.ink(r, int(cx - r.shape[1] / 2), int(cy - r.shape[0] / 2))

NAMES = [
 ('Alessio', 'Italian', '[aˈlɛssjo]', ['From Greek alexō, meaning', '“to defend or help.”'],
  'Someone whose quiet strength makes others feel safe enough to be themselves.', 9),
 ('August', 'English', '[ˈɔːɡəst]', ['From Latin Augustus, meaning', '“venerable” or “exalted.”'],
  'Someone who sees the good in others and gives it room to grow.', 6),
 ('Amir', 'Arabic', '[ʔaˈmiːr]', ['From Arabic amīr, meaning', '“prince” or “commander.”'],
  'Someone who makes others feel they belong, wherever they come from.', 8),
 ('Atlas', 'English', '[ˈætləs]', ['A name from Greek mythology,', 'possibly meaning “to endure.”'],
  'Someone with the courage to meet the unfamiliar and the tenderness to understand it.', 10),
 ('Arthur', 'British English', '[ˈɑːθə]', ['A name of debated origin, possibly', 'connected with the Celtic word', 'for “bear.”'],
  'Someone who notices what others feel, even when they cannot find the words.', 7),
]
NAMEFONT = ['IMFellEnglishSC', 1.08]
SKETCH = {1: [('train', 150, 1040, 250, -4)], 2: [('compass', 150, 1030, 200, 8)], 3: [('globe', 150, 1030, 200, -6)],
          4: [('compass', 150, 1030, 200, -10)], 5: [('globe', 150, 1030, 200, 6)]}
POST = [('ROMA', '12.IV.26'), ('LONDON', '03.VIII.26'), ('CAIRO', '17.III.26'), ('ATHENS', '21.V.26'), ('LONDON', '09.IX.26')]

def close_bird(i, width, seed=3):
    rgb, a = bird(i, width, mute=0.12)
    pad = 12
    rgb = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0)), constant_values=1); a = np.pad(a, pad)
    m = scissor(a, pad=2, eps=1.5, seed=seed)            # snipped right along the painted edge
    h, w = a.shape
    edge = paper('cream', h, w, '#efe6d2', seed)
    grain = paper('cream', h, w, None, seed + 1).mean(-1, keepdims=True)
    out = edge * (1 - a[..., None]) + rgb * np.clip(grain / grain.mean(), 0.9, 1.08) * a[..., None]
    return np.clip(out, 0, 1), np.maximum(m, a)

def flat(cv, rgb, a, x, y, rot):
    # paper lying flat: tight, faint contact shadow only, like a scan
    r2, a2 = rotate_rgba(rgb, a, rot)
    cv.put(r2, a2, int(x - (a2.shape[1] - rgb.shape[1]) / 2), int(y - (a2.shape[0] - rgb.shape[0]) / 2), shadow=0.22, sdx=1, sdy=2, sblur=1.6)

def name_card(n, name, lang, ipa, origin, meaning, b):
    cv = Canvas(age_bg(n))
    d_rgb, d_a = scaled(1, 700); d_rgb = age(d_rgb, d_a, 10 + n)
    flatplace(cv, d_rgb, d_a, 30, 70, -4 if n % 2 else -2)
    f_rgb, f_a = scaled(2, 690); f_rgb = age(f_rgb, f_a, 20 + n)
    type_in(f_rgb, f'Nº {n} / 5', 'CourierPrime', 30, 470, 110, seed=n)
    size = 96 if len(name) <= 6 else 84
    type_in(f_rgb, name, NAMEFONT[0], int(size * NAMEFONT[1]), 345, 500, seed=2 + n, depth=1.4)
    type_in(f_rgb, f'{lang}: {ipa}', 'Gentium-Italic', 36, 345, 590, seed=3 + n, depth=0.8)
    y = 690
    for i, l in enumerate(origin):
        type_in(f_rgb, l, 'CourierPrime', 25, 345, y, seed=10 + n + i); y += 38
    from comp import lines_wrap
    for i, l in enumerate(lines_wrap(meaning, 'CourierPrime-Italic', 28, 520)):
        type_in(f_rgb, l, 'CourierPrime-Italic', 28, 345, y + 60 + i * 44, seed=40 + n + i)
    flatplace(cv, f_rgb, f_a, 290, 300, 3.5 if n % 2 else 2)
    b_rgb, b_a = close_bird(b, 250 if b != 6 else 150, seed=n)
    b_rgb = age(b_rgb, b_a, 30 + n, 0.5)
    bx, by = (55, 330) if b != 6 else (90, 290)
    flatplace(cv, b_rgb, b_a, bx, by, -6 if n % 2 else 5)
    for s_name, sx, sy, sw, sr in SKETCH.get(n, []): sketch(cv.img, s_name, sx, sy, sw, sr, seed=n)
    stamp_logo(cv, 150, 1225, 230, -6 if n % 2 else 4, seed=n)
    type_in(cv.img, 'swipe >' if n < 5 else 'save for later', 'CourierPrime', 26, 950 if n < 5 else 920, 70, seed=5)
    return finish(cv.img, n)

def age_bg(seed):
    bg = background(); a = np.ones(bg.shape[:2], np.float32)
    a[:6] = a[-6:] = 0; a[:, :6] = a[:, -6:] = 0
    return age(bg, a, 100 + seed, 0.6)

def cover_card():
    cv = Canvas(age_bg(0))
    d_rgb, d_a = scaled(1, 760); flatplace(cv, age(d_rgb, d_a, 1), d_a, 200, 90, 3)
    n_rgb, n_a = scaled(5, 620); n_rgb = age(n_rgb, n_a, 2)
    type_in(n_rgb, '5', 'CourierPrime-Bold', 110, 310, 130, seed=1, depth=1.4)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        type_in(n_rgb, l, 'CourierPrime-Bold', 50, 310, 245 + i * 64, seed=2 + i, depth=1.2)
    type_in(n_rgb, 'a little archive of names', 'CourierPrime-Italic', 24, 310, 660, seed=9)
    flatplace(cv, n_rgb, n_a, 140, 330, -5)
    b_rgb, b_a = close_bird(7, 320, seed=11); flatplace(cv, age(b_rgb, b_a, 3, 0.5), b_a, 700, 820, 8)
    stamp_logo(cv, 900, 150, 270, 6, seed=0)
    type_in(cv.img, 'swipe >', 'CourierPrime', 28, 940, 1295, seed=5)
    return finish(cv.img, 0)

if __name__ == '__main__':
    out = '/home/user/Test/carousel/'
    save(cover_card(), out + '01_omslag.png')
    for i, t in enumerate(NAMES):
        save(name_card(i + 1, *t), out + f'0{i + 2}_{t[0]}.png')
