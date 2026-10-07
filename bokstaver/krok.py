"""Ger g, j och y exakt samma krok nertill: medelformen av j:s och y:s krok.

Krokens kontur (sett framifrån) under SNITT plockas ut för varje bokstav,
från där stammen går in i kroken, runt kroken och upp till spetsen. Konturen
samplas jämnt och uttrycks relativt stammens mitt vid snittet. Den gemensamma
kroken är medelvärdet av j:s och y:s. Varje bokstav formas sedan om så att
dess krok får exakt den formen: konturens förflyttning sprids mjukt till hela
krokdelen (RBF-interpolering) och tonas ut ovanför snittet, så att resten av
bokstaven är orörd. Höjdprofilen (den rundade ovansidan) följer med.

    python3 krok.py slutlig
"""
import os
import sys
import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator

from justera import ramp, slapp_i_hal
from gemensam_sving import laga

SNITT = -0.9     # krokdelen ligger under denna höjd (baslinjen = 0)
TONING = 0.45    # förflyttningen tonas ut så här långt ovanför snittet
N = 240
BOKST = ["g", "j", "y"]
FOREBILDER = ["j", "y"]


def kontur(m):
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    pl, _ = s.to_planar(to_2D=np.eye(4))
    poly = max(pl.polygons_full, key=lambda p: p.area)
    return np.array(poly.exterior.coords)[:-1]


def krokbage(m):
    """Den del av ytterkonturen som ligger under SNITT, som en öppen kedja
    från vänster korsning, runt kroken, till höger korsning."""
    p = kontur(m)
    under = p[:, 1] < SNITT
    # rulla så att kedjan börjar i en punkt ovanför snittet
    start = np.argmax(~under)
    p = np.roll(p, -start, axis=0); under = np.roll(under, -start)
    idx = np.nonzero(under)[0]
    i0, i1 = idx[0] - 1, idx[-1] + 1
    kedja = p[i0:i1 + 1].copy()
    # klipp ändpunkterna exakt på snittet
    for k, (a, b) in ((0, (kedja[0], kedja[1])), (-1, (kedja[-1], kedja[-2]))):
        t = (SNITT - a[1]) / (b[1] - a[1])
        kedja[k] = a + t * (b - a)
    # kedjan ska börja på vänster sida
    if kedja[0, 0] > kedja[-1, 0]:
        kedja = kedja[::-1]
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(kedja, axis=0).T))]
    s = np.linspace(0, L[-1], N)
    return np.column_stack([np.interp(s, L, kedja[:, 0]), np.interp(s, L, kedja[:, 1])])


def main():
    mapp = sys.argv[1]
    mesh = {n: trimesh.load(os.path.join(mapp, f"{n}.stl")) for n in BOKST}
    bagar = {n: krokbage(m) for n, m in mesh.items()}
    ankare = {n: (b[0] + b[-1]) / 2 for n, b in bagar.items()}
    relativ = {n: bagar[n] - ankare[n] for n in BOKST}
    gemensam = np.mean([relativ[n] for n in FOREBILDER], axis=0)
    t = np.linspace(0, 1, N)[:, None]
    for n in BOKST:
        m = mesh[n]
        mal = ankare[n] + gemensam
        # behåll bokstavens egna ändpunkter vid snittet (stammens bredd), tona in mot mitten
        fel0, fel1 = bagar[n][0] - mal[0], bagar[n][-1] - mal[-1]
        mal = mal + (1 - t) * fel0 * (1 - np.minimum(t * 4, 1)) + t * fel1 * (1 - np.minimum((1 - t) * 4, 1))
        flytt = mal - bagar[n]
        # fasta punkter: konturen strax ovanför snittet ska inte röra sig
        p = kontur(m)
        fast = p[(p[:, 1] > SNITT + TONING) & (p[:, 1] < SNITT + TONING + 0.6)]
        pts = np.vstack([bagar[n], fast])
        val = np.vstack([flytt, np.zeros_like(fast)])
        rbf = RBFInterpolator(pts, val, kernel="thin_plate_spline", smoothing=1e-4)
        v = m.vertices.copy()
        omr = v[:, 1] < SNITT + TONING
        d = rbf(v[omr, :2])
        w = ramp(v[omr, 1], SNITT + TONING, SNITT)[:, None]
        v[omr, :2] += d * w
        ny = trimesh.Trimesh(v, m.faces, process=False)
        ny, _ = slapp_i_hal(laga(ny)); ny = laga(ny)
        rest = np.abs(krokbage(ny) - (ankare[n] + gemensam)).max()
        print(f"{n}: största flytt {np.abs(flytt).max():.3f}, avvikelse från gemensam krok efteråt {rest:.3f}, "
              f"vattentät {ny.is_watertight}")
        ny.export(os.path.join(mapp, f"{n}.stl"))


if __name__ == "__main__":
    main()
