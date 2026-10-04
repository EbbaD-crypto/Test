"""Ger p samma runda del (skål) som b.

Skålens ytterkontur (delen till höger om stammen, mellan baslinjen och
x-höjden) och hålets kontur plockas ut för både b och p, relativt stammens
högerkant. p:s skål formas sedan om (RBF) så att båda konturerna får b:s
form. Stammens vänsterkant och nedstapeln hålls fasta.

    python3 p_skal.py slutlig
"""
import os
import sys
import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator

from justera import ramp, slapp_i_hal
from gemensam_sving import laga
from rata_stam import kant

K = np.tan(np.radians(10.0))
N = 200


def konturer(m):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    pl, _ = s.to_planar(to_2D=np.eye(4))
    poly = max(pl.polygons_full, key=lambda p: p.area)
    hal = max(poly.interiors, key=lambda r: abs(np.cross(np.diff(np.array(r.coords)[:, :2], axis=0)[:-1],
                                                     np.diff(np.array(r.coords)[:, :2], axis=0)[1:]).sum()))
    return np.array(poly.exterior.coords)[:-1], np.array(hal.coords)[:-1]


def sampla(p, n=N, sluten=False):
    if sluten:
        p = np.vstack([p, p[:1]])
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    s = np.linspace(0, L[-1], n, endpoint=not sluten)
    return np.column_stack([np.interp(s, L, p[:, 0]), np.interp(s, L, p[:, 1])])


def stamlinje(m, bas):
    """Stammens högerkant som en rak linje x = a + K*(y - bas), mätt mitt i x-höjden."""
    ys = np.linspace(bas + 0.6, bas + 1.4, 9)
    xs = []
    for y in ys:
        z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
        s = m.section(plane_origin=[0, y, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 1, 0])
        bit = sorted((d[:, 0].min(), d[:, 0].max()) for d in s.discrete)
        xs.append(bit[0][1] if len(bit) > 1 else np.nan)
    xs = np.array(xs); ok = ~np.isnan(xs)
    return np.mean(xs[ok] - K * (ys[ok] - bas))


def skalbage(m, bas, a):
    """Ytterkonturen till höger om stamlinjen mellan baslinjen och x-höjden,
    ordnad uppifrån (vid stammen), runt skålen, ner till stammen."""
    yt, hal = konturer(m)
    linje = lambda y: a + K * (y - bas)
    hoger = (yt[:, 0] > linje(yt[:, 1]) + 0.05) & (yt[:, 1] > bas - 0.15) & (yt[:, 1] < bas + 2.2)
    idx = np.nonzero(hoger)[0]
    # längsta sammanhängande bit
    brott = np.nonzero(np.diff(idx) > 1)[0]
    delar = np.split(idx, brott + 1)
    if len(delar) > 1 and delar[0][0] == 0 and delar[-1][-1] == len(yt) - 1:
        delar = [np.r_[delar[-1], delar[0]]] + delar[1:-1]
    bit = yt[max(delar, key=len)]
    if bit[0, 1] < bit[-1, 1]:
        bit = bit[::-1]
    # hålet: börja i översta punkten, medurs
    i = np.argmax(hal[:, 1]); hal = np.roll(hal, -i, axis=0)
    if np.cross(hal[1] - hal[0], hal[2] - hal[1]) > 0:
        hal = np.vstack([hal[:1], hal[1:][::-1]])
    return sampla(bit), sampla(hal, sluten=True)


def main():
    mapp = sys.argv[1]
    b = trimesh.load(os.path.join(mapp, "b.stl")); bas_b = -10.0
    p = trimesh.load(os.path.join(mapp, "p.stl")); bas_p = 0.0
    ab, ap = stamlinje(b, bas_b), stamlinje(p, bas_p)
    bage_b, hal_b = skalbage(b, bas_b, ab)
    bage_p, hal_p = skalbage(p, bas_p, ap)
    # b:s former flyttade till p:s stam och baslinje
    flytta = np.array([ap - ab, bas_p - bas_b])
    mal_bage, mal_hal = bage_b + flytta, hal_b + flytta
    # ändpunkterna av bågen ska sitta kvar mot p:s stam: tona in skillnaden
    t = np.linspace(0, 1, N)[:, None]
    for k, tt in ((0, 1 - np.minimum(t * 5, 1)), (-1, 1 - np.minimum((1 - t) * 5, 1))):
        mal_bage += (bage_p[k] - mal_bage[k]) * tt
    yt, _ = konturer(p)
    linje = lambda y: ap + K * (y - bas_p)
    fast = yt[(yt[:, 0] < linje(yt[:, 1]) - 0.15) | (yt[:, 1] < bas_p - 0.5)]
    pts = np.vstack([bage_p, hal_p, fast])
    val = np.vstack([mal_bage - bage_p, mal_hal - hal_p, np.zeros_like(fast)])
    rbf = RBFInterpolator(pts, val, kernel="thin_plate_spline", smoothing=1e-4)
    v = p.vertices.copy()
    omr = (v[:, 1] > bas_p - 0.6) & (v[:, 0] > linje(v[:, 1]) - 0.25)
    w = (ramp(v[omr, 1], bas_p - 0.6, bas_p - 0.2) * ramp(v[omr, 0], linje(v[omr, 1]) - 0.25, linje(v[omr, 1]) + 0.05))[:, None]
    v[omr, :2] += rbf(v[omr, :2]) * w
    ny = trimesh.Trimesh(v, p.faces, process=False)
    ny, _ = slapp_i_hal(laga(ny)); ny = laga(ny)
    nb, nh = skalbage(ny, bas_p, stamlinje(ny, bas_p))
    print(f"p: största flytt {np.abs(val).max():.3f}, avvikelse från b:s skål efteråt: båge {np.abs(nb - mal_bage).max():.3f}, "
          f"hål {np.abs(nh - mal_hal).max():.3f}, vattentät {ny.is_watertight}")
    ny.export(os.path.join(mapp, "p.stl"))


if __name__ == "__main__":
    main()
