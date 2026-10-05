"""Deep, exclusive grade: rich darker backgrounds, light cards glow on top."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
import collage2 as C
import build4 as B4, build3 as B
def deep(x, depth=1.45, sat=1.25, bg=False):
    g = x.mean(-1, keepdims=True)
    x = np.clip(g + (x - g) * sat, 0, 1)                      # richer colour
    x = x ** depth                                             # deeper midtones
    sh = (1 - x.mean(-1, keepdims=True)) ** 2                  # warm, brown shadows
    x = x * (1 - 0.18 * sh) + np.array([0.20, 0.11, 0.07], np.float32) * 0.18 * sh
    if bg:
        h, w = x.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
        v = 1 - 0.28 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        x = x * v[..., None]
    return np.clip(x, 0, 1).astype(np.float32)
B4.warm = lambda b: deep(b, 1.55, 1.3, bg=True)
_scene = C.scene.__wrapped__ if hasattr(C.scene, '__wrapped__') else None
def scene(fn, H):
    bg, layers, ex = C._scene(fn, H)
    for l in layers:
        if id(l.rgb) not in C.CARD_IDS and not l.ink: l.rgb = deep(l.rgb, 1.3, 1.2)
    return bg, layers, ex
B4.scene = scene
def _main():
    from comp import save, finish
    for i, fn in enumerate(B4.FNS):
        bg, layers, ex = scene(fn, 1350)
        save(finish(B.render(bg, layers, 99, 0, 1350, ex), i), f'/home/user/Test/carousel/{B.NAMES_OUT[i]}.png'); print('ok', i, flush=True)

# --- no logo anywhere: drop the stamped logo, end card is just the name typed
_s2 = scene
def scene(fn, H):
    bg, layers, ex = _s2(fn, H)
    layers = [l for l in layers if not l.ink]
    if fn.__name__ == 'sc_cover':
        from roundlogo import logo_rgba as rl
        from build3 import L
        lg = rl(250, seed=1)
        layers.append(L(lg[..., :3], lg[..., 3] * 0.88, 340, 455 if H < 1500 else 640, -8, g=max(l.g for l in layers) + 1, frm=(0, 0), ink=True))
    return bg, layers, ex
B4.scene = scene
def end_scene(H):
    from build3 import L
    from aged import type_in
    import comp
    bg = B4.warm(B.scan(B.R + 'rivet_papper_1.jpg', H, 1.0))
    c, a = B.card(1, 'white', 1.12); C.CARD_IDS.add(id(c))
    c = C.archive.plain_card('white', 7); c = C.aged.age(c, a if a.shape == c.shape[:2] else C.CARD_A, 3, 0.45)
    cx = c.shape[1] // 2
    from archive import CARD_A
    c = cv2.resize(c, (a.shape[1], a.shape[0])); cx = c.shape[1] // 2
    from roundlogo import logo_rgba as rl
    lg = rl(440, seed=3); A = lg[..., 3:] * 0.92; y0, x0 = 120, cx - 220
    reg = c[y0:y0 + 440, x0:x0 + 440]; c[y0:y0 + 440, x0:x0 + 440] = reg * (1 - A) + lg[..., :3] * reg ** 0.3 * A
    type_in(c, 'a little archive of names', 'CourierPrime-Italic', 32, cx, 640, seed=2)
    type_in(c, 'save for later', 'CourierPrime', 28, cx, 760, seed=4)
    C.CARD_IDS.add(id(c))
    return bg, [L(c, a, 0, 0, 0, g=0, frm=(0, 0))], (lambda cv, H: None)
B4.end_scene = end_scene
if __name__ == '__main__':
    from comp import save, finish
    for i, fn in enumerate(B4.FNS):
        bg, layers, ex = scene(fn, 1350)
        save(finish(B.render(bg, layers, 99, 0, 1350, ex), i), f'/home/user/Test/carousel/{B.NAMES_OUT[i]}.png'); print('ok', i, flush=True)
