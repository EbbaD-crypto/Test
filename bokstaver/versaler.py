"""Versaler A–Ö som matchar gemenerna.

Varje versal ritas som mittlinjer (kubiska Bézierkurvor) i ett rakt (0°)
koordinatsystem med versalhöjd VERSAL och sveps med gemenernas halva
linjebredd (HALV), så att linjetjocklek och runda ändar blir desamma.
Formerna följer gemenerna (O av o, C av c, S av s, V/W/X/Z av v/w/x/z, J av j,
skålar som b:s) och staplarna får samma lätta sväng som l. Sist lutas allt
LUTNING grader som resten av typsnittet.

    python3 versaler.py          # 2D-förhandsvisning (versaler_2d.png) + konturer (versaler.pkl)
"""
import pickle
import os
import sys
import numpy as np
from scipy import ndimage

VERSAL = 4.0
HALV = 0.29
LUTNING = float(os.environ.get("LUTNING", 10.0))
K = np.tan(np.radians(LUTNING))
RUT = 0.01
LO, HI = HALV, VERSAL - HALV          # mittlinjens nedre/övre läge
OV = 0.04                              # överskjutning för runda former


def bez(p0, c1, c2, p3, n=120):
    p = np.array([p0, c1, c2, p3], float)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]


def kedja(start, *seg):
    ut, p0 = [], start
    for c1, c2, p3 in seg:
        ut.append(bez(p0, c1, c2, p3)); p0 = p3
    return np.vstack(ut)


