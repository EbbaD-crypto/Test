"""The Little Archive – name cards pulled out of the archive folder. No birds."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
from final import *          # age, flatplace, type_in, sketch, stamp_logo, scaled, finish, NAMES, background, age_bg
from comp import lines_wrap, save, Canvas, rotate_rgba
T = 640                       # head-room above the folder for the pulled card
PULL = 380
def folder_parts():
    rgb, a = scaled(2, 690)
    cream = (rgb[..., 0] > rgb[..., 2] + 0.06)
    front_a = a * cream.astype(np.float32)
    front_a = cv2.GaussianBlur(front_a, (0, 0), 0.7)
    # clean card texture from the visible blue card, mirrored to full card length
    tex = rgb[20:200, 70:620]
    t = np.concatenate([tex, tex[::-1]], 0); t = np.concatenate([t] * 3, 0)
    cw, ch = 608, 860
    card = cv2.resize(t, (cw, t.shape[0] * cw // tex.shape[1]))[:ch]
    m = np.zeros((ch, cw), np.uint8); cv2.rectangle(m, (12, 0), (cw - 13, ch - 1), 1, -1); cv2.rectangle(m, (0, 12), (cw - 1, ch - 13), 1, -1)
    for cx_, cy_ in [(12, 12), (cw - 13, 12), (12, ch - 13), (cw - 13, ch - 13)]: cv2.circle(m, (cx_, cy_), 12, 1, -1)
    ca = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.7)
    return rgb, front_a, card, ca
FOLDER, FRONT_A, CARD0, CARD_A = folder_parts()
def make_card(n, name, lang, ipa, origin, meaning, color=None):
    from comp import tint
    c0 = tint(CARD0.copy(), color, 0.85) if color else CARD0.copy()
    c = age(c0, CARD_A, 50 + n, 0.7)
    W_ = c.shape[1]; cx = W_ // 2
    type_in(c, f'Nº {n} / 5', 'CourierPrime', 28, W_ - 110, 48, seed=n)
    type_in(c, name, 'IMFellEnglishSC', 96 if len(name) <= 6 else 86, cx, 165, seed=2 + n, depth=1.2)
    type_in(c, f'{lang}: {ipa}', 'Gentium-Italic', 34, cx, 245, seed=3 + n)
    y = 318
    for i, l in enumerate(origin): type_in(c, l, 'CourierPrime', 23, cx, y, seed=10 + n + i); y += 34
    y += 30
    for i, l in enumerate(lines_wrap(meaning, 'CourierPrime-Italic', 25, 500)):
        type_in(c, l, 'CourierPrime-Italic', 25, cx, y + i * 38, seed=40 + n + i)
    return c
def make_front(n):
    f = age(FOLDER.copy(), FRONT_A, 20 + n)
    return f
def folder_unit(front, card, pull, n, sk=None):
    """folder with card pulled up by `pull` px; local canvas with head-room T"""
    h, w = FOLDER.shape[:2]
    rgb = np.zeros((h + T, w, 3), np.float32); a = np.zeros((h + T, w), np.float32)
    cy = T - pull
    ch = CARD_A.shape[0]; ys, ye = max(cy, 0), min(cy + ch, h + T)
    rgb[ys:ye, 44:44 + card.shape[1]] = card[ys - cy:ye - cy]; a[ys:ye, 44:44 + card.shape[1]] = CARD_A[ys - cy:ye - cy]
    # thin shadow of the folder lip on the card
    lip = cv2.GaussianBlur(np.pad(FRONT_A, ((T, 0), (0, 0)))[:, :], (0, 0), 3)
    shade = np.clip(np.roll(lip, -4, 0) - np.pad(FRONT_A, ((T, 0), (0, 0))), 0, 1) * 0.25
    rgb *= (1 - shade[..., None])
    FA = FRONT_A[..., None]
    rgb[T:] = rgb[T:] * (1 - FA) + front * FA; a[T:] = np.maximum(a[T:], FRONT_A)
    return rgb, a
def name_card2(n, name, lang, ipa, origin, meaning, _b=None, pull=PULL, card=None, front=None, rot=None, bg=None, divider=True):
    cv = Canvas(age_bg(n) if bg is None else bg.copy())
    if divider: d_rgb, d_a = scaled(1, 700); flatplace(cv, age(d_rgb, d_a, 10 + n), d_a, 30, 60, -4 if n % 2 else -2)
    card = card if card is not None else make_card(n, name, lang, ipa, origin, meaning)
    front = front if front is not None else decorate_front(make_front(n), n)
    rgb, a = folder_unit(front, card, pull, n)
    flatplace(cv, rgb, a, 300, 500 - T, (2.5 if n % 2 else 1.5) if rot is None else rot)
    type_in(cv.img, 'swipe >' if n < 5 else 'save for later', 'CourierPrime', 26, 950 if n < 5 else 920, 50, seed=5)
    return finish(cv.img, n)
def decorate_front(f, n):
    # logo stamp + hand-drawn travel sketch on the folder front
    from logo import logo_rgba
    from comp import rot_rgba4
    r = rot_rgba4(logo_rgba(250, seed=n), -3); A = r[..., 3:] * 0.85
    h, w = A.shape[:2]; y0, x0 = 600, 690 - w - 50
    reg = f[y0:y0 + h, x0:x0 + w]; f[y0:y0 + h, x0:x0 + w] = reg * (1 - A) + r[..., :3] * reg ** 0.3 * A
    for s_name, _, _, sw, sr in SKETCH.get(n, []): sketch(f, s_name, 170, 690, sw, sr, seed=n)
    return f
def cover2():
    cv = Canvas(age_bg(0))
    d_rgb, d_a = scaled(1, 760); flatplace(cv, age(d_rgb, d_a, 1), d_a, 200, 90, 3)
    n_rgb, n_a = scaled(5, 620); n_rgb = age(n_rgb, n_a, 2)
    type_in(n_rgb, '5', 'IMFellEnglishSC', 120, 310, 130, seed=1, depth=1.2)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        type_in(n_rgb, l, 'IMFellEnglishSC', 54, 310, 245 + i * 64, seed=2 + i, depth=1.1)
    type_in(n_rgb, 'a little archive of names', 'CourierPrime-Italic', 24, 310, 660, seed=9)
    flatplace(cv, n_rgb, n_a, 140, 330, -5)
    sketch(cv.img, 'globe', 860, 1050, 230, 6, seed=3)
    stamp_logo(cv, 900, 150, 270, 6, seed=0)
    type_in(cv.img, 'swipe >', 'CourierPrime', 28, 940, 1295, seed=5)
    return finish(cv.img, 0)
if __name__ == '__main__':
    out = '/home/user/Test/carousel/'
    save(cover2(), out + '01_omslag.png')
    for i, t in enumerate(NAMES): save(name_card2(i + 1, *t), out + f'0{i + 2}_{t[0]}.png')
