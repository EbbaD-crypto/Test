"""Ger alla bokstäver samma lutning, LUTNING grader åt höger.

Utgår från bokstäverna som justera.py gjort (rätt höjder och släpp i hålen)
och gör tre saker per bokstav:

1. Hela bokstaven skjuvas runt baslinjen så att huvudstapeln i x-höjdszonen
   lutar LUTNING. Formen i övrigt följer med oförändrad. Runda bokstäver utan
   stapel (c, e, o, s, v, w, x, z) skjuvas lika mycket som medianen av de andra.
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

# Huvudstapel i x-höjdszonen: V = stapeln längst till vänster, H = längst till
# höger, E = den enda stapeln, M = medel av vänster och höger (n, m, u),
# R = rund bokstav (ingen stapel).
REGEL = {
    "a1": "H", "a2": "H", "b": "V", "d1": "H", "f": "E", "g": "H", "h": "V", "i": "E",
    "j": "E", "k": "V", "l": "E", "m": "M", "n": "M", "p": "V", "q1": "H", "q2": "H",
    "r": "V", "t1": "E", "t2": "E", "u": "M", "y": "H", "L": "V", "utropstecken": "E",
}
RUNDA = {"c1", "c2", "c3", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "o",
         "s1", "s2", "s3", "s4", "s5", "v", "w1", "w2", "x", "z"}
ORORDA = {"bage", "prick", "punkt", "langt-bort"}
UPPSTAPLAR = {"b", "d1", "h", "k", "l", "t1", "t2"}
NEDSTAPLAR = {"g": (-0.3, -1.2), "j": (-0.3, -1.2), "p": (-0.3, -1.4), "y": (-0.3, -1.2),
              "q1": (-1.0, -1.8), "q2": (-1.0, -1.7), "f": (-0.4, -1.3)}
PRICKAR = {"i-prick": "i", "j-prick": "j", "utropstecken-prick": "utropstecken"}
BASLINJE = {"f": -20.0, "i": -19.95, "i-prick": -19.95, "j-prick": 0.0, "utropstecken-prick": 0.0}


def stapelbitar(m, y):
    """x-intervall för varje stapel i ett tvärsnitt vid höjden y."""
    zc = (m.bounds[0, 2] + m.bounds[1, 2]) / 2
    s = m.section(plane_origin=[0, y, zc], plane_normal=[0, 1, 0])
    if s is None:
        return []
    return sorted((d[:, 0].min(), d[:, 0].max()) for d in s.discrete)


def lutning(m, bas, ylo, yhi, regel):
    """Mittlinjens lutning (tan) för den valda stapeln mellan ylo och yhi."""
    ys, xs = [], []
    for y in np.linspace(bas + ylo, bas + yhi, 24):
        bitar = [b for b in stapelbitar(m, y) if b[1] - b[0] < 0.9]
        if not bitar:
            continue
        if regel == "E":
            if len(bitar) != 1:
                continue
            x = sum(bitar[0]) / 2
        elif regel == "V":
            x = sum(bitar[0]) / 2
        elif regel == "H":
            x = sum(bitar[-1]) / 2
        else:  # M
            if len(bitar) < 2:
                continue
            x = (sum(bitar[0]) + sum(bitar[-1])) / 4
        ys.append(y); xs.append(x)
    return np.polyfit(ys, xs, 1)[0] if len(ys) > 5 else None


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

    # 1. Skjuvning för bokstäver med stapel
    dk, fore = {}, {}
    for namn, regel in REGEL.items():
        m = trimesh.load(filer[namn]); bas = baser[namn]
        zon = (1.8, 3.4) if namn == "utropstecken" else (0.45, 1.55)
        k = lutning(m, bas, *zon, regel)
        fore[namn] = k
        dk[namn] = 0.0 if k is None else K_MAL - k
    median = float(np.median([v for v in dk.values()]))
    for namn in RUNDA:
        dk[namn] = median
    for prick, bok in PRICKAR.items():
        dk[prick] = dk[bok]
    print(f"runda bokstäver skjuvas {grader(median):+.1f}° (median)")

    for namn, fil in sorted(filer.items()):
        m = trimesh.load(fil)
        if namn in ORORDA or namn not in dk:
            m.export(os.path.join(ut, f"{namn}.stl")); continue
        bas = baser[namn]
        m = skjuv_hela(m, bas, dk[namn])
        rad = f"{namn:20s} hela {grader(fore.get(namn)) if namn in fore else float('nan'):5.1f}° → {LUTNING}° (skjuv {grader(dk[namn]):+.1f}°)"
        if namn in UPPSTAPLAR:
            k = lutning(m, bas, 2.4, 3.5, "E" if namn in ("l", "t1", "t2") else ("H" if namn == "d1" else "V"))
            if k is not None:
                m = skjuv_del(m, bas, K_MAL - k, 1.9, 2.6)
                rad += f"; uppstapel {grader(k):.1f}° → {LUTNING}°"
        if namn in NEDSTAPLAR:
            a, b = NEDSTAPLAR[namn]
            k = lutning(m, bas, b, a, "E")
            if k is not None:
                start = a + 0.6
                m = skjuv_del(m, bas, K_MAL - k, start, a - 0.1)
                rad += f"; nedstapel {grader(k):.1f}° → {LUTNING}°"
        m, hal = slapp_i_hal(m)
        if not hal:
            m.fix_normals()
        rad += f"; vattentät {m.is_watertight}"
        print(rad)
        m.export(os.path.join(ut, f"{namn}.stl"))


if __name__ == "__main__":
    main()
