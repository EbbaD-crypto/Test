"""Milk Honey colour font for names/titles (rendered by Chromium, pasted onto paper)."""
import sys, os, json, subprocess, hashlib; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
import airy                     # current approved look
import collage2 as C, build3 as B
CACHE = 'mhcache2'
def render_many(items):
    todo = [(t, px, f'{CACHE}/{hashlib.md5(f"{t}|{px}".encode()).hexdigest()}.png') for t, px in items]
    need = [x for x in todo if not os.path.exists(x[2])]
    if need: subprocess.run(['node', 'v3/mhrender.js', json.dumps(need)], check=True)
    return {(t, px): f for t, px, f in todo}
def load(t, px):
    f = render_many([(t, px)])[(t, px)]
    im = cv2.imread(f, cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    rgb = im[..., 2::-1]; a = im[..., 3]
    ys, xs = np.where(a > 0.02); return rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1], a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
def paste(img, t, px, cx, cy):
    rgb, a = load(t, px); h, w = a.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, img.shape[1]), min(y0 + h, img.shape[0])
    if X1 <= X0 or Y1 <= Y0: return
    A = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None] * 0.96; R = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    reg = img[Y0:Y1, X0:X1]
    pig = R * np.clip(reg.mean(-1, keepdims=True) / 0.9, 0.8, 1.04)    # watercolour sits in the paper grain
    img[Y0:Y1, X0:X1] = reg * (1 - A) + pig * A
_orig = C._orig
def type_mh(rgb, text, font, size, cx, cy, color='#2f2622', seed=0, depth=1.0, ink=0.9, align='c'):
    if font == 'IMFellEnglishSC':
        return paste(rgb, text, int(size * 0.95), cx, cy)
    return _orig(rgb, text, font, size, cx, cy, color=color, seed=seed, depth=depth, ink=ink, align=align)
C._orig = type_mh; B.type_in = type_mh
if __name__ == '__main__':
    import build4 as B4, comp
    for i, fn in enumerate(B4.FNS):
        bg, layers, ex = B4.scene(fn, 1350)
        comp.save(comp.finish(B.render(bg, layers, 99, 0, 1350, ex), i), f'/home/user/Test/carousel/{B.NAMES_OUT[i]}.png'); print('ok', i, flush=True)
