"""Back to the collages: user's papers + cut-out symbols + plain cards. Toned down, darker & larger card text."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
import aged, archive
from archive import CARD_A, lines_wrap
INK = '#1d1815'
# darker, cleaner typewriter ink for everything typed from now on
_orig = aged.type_in
def type_dark(rgb, text, font, size, cx, cy, color=INK, seed=0, depth=1.0, ink=1.0, align='c'):
    return _orig(rgb, text, font, size, cx, cy, color=INK if color in ('#2f2622', '#2e2a28') else color, seed=seed, depth=depth, ink=ink, align=align)
aged.type_in = type_dark; archive.type_in = type_dark
# larger card text
def make_card(n, name, lang, ipa, origin, meaning, color=None):
    c0 = archive.plain_card(color or 'white', n)
    c = aged.age(c0, CARD_A, 50 + n, 0.45)
    W_ = c.shape[1]; cx = W_ // 2
    type_dark(c, f'Nº {n} / 5', 'CourierPrime', 28, W_ - 110, 50, seed=n)
    type_dark(c, name, 'IMFellEnglishSC', 104 if len(name) <= 6 else 92, cx, 170, seed=2 + n, depth=1.2)
    type_dark(c, f'{lang}  {ipa}', 'Gentium-Italic', 38, cx, 255, seed=3 + n)
    y = 335
    for i, l in enumerate(lines_wrap(' '.join(origin), 'CourierPrime', 27, 530)):
        type_dark(c, l, 'CourierPrime', 27, cx, y, seed=10 + n + i); y += 40
    y += 26
    for i, l in enumerate(lines_wrap(meaning, 'CourierPrime-Italic', 28, 530)):
        type_dark(c, l, 'CourierPrime-Italic', 28, cx, y + i * 43, seed=40 + n + i)
    return c
archive.make_card = make_card
import build3 as B
B.make_card = make_card
CARD_IDS = set()
_card = B.card
def card_tag(*a, **k):
    rgb, al = _card(*a, **k); CARD_IDS.add(id(rgb)); return rgb, al
B.card = card_tag
import build4 as B4
B4.STRIPS = {}                                   # no coloured strips
def mute(x, amt=0.38):
    g = x.mean(-1, keepdims=True)
    x = x * (1 - amt) + g * amt                  # desaturate
    cream = np.array([0.93, 0.90, 0.84], np.float32)
    return np.clip(x * 0.86 + cream * 0.14, 0, 1).astype(np.float32)   # lift & soften contrast
B4.warm = lambda bg: mute(bg, 0.45)
_scene = B4.scene
def scene(fn, H):
    bg, layers, ex = _scene(fn, H)
    for l in layers:
        if id(l.rgb) not in CARD_IDS and not l.ink: l.rgb = mute(l.rgb, 0.3)
    return bg, layers, ex
B4.scene = scene
if __name__ == '__main__':
    from comp import save, finish
    for i, fn in enumerate(B4.FNS):
        bg, layers, ex = scene(fn, 1350)
        save(finish(B.render(bg, layers, 99, 0, 1350, ex), i), f'/home/user/Test/carousel/{B.NAMES_OUT[i]}.png'); print('ok', i, flush=True)
