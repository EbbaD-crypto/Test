"""Ritar före/efter sett uppifrån för alla bokstäver som justera.py ändrat.

    python3 jamfor.py a-z.30.sep.stl justerade jamforelse.png
"""
import os
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from justera import BOKSTAVER, OVRIGA, hitta, XHOJD, UPP, NED

ORDNING = ["b", "d1", "d2", "d3", "d4", "d5", "h", "k", "l", "t1", "t2", "L", "utropstecken", "f",
           "g", "j", "p", "q1", "q2", "y", "a1", "a2", "e1", "o"]


def silhuett(ax, m, dx, dy, farg):
    """Bokstavens tvärsnitt på halva höjden, sett uppifrån (hålen syns tydligt)."""
    z0, z1 = m.bounds[0, 2], m.bounds[1, 2]
    snitt = m.section(plane_origin=[0, 0, z0 + 0.5 * (z1 - z0)], plane_normal=[0, 0, 1])
    plan, _ = snitt.to_planar(to_2D=np.eye(4))
    for poly in plan.polygons_full:
        for ring, f in [(poly.exterior, farg)] + [(i, "white") for i in poly.interiors]:
            xy = np.array(ring.coords) - [dx, dy]
            ax.fill(xy[:, 0], xy[:, 1], color=f, lw=0)


def main():
    kalla, mapp, ut = sys.argv[1:4]
    original = {}
    for p in trimesh.load(kalla, force="mesh").split(only_watertight=False):
        if len(p.faces) <= 3000:
            continue
        info = hitta(BOKSTAVER, p)
        namn = info["namn"] if info else hitta(OVRIGA, p)
        bas = info["bas"] if info else p.bounds[0, 1]
        original[namn] = (p, bas)
    per_rad = 12
    rader = (len(ORDNING) + per_rad - 1) // per_rad
    fig, axs = plt.subplots(2 * rader, per_rad, figsize=(1.6 * per_rad, 3.6 * 2 * rader), dpi=110)
    for j, namn in enumerate(ORDNING):
        p, bas = original[namn]
        ny = trimesh.load(os.path.join(mapp, f"{namn}.stl"))
        dx = p.bounds[0, 0]
        for rad, (m, farg) in enumerate(((p, "#555"), (ny, "#c0503c"))):
            ax = axs[2 * (j // per_rad) + rad, j % per_rad]
            silhuett(ax, m, dx, bas, farg)
            for y, s in ((0, "-"), (XHOJD, "-"), (UPP, "--"), (-NED, "--")):
                ax.axhline(y, color="#4a7be0", lw=0.6, ls=s)
            ax.set_xlim(-0.4, 2.8); ax.set_ylim(-2.7, 4.6); ax.set_aspect("equal")
            if rad == 0:
                ax.set_title(namn.replace("utropstecken", "!"), fontsize=10)
    for ax in axs.ravel():
        ax.axis("off")
    for r in range(rader):
        axs[2 * r, 0].text(-0.5, 0.9, "före", rotation=90, ha="right", fontsize=10)
        axs[2 * r + 1, 0].text(-0.5, 0.9, "efter", rotation=90, ha="right", fontsize=10)
    plt.subplots_adjust(wspace=0.02, hspace=0.05)
    plt.savefig(ut, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
