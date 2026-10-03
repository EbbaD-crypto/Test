"""Renderar 3D-bokstäverna: framifrån (rendering.png) och från sidan (rendering_sida.png)."""
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

FARGER = {"V": (0.62, 0.66, 0.90), "a": (0.93, 0.47, 0.42), "e": (0.98, 0.86, 0.48), "r": (0.56, 0.78, 0.55)}
meshes = {b: trimesh.load(f"bokstav_{b}.stl").simplify_quadric_decimation(face_count=40000) for b in "Vaer"}

def rendera(fil, elev, azim, storlek):
    fig = plt.figure(figsize=storlek, dpi=130)
    ax = fig.add_subplot(projection="3d")
    ljus = np.array([-0.4, 0.5, 0.9]); ljus /= np.linalg.norm(ljus)
    for b, m in meshes.items():
        d = m.face_normals @ ljus
        ljusstyrka = 0.45 + 0.55 * np.clip(d, 0, 1)
        glans = 0.5 * np.clip(d, 0, 1) ** 40
        farg = np.clip(np.outer(ljusstyrka, FARGER[b]) + glans[:, None], 0, 1)
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=farg, edgecolor="none"))
    ax.set_xlim(0, 210); ax.set_ylim(0, 297); ax.set_zlim(-60, 60)
    ax.set_box_aspect((210, 297, 120))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.patch.set_facecolor("#f2efe9"); ax.set_facecolor("#f2efe9")
    plt.savefig(fil, bbox_inches="tight", facecolor=fig.get_facecolor())

rendera("rendering.png", 55, -95, (9, 11))
rendera("rendering_sida.png", 12, -60, (11, 8))
