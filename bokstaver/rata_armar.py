"""Sänker h:ets båge och k:ets arm till x-höjden (stapeln rörs inte), och g:s
topp en aning.

Punkter till höger om uppstapeln och mellan y = 1,2 och 3,0 trycks ihop i höjd
mot y = 1,2 så att den högsta punkten hamnar på målet. Övergången från stapeln
är mjuk (vikten går från 0 vid stapelns högerkant till 1 en bit ut).

    python3 rata_armar.py <mapp med slutlig/>   (kopior av originalen sparas i <mapp>/fore_armar/)
"""
import os
import shutil
import sys
import numpy as np
import trimesh

from finputs import langs_lutning, spara
from kolla_hojder import BAS

K = np.tan(np.radians(10))
MAL = {"h": 2.0, "k": 2.0}
Y0, Y1 = 1.2, 3.0
RAMP = 0.9          # mjuk övergång från stapeln (lång, så att det inte blir någon grop vid fogen)


def stapelns_hogerkant(m, x0, bas):
    """Uppstapelns högerkant (rak, utan lutning) mätt på y = 2,6–3,2."""
    v = m.vertices
    y = v[:, 1] - bas
    sel = (y > 2.6) & (y < 3.2)
    return np.percentile((v[sel, 0] - x0) - K * y[sel], 99)


def tryck_ner(m, bas, mal):
    """Flytta hela bågen/armen (allt till höger om stapeln) nedåt längs lutningen
    så att dess högsta punkt hamnar på mal. Formen behålls; nära stapeln och
    längst ner på benet tonas förflyttningen ut mjukt, så att fogen mot stapeln
    inte får någon grop."""
    v = m.vertices.copy()
    x0 = m.bounds[0, 0]
    y = v[:, 1] - bas
    xd = (v[:, 0] - x0) - K * y
    kant = stapelns_hogerkant(m, x0, bas)
    sm = lambda t: (lambda c: c * c * (3 - 2 * c))(np.clip(t, 0, 1))
    wx = sm((xd - kant + 0.05) / 0.35)               # 0 i stapeln -> 1 en bit ut
    wy = sm((y - 0.6) / 0.8)                         # benets fot står kvar
    bage = (xd > kant + 0.3) & (y > Y0) & (y < Y1)
    topp = y[bage].max()
    d = topp - mal
    dy = -d * wx * wy
    v[:, 0] += K * dy
    v[:, 1] += dy
    return trimesh.Trimesh(v, m.faces, process=False), topp


def main():
    mapp = sys.argv[1]
    spar = os.path.join(mapp, "fore_armar"); os.makedirs(spar, exist_ok=True)
    for n in list(MAL) + ["g"]:
        if not os.path.exists(os.path.join(spar, f"{n}.stl")):
            shutil.copy(os.path.join(mapp, f"{n}.stl"), spar)
    for n, mal in MAL.items():
        m = trimesh.load(os.path.join(spar, f"{n}.stl"))
        bas = BAS[n]
        ny, topp = tryck_ner(m, bas, mal)
        ny = spara(ny, os.path.join(mapp, f"{n}.stl"), hal=False)
        print(f"{n}: båge/arm {topp:.3f} -> {mal}, uppstapel {ny.bounds[1, 1] - bas:.3f}, vattentät {ny.is_watertight}")
    g = trimesh.load(os.path.join(spar, "g.stl"))
    d = 2.01 - (g.bounds[1, 1] - BAS["g"])
    g = spara(langs_lutning(g, BAS["g"], 0.3, 1.7, d), os.path.join(mapp, "g.stl"), hal=True)
    print(f"g: topp -> {g.bounds[1, 1] - BAS['g']:.3f}, botten {g.bounds[0, 1] - BAS['g']:.3f}, vattentät {g.is_watertight}")


if __name__ == "__main__":
    main()
