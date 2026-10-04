"""Ger alla upp- och nedstaplar samma sväng och samma lutning.

Svängen = hur stammens ytterkant avviker från en rak linje. Den gemensamma
svängen är medelvärdet av förebildernas svängar, skalad till deras
genomsnittliga styrka (så att hela svängen behålls). Varje stam flyttas sedan
i sidled så att kanten blir: rak linje med LUTNING grader + den gemensamma
svängen. Tvärstreck (t, q) räknas bort i mätningen.

    LUTNING=10 python3 gemensam_sving.py lutade10 utmapp
"""
import os
import shutil
import sys
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter1d

import pymeshfix

from justera import ramp, slapp_i_hal
from rata_stam import kant

LUTNING = float(os.environ.get("LUTNING", 10.0))
K = np.tan(np.radians(LUTNING))

# namn: (baslinje, stamsida, höjder som ska räknas bort, t.ex. tvärstreck)
UPP = {"h": (-0.06, "V", None), "k": (-0.09, "V", None), "b": (-10.00, "V", None),
       "l": (-19.96, "V", None), "d1": (-10.01, "H", None),
       "t1": (-20.04, "V", (1.4, 2.2)), "t2": (-20.05, "V", (1.4, 2.2))}
NED = {"g": (0.0, "H", None), "j": (0.0, "H", None), "p": (0.0, "V", None), "y": (0.0, "H", None),
       "q1": (0.0, "H", (-1.1, -0.3)), "q2": (0.0, "H", (-1.1, -0.3))}
GRUPPER = [("uppstaplar", UPP, (0.3, 3.7), ["h", "k", "b", "l", "d1"]),
           ("nedstaplar", NED, (-1.5, 1.6), ["g", "j", "p", "y"])]


def kant_eller_nan(m, y, sida):
    try:
        return kant(m, y, sida)
    except (IndexError, AttributeError):
        return np.nan  # ingen stam på den höjden


def kantprofil(m, bas, sida, t, bort):
    xe = np.array([kant_eller_nan(m, bas + y, sida) for y in t])
    ok = ~np.isnan(xe)
    if bort:
        ok &= (t < bort[0]) | (t > bort[1])
    return np.interp(t, t[ok], xe[ok])


def sving(t, xe):
    k, c = np.polyfit(t, xe, 1)
    return gaussian_filter1d(xe - (k * t + c), 2, mode="nearest")


def laga(m):
    """Laga små glipor så att bokstaven blir vattentät (formen ändras inte)."""
    if m.is_watertight:
        return m
    v, f = pymeshfix.clean_from_arrays(np.asarray(m.vertices), np.asarray(m.faces))
    r = trimesh.Trimesh(v, f); r.fix_normals()
    return r


def main():
    mapp, ut = sys.argv[1:3]
    if os.path.abspath(mapp) != os.path.abspath(ut):
        shutil.copytree(mapp, ut, dirs_exist_ok=True)
    for grupp, bokst, zon, forebilder in GRUPPER:
        t = np.linspace(*zon, 60)
        profiler = {}
        for namn, (bas, sida, bort) in bokst.items():
            m = trimesh.load(os.path.join(ut, f"{namn}.stl"))
            profiler[namn] = kantprofil(m, bas, sida, t, bort)
        sv = [sving(t, profiler[n]) for n in forebilder]
        medel = np.mean(sv, axis=0)
        styrka = np.mean([np.ptp(s) for s in sv])
        gemensam = medel * styrka / np.ptp(medel)
        print(f"{grupp}: gemensam sväng {styrka:.2f} (förebilder {', '.join(forebilder)})")
        for namn, (bas, sida, bort) in bokst.items():
            fil = os.path.join(ut, f"{namn}.stl")
            m = trimesh.load(fil)
            xe = profiler[namn]
            mal = xe.mean() + K * (t - t.mean()) + gemensam
            dx = gaussian_filter1d(mal - xe, 2, mode="nearest")
            v = m.vertices.copy()
            d = np.interp(v[:, 1] - bas, t, dx)
            xs = kant(m, bas + (1.2 if grupp == "uppstaplar" else -0.8), sida)
            wx = 1 - ramp(v[:, 0], xs + 0.55, xs + 0.85) if sida == "V" else ramp(v[:, 0], xs - 0.85, xs - 0.55)
            v[:, 0] += d * wx
            ny = trimesh.Trimesh(v, m.faces, process=False)
            fore = np.ptp(sving(t, xe))
            efter = np.ptp(sving(t, kantprofil(ny, bas, sida, t, bort)))
            ny, _ = slapp_i_hal(laga(ny))
            ny = laga(ny)
            print(f"  {namn:3s} sväng {fore:.2f} → {efter:.2f}, vattentät {ny.is_watertight}")
            ny.export(fil)


if __name__ == "__main__":
    main()
