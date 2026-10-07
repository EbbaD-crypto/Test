"""Skuggad bild uppifrån (lite snett ljus) av en eller flera STL-filer, för att
granska 3D-formen.

    python3 rendera.py ut.png fil1.stl fil2.stl ...
"""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def skugga(m, rut=0.01):
    x0, y0 = m.bounds[0, :2] - 0.1
    x1, y1 = m.bounds[1, :2] + 0.1
    xs, ys = np.arange(x0, x1, rut), np.arange(y0, y1, rut)
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, m.bounds[1, 2] + 1)])
    d = np.tile([0, 0, -1.0], (X.size, 1))
    loc, ri, ti = m.ray.intersects_location(o, d, multiple_hits=False)
    bild = np.ones(X.size)
    ljus = np.array([-0.5, 0.6, 1.0]); ljus /= np.linalg.norm(ljus)
    n = m.face_normals[ti]
    bild[ri] = 0.25 + 0.75 * np.clip(n @ ljus, 0, 1)
    return bild.reshape(X.shape), (x0, x1, y0, y1)


def main():
    ut, filer = sys.argv[1], sys.argv[2:]
    fig, axs = plt.subplots(1, len(filer), figsize=(4 * len(filer), 5), squeeze=False)
    for ax, f in zip(axs[0], filer):
        m = trimesh.load(f)
        b, ext = skugga(m)
        ax.imshow(b, cmap="gray", origin="lower", extent=ext, vmin=0, vmax=1)
        ax.set_aspect("equal"); ax.axis("off"); ax.set_title(f.split("/")[-1], fontsize=9)
    plt.savefig(ut, bbox_inches="tight", facecolor="white", dpi=110)


if __name__ == "__main__":
    main()
