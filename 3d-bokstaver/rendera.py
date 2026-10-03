"""Renderar 3D-bokstäverna till en bild (rendering.png)."""
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

fig = plt.figure(figsize=(9, 11), dpi=130)
ax = fig.add_subplot(projection="3d")
ljus = np.array([-0.4, 0.5, 0.9]); ljus /= np.linalg.norm(ljus)
for b in "Vaer":
    m = trimesh.load(f"bokstav_{b}.stl")
    m = m.simplify_quadric_decimation(face_count=50000)
    n = m.face_normals
    ljusstyrka = 0.18 + 0.75 * np.clip(n @ ljus, 0, 1) + 0.25 * np.clip(n @ ljus, 0, 1) ** 30
    farg = np.clip(np.outer(ljusstyrka, [0.16, 0.16, 0.19]) * 2.2, 0, 1)
    pc = Poly3DCollection(m.triangles, facecolors=farg, edgecolor="none")
    ax.add_collection3d(pc)
ax.set_xlim(0, 210); ax.set_ylim(0, 297); ax.set_zlim(-60, 60)
ax.set_box_aspect((210, 297, 120))
ax.view_init(elev=55, azim=-95)
ax.set_axis_off()
fig.patch.set_facecolor("#f2efe9"); ax.set_facecolor("#f2efe9")
plt.savefig("rendering.png", bbox_inches="tight", facecolor=fig.get_facecolor())