def linje(p0, p1, bage=0.0):
    """Nästan rak linje med en lätt handritad båge (bage = utbuktning i enheter)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0; n = np.array([-d[1], d[0]]) / np.hypot(*d)
    return bez(p0, p0 + d / 3 + n * bage * 1.33, p0 + 2 * d / 3 + n * bage * 1.33, p1)


def ellips(cx, cy, rx, ry, n=400):
    v = np.linspace(0, 2 * np.pi, n)
    return np.column_stack([cx + rx * np.cos(v), cy + ry * np.sin(v)])


def stam(x, bage=0.03):
    """Stapel som l: lätt sväng, rund i båda ändar."""
    return linje((x, LO), (x, HI), bage)


# --- Versalerna (raka, före lutning) -----------------------------------------
def A():
    top = (1.35, HI + 0.02)
    return [linje((0.35, LO), top, 0.04), linje(top, (2.35, LO), 0.04), linje((0.8, 1.45), (1.9, 1.45), -0.02)]

def B():
    return [stam(0.35),
            kedja((0.35, HI), ((1.2, HI + 0.05), (1.8, HI - 0.1), (1.8, 2.95)),
                  ((1.8, 2.35), (1.2, 2.08), (0.35, 2.08))),
            kedja((0.35, 2.08), ((1.4, 2.1), (2.05, 1.85), (2.05, 1.2)),
                  ((2.05, 0.5), (1.4, LO - 0.03), (0.35, LO)))]

def C():
    return [kedja((2.3, 3.3), ((2.0, HI + 0.12), (1.6, HI + OV), (1.4, HI + OV)),
                  ((0.6, HI + OV), (0.25, 3.0), (0.25, 2.0)),
                  ((0.25, 0.9), (0.7, LO - OV), (1.45, LO - OV)),
                  ((1.85, LO - OV), (2.2, 0.45), (2.35, 0.75)))]

def D():
    return [stam(0.35),
            kedja((0.35, HI), ((1.6, HI + 0.06), (2.45, 3.3), (2.45, 2.0)),
                  ((2.45, 0.7), (1.6, LO - 0.06), (0.35, LO)))]

def E():
    return [stam(0.35), linje((0.35, HI), (2.0, HI + 0.03), -0.02), linje((0.35, 2.05), (1.6, 2.05), 0.0),
            kedja((0.35, LO), ((1.0, LO - 0.04), (1.8, LO - 0.05), (2.1, LO + 0.12)))]

def F():
    return [stam(0.35), linje((0.35, HI), (2.0, HI + 0.03), -0.02), linje((0.35, 2.0), (1.6, 2.0), 0.0)]

def G():
    return [kedja((2.3, 3.3), ((2.0, HI + 0.12), (1.6, HI + OV), (1.4, HI + OV)),
                  ((0.6, HI + OV), (0.25, 3.0), (0.25, 2.0)),
                  ((0.25, 0.9), (0.7, LO - OV), (1.45, LO - OV)),
                  ((2.0, LO - OV), (2.35, 0.6), (2.35, 1.1)),
                  ((2.35, 1.4), (2.35, 1.6), (2.35, 1.75))),
            linje((1.5, 1.75), (2.35, 1.75), 0.0)]

def H():
    return [stam(0.35), stam(2.2), linje((0.35, 2.0), (2.2, 2.0), 0.02)]

def I():
    return [stam(0.4)]

def J_():
    return [kedja((1.65, HI), ((1.68, 2.8), (1.66, 1.6), (1.6, 1.05)),
                  ((1.5, 0.35), (1.1, LO - 0.05), (0.75, LO - 0.04)),
                  ((0.45, LO - 0.03), (0.3, 0.45), (0.28, 0.7)))]

def K_():
    return [stam(0.35), linje((2.15, HI), (0.45, 1.75), -0.04), linje((1.0, 2.25), (2.25, LO), 0.05)]

def M():
    return [stam(0.35), stam(2.85), kedja((0.35, HI), ((0.9, 2.6), (1.4, 1.4), (1.6, 1.2)),
                                          ((1.8, 1.4), (2.3, 2.6), (2.85, HI)))]

def N():
    return [stam(0.35), stam(2.25), linje((0.35, HI), (2.25, LO), 0.04)]

def O():
    return [ellips(1.4, 2.0, 1.12, HI - 2.0 + OV)]

def P():
    return [stam(0.35), kedja((0.35, HI), ((1.4, HI + 0.06), (2.1, HI - 0.15), (2.1, 2.8)),
                              ((2.1, 2.05), (1.4, 1.75), (0.35, 1.8)))]

def Q():
    return O() + [kedja((1.55, 0.75), ((1.85, 0.45), (2.15, 0.05), (2.55, -0.05)))]

def R_():
    return P() + [linje((1.05, 1.8), (2.2, LO), 0.05)]

def S():
    return [kedja((2.15, 3.3), ((1.95, HI + 0.08), (1.6, HI + OV), (1.25, HI + OV)),
                  ((0.6, HI + OV), (0.3, 3.4), (0.35, 2.9)),
                  ((0.45, 2.3), (1.1, 2.15), (1.4, 2.0)),
                  ((2.0, 1.75), (2.25, 1.3), (2.15, 0.85)),
                  ((2.0, 0.35), (1.5, LO - OV), (1.05, LO - OV)),
                  ((0.6, LO - OV), (0.3, 0.45), (0.22, 0.7)))]

def T():
    return [linje((0.2, HI), (2.4, HI + 0.03), -0.02), linje((1.3, HI), (1.3, LO), 0.03)]

def U():
    return [kedja((0.35, HI), ((0.35, 2.4), (0.35, 1.6), (0.38, 1.2)),
                  ((0.45, 0.45), (0.85, LO - OV), (1.3, LO - OV)),
                  ((1.75, LO - OV), (2.15, 0.45), (2.2, 1.2)),
                  ((2.22, 1.6), (2.22, 2.4), (2.22, HI)))]

def V():
    bott = (1.25, LO - 0.02)
    return [linje((0.25, HI), bott, -0.04), linje(bott, (2.25, HI), -0.04)]

def W():
    return [linje((0.2, HI), (0.85, LO), -0.03), linje((0.85, LO), (1.55, 2.6), -0.02),
            linje((1.55, 2.6), (2.25, LO), -0.02), linje((2.25, LO), (2.9, HI), -0.03)]

def X():
    return [linje((0.3, HI), (2.2, LO), 0.04), linje((2.2, HI), (0.3, LO), 0.04)]

def Y():
    return [linje((0.3, HI), (1.25, 1.95), 0.03), linje((2.2, HI), (1.25, 1.95), -0.03), linje((1.25, 1.95), (1.25, LO), 0.02)]

def Z():
    return [kedja((0.3, HI - 0.05), ((0.4, HI + 0.02), (1.4, HI), (2.1, HI))),
            linje((2.1, HI), (0.3, LO), 0.05),
            kedja((0.3, LO), ((1.0, LO - 0.05), (1.8, LO - 0.05), (2.15, LO + 0.12)))]


RING_R, RING_HALV = 0.45, 0.18   # ringens mittlinje och halva tjocklek (hål ca 0.55 i diameter)
RING_Y = VERSAL + 1.0            # ringen är en egen del, med glipa över A:s spets


def ring(cx, cy):
    return [ellips(cx, cy, RING_R, RING_R)]


VERSALER = {"A": A, "B": B, "C": C, "D": D, "E": E, "F": F, "G": G, "H": H, "I": I, "J": J_, "K": K_,
            "M": M, "N": N, "O": O, "P": P, "Q": Q, "R": R_, "S": S, "T": T, "U": U, "V": V, "W": W,
            "X": X, "Y": Y, "Z": Z}
# Å, Ä, Ö: A/O med ring eller prickar (prickarna läggs till som separata delar i 3D)
DIAKRIT = {"Å": ("A", "ring", 1.35), "Ä": ("A", "prickar", 1.35), "Ö": ("O", "prickar", 1.4)}
PRICK_Y = VERSAL + 0.55   # prickarnas/ringens mitt ovanför versalhöjden
PRICK_DX = 0.45


def mask(banor, halv=HALV, extra=None):
    """Svep banorna med cirklar (radie halv) och luta; ger mask + origo."""
    pts = np.vstack(banor)
    sh = lambda p: np.column_stack([p[:, 0] + K * p[:, 1], p[:, 1]])
    alla = sh(pts)
    x0, y0 = alla.min(0) - halv - 0.1
    x1, y1 = alla.max(0) + halv + 0.1
    W, H = int((x1 - x0) / RUT) + 1, int((y1 - y0) / RUT) + 1
    lin = np.zeros((H, W), bool)
    for b in banor:
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(b, axis=0).T))]
        t = np.arange(0, L[-1] + 1e-9, RUT / 2)
        q = sh(np.column_stack([np.interp(t, L, b[:, 0]), np.interp(t, L, b[:, 1])]))
        lin[np.round((q[:, 1] - y0) / RUT).astype(int), np.round((q[:, 0] - x0) / RUT).astype(int)] = True
    d = ndimage.distance_transform_edt(~lin) * RUT
    d = ndimage.gaussian_filter(d, 2)
    return d <= halv, x0, y0


def bygg_alla():
    ut = {}
    for n, f in VERSALER.items():
        ut[n] = mask(f())
    for n, (bas, typ, cx) in DIAKRIT.items():
        banor = VERSALER[bas]()
        ut[n] = mask(banor)  # ring och prickar är egna delar
        if typ == "ring":
            ut[n + "-ring"] = mask(ring(cx, RING_Y), halv=RING_HALV)
    return ut


# Gemener att visa bredvid versalerna (filnamn i slutlig/)
GEMENER = {"a": "a1", "b": "b", "c": "c1", "d": "d1", "e": "e1", "f": "f", "g": "g", "h": "h",
           "i": "i", "j": "j", "k": "k", "l": "l", "m": "m", "n": "n", "o": "o", "p": "p", "q": "q1",
           "r": "r", "s": "s1", "t": "t1", "u": "u", "v": "v", "w": "w1", "x": "x", "y": "y", "z": "z"}
NEDRE = {"f", "g", "j", "p", "q1", "y"}
PRICKAR = {"i": "i-prick", "j": "j-prick"}


def gemen_polygoner(mapp, fil):
    """Gemenens tvärsnitt sett framifrån, flyttad till baslinje 0 och vänsterkant 0."""
    import trimesh
    m = trimesh.load(os.path.join(mapp, fil + ".stl"))
    bas = m.bounds[0, 1] + (2.1 if fil in NEDRE else 0)
    dx = m.bounds[0, 0]
    delar = [m] + ([trimesh.load(os.path.join(mapp, PRICKAR[fil] + ".stl"))] if fil in PRICKAR else [])
    ut = []
    for d in delar:
        z0, z1 = d.bounds[0, 2], d.bounds[1, 2]
        s = d.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
        plan, _ = s.to_2D(to_2D=np.eye(4))
        for p in plan.polygons_full:
            ut.append([np.array(p.exterior.coords) - [dx, bas]] + [np.array(r.coords) - [dx, bas] for r in p.interiors])
    return ut, m.bounds[1, 0] - dx


def rita_mask(ax, m, x0, y0, dx=0):
    ax.imshow(np.ma.masked_where(~m, m), cmap="Greys", vmin=0, vmax=1, origin="lower", interpolation="bilinear",
              extent=(x0 + dx, x0 + dx + m.shape[1] * RUT, y0, y0 + m.shape[0] * RUT))


def rita_versal(ax, ut, n, dx=0, mapp=None):
    if n == "L":
        if mapp:
            for p in gemen_polygoner(mapp, "L")[0]:
                for j, r in enumerate(p):
                    ax.fill(r[:, 0] + dx, r[:, 1], color="k" if j == 0 else "white", lw=0)
        return
    rita_mask(ax, *ut[n], dx=dx)
    if n + "-ring" in ut:
        rita_mask(ax, *ut[n + "-ring"], dx=dx)
    if n in ("Ä", "Ö"):
        import matplotlib.pyplot as plt
        cx = DIAKRIT[n][2]
        for sx in (-PRICK_DX, PRICK_DX):
            ax.add_patch(plt.Circle((cx + sx + K * PRICK_Y + dx, PRICK_Y), 0.3, color="k"))


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ut = bygg_alla()
    pickle.dump(ut, open("versaler.pkl", "wb"))
    ordning = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ")
    fig, axs = plt.subplots(3, 10, figsize=(20, 10), dpi=100)
    for ax, n in zip(axs.ravel(), ordning):
        if n == "L":
            ax.text(0.5, 0.4, "L\n(ditt eget)", ha="center", va="center", transform=ax.transAxes)
        rita_versal(ax, ut, n)
        for y in (0, 2, 4):
            ax.axhline(y, color="#9ab", lw=0.5)
        ax.set_xlim(-0.3, 4.3); ax.set_ylim(-0.4, 5.8); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(n)
    axs.ravel()[-1].axis("off")
    plt.savefig("versaler_2d.png", bbox_inches="tight", facecolor="white")

    # Versal + gemen i par, med dina riktiga gemener
    if len(sys.argv) > 1:
        mapp = sys.argv[1]
        par = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        fig, axs = plt.subplots(4, 7, figsize=(21, 13), dpi=100)
        for ax, n in zip(axs.ravel(), par):
            rita_versal(ax, ut, n, mapp=mapp)
            polys, _ = gemen_polygoner(mapp, GEMENER[n.lower()])
            bredd = (ut[n][0].shape[1] * RUT + ut[n][1]) if n != "L" else gemen_polygoner(mapp, "L")[1]
            for p in polys:
                for j, r in enumerate(p):
                    ax.fill(r[:, 0] + bredd + 0.2, r[:, 1], color="k" if j == 0 else "white", lw=0)
            for y, st in ((0, "-"), (2, "-"), (4, "-"), (-2.1, "--")):
                ax.axhline(y, color="#9ab", lw=0.5, ls=st)
            ax.set_xlim(-0.3, 7.0); ax.set_ylim(-2.4, 5.0); ax.set_aspect("equal"); ax.axis("off")
        for ax in axs.ravel()[len(par):]:
            ax.axis("off")
        plt.subplots_adjust(wspace=0.02, hspace=0.02)
        plt.savefig("versaler_par.png", bbox_inches="tight", facecolor="white")
    print("ok")
