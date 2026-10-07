"""Jämnar ut små gupp och inbuktningar i en bokstavs kontur (sett framifrån).

Ytterkonturen och hålens konturer samplas jämnt och utjämnas längs sin egen
längd (gaussfilter). Skillnaden sprids till hela bokstaven med en mjuk
interpolering (RBF) i x och y; höjdprofilen följer med. Den övergripande
formen behålls, bara små vågor försvinner.

    python3 jamna_kontur.py fil.stl [sigma]
"""
import sys
import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator
from scipy.ndimage import gaussian_filter1d

from justera import slapp_i_hal
from gemensam_sving import laga


def ringar(m):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    pl, _ = s.to_planar(to_2D=np.eye(4))
    ut = []
    for poly in pl.polygons_full:
        for r in [poly.exterior] + list(poly.interiors):
            ut.append(np.array(r.coords)[:-1])
    return ut


def jamna(fil, sigma=0.12, steg=0.01):
    m = trimesh.load(fil)
    pts, flytt = [], []
    for r in ringar(m):
        rr = np.vstack([r, r[:1]])
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(rr, axis=0).T))]
        s = np.arange(0, L[-1], steg)
        q = np.column_stack([np.interp(s, L, rr[:, 0]), np.interp(s, L, rr[:, 1])])
        n = max(1.0, sigma / steg)
        qs = np.column_stack([gaussian_filter1d(q[:, i], n, mode="wrap") for i in (0, 1)])
        pts.append(q[::3]); flytt.append((qs - q)[::3])
    pts, flytt = np.vstack(pts), np.vstack(flytt)
    rbf = RBFInterpolator(pts, flytt, kernel="thin_plate_spline", smoothing=1e-3)
    v = m.vertices.copy()
    v[:, :2] += rbf(v[:, :2])
    ny = laga(trimesh.Trimesh(v, m.faces, process=False))
    ny, _ = slapp_i_hal(ny); ny = laga(ny)
    print(f"{fil.split('/')[-1]}: största flytt {np.abs(flytt).max():.3f}, vattentät {ny.is_watertight}")
    ny.export(fil)


if __name__ == "__main__":
    jamna(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.12)
