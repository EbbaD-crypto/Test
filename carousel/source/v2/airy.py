"""Zara Home Kids feel: warm airy daylight, blush neutrals, soft window-shadow play."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
import comp
import deep as Dp
import collage2 as C
import build4 as B4, build3 as B
def airy(x, lift=0.42, sat=0.9):
    g = x.mean(-1, keepdims=True); x = g + (x - g) * sat
    x = 1 - (1 - x) * (1 - lift)                                # lift shadows -> airy, not grey
    x = x * np.array([1.0, 0.975, 0.93], np.float32)            # warm sunlight
    return np.clip(x, 0, 1).astype(np.float32)
B4.warm = lambda b: airy(b, 0.40, 0.88)
def scene(fn, H):
    bg, layers, ex = C._scene(fn, H)        # card-safe base scene
    for l in layers:
        if id(l.rgb) not in C.CARD_IDS and not l.ink: l.rgb = airy(l.rgb, 0.22, 0.92)
    keep = Dp.scene.__code__                # reuse logo handling from deep.scene
    return bg, layers, ex
# reuse deep's logo logic (round logo on cover, no old logo) but with airy colours
_deep_scene = Dp.scene
Dp.deep = lambda x, *a, **k: x                # disable the dark grade
B4.warm = lambda b: airy(b, 0.40, 0.88)
_base = C._scene
def base_airy(fn, H):
    bg, layers, ex = _base(fn, H)
    bg = airy(bg, 0.40, 0.88)
    for l in layers:
        if id(l.rgb) not in C.CARD_IDS and not l.ink: l.rgb = airy(l.rgb, 0.22, 0.92)
    return bg, layers, ex
C._scene = base_airy
B4.warm = lambda b: b                        # base_airy grades the bg itself
# --- window light: soft diagonal mullion shadows + warm glow from upper left
_cache = {}
def window(h, w):
    if (h, w) not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        u = (xx * 0.8 + yy * 0.6)                                   # diagonal coordinate
        bars = ((u % 620) < 70).astype(np.float32) + (((u + 310) % 620) < 22).astype(np.float32) * 0.8
        bars *= (yy > h * 0.08).astype(np.float32)
        bars = cv2.GaussianBlur(bars, (0, 0), 22)
        glow = np.exp(-(((xx - w * 0.15) / (w * 1.1)) ** 2 + ((yy + h * 0.1) / (h * 1.0)) ** 2))
        light = (0.92 + 0.10 * glow) * (1 - 0.13 * bars)
        _cache[(h, w)] = light[..., None].astype(np.float32)
    return _cache[(h, w)]
_finish = comp.finish
def finish(img, seed=0):
    img = np.clip(img * window(*img.shape[:2]), 0, 1)
    return _finish(img, seed)
comp.finish = finish
if __name__ == '__main__':
    for i, fn in enumerate(B4.FNS):
        bg, layers, ex = B4.scene(fn, 1350)
        comp.save(finish(B.render(bg, layers, 99, 0, 1350, ex), i), f'/home/user/Test/carousel/{B.NAMES_OUT[i]}.png'); print('ok', i, flush=True)
