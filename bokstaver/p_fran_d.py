"""Gör p av d1 vridet 180° (som u av n).

d:ets skål hamnar mellan baslinjen och x-höjden, och uppstapeln med sin krok
blir en nedstapel. Lutningen behålls (en vridning ändrar den inte). Delen
under baslinjen skalas jämnt så att nedstapeln slutar på samma djup som
g, j och y. Sist görs släppet i hålet.

    python3 p_fran_d.py slutlig
"""
import os
import sys
import numpy as np
import trimesh

from justera import ramp, integral, slapp_i_hal, NED, XHOJD
from gemensam_sving import laga

BAS_D = -10.01


def main():
    mapp = sys.argv[1]
    d = trimesh.load(os.path.join(mapp, "d1.stl"))
    gammal = trimesh.load(os.path.join(mapp, "p.stl"))
    p = d.copy()
    # vrid 180° runt z-axeln kring mitten av x-höjdsbandet
    mitt = np.array([(d.bounds[0, 0] + d.bounds[1, 0]) / 2, BAS_D + XHOJD / 2, 0])
    p.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1], mitt))
    # flytta så att baslinjen hamnar på 0 och bokstaven där gamla p låg
    p.apply_translation([gammal.bounds[0, 0] - p.bounds[0, 0], 0 - BAS_D, 0])
    v = p.vertices.copy(); y = v[:, 1]
    # nedstapeln: skala jämnt under baslinjen till djupet NED, mjuk övergång
    m0 = 0.3
    skala = (-NED - m0) / (y.min() - m0)
    sigma = lambda t: skala + (1 - skala) * ramp(t, m0 - 0.3, m0 + 0.3)
    v[:, 1] = m0 + integral(sigma, y, m0)
    p = trimesh.Trimesh(v, p.faces, process=False)
    p.fix_normals()
    p, _ = slapp_i_hal(laga(p)); p = laga(p)
    print(f"p från d: topp {p.bounds[1, 1]:.2f}, djup {p.bounds[0, 1]:.2f}, djupskala {skala:.3f}, vattentät {p.is_watertight}")
    p.export(os.path.join(mapp, "p.stl"))


if __name__ == "__main__":
    main()
