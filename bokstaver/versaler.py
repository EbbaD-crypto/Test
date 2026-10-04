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


# --- Svängar (i samma anda som ditt L och gemenernas fötter) -------------------
def entre(x, y=HI):
    """Insväng uppe till vänster som leder in i en stapel."""
    return kedja((x - 0.55, y - 0.4), ((x - 0.55, y - 0.05), (x - 0.25, y + 0.06), (x, y)))


def flick(x, y0=0.8, lut=0.0):
    """Fot som svänger ut åt höger, som på gemenerna (h, n, a)."""
    x1 = x + lut * (y0 - LO - 0.1)
    return kedja((x, y0), ((x1, LO + 0.1), (x1 + 0.15, LO - 0.04), (x1 + 0.33, LO - 0.03)),
                 ((x1 + 0.48, LO - 0.02), (x1 + 0.58, LO + 0.12), (x1 + 0.66, LO + 0.32)))


def snirkel(x, y0=0.85, lut=0.0):
    """Fot som snirklar ut åt vänster, som nedre svängen på ditt L."""
    x1 = x + lut * (y0 - LO - 0.1)
    return kedja((x, y0), ((x1, LO + 0.05), (x1 - 0.2, LO - 0.05), (x1 - 0.42, LO - 0.01)),
                 ((x1 - 0.6, LO + 0.03), (x1 - 0.7, LO + 0.22), (x1 - 0.6, LO + 0.42)))


def stapel(x, topp=True, fot="snirkel", bage=0.07):
    """Stapel med lätt sväng, valfri insväng upptill och fot (snirkel/flick/None)."""
    y0 = 0.85 if fot else LO
    ut = [linje((x, HI), (x, y0), bage)]
    if topp:
        ut.append(entre(x))
    if fot == "snirkel":
        ut.append(snirkel(x, y0))
    elif fot == "flick":
        ut.append(flick(x, y0))
    return ut


