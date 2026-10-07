"""Flyttar ner g:s skål så att den ligger mellan baslinjen och x-höjden,
som skålen i a, d och q. Nedstapeln kortas lika mycket (mjukt i stammen)
så att den slutar på samma djup som förut; skål och krok behåller formen.

    python3 g_skal.py g.stl
"""
import sys
import numpy as np
import trimesh
import pymeshfix

from justera import ramp, integral, slapp_i_hal

XHOJD, BAS = 2.0, 0.0


def laga(m):
    if m.is_watertight:
        return m
    v, f = pymeshfix.clean_from_arrays(np.asarray(m.vertices), np.asarray(m.faces))
    r = trimesh.Trimesh(v, f); r.fix_normals()
    return r


def skaltopp(m):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    v = np.vstack(s.discrete)
    v = v[(v[:, 0] > m.bounds[0, 0] + 0.9) & (v[:, 0] < m.bounds[0, 0] + 1.4)]
    return v[:, 1].max() - BAS


def main():
    fil = sys.argv[1]
    g = trimesh.load(fil)
    delta = XHOJD - skaltopp(g)
    v = g.vertices.copy(); y = v[:, 1] - BAS
    w = lambda t: ramp(t, -1.0, -0.7) * ramp(t, 0.2, -0.1)
    v[:, 1] += delta * integral(w, y, -1.0) / integral(w, np.array([0.2]), -1.0)[0]
    ny, _ = slapp_i_hal(laga(trimesh.Trimesh(v, g.faces, process=False)))
    ny = laga(ny)
    print(f"g: skålen flyttad {delta:+.2f}, topp {skaltopp(ny):.2f}, vattentät {ny.is_watertight}")
    ny.export(fil)


if __name__ == "__main__":
    main()
