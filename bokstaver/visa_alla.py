"""Visar alla bokstäver (versaler och gemener) i 3D, skuggade, på gemensam
baslinje – så som de ser ut i de senaste filerna.

    python3 visa_alla.py <mapp med slutlig/> <leveransmapp> ut.png
"""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kolla_hojder import BAS

RADER = ["ABCDEFGHIJKLMNO", "PQRSTUVWXYZÅÄÖ", "abcdefghijklmn", "opqrstuvwxyzåäö"]
GEMEN_FIL = {"a": "a1", "c": "c1", "d": "d1", "e": "e1", "q": "q1", "s": "s1", "t": "t1", "w": "w1"}
VERSAL_FIL = {"Å": "AA", "Ä": "AE", "Ö": "OE"}
MELLAN = 0.7
RUT = 0.012


def delar(c, slut, lev):
    """Meshar (redan i rätt läge sinsemellan) + baslinje för ett tecken."""
    if c.isupper():
        namn = "versal_" + VERSAL_FIL.get(c, c)
        filer = [f"{lev}/{namn}.stl"] + [f"{lev}/{namn}_prick{i}.stl" for i in (1, 2)]
        bas = -20.10 if c == "L" else 0.0
    elif c in "åäö":
        namn = {"å": "gemen_aa", "ä": "gemen_ae", "ö": "gemen_oe"}[c]
        filer = [f"{lev}/{namn}.stl"] + [f"{lev}/{namn}_prick{i}.stl" for i in (1, 2)]
        bas = -20.0 if c == "ö" else -10.0
    elif c == "h":
        filer, bas = [f"{lev}/h.stl"], BAS["h"]
    elif c in "ij":
        filer = [f"{slut}/{c}.stl", f"{slut}/{c}-prick.stl"]
        bas = BAS[c]
    else:
        g = GEMEN_FIL.get(c, c)
        filer = [f"{slut}/{g}.stl"]
        m = trimesh.load(filer[0]); bas = BAS.get(g, m.bounds[0, 1])
    import os
    ms = [trimesh.load(f) for f in filer if os.path.exists(f)]
    return ms, bas


def rad_mesh(text, slut, lev):
    x, allt = 0.0, []
    for c in text:
        ms, bas = delar(c, slut, lev)
        mn = min(m.bounds[0, 0] for m in ms); mx = max(m.bounds[1, 0] for m in ms)
        for m in ms:
            m = m.copy()
            m.apply_translation([x - mn, -bas, -m.bounds[0, 2] if m is ms[0] else 0])
            allt.append(m)
        # prickar ska ha samma z-läge som bokstaven
        z0 = ms[0].bounds[0, 2]
        for m in allt[-len(ms) + 1:] if len(ms) > 1 else []:
            m.apply_translation([0, 0, -z0])
        x += mx - mn + MELLAN
    return trimesh.util.concatenate(allt), x


def skugga(m, x1):
    xs, ys = np.arange(-0.3, x1, RUT), np.arange(-2.4, 5.4, RUT)
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, m.bounds[1, 2] + 1)])
    loc, ri, ti = m.ray.intersects_location(o, np.tile([0, 0, -1.0], (X.size, 1)), multiple_hits=False)
    b = np.ones(X.size)
    ljus = np.array([-0.5, 0.6, 1.0]); ljus /= np.linalg.norm(ljus)
    b[ri] = 0.25 + 0.75 * np.clip(m.face_normals[ti] @ ljus, 0, 1)
    return b.reshape(X.shape), (xs[0], xs[-1], ys[0], ys[-1])


def main():
    slut, lev, ut = sys.argv[1:4]
    bilder = [skugga(*rad_mesh(r, slut, lev)) for r in RADER]
    bredd = max(e[1] for _, e in bilder)
    fig, axs = plt.subplots(len(RADER), 1, figsize=(26, 3.6 * len(RADER)))
    for ax, (b, ext) in zip(axs, bilder):
        ax.imshow(b, cmap="gray", origin="lower", extent=ext, vmin=0, vmax=1)
        ax.set_xlim(-0.3, bredd); ax.set_aspect("equal"); ax.axis("off")
    plt.subplots_adjust(hspace=0.02)
    plt.savefig(ut, bbox_inches="tight", facecolor="white", dpi=90)


if __name__ == "__main__":
    main()
