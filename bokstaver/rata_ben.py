"""Ger alla ben i n, m och h samma lutning (10°) som u:s armar och resten av
typsnittet, utan att göra dem stela.

För varje ben mäts mittlinjen mellan y = 0,4 och 1,5; benets *medellutning*
(rak linje anpassad till mittlinjen) vrids till 10° runt benets överdel, så att
benets egen sväng behålls. Bågarna ovanför (y > 1,7) rörs inte. Förflyttningen
sprids mjukt till hela bokstaven med RBF (som i jamna_kontur.py).

    python3 rata_ben.py <mapp med slutlig/> [--forhand bild.png]
"""
import os
import shutil
import sys
import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator
from shapely.ops import unary_union
from shapely.geometry import LineString

from finputs import spara
from kolla_hojder import BAS

K = np.tan(np.radians(10))
BOKSTAVER = {"n": -19.169, "m": -0.015, "h": -0.06}
HOPPA = {"h": {0}}      # h:s vänstra "ben" är uppstapeln: den rörs inte (skulle ge en knyck)
Y_LAG, Y_TOPP, Y_FRI = 0.4, 1.5, 1.75


def kontur(m):
    z0, z1 = m.bounds[:, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4))
    return unary_union(list(p.polygons_full))


def benmitter(P, x0, x1, bas, ys):
    """Mitten på varje ben (vänster -> höger) på höjderna ys."""
    ut = []
    for y in ys:
        g = P.intersection(LineString([(x0 - 1, bas + y), (x1 + 1, bas + y)]))
        qs = sorted(getattr(g, "geoms", [g]), key=lambda q: q.bounds[0])
        ut.append([((q.bounds[0] + q.bounds[2]) / 2, q.bounds[0], q.bounds[2]) for q in qs])
    return ut


def flyttfalt(m, bas, hoppa=(), mal=None):
    """mal: önskad lutning (grader) per ben; standard 10° för alla."""
    """Kontrollpunkter (x, y) och deras förflyttning i x."""
    P = kontur(m)
    ys = np.arange(Y_LAG, Y_TOPP + 1e-6, 0.05)
    rader = benmitter(P, m.bounds[0, 0], m.bounds[1, 0], bas, ys)
    antal = max(len(r) for r in rader)
    behall = [len(r) == antal for r in rader]          # bara höjder där alla ben är åtskilda
    ys = ys[behall]; rader = [r for r, b in zip(rader, behall) if b]
    pts, dx = [], []
    vinklar = []
    for b in range(antal):
        c = np.array([r[b][0] for r in rader])
        k, c0 = np.polyfit(ys, c, 1)                 # medellutning (dx/dy)
        vinklar.append(np.degrees(np.arctan(k)))
        km = K if mal is None or mal[b] is None else np.tan(np.radians(mal[b]))
        if b in hoppa:
            km = k                                   # står still
        # vrid medellinjen till målvinkeln runt benets överdel (y = Y_TOPP)
        d = lambda y, k=k, km=km: (km - k) * (y - Y_TOPP)
        for y, r in zip(ys, rader):
            for x in (r[b][1], r[b][0], r[b][2]):
                pts.append((x, bas + y)); dx.append(d(y))
        for y in np.arange(-0.1, Y_LAG, 0.05):       # foten följer med benet
            xc = c0 + k * y
            for x in (xc - 0.35, xc, xc + 0.35):
                pts.append((x, bas + y)); dx.append(d(y))
    # fasta punkter: allt ovanför Y_FRI (bågar, uppstapel) står still
    for q in getattr(P, "geoms", [P]):
        for ring in [q.exterior] + list(q.interiors):
            r = np.array(ring.coords)
            for x, y in r[::4]:
                if y - bas > Y_FRI:
                    pts.append((x, y)); dx.append(0.0)
    return np.array(pts), np.array(dx), vinklar


def rata(m, bas, hoppa=(), mal=None):
    pts, dx, vinklar = flyttfalt(m, bas, hoppa, mal)
    f = RBFInterpolator(pts, dx, kernel="thin_plate_spline", smoothing=1e-3)
    v = m.vertices.copy()
    v[:, 0] += f(v[:, :2])
    return trimesh.Trimesh(v, m.faces, process=False), vinklar


def main():
    mapp = sys.argv[1]
    spar = os.path.join(mapp, "fore_ben"); os.makedirs(spar, exist_ok=True)
    for n, bas in BOKSTAVER.items():
        if not os.path.exists(os.path.join(spar, f"{n}.stl")):
            shutil.copy(os.path.join(mapp, f"{n}.stl"), spar)
        m = trimesh.load(os.path.join(spar, f"{n}.stl"))
        ny, fore = rata(m, bas, HOPPA.get(n, ()))
        _, _, efter = flyttfalt(ny, bas)
        ny = spara(ny, os.path.join(mapp, f"{n}.stl"), hal=False)
        print(f"{n}: benens lutning {[round(v, 1) for v in fore]} -> {[round(v, 1) for v in efter]}, vattentät {ny.is_watertight}")


if __name__ == "__main__":
    main()
