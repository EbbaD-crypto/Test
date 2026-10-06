"""Färgbild av handtagen (snett framifrån, mjukt ljus).

    python3 visa.py               # handtag.png, marshmallow.png
"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

MAPP = os.path.dirname(os.path.abspath(__file__))
FARGER = {"snirkel": "#d9a42a", "marang": "#e8857a",   # senapsgul och korall
          "marshmallow": "#f4c6cf", "spett": "#fbf3ea"}   # marshmallowrosa och -vit
BAKGRUND = "#f3ece0"


def rita(ax, m, farg, zoom, elev=28, azim=-62):
    m = m.simplify_quadric_decimation(face_count=30000) if len(m.faces) > 30000 else m
    ljus = np.array([-0.4, -0.7, 0.8]); ljus /= np.linalg.norm(ljus)
    n = m.face_normals
    sken = 0.45 + 0.55 * np.clip(n @ ljus, 0, 1)
    bas = np.array(matplotlib.colors.to_rgb(farg))
    c = np.clip(bas[None] * sken[:, None] + 0.12 * np.clip(n @ ljus, 0, 1)[:, None] ** 8, 0, 1)
    ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=c, edgecolors=c, linewidths=0.2))
    lo, hi = m.bounds
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo, zoom=zoom); ax.view_init(elev, azim); ax.set_axis_off()
    ax.set_facecolor(BAKGRUND)


PAR = {"handtag": (("snirkel", "Snirkel – greppbygel 128 mm c/c"), ("marang", "Maräng – knopp Ø 37 mm")),
       "marshmallow": (("spett", "Spett – greppbygel 128 mm c/c"), ("marshmallow", "Marshmallow – knopp Ø 35 mm"))}


def main():
    for bild, par in PAR.items():
        rita_par(bild, par)


def rita_par(bild, par):
    fig = plt.figure(figsize=(15, 6), facecolor=BAKGRUND)
    for i, (namn, rubrik) in enumerate(par):
        ax = fig.add_axes([0, 0, 0.62, 1] if i == 0 else [0.6, 0, 0.4, 0.92], projection="3d")
        rita(ax, trimesh.load(os.path.join(MAPP, f"{namn}.stl")), FARGER[namn], 1.05 if i == 0 else 0.85)
        fig.text(0.31 if i == 0 else 0.8, 0.92, rubrik, fontsize=15, color="#4a3b2c", ha="center")
    plt.savefig(os.path.join(MAPP, f"{bild}.png"), dpi=110, facecolor=BAKGRUND)


if __name__ == "__main__":
    main()
