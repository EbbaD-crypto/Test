"""Jämför sätt att flytta h:ets toppknorr till vänstra benets fot.

1. Rak spegling: toppen (med en bit stapel) speglas upp-och-ner och sätts på benet.
2. Nuvarande: bara kulan (knorren) speglas rakt, benet växer ner i den.

    python3 h_knorr_varianter.py <mapp med slutlig/> ut.png
"""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import box
from shapely.ops import unary_union, transform

import h_knorr as H

FRAN = 3.0      # toppen ovanför denna höjd flyttas


def rak_spegling(hp, x0, topp_y):
    """Variant 1: spegla toppen upp-och-ner kring en vågrät linje, placera på benet."""
    bit = hp.intersection(box(x0 - 1, FRAN, x0 + H.BEN_X + 0.6, 5))
    hojd = topp_y - FRAN
    st = H.kanter(hp, x0, FRAN + 0.02); bn = H.kanter(hp, x0, hojd - 0.05)
    dx = bn.mean() - st.mean()
    knorr = transform(lambda x, y: (np.asarray(x) + dx, hojd - (np.asarray(y) - FRAN) - 0.03), bit)
    rest = hp.difference(box(x0 - 1, -1, x0 + H.BEN_X, hojd - 0.05))
    return unary_union([rest, knorr]).buffer(0.01).buffer(-0.01)


def main():
    mapp, ut = sys.argv[1:3]
    h = trimesh.load(f"{mapp}/h.stl"); z0, z1 = h.bounds[:, 2]
    s = h.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4)); hp = unary_union(list(p.polygons_full))
    x0 = h.bounds[0, 0]; topp_y = hp.bounds[3]
    varianter = [("1. toppen + en bit stapel speglad\n(stapelbiten lutar åt fel håll → knyck)", rak_spegling(hp, x0, topp_y)),
                 ("2. bara knorren speglad\n(nuvarande)", H.speglad_knorr(hp, x0, 0.0))]
    fig, axs = plt.subplots(1, 2, figsize=(10, 6))
    for ax, (t, g) in zip(axs, varianter):
        for q in getattr(g, "geoms", [g]):
            x, y = q.exterior.xy; ax.fill(np.array(x) - x0, y, color="k", lw=0)
            for i in q.interiors:
                x, y = i.xy; ax.fill(np.array(x) - x0, y, color="white", lw=0)
        for y in (0, 2, 4):
            ax.axhline(y, color="#4a7be0", lw=0.6)
        ax.set_xlim(-0.5, 2.6); ax.set_ylim(-0.3, 4.3); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t)
    plt.savefig(ut, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
