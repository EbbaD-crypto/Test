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
    top = m.face_normals[:, 2] > 0.05
    tri = m.triangles[top][:, :, :2] - [dx, dy]
    ax.add_collection(PolyCollection(tri, facecolor=farg, edgecolor="none"))


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
    fig, axs = plt.subplots(2, len(ORDNING), figsize=(1.6 * len(ORDNING), 7.5), dpi=110)
    for j, namn in enumerate(ORDNING):
        p, bas = original[namn]
        ny = trimesh.load(os.path.join(mapp, f"{namn}.stl"))
        dx = p.bounds[0, 0]
        for rad, (m, farg) in enumerate(((p, "#555"), (ny, "#c0503c"))):
            ax = axs[rad, j]
            silhuett(ax, m, dx, bas, farg)
            for y, s in ((0, "-"), (XHOJD, "-"), (UPP, "--"), (-NED, "--")):
                ax.axhline(y, color="#4a7be0", lw=0.6, ls=s)
            ax.set_xlim(-0.4, 2.8); ax.set_ylim(-2.7, 4.6); ax.set_aspect("equal"); ax.axis("off")
            if rad == 0:
                ax.set_title(namn.replace("utropstecken", "!"), fontsize=8)
    axs[0, 0].text(-0.5, 0.9, "före", rotation=90, ha="right", fontsize=9)
    axs[1, 0].text(-0.5, 0.9, "efter", rotation=90, ha="right", fontsize=9)
    plt.subplots_adjust(wspace=0.02, hspace=0.05)
    plt.savefig(ut, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
