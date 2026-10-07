"""Mäter hur brant väggarna i hålen lutar (släppvinkel) på en STL.

Ovansidan rastreras uppifrån; i ett band runt varje hål räknas den brantaste
lutningen. Släppvinkeln = 90° - brantaste lutningen (0° = lodrät vägg).

    python3 kolla_slapp.py fil1.stl fil2.stl ...
"""
import sys
import numpy as np
import trimesh
from scipy import ndimage

RUT = 0.01


def topp(m):
    x0, y0 = m.bounds[0, :2] - 0.05
    x1, y1 = m.bounds[1, :2] + 0.05
    xs, ys = np.arange(x0, x1, RUT), np.arange(y0, y1, RUT)
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, m.bounds[1, 2] + 1)])
    loc, ri, _ = m.ray.intersects_location(o, np.tile([0, 0, -1.0], (X.size, 1)), multiple_hits=False)
    Z = np.full(X.size, m.bounds[0, 2]); Z[ri] = loc[:, 2]
    return Z.reshape(X.shape) - m.bounds[0, 2]


def slappvinkel(m):
    Z = topp(m)
    fot = Z > 1e-3
    hal = ndimage.binary_fill_holes(fot) & ~fot
    hal = ndimage.binary_opening(hal, iterations=2)
    if not hal.any():
        return None
    band = ndimage.binary_dilation(hal, iterations=int(0.12 / RUT)) & fot
    gy, gx = np.gradient(Z, RUT)
    lut = np.degrees(np.arctan(np.hypot(gx, gy)))[band]
    return 90 - np.percentile(lut, 99)


for f in sys.argv[1:]:
    v = slappvinkel(trimesh.load(f))
    print(f.split("/")[-1], "inget hål" if v is None else f"släpp i hålen ≈ {v:.1f}°")
