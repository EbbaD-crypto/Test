"""Formar om en bokstav sett framifrån till en ny kontur (2D), utan att röra
höjdprofilen: konturens punkter flyttas till närmaste punkt på den nya
konturen, och förflyttningen sprids mjukt till hela bokstaven (RBF).

Används för små formändringar (ta bort en knopp, runda av ett hörn)."""
import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator
from shapely.geometry import Point
from shapely.ops import nearest_points, unary_union


def kontur(m):
    z0, z1 = m.bounds[:, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4))
    return unary_union(list(p.polygons_full))


def ringar(P, steg=0.02):
    ut = []
    for q in getattr(P, "geoms", [P]):
        for r in [q.exterior] + list(q.interiors):
            L = r.length
            ut += [r.interpolate(t).coords[0] for t in np.arange(0, L, steg)]
    return np.array(ut)


def varpa(m, ny_kontur, gammal=None):
    gammal = gammal if gammal is not None else kontur(m)
    pts = ringar(gammal)
    granser = ny_kontur.boundary
    mal = np.array([nearest_points(Point(p), granser)[1].coords[0] for p in pts])
    flytt = mal - pts
    f = RBFInterpolator(pts, flytt, kernel="thin_plate_spline", smoothing=1e-4, neighbors=200)
    v = m.vertices.copy()
    v[:, :2] += f(v[:, :2])
    return trimesh.Trimesh(v, m.faces, process=False)