def vag(p0, p1, amp=0.08):
    """Vågigt tvärstreck (S-sväng)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0; n = np.array([-d[1], d[0]]) / np.hypot(*d)
    return bez(p0, p0 + d / 3 + n * amp * 2, p0 + 2 * d / 3 - n * amp * 2, p1)


def stam(x, bage=0.03):
    return linje((x, LO), (x, HI), bage)


# --- Versalerna (raka, före lutning) -----------------------------------------
def A():
    top = (1.35, HI + 0.02)
    return [kedja((-0.05, LO + 0.3), ((0.05, LO - 0.05), (0.3, LO - 0.04), (0.5, 0.55))),
            linje((0.5, 0.55), top, 0.1), linje(top, (2.15, 0.8), -0.06), flick(2.15, 0.8, 0.25),
            vag((0.55, 1.35), (2.15, 1.5), 0.07)]

def B():
    return stapel(0.35, fot="snirkel") + [
            kedja((0.35, HI), ((1.2, HI + 0.05), (1.8, HI - 0.1), (1.8, 2.95)),
                  ((1.8, 2.35), (1.2, 2.08), (0.35, 2.08))),
            kedja((0.35, 2.08), ((1.4, 2.1), (2.05, 1.85), (2.05, 1.2)),
                  ((2.05, 0.5), (1.4, LO - 0.03), (0.35, LO)))]

def C():
    return [kedja((1.95, 3.15), ((2.15, 2.95), (2.45, 3.15), (2.35, 3.42)),
                  ((2.2, HI + 0.12), (1.75, HI + OV), (1.4, HI + OV)),
                  ((0.6, HI + OV), (0.25, 3.0), (0.25, 2.0)),
                  ((0.25, 0.9), (0.7, LO - OV), (1.45, LO - OV)),
                  ((1.95, LO - OV), (2.35, 0.5), (2.5, 0.95)))]

def D():
    return stapel(0.35, fot="snirkel") + [
            kedja((0.35, HI), ((1.6, HI + 0.06), (2.45, 3.3), (2.45, 2.0)),
                  ((2.45, 0.7), (1.6, LO - 0.06), (0.35, LO)))]

def E():
    return stapel(0.35, fot=None) + [vag((0.35, HI), (2.15, HI + 0.12), 0.06), vag((0.35, 2.05), (1.65, 2.12), 0.05),
            kedja((0.35, LO), ((1.0, LO - 0.08), (1.75, LO + 0.0), (2.3, LO + 0.32)))]

def F():
    return stapel(0.35, fot="snirkel") + [vag((0.35, HI), (2.15, HI + 0.12), 0.06), vag((0.35, 2.0), (1.65, 2.07), 0.05)]

def G():
    return [kedja((1.95, 3.15), ((2.15, 2.95), (2.45, 3.15), (2.35, 3.42)),
                  ((2.2, HI + 0.12), (1.75, HI + OV), (1.4, HI + OV)),
                  ((0.6, HI + OV), (0.25, 3.0), (0.25, 2.0)),
                  ((0.25, 0.9), (0.7, LO - OV), (1.45, LO - OV)),
                  ((2.0, LO - OV), (2.35, 0.6), (2.35, 1.1)),
                  ((2.35, 1.4), (2.35, 1.6), (2.35, 1.8))),
            vag((1.35, 1.7), (2.65, 1.85), 0.05)]

def H():
    return stapel(0.35, fot="snirkel") + stapel(2.2, topp=False, fot="flick") + [vag((0.35, 1.95), (2.2, 2.1), 0.07)]

def I():
    return stapel(0.6, fot="flick")

def J_():
    return [kedja((1.05, HI - 0.3), ((1.15, HI + 0.05), (1.5, HI + 0.06), (1.7, HI)),
                  ((1.72, 2.8), (1.7, 1.6), (1.62, 1.05)),
                  ((1.5, 0.35), (1.1, LO - 0.06), (0.7, LO - 0.05)),
                  ((0.35, LO - 0.04), (0.12, 0.35), (0.2, 0.75)))]

def K_():
    return stapel(0.35, fot="snirkel") + [kedja((2.35, HI - 0.1), ((2.2, HI + 0.05), (1.9, HI), (1.6, 2.8)),
                                                ((1.2, 2.3), (0.8, 1.85), (0.4, 1.75))),
                                          linje((0.95, 2.2), (2.05, 0.8), 0.06), flick(2.05, 0.8, 0.3)]

def M():
    return stapel(0.35, fot="snirkel") + stapel(2.85, topp=False, fot="flick") + [
            kedja((0.35, HI), ((0.9, 2.6), (1.4, 1.4), (1.6, 1.2)), ((1.8, 1.4), (2.3, 2.6), (2.85, HI)))]

def N():
    return stapel(0.35, fot="snirkel") + [linje((0.35, HI), (2.25, LO), 0.08),
            kedja((2.25, LO), ((2.25, 1.5), (2.25, 2.8), (2.27, HI)), ((2.3, HI + 0.12), (2.55, HI + 0.1), (2.75, HI - 0.15)))]

def O():
    return [ellips(1.4, 2.0, 1.12, HI - 2.0 + OV)]

def P():
    return stapel(0.35, fot="snirkel") + [kedja((0.35, HI), ((1.4, HI + 0.06), (2.1, HI - 0.15), (2.1, 2.8)),
                                                ((2.1, 2.05), (1.4, 1.75), (0.35, 1.8)))]

def Q():
    return O() + [kedja((1.25, 0.65), ((1.65, 0.2), (2.0, -0.15), (2.4, -0.1)),
                        ((2.6, -0.07), (2.78, 0.02), (2.9, 0.18)))]

def R_():
    return P() + [linje((1.05, 1.8), (2.0, 0.8), 0.06), flick(2.0, 0.8, 0.3)]

def S():
    return [kedja((1.85, 3.15), ((2.05, 2.95), (2.4, 3.15), (2.25, 3.42)),
                  ((2.05, HI + 0.1), (1.6, HI + OV), (1.25, HI + OV)),
                  ((0.6, HI + OV), (0.3, 3.4), (0.35, 2.9)),
                  ((0.45, 2.3), (1.1, 2.15), (1.4, 2.0)),
                  ((2.0, 1.75), (2.25, 1.3), (2.15, 0.85)),
                  ((2.0, 0.35), (1.5, LO - OV), (1.05, LO - OV)),
                  ((0.55, LO - OV), (0.15, 0.3), (0.12, 0.65)),
                  ((0.1, 0.85), (0.25, 0.95), (0.4, 0.85)))]

def T():
    return [kedja((0.0, HI - 0.35), ((0.05, HI + 0.05), (0.6, HI + 0.12), (1.2, HI)),
                  ((1.8, HI - 0.1), (2.3, HI - 0.06), (2.6, HI + 0.12))),
            linje((1.35, HI), (1.35, 0.85), 0.07), snirkel(1.35, 0.85)]

def U():
    return [entre(0.35),
            kedja((0.35, HI), ((0.35, 2.4), (0.35, 1.6), (0.38, 1.2)),
                  ((0.45, 0.45), (0.85, LO - OV), (1.3, LO - OV)),
                  ((1.75, LO - OV), (2.15, 0.45), (2.2, 1.2)),
                  ((2.22, 1.6), (2.22, 2.4), (2.22, HI))),
            linje((2.22, HI), (2.22, 0.8), -0.03), flick(2.22, 0.8)]

def V():
    bott = (1.25, LO - 0.02)
    return [entre(0.3), linje((0.3, HI), bott, -0.06),
            kedja(bott, ((1.6, 1.4), (2.0, 2.9), (2.3, HI)), ((2.4, HI + 0.1), (2.6, HI + 0.08), (2.7, HI - 0.12)))]

def W():
    return [entre(0.25), linje((0.25, HI), (0.85, LO), -0.05), linje((0.85, LO), (1.55, 2.6), -0.03),
            linje((1.55, 2.6), (2.25, LO), -0.03),
            kedja((2.25, LO), ((2.55, 1.4), (2.75, 2.9), (2.95, HI)), ((3.05, HI + 0.1), (3.25, HI + 0.08), (3.35, HI - 0.12)))]

def X():
    return [entre(0.3), vag((0.3, HI), (2.0, 0.8), 0.06), flick(2.0, 0.8, 0.45),
            vag((2.3, HI), (0.3, LO), -0.06)]

def Y():
    return [entre(0.3), linje((0.3, HI), (1.25, 1.95), 0.06), linje((2.2, HI), (1.25, 1.95), -0.06),
            linje((1.25, 1.95), (1.25, 0.85), 0.04), snirkel(1.25, 0.85)]

def Z():
    return [kedja((0.05, HI - 0.35), ((0.1, HI + 0.05), (0.6, HI + 0.1), (1.2, HI)),
                  ((1.6, HI - 0.06), (1.9, HI - 0.04), (2.1, HI))),
            linje((2.1, HI), (0.3, LO), 0.08),
            kedja((0.3, LO), ((0.9, LO + 0.1), (1.5, LO - 0.1), (2.0, LO - 0.05)),
                  ((2.2, LO - 0.03), (2.35, LO + 0.1), (2.4, LO + 0.3)))]


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
        ax.set_xlim(-0.9, 4.3); ax.set_ylim(-0.4, 5.8); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(n)
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
            ax.set_xlim(-0.9, 6.6); ax.set_ylim(-2.4, 5.0); ax.set_aspect("equal"); ax.axis("off")
        for ax in axs.ravel()[len(par):]:
            ax.axis("off")
        plt.subplots_adjust(wspace=0.02, hspace=0.02)
        plt.savefig("versaler_par.png", bbox_inches="tight", facecolor="white")
    print("ok")
