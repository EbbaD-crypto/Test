"""Gör om upp- och nedstapelbokstäverna från originalet utan knyckar.

Inga lokala vinkeländringar: hela bokstaven skjuvas som en enhet till
LUTNING grader (mätt över både x-höjdsdelen och nedstapeln). Djupet ställs
in genom att hela delen under baslinjen skalas jämnt i höjdled, med mjuk
(C1-kontinuerlig) övergång vid baslinjen. g:s skål flyttas ner till
x-höjden på samma sätt. Sist görs släppet i hålen.

    LUTNING=10 python3 utan_knyck.py a-z.30.sep.stl utmapp
"""
import os
import sys
import numpy as np
import trimesh

from justera import BOKSTAVER, OVRIGA, hitta, ramp, integral, slapp_i_hal, NED, XHOJD, UPP
from lutning import snedhet
from gemensam_sving import laga

LUTNING = float(os.environ.get("LUTNING", 10.0))
K = np.tan(np.radians(LUTNING))
BOKST = {"g": 0.0, "j": 0.0, "p": 0.0, "q1": 0.0, "q2": 0.0, "y": 0.0, "f": -20.0}
# Uppstaplar: höjden ställs in genom jämn skalning ovanför x-höjdsområdet
UPPST = {"b": -10.00, "d1": -10.01, "h": -0.06, "k": -0.09, "l": -19.96,
         "t1": -20.04, "t2": -20.05, "L": -20.10, "utropstecken": 0.0}
BEHALL_DJUP = {"f"}  # f behåller sitt originaldjup


def skaltopp(m, bas):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    v = np.vstack(s.discrete)
    v = v[(v[:, 0] > m.bounds[0, 0] + 0.9) & (v[:, 0] < m.bounds[0, 0] + 1.4)]
    return v[:, 1].max() - bas


def omforma_hojd(y, lyft, skala, mitt=0.3, bredd=0.3):
    """y' = ∫ lutning: 1 ovanför baslinjeområdet, skala under, mjuk övergång.
    lyft flyttar allt ovanför (för g:s skål)."""
    sigma = lambda t: skala + (1 - skala) * ramp(t, mitt - bredd, mitt + bredd)
    return mitt + lyft + integral(sigma, y, mitt)


def main():
    kalla, ut = sys.argv[1:3]
    os.makedirs(ut, exist_ok=True)
    for p in trimesh.load(kalla, force="mesh").split(only_watertight=False):
        if len(p.faces) <= 3000:
            continue
        info = hitta(BOKSTAVER, p)
        namn = info["namn"] if info else hitta(OVRIGA, p)
        if namn in UPPST:
            bas = UPPST[namn]
            v = p.vertices.copy(); y = v[:, 1] - bas
            mitt = 1.7  # skalningen börjar mjukt strax under x-höjden
            skala = (UPP - mitt) / (y.max() - mitt)
            sigma = lambda t: 1 + (skala - 1) * ramp(t, mitt - 0.3, mitt + 0.3)
            v[:, 1] = bas + mitt + integral(sigma, y, mitt)
            m = trimesh.Trimesh(v, p.faces, process=False)
            zon = (1.6, 3.6) if namn == "utropstecken" else (0.25, 3.7)
            g0 = snedhet(m, bas, *zon)
            v = m.vertices.copy(); v[:, 0] += (K - np.tan(np.radians(g0))) * (v[:, 1] - bas)
            m = trimesh.Trimesh(v, p.faces, process=False)
            g1 = snedhet(m, bas, *zon)
            m, _ = slapp_i_hal(laga(m))
            m = laga(m)
            print(f"{namn:3s} höjdskala {skala:.3f}, lutning {g0:.1f}° → {g1:.1f}°, topp {m.bounds[1, 1] - bas:.2f}, "
                  f"vattentät {m.is_watertight}")
            m.export(os.path.join(ut, f"{namn}.stl"))
            continue
        if namn not in BOKST:
            continue
        bas = BOKST[namn]
        v = p.vertices.copy(); y = v[:, 1] - bas
        lyft = XHOJD - skaltopp(p, bas) if namn == "g" else 0.0
        if namn in BEHALL_DJUP:
            skala = 1.0
        else:
            # skala så att botten hamnar på −NED efter ev. lyft
            mitt = 0.3
            botten = y.min()
            skala = (-NED - mitt - lyft) / (botten - mitt)
        v[:, 1] = bas + omforma_hojd(y, lyft, skala)
        m = trimesh.Trimesh(v, p.faces, process=False)
        g0 = snedhet(m, bas, -1.6, 1.75)
        v = m.vertices.copy(); v[:, 0] += (K - np.tan(np.radians(g0))) * (v[:, 1] - bas)
        m = trimesh.Trimesh(v, p.faces, process=False)
        g1 = snedhet(m, bas, -1.6, 1.75)
        m, _ = slapp_i_hal(laga(m))
        m = laga(m)
        print(f"{namn:3s} lyft {lyft:+.2f}, djupskala {skala:.3f}, lutning {g0:.1f}° → {g1:.1f}°, "
              f"djup {m.bounds[0, 1] - bas:.2f}, topp {m.bounds[1, 1] - bas:.2f}, vattentät {m.is_watertight}")
        m.export(os.path.join(ut, f"{namn}.stl"))


if __name__ == "__main__":
    main()
