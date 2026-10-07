"""Färgbild av handtagen (snett framifrån, mjukt ljus).

    python3 visa.py               # handtag.png, marshmallow.png, twist.png
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
    """m och farg kan också vara listor (en del per färg)."""
    if not isinstance(m, list):
        m, farg = [m], [farg]
    ljus = np.array([-0.4, -0.7, 0.8]); ljus /= np.linalg.norm(ljus)
    tri, col = [], []
    for mi, fi in zip(m, farg):
        if len(mi.faces) > 30000:
            mi = mi.simplify_quadric_decimation(face_count=30000)
        n = mi.face_normals
        sken = 0.45 + 0.55 * np.clip(n @ ljus, 0, 1)
        bas = np.array(matplotlib.colors.to_rgb(fi))
        col.append(np.clip(bas[None] * sken[:, None] + 0.12 * np.clip(n @ ljus, 0, 1)[:, None] ** 8, 0, 1))
        tri.append(mi.vertices[mi.faces])
    tri, col = np.vstack(tri), np.vstack(col)
    ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors=col, linewidths=0.2))
    lo = np.min([mi.bounds[0] for mi in m], 0)
    hi = np.max([mi.bounds[1] for mi in m], 0)
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo, zoom=zoom); ax.view_init(elev, azim); ax.set_axis_off()
    ax.set_facecolor(BAKGRUND)


PAR = {"handtag": (("snirkel", "Snirkel – greppbygel 128 mm c/c"), ("marang", "Maräng – knopp Ø 37 mm")),
       "marshmallow": (("spett", "Spett – greppbygel 128 mm c/c"), ("marshmallow", "Marshmallow – knopp Ø 35 mm"))}


TWIST = {"rosa": "#f4a9c4", "gul": "#f7e6a0", "bla": "#93d3e6", "vit": "#fbf7f1", "stolpar": "#fbf7f1"}


def main():
    for bild, par in PAR.items():
        rita_par(bild, par)
    rita_twist()


def rita_twist():
    fig = plt.figure(figsize=(15, 6.5), facecolor=BAKGRUND)
    delar = [trimesh.load(os.path.join(MAPP, "twist", f"{k}.stl")) for k in TWIST]
    for i, (elev, azim, zoom) in enumerate(((28, -62, 1.05), (4, -90, 0.95))):
        ax = fig.add_axes([0.5 * i, 0, 0.5, 0.9], projection="3d")
        rita(ax, delar, list(TWIST.values()), zoom, elev, azim)
    fig.text(0.5, 0.92, "Twist – greppbygel 128 mm c/c, vriden marshmallow i fyra färger",
             fontsize=15, color="#4a3b2c", ha="center")
    plt.savefig(os.path.join(MAPP, "twist.png"), dpi=110, facecolor=BAKGRUND)


def rita_par(bild, par):
    fig = plt.figure(figsize=(15, 6), facecolor=BAKGRUND)
    for i, (namn, rubrik) in enumerate(par):
        ax = fig.add_axes([0, 0, 0.62, 1] if i == 0 else [0.6, 0, 0.4, 0.92], projection="3d")
        rita(ax, trimesh.load(os.path.join(MAPP, f"{namn}.stl")), FARGER[namn], 1.05 if i == 0 else 0.85)
        fig.text(0.31 if i == 0 else 0.8, 0.92, rubrik, fontsize=15, color="#4a3b2c", ha="center")
    plt.savefig(os.path.join(MAPP, f"{bild}.png"), dpi=110, facecolor=BAKGRUND)


if __name__ == "__main__":
    main()
