"""Renderar 3D-bokstäverna: framifrån (rendering.png) och från sidan (rendering_sida.png).

    python3 rendera.py                              # Vaer i den här mappen
    python3 rendera.py --mapp abcd --namn a1 a2 b c d
"""
import argparse
import os
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

arg = argparse.ArgumentParser()
arg.add_argument("--mapp", default=".")
arg.add_argument("--namn", nargs="+", default=["V", "a", "e", "r"])
argv = arg.parse_args()

PALETT = [(0.62, 0.66, 0.90), (0.93, 0.47, 0.42), (0.98, 0.86, 0.48), (0.56, 0.78, 0.55), (0.90, 0.62, 0.78)]
meshes = {b: trimesh.load(os.path.join(argv.mapp, f"bokstav_{b}.stl")).simplify_quadric_decimation(face_count=40000)
          for b in argv.namn}
(x0, y0, _), (x1, y1, _) = np.array([m.bounds for m in meshes.values()]).min(0)[0], np.array([m.bounds for m in meshes.values()]).max(0)[1]
x0, y0, x1, y1 = x0 - 5, y0 - 5, x1 + 5, y1 + 5


def rendera(fil, elev, azim, bredd):
    hojd = bredd * (y1 - y0) / (x1 - x0) + 2
    fig = plt.figure(figsize=(bredd, hojd), dpi=130)
    ax = fig.add_subplot(projection="3d")
    ljus = np.array([-0.4, 0.5, 0.9]); ljus /= np.linalg.norm(ljus)
    for i, m in enumerate(meshes.values()):
        d = m.face_normals @ ljus
        ljusstyrka = 0.45 + 0.55 * np.clip(d, 0, 1)
        glans = 0.5 * np.clip(d, 0, 1) ** 40
        farg = np.clip(np.outer(ljusstyrka, PALETT[i % len(PALETT)]) + glans[:, None], 0, 1)
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=farg, edgecolor="none"))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(-46, 74)
    ax.set_box_aspect((x1 - x0, y1 - y0, 120))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.patch.set_facecolor("#f2efe9"); ax.set_facecolor("#f2efe9")
    plt.savefig(os.path.join(argv.mapp, fil), bbox_inches="tight", facecolor=fig.get_facecolor())


rendera("rendering.png", 55, -95, 9 if x1 - x0 < 400 else 16)
rendera("rendering_sida.png", 8, -75, 11 if x1 - x0 < 400 else 16)
