"""h som en blandning av två h (t.ex. utan knorr och med knorr nedtill).

Konturerna blandas via avståndsfält (t = 0: första, t = 1: andra), och höjden
i området där de skiljer sig räknas fram från avståndet till kanten med samma
profil som resten av bokstäverna. Övriga h:et är orört.

    python3 h_blandning.py h_utan.stl h_med.stl ut.stl [t=0.5]
"""
import sys
import numpy as np
import trimesh
from scipy import ndimage
import versaler_3d as v3

RUT = 0.01


def hojdfalt(m, xs, ys):
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, m.bounds[1, 2] + 1)])
    loc, ri, _ = m.ray.intersects_location(o, np.tile([0, 0, -1.0], (X.size, 1)), multiple_hits=False)
    Z = np.zeros(X.size); Z[ri] = loc[:, 2] - m.bounds[0, 2]
    return Z.reshape(X.shape)


def sdf(mask):
    return (ndimage.distance_transform_edt(~mask) - ndimage.distance_transform_edt(mask)) * RUT


def blanda(a, b, t=0.5):
    lo = np.minimum(a.bounds[0], b.bounds[0])[:2] - 0.1
    hi = np.maximum(a.bounds[1], b.bounds[1])[:2] + 0.1
    xs, ys = np.arange(lo[0], hi[0], RUT), np.arange(lo[1], hi[1], RUT)
    Za, Zb = hojdfalt(a, xs, ys), hojdfalt(b, xs, ys)
    ma, mb = Za > 1e-3, Zb > 1e-3
    M = (1 - t) * sdf(ma) + t * sdf(mb) < 0
    M = ndimage.binary_opening(ndimage.binary_closing(M, iterations=2), iterations=2)
    # område där de två skiljer sig
    olika = (ma != mb) | (abs(Za - Zb) > 0.01)
    w = ndimage.gaussian_filter(ndimage.binary_dilation(olika, iterations=int(0.15 / RUT)).astype(float), 0.08 / RUT)
    w = np.clip(w * 1.5, 0, 1)
    d = ndimage.distance_transform_edt(np.pad(M, 1))[1:-1, 1:-1] * RUT
    Zp = v3.hojd_fran_kant(np.maximum(d - RUT / 2, 0)) * (a.extents[2] / v3.HOJD)
    Zp = ndimage.gaussian_filter(Zp, 2.0)
    Zm = np.where(ma & mb, (1 - t) * Za + t * Zb, np.maximum(Za, Zb))
    Z = np.where(M, (1 - w) * Zm + w * Zp, 0.0)
    Z = np.where(M, np.maximum(Z, 0.004), 0)
    v3.RUT = RUT
    m = v3.till_mesh(Z, xs[0], ys[0])
    m.apply_translation([0, 0, a.bounds[0, 2]])
    if len(m.faces) > 150000:
        m = m.simplify_quadric_decimation(face_count=150000)
    if not m.is_watertight:
        from gemensam_sving import laga
        m = laga(m)
    return m


if __name__ == "__main__":
    a, b = trimesh.load(sys.argv[1]), trimesh.load(sys.argv[2])
    t = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    m = blanda(a, b, t)
    m.export(sys.argv[3])
    print("vattentät", m.is_watertight, m.bounds.round(3).tolist())
