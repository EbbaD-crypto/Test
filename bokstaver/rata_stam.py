"""Rätar huvudstammen i h, k, b och d så att ytterkanten blir en rak linje
med samma lutning som resten av typsnittet.

Stammens ytterkant mäts i många höjder. Varje höjd flyttas i sidled så att
kanten får LUTNING grader totalt. SVING styr hur mycket av originalets
sväng som behålls (0 = helt rak, 1 = hela svängen).
Förskjutningen jämnas ut i höjdled och påverkar bara stamsidan av bokstaven
(mjuk övergång i x), så bågar och armar på andra sidan ligger kvar.

    LUTNING=10 python3 rata_stam.py lutade10 a-z.30.sep.stl
"""
import os
import sys
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter1d

from justera import ramp, slapp_i_hal

LUTNING = float(os.environ.get("LUTNING", 10.0))
SVING = float(os.environ.get("SVING", 0.0))  # andel av originalets sväng som behålls
K = np.tan(np.radians(LUTNING))
# namn: (baslinje, stamsida V/H, höjdintervall för stammen över baslinjen)
STAMMAR = {"h": (-0.06, "V", (0.3, 3.7)), "k": (-0.09, "V", (0.3, 3.7)),
           "b": (-10.00, "V", (0.3, 3.7)), "d1": (-10.01, "H", (0.3, 3.7))}


def kant(m, y, sida):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, y, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 1, 0])
    bit = sorted((d[:, 0].min(), d[:, 0].max()) for d in s.discrete)
    return bit[0][0] if sida == "V" else bit[-1][1]


def kantlutning(m, bas, lo, hi, sida):
    ys = np.linspace(bas + lo, bas + hi, 12)
    return np.degrees(np.arctan(np.polyfit(ys, [kant(m, y, sida) for y in ys], 1)[0]))


def rata(m, bas, sida, zon, sving=0.0):
    """sving = hur mycket av stammens ursprungliga sväng som behålls
    (0 = helt rak, 1 = hela svängen kvar, bara den totala lutningen ändras)."""
    ys = np.linspace(bas + zon[0], bas + zon[1], 60)
    xe = np.array([kant(m, y, sida) for y in ys])
    # svängen = kantens avvikelse från sin egen räta linje
    k, c = np.polyfit(ys, xe, 1)
    avvik = gaussian_filter1d(xe - (k * ys + c), 2, mode="nearest")
    # mål: rak linje med rätt lutning genom kantens medelläge, plus den sväng som behålls
    xt = xe.mean() + K * (ys - ys.mean()) + sving * avvik
    dx = gaussian_filter1d(xt - xe, 3, mode="nearest")
    v = m.vertices.copy()
    d = np.interp(v[:, 1], ys, dx)  # utanför zonen: samma förskjutning som i änden
    xs = kant(m, bas + 1.2, sida)
    if sida == "V":
        wx = 1 - ramp(v[:, 0], xs + 0.55, xs + 0.85)
    else:
        wx = ramp(v[:, 0], xs - 0.85, xs - 0.55)
    v[:, 0] += d * wx
    return trimesh.Trimesh(v, m.faces, process=False)


def main():
    mapp = sys.argv[1]
    for namn, (bas, sida, zon) in STAMMAR.items():
        fil = os.path.join(mapp, f"{namn}.stl")
        m = trimesh.load(fil)
        fore = [kantlutning(m, bas, a, b, sida) for a, b in ((2.4, 3.6), (0.8, 1.8))]
        ny = rata(m, bas, sida, zon, SVING)
        efter = [kantlutning(ny, bas, a, b, sida) for a, b in ((2.4, 3.6), (0.8, 1.8))]
        ny, _ = slapp_i_hal(ny)
        print(f"{namn}: stam upptill {fore[0]:.1f}° → {efter[0]:.1f}°, nedtill {fore[1]:.1f}° → {efter[1]:.1f}°, "
              f"vattentät {ny.is_watertight}")
        ny.export(fil)


if __name__ == "__main__":
    main()
