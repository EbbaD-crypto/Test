"""Ger o samma innanmäte (hål) som a: samma form, storlek och lutning,
centrerat där o:s hål sitter. o:s yttre form hålls fast. Hålets kontur
formas om med en mjuk interpolering (RBF) över hela bokstaven.

    python3 o_hal.py o.stl a1.stl
"""
import sys
import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator

from justera import slapp_i_hal
from gemensam_sving import laga

N = 240


def konturer(m):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    pl, _ = s.to_planar(to_2D=np.eye(4))
    p = max(pl.polygons_full, key=lambda p: p.area)
    hal = max(p.interiors, key=lambda r: abs(_area(np.array(r.coords))))
    return np.array(p.exterior.coords)[:-1], np.array(hal.coords)[:-1]


def _area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * (np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def sampla_sluten(p, n=N):
    """Jämn sampling, start i översta punkten, moturs."""
    if _area(p) < 0:
        p = p[::-1]
    p = np.roll(p, -np.argmax(p[:, 1]), axis=0)
    pp = np.vstack([p, p[:1]])
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(pp, axis=0).T))]
    s = np.linspace(0, L[-1], n, endpoint=False)
    return np.column_stack([np.interp(s, L, pp[:, 0]), np.interp(s, L, pp[:, 1])])


def main():
    ofil, afil = sys.argv[1:3]
    o, a = trimesh.load(ofil), trimesh.load(afil)
    o_yttre, o_hal = konturer(o)
    _, a_hal = konturer(a)
    oh, ah = sampla_sluten(o_hal), sampla_sluten(a_hal)
    # a:s hål flyttat till o:s hålcentrum (ytcentrum)
    centrum = lambda p: p.mean(axis=0)
    mal = ah - centrum(ah) + centrum(oh)
    # matcha startpunkt så att förflyttningen blir minimal
    basta = min(range(N), key=lambda k: np.abs(np.roll(mal, -k, axis=0) - oh).sum())
    mal = np.roll(mal, -basta, axis=0)
    yt = sampla_sluten(o_yttre, 300)
    pts = np.vstack([oh, yt])
    val = np.vstack([mal - oh, np.zeros_like(yt)])
    rbf = RBFInterpolator(pts, val, kernel="thin_plate_spline", smoothing=1e-4)
    v = o.vertices.copy()
    v[:, :2] += rbf(v[:, :2])
    ny = laga(trimesh.Trimesh(v, o.faces, process=False))
    ny, _ = slapp_i_hal(ny); ny = laga(ny)
    _, nh = konturer(ny)
    nh = sampla_sluten(nh)
    print(f"o: största flytt {np.abs(mal - oh).max():.3f}, hålets area {abs(_area(oh)):.3f} → {abs(_area(nh)):.3f} "
          f"(a: {abs(_area(ah)):.3f}), vattentät {ny.is_watertight}")
    ny.export(ofil)


if __name__ == "__main__":
    main()
