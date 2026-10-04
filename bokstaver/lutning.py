"""Ger alla bokstäver samma lutning, LUTNING grader åt höger.

Utgår från bokstäverna som justera.py gjort (rätt höjder och släpp i hålen)
och gör tre saker per bokstav:

1. Hela bokstaven skjuvas runt baslinjen så att den lutar LUTNING i
   x-höjdszonen. Formen i övrigt följer med oförändrad. Diagonala och
   S-formade bokstäver (s, v, w, x, z) skjuvas lika mycket som medianen.
2. Upp- och nedstaplar som efter det lutar annorlunda skjuvas separat, med mjuk
   övergång vid x-höjden/baslinjen, så att stapeln blir rak hela vägen.
3. Släppet i hålen görs om (minst SLAPP_HAL), eftersom skjuvningen kan ändra
   väggarnas vinkel något.

Prickarna på i, j och ! följer med sin bokstav.

    python3 lutning.py justerade a-z.30.sep.stl u.stl lutade
"""
import os
import sys
import numpy as np
import trimesh

from justera import BOKSTAVER, OVRIGA, hitta, ramp, integral, slapp_i_hal, SLAPP_HAL

LUTNING = float(os.environ.get("LUTNING", 6.0))  # grader; kan ändras med miljövariabeln LUTNING
K_MAL = np.tan(np.radians(LUTNING))

# Lutningen mäts som medianen av alla nästan lodräta bitar av konturen (sett
# framifrån) inom en zon. Det är ett vanligt sätt att mäta snedhet i
# handskrift och påverkas lite av fötter, bågar och fogar.
# Zon för hela bokstavens lutning (relativt baslinjen):
ZON = {"utropstecken": (1.6, 3.6), "L": (1.5, 3.5)}
STANDARDZON = (0.25, 1.75)
# Diagonala och S-formade bokstäver saknar lodräta staplar och skjuvas som medianen
MEDIAN = {"s1", "s2", "s3", "s4", "s5", "v", "w1", "w2", "x", "z"}
ORORDA = {"bage", "prick", "punkt", "langt-bort"}
UPPSTAPLAR = {"b", "d1", "h", "k", "l", "t1", "t2"}
UPPZON = (2.3, 3.7)
NEDSTAPLAR = {"g": (-0.3, -1.6), "j": (-0.3, -1.6), "p": (-0.3, -1.6), "y": (-0.3, -1.6),
              "q1": (-1.0, -1.9), "q2": (-1.0, -1.9), "f": (-0.4, -1.6)}
PRICKAR = {"i-prick": "i", "j-prick": "j", "utropstecken-prick": "utropstecken"}
BASLINJE = {"f": -20.0, "i": -19.95, "i-prick": -19.95, "j-prick": 0.0, "utropstecken-prick": 0.0}


def snedhet(m, bas, ylo, yhi):
    """Typisk lutning (grader, + = åt höger) för konturen mellan ylo och yhi."""
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    vinklar, vikter = [], []
    for d in s.discrete:
        p = d[:, :2]
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        t = np.arange(0, L[-1], 0.03)
        q = np.column_stack([np.interp(t, L, p[:, 0]), np.interp(t, L, p[:, 1])])
        dq = np.diff(q, axis=0); mitt = (q[1:] + q[:-1]) / 2
        th = (np.degrees(np.arctan2(dq[:, 0], dq[:, 1])) + 90) % 180 - 90
        ok = (np.abs(th) < 35) & (mitt[:, 1] - bas > ylo) & (mitt[:, 1] - bas < yhi)
        vinklar += list(th[ok]); vikter += list(np.hypot(*dq[ok].T))
    if len(vinklar) < 5:
        return None
    v, w = np.array(vinklar), np.array(vikter)
    o = np.argsort(v); c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, c[-1] / 2)])


def skjuv_hela(m, bas, dk):
    v = m.vertices.copy(); v[:, 0] += dk * (v[:, 1] - bas)
    return trimesh.Trimesh(v, m.faces, process=False)


def skjuv_del(m, bas, dk, start, slut):
    """Skjuv bara bortom start (mjuk övergång till slut), t.ex. en uppstapel."""
    v = m.vertices.copy(); y = v[:, 1] - bas
    w = lambda t: ramp(t, start, slut)
    v[:, 0] += dk * integral(w, y, start)
    return trimesh.Trimesh(v, m.faces, process=False)


def grader(k):
    return float("nan") if k is None else np.degrees(np.arctan(k))


def main():
    mapp, kalla, ufil, ut = sys.argv[1:5]
    os.makedirs(ut, exist_ok=True)
    # Baslinjer från originalfilen
    baser = {}
    for p in trimesh.load(kalla, force="mesh").split(only_watertight=False):
        if len(p.faces) <= 3000:
            continue
        info = hitta(BOKSTAVER, p)
        namn = info["namn"] if info else hitta(OVRIGA, p)
        baser[namn] = info["bas"] if info and "bas" in info else BASLINJE.get(namn, p.bounds[0, 1])
    filer = {os.path.splitext(f)[0]: os.path.join(mapp, f) for f in os.listdir(mapp) if f.endswith(".stl")}
    filer["u"] = ufil
    u = trimesh.load(ufil)
    baser["u"] = u.bounds[0, 1]

    # 1. Hela bokstavens skjuvning
    dk, fore = {}, {}
    for namn, fil in filer.items():
        if namn in ORORDA or namn in MEDIAN or namn in PRICKAR:
            continue
        g = snedhet(trimesh.load(fil), baser[namn], *ZON.get(namn, STANDARDZON))
        if g is None:
            continue
        fore[namn] = g
        dk[namn] = K_MAL - np.tan(np.radians(g))
    median = float(np.median(list(dk.values())))
    for namn in MEDIAN:
        dk[namn] = median
    for prick, bok in PRICKAR.items():
        dk[prick] = dk[bok]
    print(f"s, v, w, x, z skjuvas {grader(median):+.1f}° (median)")

    for namn, fil in sorted(filer.items()):
        m = trimesh.load(fil)
        if namn in ORORDA or namn not in dk:
            m.export(os.path.join(ut, f"{namn}.stl")); continue
        bas = baser[namn]
        m = skjuv_hela(m, bas, dk[namn])
        rad = f"{namn:20s} hela {fore.get(namn, float('nan')):5.1f}° → {LUTNING}° (skjuv {grader(dk[namn]):+.1f}°)"
        if namn in UPPSTAPLAR:
            g = snedhet(m, bas, *UPPZON)
            if g is not None:
                m = skjuv_del(m, bas, K_MAL - np.tan(np.radians(g)), 1.9, 2.6)
                rad += f"; uppstapel {g:.1f}° → {LUTNING}°"
        if namn in NEDSTAPLAR:
            a, b = NEDSTAPLAR[namn]
            g = snedhet(m, bas, b, a)
            if g is not None:
                m = skjuv_del(m, bas, K_MAL - np.tan(np.radians(g)), a + 0.6, a - 0.1)
                rad += f"; nedstapel {g:.1f}° → {LUTNING}°"
        m, hal = slapp_i_hal(m)
        if not hal:
            m.fix_normals()
        rad += f"; vattentät {m.is_watertight}"
        print(rad)
        m.export(os.path.join(ut, f"{namn}.stl"))


if __name__ == "__main__":
    main()
