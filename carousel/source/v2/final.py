import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
from bird import *

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
    cv = Canvas(background())
    d_rgb, d_a = scaled(1, 700); place(cv, d_rgb, d_a, 30, 70, -4 if n % 2 else -2)
    f_rgb, f_a = scaled(2, 690)
    ink_local(f_rgb, f'Nº {n} / 5', 'CourierPrime', 32, 470, 110, INK, n, bleed=0.25, grain=0.04)
    size = 132 if len(name) <= 6 else 118
    ink_local(f_rgb, name, 'LibreCaslonText', size, 345, 415, INK, 2 + n, bleed=0.3, grain=0.04, op=1)
    ink_local(f_rgb, f'{lang}:  {ipa}', 'Gentium-Italic', 42, 345, 535, INK, 3 + n, bleed=0.25, grain=0.03, op=1)
    y = 635
    for i, l in enumerate(origin):
        ink_local(f_rgb, l, 'CourierPrime', 27, 345, y, INK, 10 + n + i, bleed=0.25, grain=0.04, op=1); y += 40
    para_local(f_rgb, meaning, 'LibreCaslonText-Italic', 32, 345, y + 90, 560, 50, '#43342c', 20 + n, bleed=0.25, grain=0.03, op=1)
    place(cv, f_rgb, f_a, 290, 300, 3.5 if n % 2 else 2)
    b_rgb, b_a = close_bird(b, 250 if b != 6 else 150, seed=n)
    bx, by = (55, 330) if b != 6 else (90, 290)
    flat(cv, b_rgb, b_a, bx, by, -6 if n % 2 else 5)
    postmark(cv, 190, 1210, *POST[n - 1], rot=-12, color='#4b3f3a', seed=7 + n)
    if n < 5: write(cv, 'swipe  »', 'LibreCaslonText-Italic', 28, 960, 70, INK, rot=0, seed=5, grain=0.04)
    else: write(cv, 'save for later', 'LibreCaslonText-Italic', 28, 930, 70, INK, rot=0, seed=5, grain=0.04)
    return finish(cv.img, n)

def cover_card():
    cv = Canvas(background())
    d_rgb, d_a = scaled(1, 760); place(cv, d_rgb, d_a, 200, 90, 3)
    n_rgb, n_a = scaled(5, 620)
    ink_local(n_rgb, '5', 'LibreCaslonText', 120, 310, 130, INK, 1, bleed=0.3, grain=0.04, op=1)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        ink_local(n_rgb, l, 'LibreCaslonText-Italic', 52, 310, 245 + i * 68, INK, 2 + i, bleed=0.25, grain=0.03, op=1)
    ink_local(n_rgb, 'a little archive of names', 'CourierPrime', 24, 310, 660, INK, 9, bleed=0.25, grain=0.04)
    place(cv, n_rgb, n_a, 140, 330, -5)
    b_rgb, b_a = close_bird(7, 320, seed=11); flat(cv, b_rgb, b_a, 700, 820, 8)
    postmark(cv, 860, 160, 'PARIS', '2026', rot=10, color='#4b3f3a', seed=3)
    write(cv, 'swipe  »', 'LibreCaslonText-Italic', 30, 930, 1295, INK, rot=0, seed=5, grain=0.04)
    return finish(cv.img, 0)

if __name__ == '__main__':
    out = '/home/user/Test/carousel/'
    save(cover_card(), out + '01_omslag.png')
    for i, t in enumerate(NAMES):
        save(name_card(i + 1, *t), out + f'0{i + 2}_{t[0]}.png')
