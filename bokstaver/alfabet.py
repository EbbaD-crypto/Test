"""Sätter ihop det slutliga alfabetet och mäter hur konsekvent det är i 2D.

    python3 alfabet.py a-z.30.sep.stl justerade [bild.png]
"""
import os
import sys
import numpy as np
import trimesh
from scipy import ndimage
from skimage.morphology import skeletonize
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from justera import BOKSTAVER, OVRIGA, hitta

# Representant för varje bokstav (första varianten) och tillhörande prickar
VAL = {"a": "a1", "b": "b", "c": "c3", "d": "d1", "e": "e4", "f": "f", "g": "g", "h": "h", "i": "i",
       "j": "j", "k": "k", "l": "l", "m": "m", "n": "n", "o": "o", "p": "p", "q": "q2", "r": "r",
       "s": "s1", "t": "t1", "u": "u", "v": "v", "w": "w1", "x": "x", "y": "y", "z": "z"}
PRICKAR = {"i": "i-prick", "j": "j-prick"}
RUT = 0.01


def basl(namn, p):
    info = hitta(BOKSTAVER, p)
    if info and "bas" in info:
        return info["bas"]
    if namn == "f":
        return -20.0
    if namn in ("i", "i-prick"):
        return -19.95
    if namn in ("j-prick",):
        return 0.0
    return p.bounds[0, 1]


def kontur(m):
    """Konturen sett framifrån: tvärsnitt strax ovanför baksidan."""
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    pl, _ = s.to_planar(to_2D=np.eye(4))
    return pl.polygons_full


def rastrera(polys, dx, dy, w, h):
    img = Image.new("L", (int(w / RUT), int(h / RUT)), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        d.polygon([((x - dx) / RUT, (h - (y - dy)) / RUT) for x, y in p.exterior.coords], fill=255)
        for i in p.interiors:
            d.polygon([((x - dx) / RUT, (h - (y - dy)) / RUT) for x, y in i.coords], fill=0)
    return np.array(img)[::-1] > 0


def main():
    kalla, mapp = sys.argv[1:3]
    delar = {}
    for p in trimesh.load(kalla, force="mesh").split(only_watertight=False):
        if len(p.faces) <= 3000:
            continue
        info = hitta(BOKSTAVER, p)
        delar[info["namn"] if info else hitta(OVRIGA, p)] = p
    glyf = {}
    for bok, namn in VAL.items():
        fil = os.path.join(mapp, f"{namn}.stl")
        m = trimesh.load(fil) if os.path.exists(fil) else delar[namn]
        bas = basl(namn, delar.get(namn, m))
        polys = list(kontur(m))
        if bok in PRICKAR:
            pfil = os.path.join(mapp, f"{PRICKAR[bok]}.stl")
            pr = trimesh.load(pfil) if os.path.exists(pfil) else delar[PRICKAR[bok]]
            polys += list(kontur(pr))
        glyf[bok] = (polys, bas)

    # Mätningar
    print("bokst  linje(median)  bredd   topp   botten")
    rader = []
    for bok, (polys, bas) in glyf.items():
        x0 = min(p.bounds[0] for p in polys); x1 = max(p.bounds[2] for p in polys)
        y0 = min(p.bounds[1] for p in polys); y1 = max(p.bounds[3] for p in polys)
        m = rastrera(polys, x0 - 0.1, y0 - 0.1, x1 - x0 + 0.2, y1 - y0 + 0.2)
        dt = ndimage.distance_transform_edt(m) * RUT
        sk = skeletonize(m)
        # bort med skelettets ändar (rundade avslut) så att bara staplarna räknas
        v = dt[sk]; v = v[v > np.percentile(v, 15)]
        linje = 2 * np.median(v)
        rader.append((bok, linje, x1 - x0, y1 - bas, y0 - bas))
        print(f"  {bok}     {linje:5.2f}        {x1 - x0:5.2f}  {y1 - bas:5.2f}  {y0 - bas:5.2f}")
    linjer = np.array([r[1] for r in rader])
    print(f"linjetjocklek: median {np.median(linjer):.2f}, min {linjer.min():.2f} ({rader[linjer.argmin()][0]}), "
          f"max {linjer.max():.2f} ({rader[linjer.argmax()][0]}), spridning ±{100 * linjer.std() / np.median(linjer):.0f} %")

    # Bilder: alfabetet och några ord
    def satt(ax, text, y, avst=0.25):
        x = 0.0
        for c in text:
            if c == " ":
                x += 1.0; continue
            polys, bas = glyf[c]
            x0 = min(p.bounds[0] for p in polys)
            for p in polys:
                for ring, f in [(p.exterior, "#222")] + [(i, "white") for i in p.interiors]:
                    xy = np.array(ring.coords) - [x0 - x, bas - y]
                    ax.fill(xy[:, 0], xy[:, 1], color=f, lw=0)
            x += max(p.bounds[2] for p in polys) - x0 + avst
        return x

    rader_text = ["abcdefghijklm", "nopqrstuvwxyz", "lera och gips", "hamburgefonstiv", "kvalitet bryggor"]
    fig, ax = plt.subplots(figsize=(14, 2.2 * len(rader_text)), dpi=110)
    bredast = 0
    for i, t in enumerate(rader_text):
        y = -i * 6.5
        for yy in (0, 2, 4, -2.1):
            ax.axhline(y + yy, color="#cfd8ea", lw=0.5, zorder=0)
        bredast = max(bredast, satt(ax, t, y))
    ax.set_xlim(-0.5, bredast + 0.5); ax.set_ylim(-(len(rader_text) - 1) * 6.5 - 2.8, 4.6)
    ax.set_aspect("equal"); ax.axis("off")
    plt.savefig(sys.argv[3] if len(sys.argv) > 3 else "alfabet.png", bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
