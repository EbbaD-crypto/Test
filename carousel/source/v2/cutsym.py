import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2
from comp import rd, paper, scissor, wobble
from sketch import sketch
from aged import age
def cut_symbol(name, width, seed=0, tone='#f3ead6', wash=0.5):
    """pen sketch drawn on a scrap of paper, cut out with scissors, aged like a scan"""
    l = rd(f'ill/{name}_line.png')[..., 3]; f = rd(f'ill/{name}_fill.png')[..., 3]
    s = width / l.shape[1]; sz = (int(width), int(l.shape[0] * s))
    shape = np.maximum(cv2.resize(l, sz, interpolation=cv2.INTER_AREA), cv2.resize(f, sz, interpolation=cv2.INTER_AREA))
    pad = 40; shape = np.pad(shape, pad); h, w = shape.shape
    pg = paper('cream', h, w, tone, seed)
    import sketch as SK
    SK_w = width
    sketch(pg, name, w / 2, h / 2, SK_w, 0, seed=seed, wash=wash)
    m = scissor(shape, pad=16, eps=3.5, seed=seed)
    pg = age(pg, m, 200 + seed, 0.8)
    ys, xs = np.where(m > 0.05); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return pg[y0:y1, x0:x1].astype(np.float32), m[y0:y1, x0:x1].astype(np.float32)
if __name__ == '__main__':
    tiles = []
    for i, n in enumerate(['train', 'globe', 'compass', 'balloon', 'suitcase', 'plane', 'sailboat', 'map']):
        rgb, a = cut_symbol(n, 300, i)
        c = np.ones((420, 420, 3), np.float32) * np.array([0.72, 0.64, 0.52])
        h, w = a.shape; y, x = (420 - h) // 2, (420 - w) // 2
        c[y:y+h, x:x+w] = c[y:y+h, x:x+w] * (1 - a[..., None]) + rgb * a[..., None]
        tiles.append(c)
    sheet = np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])])
    cv2.imwrite('v3/symbols.png', (sheet[..., ::-1] * 255).astype(np.uint8))
