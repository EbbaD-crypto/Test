"""Finputs enligt typsnittsreglerna.

1. f: stammen mellan tvärstrecket och kroken förlängs så att toppen når
   uppstaplarnas höjd (UPP). Kroken flyttas oförändrad.
2. t: stammen ovanför tvärstrecket kortas så att toppen hamnar på T_HOJD.
3. Prickarna på i och j flyttas till samma höjd.
4. y och z ställs in så att toppen ligger exakt på x-höjden; g:s öra sänks.
5. o görs ungefär lika brett som n utan att linjen blir tjockare: sidorna
   flyttas utåt, så att bara hålet blir bredare.

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

    # 1. f
    f = las("f"); bas = -20.0
    d = UPP - (f.bounds[1, 1] - bas)
    f = spara(langs_lutning(f, bas, 1.45, 1.85, d), fil("f"), hal=False)
    print(f"f: topp {f.bounds[1, 1] - bas:.2f} (förlängd {d:+.2f})")

    # 2. t
    for n, bas in (("t1", -20.04), ("t2", -20.05)):
        t = las(n)
        d = T_HOJD - (t.bounds[1, 1] - bas)
        t = spara(langs_lutning(t, bas, 2.2, 3.4, d), fil(n), hal=False)
        print(f"{n}: topp {t.bounds[1, 1] - bas:.2f} (kortad {d:+.2f})")

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

    # 5. o bredare utan tjockare linje: sidorna flyttas utåt längs lutningen
    o = las("o"); n = las("n")
    bas = o.bounds[0, 1]
    oka = 0.6 * (n.extents[0] - o.extents[0])  # runda bokstäver lite smalare än n
    v = o.vertices.copy()
    mitt_x = (o.bounds[0, 0] + o.bounds[1, 0]) / 2 + K * (v[:, 1] - (bas + XHOJD / 2))
    # mjuk fördelning så att o:et förblir runt (ingen fyrkantig form)
    bredd = 0.45
    v[:, 0] += 0.5 * oka * np.tanh((v[:, 0] - mitt_x) / bredd) / np.tanh(0.9 / bredd)
    o2 = spara(trimesh.Trimesh(v, o.faces, process=False), fil("o"))
    print(f"o: bredd {o.extents[0]:.2f} → {o2.extents[0]:.2f} (n {n.extents[0]:.2f})")


if __name__ == "__main__":
    main()
