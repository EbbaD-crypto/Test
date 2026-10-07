"""Finputs enligt typsnittsreglerna.

1. f lämnas med sin egen, kortare topp (f ska inte vara lika högt som h).
2. t behåller full höjd (lika högt som h).
3. Prickarna på i och j flyttas till samma höjd.
4. y och z ställs in så att toppen ligger exakt på x-höjden; g:s öra sänks.
5. o: görs i o_hal.py, där o får samma innanmäte som a.

Förlängning/förkortning görs längs bokstavens lutning (LUTNING grader), inte
rakt upp, så att en sträckt stapel behåller sin vinkel. Sist görs släppet i
hålen och bokstäverna lagas om något blivit otätt.

    python3 finputs.py slutlig
"""
import os
import sys
import numpy as np
import trimesh

from justera import ramp, integral, slapp_i_hal, UPP, XHOJD
from gemensam_sving import laga

LUTNING = float(os.environ.get("LUTNING", 10.0))
K = np.tan(np.radians(LUTNING))
T_HOJD = 3.0


def langs_lutning(m, bas, a, b, delta, mjuk=0.12):
    """Sträck (delta > 0) eller korta (delta < 0) bandet a–b (över baslinjen)
    längs lutningen; allt ovanför bandet flyttas med oförändrat."""
    v = m.vertices.copy()
    y = v[:, 1] - bas
    w = lambda t: ramp(t, a, a + mjuk) * ramp(t, b, b - mjuk)
    langd = integral(w, np.array([b]), a)[0]
    D = delta / langd * integral(w, y, a)
    v[:, 0] += K * D
    v[:, 1] += D
    return trimesh.Trimesh(v, m.faces, process=False)


def flytta_langs_lutning(m, delta):
    v = m.vertices.copy()
    v[:, 0] += K * delta
    v[:, 1] += delta
    return trimesh.Trimesh(v, m.faces, process=False)


def spara(m, fil, hal=True):
    m = laga(m)
    if hal:
        m, _ = slapp_i_hal(m)
        m = laga(m)
    m.export(fil)
    return m


def main():
    mapp = sys.argv[1]
    las = lambda n: trimesh.load(os.path.join(mapp, f"{n}.stl"))
    fil = lambda n: os.path.join(mapp, f"{n}.stl")

    # 1. f behåller sin egen, kortare topp (ditt typsnitt har f lägre än h)

    # 2. t behåller full höjd, lika högt som h

    # 3. prickar på samma höjd (medel av i och j)
    pi, pj = las("i-prick"), las("j-prick")
    topp_i, topp_j = pi.bounds[1, 1] - (-19.95), pj.bounds[1, 1] - 0.0
    mal = (topp_i + topp_j) / 2
    for n, m, topp in (("i-prick", pi, topp_i), ("j-prick", pj, topp_j)):
        m = spara(flytta_langs_lutning(m, mal - topp), fil(n), hal=False)
        print(f"{n}: topp {topp:.2f} → {mal:.2f}")

    # 4. y, z på x-höjden; g:s öra
    y_ = las("y"); d = XHOJD - y_.bounds[1, 1]
    y_ = spara(langs_lutning(y_, 0.0, 0.9, 1.7, d), fil("y"), hal=False)
    print(f"y: topp {y_.bounds[1, 1]:.2f}")
    z = las("z"); bas = z.bounds[0, 1]; d = XHOJD - (z.bounds[1, 1] - bas)
    z = spara(langs_lutning(z, bas, 0.6, 1.5, d), fil("z"), hal=False)
    print(f"z: topp {z.bounds[1, 1] - bas:.2f}")
    g = las("g"); v = g.vertices.copy()
    skal = 1.85, (2.03 - 1.85) / (g.bounds[1, 1] - 1.85)
    over = v[:, 1] > skal[0]
    hoger = ramp(v[:, 0], g.bounds[0, 0] + 1.5, g.bounds[0, 0] + 1.9)
    ny_y = skal[0] + (v[:, 1] - skal[0]) * skal[1]
    v[over, 1] += (ny_y[over] - v[over, 1]) * hoger[over]
    g = spara(trimesh.Trimesh(v, g.faces, process=False), fil("g"))
    print(f"g: örat {g.bounds[1, 1]:.2f}")

    # 5. o: se o_hal.py (o får a:s innanmäte i stället för att breddas)


if __name__ == "__main__":
    main()
