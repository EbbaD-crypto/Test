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
    """Liten, diskret insväng upptill."""
    return kedja((x - 0.38, y - 0.1), ((x - 0.3, y + 0.04), (x - 0.12, y + 0.04), (x, y)))


def flick(x, y0=0.8, lut=0.0):
    """Samma korta, mjuka fot åt höger som på A, H och M."""
    return svans(x, y0, lut)


def svans(x, y0=0.8, lut=0.0):
    """Liten, mjuk avslutning åt höger, som slutet på ditt lilla a."""
    x1 = x + lut * (y0 - LO - 0.1)
    return kedja((x, y0), ((x1, LO + 0.06), (x1 + 0.08, LO - 0.03), (x1 + 0.2, LO - 0.02)),
                 ((x1 + 0.28, LO - 0.01), (x1 + 0.34, LO + 0.02), (x1 + 0.38, LO + 0.07)))


def kort_snirkel(x, y0=0.8):
    """Liten, mjuk avslutning åt vänster (spegling av svans)."""
    return kedja((x, y0), ((x, LO + 0.06), (x - 0.08, LO - 0.03), (x - 0.2, LO - 0.02)),
                 ((x - 0.28, LO - 0.01), (x - 0.34, LO + 0.02), (x - 0.38, LO + 0.07)))


def kort_entre(x, y=HI):
    """Kort, mjuk insväng upptill."""
    return kedja((x - 0.42, y - 0.12), ((x - 0.32, y + 0.05), (x - 0.13, y + 0.05), (x, y)))


def snirkel(x, y0=0.8, lut=0.0):
    """Samma korta, mjuka fot åt vänster som på H och M."""
    return kort_snirkel(x, y0)


def stapel(x, topp=True, fot="snirkel", bage=0.1):
    """Stapel med lätt böj (som H:s vänstra), insväng upptill och kort fot."""
    y0 = 0.8 if fot else LO
    ut = [kedja((x, HI), ((x + bage, 2.7), (x + bage, 1.5), (x, y0)))]
    if topp:
        ut.append(entre(x))
    if fot == "snirkel":
        ut.append(kort_snirkel(x, y0))
    elif fot == "flick":
        ut.append(svans(x, y0))
    return ut


def vag(p0, p1, amp=0.08):
    """Vågigt tvärstreck (S-sväng)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0; n = np.array([-d[1], d[0]]) / np.hypot(*d)
    return bez(p0, p0 + d / 3 + n * amp * 2, p0 + 2 * d / 3 - n * amp * 2, p1)


def stam(x, bage=0.03):
    return linje((x, LO), (x, HI), bage)


def bage_ellips(cx, cy, rx, ry, v0, v1, n=300):
    v = np.radians(np.linspace(v0, v1, n))
    return np.column_stack([cx + rx * np.cos(v), cy + ry * np.sin(v)])


# --- Versalerna (raka, före lutning) -----------------------------------------
def A():
    ben = kedja((-0.02, LO + 0.1), ((0.05, LO - 0.04), (0.3, LO - 0.04), (0.5, 0.55)),
                ((0.78, 1.7), (0.95, HI + 0.02), (1.42, HI + 0.02)),
                ((1.9, HI + 0.02), (2.2, 1.9), (2.3, 0.8)))
    # tvärstrecket slutar precis i benen (inga knölar utanför)
    y = 1.6
    i = np.where(np.diff(np.sign(ben[:, 1] - y)))[0]
    x0, x1 = ben[i[0], 0], ben[i[-1], 0]
    return [ben, svans(2.3, 0.8, 0.05), vag((x0, y), (x1, y + 0.08), 0.03)]


def B():
    return stapel(0.35, fot="snirkel") + [
            kedja((0.35, HI), ((1.3, HI + 0.12), (1.95, HI - 0.05), (1.9, 2.95)),
                  ((1.85, 2.35), (1.2, 2.08), (0.5, 2.08))),
            kedja((0.5, 2.08), ((1.5, 2.1), (2.2, 1.85), (2.15, 1.15)),
                  ((2.1, 0.45), (1.4, LO - 0.08), (0.35, LO)))]

def C():
    return [kedja((2.45, 3.05), ((2.4, 3.4), (1.95, HI + OV), (1.4, HI + OV)),
                  ((0.6, HI + OV), (0.25, 3.0), (0.25, 2.0)),
                  ((0.25, 0.9), (0.7, LO - OV), (1.45, LO - OV)),
                  ((1.95, LO - OV), (2.35, 0.4), (2.45, 0.75)))]

def D():
    return stapel(0.35, fot="snirkel") + [
            kedja((0.35, HI), ((1.8, HI + 0.12), (2.6, 3.3), (2.6, 2.0)),
                  ((2.6, 0.6), (1.7, LO - 0.1), (0.35, LO)))]

def E():
    """E som en spegelvänd trea (Ɛ): två runda bågar som möts i mitten."""
    return [kedja((2.2, 3.25), ((2.05, HI + 0.05), (1.65, HI + OV), (1.3, HI + OV)),
                  ((0.75, HI + OV), (0.45, 3.3), (0.48, 2.85)),
                  ((0.52, 2.4), (1.0, 2.12), (1.65, 2.12))),
            kedja((1.65, 2.12), ((0.85, 2.0), (0.25, 1.7), (0.25, 1.1)),
                  ((0.25, 0.45), (0.75, LO - OV), (1.35, LO - OV)),
                  ((1.85, LO - OV), (2.25, 0.35), (2.35, 0.7)))]


def F():
    return stapel(0.55, topp=False, fot="snirkel") + [
            kedja((0.1, HI - 0.1), ((0.15, HI + 0.06), (0.6, HI + 0.12), (1.2, HI)),
                  ((1.8, HI - 0.1), (2.3, HI - 0.06), (2.6, HI + 0.12))),
            vag((0.3, 1.95), (1.75, 2.1), 0.07)]

def G():
    return [kedja((2.45, 3.05), ((2.4, 3.4), (1.95, HI + OV), (1.4, HI + OV)),
                  ((0.6, HI + OV), (0.25, 3.0), (0.25, 2.0)),
                  ((0.25, 0.9), (0.7, LO - OV), (1.45, LO - OV)),
                  ((2.0, LO - OV), (2.35, 0.6), (2.35, 1.1)),
                  ((2.35, 1.4), (2.35, 1.6), (2.35, 1.8))),
            vag((1.35, 1.7), (2.65, 1.85), 0.05)]

def H_enkel():
    v, h = 0.35, 2.45
    return [kort_entre(v), linje((v, HI), (v, 0.8), 0.08), kort_snirkel(v, 0.8),
            linje((h, HI), (h, 0.8), 0.08), svans(h, 0.8),
            vag((v + 0.1, 1.98), (h + 0.06, 2.06), 0.04)]



def H():
    """Skrivstils-H (din skiss): vänster stapel slutar i en ögla som blir ett
    stigande tvärstreck; höger stapel svänger ut åt höger nedtill."""
    vanster = kedja((0.17, HI - 0.1), ((0.25, HI + 0.04), (0.43, HI + 0.04), (0.55, HI)),
                    ((0.85, 2.7), (0.78, 1.3), (0.52, 0.7)),
                    ((0.46, 0.3), (0.2, LO - 0.08), (-0.15, LO - 0.06)),
                    ((-0.62, LO - 0.04), (-0.95, 0.5), (-0.78, 1.0)),
                    ((-0.62, 1.48), (-0.05, 1.6), (0.5, 1.64)),
                    ((1.1, 1.72), (1.8, 1.95), (2.42, 2.2)))
    hoger = kedja((2.55, HI), ((2.38, 2.8), (2.35, 1.5), (2.42, 0.85)),
                  ((2.44, LO + 0.06), (2.52, LO - 0.03), (2.64, LO - 0.02)),
                  ((2.72, LO - 0.01), (2.78, LO + 0.02), (2.82, LO + 0.07)))
    return [vanster, hoger]

def I():
    return stapel(0.6, fot="flick")

def J_():
    """J med rund båge nedtill (halvcirkel) och liten avslutning."""
    topp = kedja((1.37, HI - 0.08), ((1.43, HI + 0.05), (1.6, HI + 0.05), (1.75, HI)),
                 ((1.85, 2.8), (1.72, 1.8), (1.7, 1.0)))
    return [topp, bage_ellips(1.08, 1.0, 0.62, 0.66, 0, -168)]


def K_():
    return stapel(0.35, fot="snirkel") + [
            kedja((2.6, HI - 0.02), ((2.3, HI + 0.12), (1.85, 3.4), (1.45, 2.65)),
                  ((1.15, 2.1), (0.75, 1.88), (0.4, 1.85))),
            kedja((0.95, 1.95), ((1.45, 2.0), (1.85, 1.45), (2.05, 0.8))), flick(2.05, 0.8, 0.2)]

def L_fot(xb, lut, yb=1.0):
    """Ny, balanserad fot till ditt L (rak, före lutning). Börjar i stammens
    mitt (xb, yb) och fortsätter i stammens riktning (lut = dx/dy)."""
    x08 = xb - lut * (yb - 0.8)
    stam = kedja((xb, yb), ((xb - lut * 0.1, yb - 0.1), (x08 - lut * 0.35, 0.45), (x08 - 0.2, LO + 0.03)),
                 ((x08 - 0.27, LO + 0.05), (x08 - 0.3, LO + 0.07), (x08 - 0.32, LO + 0.08)))
    fot = kedja((x08 - 0.32, LO + 0.08), ((x08 - 0.05, LO - 0.06), (x08 + 0.75, LO - 0.06), (x08 + 1.3, LO - 0.03)),
                ((x08 + 1.5, LO - 0.02), (x08 + 1.62, LO + 0.04), (x08 + 1.7, LO + 0.13)))
    return np.vstack([stam, fot])


def L_mask(mapp, skarv=1.3):
    """Ditt original-L ovanför skarv; nedanför ritas din stam vidare (samma mittlinje
    och tjocklek) ner i en ny, balanserad fot. Samma rutnät som versalerna."""
    from PIL import Image, ImageDraw
    polys, _ = gemen_polygoner(mapp, "L")
    alla = np.vstack([r for p in polys for r in p])
    x0, y0 = alla.min(0) - 0.6
    x1, y1 = alla.max(0) + 0.6
    W, H = int((x1 - x0) / RUT) + 1, int((y1 - y0) / RUT) + 1
    bild = Image.new("1", (W, H), 0); d = ImageDraw.Draw(bild)
    pix = lambda r: [((x - x0) / RUT, (y - y0) / RUT) for x, y in r]
    for p in polys:
        d.polygon(pix(p[0]), fill=1)
        for hal in p[1:]:
            d.polygon(pix(hal), fill=0)
    orig = np.array(bild, bool)
    # stammens mitt och halva bredd (vinkelrätt) för y i [skarv, skarv + 0.6], rak (före lutning)
    ys = np.arange(skarv, skarv + 1.3, 0.02)
    c, w = [], []
    for y in ys:
        kol = np.where(orig[int((y - y0) / RUT)])[0]
        c.append(x0 + kol.mean() * RUT - K * y); w.append((kol[-1] - kol[0]) * RUT / 2)
    from scipy.ndimage import gaussian_filter1d
    yb = skarv + 0.15
    pc = np.polyfit(ys, c, 2)
    lut = np.polyval(np.polyder(pc), yb)
    xb = np.polyval(pc, yb)
    halv0 = 0.97 * np.interp(yb, ys, gaussian_filter1d(np.array(w), 3)) * np.cos(np.arctan(K + lut))
    # överlapp: följ din stams mittlinje och tjocklek från y = 2.3 ner till yb
    from scipy.ndimage import gaussian_filter1d
    cs, ws = gaussian_filter1d(np.array(c), 3), gaussian_filter1d(np.array(w), 3)
    yo = np.linspace(2.3, yb, 60)[:-1]
    over = np.column_stack([np.interp(yo, ys, cs), yo])
    r_over = np.interp(yo, ys, ws) * np.cos(np.arctan(K + np.interp(yo, ys, np.gradient(cs, ys))))
    r_over *= 0.97   # ligger precis innanför din stam där de överlappar
    fot = L_fot(xb, lut, yb)
    Lf = np.r_[0, np.cumsum(np.hypot(*np.diff(fot, axis=0).T))]
    r_fot = halv0 + (HALV - halv0) * np.clip(Lf / 1.2, 0, 1)
    bana = np.vstack([over, fot]); rad = np.r_[r_over, r_fot]
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(bana, axis=0).T))]
    t = np.arange(0, L[-1], RUT / 2)
    q = np.column_stack([np.interp(t, L, bana[:, 0]), np.interp(t, L, bana[:, 1])])
    r = np.interp(t, L, rad)
    fot = Image.new("1", (W, H), 0); d = ImageDraw.Draw(fot)
    for (x, y), rr in zip(q, r):
        X, Y = (x + K * y - x0) / RUT, (y - y0) / RUT; R = rr / RUT
        d.ellipse([X - R, Y - R, X + R, Y + R], fill=1)
    fot = np.array(fot, bool)
    orig[: int((skarv + 0.05 - y0) / RUT)] = False
    sdf = lambda b: (ndimage.distance_transform_edt(~b) - ndimage.distance_transform_edt(b)) * RUT
    d1, d2, k = sdf(orig), sdf(fot), 0.1
    h = np.clip(0.5 + 0.5 * (d2 - d1) / k, 0, 1)
    dd = d2 * (1 - h) + d1 * h - k * h * (1 - h)
    return ndimage.gaussian_filter((dd < 0).astype(float), 2) > 0.5, x0, y0


def M():
    """M i samma anda som skrivstils-H: insvängen går över toppen och direkt ner
    i diagonalen; vänster stapel hänger ner från toppen med en lätt böj."""
    v, h = 0.55, 3.1
    over = kedja((v - 0.38, HI - 0.1), ((v - 0.3, HI + 0.04), (v - 0.12, HI + 0.04), (v, HI)),
                 ((0.95, HI - 0.02), (1.45, 1.9), (1.75, 1.2)),
                 ((2.05, 1.9), (2.45, HI - 0.02), (2.8, HI)),
                 ((3.0, HI + 0.05), (3.2, 3.2), (h, 0.8)))
    stam = kedja((v, HI), ((0.52, 2.7), (0.62, 1.5), (0.52, 0.8)))
    return [over, stam, kort_snirkel(0.55, 0.8), svans(h, 0.8)]
def N():
    """N som M: insvängen går över toppen och ner i diagonalen."""
    v, h = 0.55, 2.5
    over = kedja((v - 0.38, HI - 0.1), ((v - 0.3, HI + 0.04), (v - 0.12, HI + 0.04), (v, HI)),
                 ((0.95, HI - 0.02), (1.7, 1.2), (2.05, LO + 0.05)),
                 ((2.25, LO - 0.06), (h, 0.4), (h, 1.2)),
                 ((h, 2.4), (h + 0.03, HI + 0.04), (h + 0.2, HI + 0.04)),
                 ((h + 0.28, HI + 0.03), (h + 0.33, HI - 0.0), (h + 0.36, HI - 0.05)))
    stam = kedja((v, HI), ((0.52, 2.7), (0.62, 1.5), (0.52, 0.8)))
    return [over, stam, kort_snirkel(0.52, 0.8)]


def O():
    return [ellips(1.4, 2.0, 1.12, HI - 2.0 + OV)]

def P():
    return stapel(0.35, fot="snirkel") + [kedja((0.35, HI), ((1.4, HI + 0.06), (2.1, HI - 0.15), (2.1, 2.8)),
                                                ((2.1, 2.05), (1.4, 1.75), (0.35, 1.8)))]

def Q():
    return O() + [kedja((1.25, 0.65), ((1.65, 0.2), (2.0, -0.15), (2.4, -0.1)),
                        ((2.6, -0.07), (2.72, -0.05), (2.82, 0.0)))]

def R_():
    return P() + [linje((1.05, 1.8), (2.0, 0.8), 0.06), flick(2.0, 0.8, 0.3)]

def S():
    """Helrund S: två ellipsbågar som möts mjukt i mitten, inga raka partier."""
    mitt = 2.06
    ry1 = (HI + 0.02 - mitt) / 2; ry2 = (mitt - (LO - OV)) / 2
    topp = bage_ellips(1.3, mitt + ry1, 0.8, ry1, 20, 270)
    botten = bage_ellips(1.3, mitt - ry2, 0.92, ry2, 90, -155)
    return [np.vstack([topp, botten])]


def T():
    return [kedja((0.15, HI - 0.08), ((0.2, HI + 0.06), (0.6, HI + 0.12), (1.2, HI + 0.02)),
                  ((1.6, HI - 0.04), (1.9, HI - 0.03), (2.1, HI + 0.04))),
            linje((1.3, HI), (1.3, 0.85), 0.1), snirkel(1.3, 0.85)]


def U():
    return [entre(0.35),
            kedja((0.35, HI), ((0.35, 2.4), (0.35, 1.6), (0.38, 1.2)),
                  ((0.45, 0.45), (0.85, LO - OV), (1.3, LO - OV)),
                  ((1.75, LO - OV), (2.15, 0.45), (2.2, 1.2)),
                  ((2.22, 1.6), (2.22, 2.4), (2.22, HI))),
            linje((2.22, HI), (2.22, 0.8), -0.03), flick(2.22, 0.8)]

def V():
    return [entre(0.3),
            kedja((0.3, HI), ((0.45, 2.3), (0.85, LO - 0.08), (1.2, LO)),
                  ((1.55, LO + 0.1), (2.0, 2.5), (2.3, HI)),
                  ((2.36, HI + 0.07), (2.5, HI + 0.07), (2.6, HI + 0.0)))]

def W():
    return [entre(0.25),
            kedja((0.25, HI), ((0.35, 2.0), (0.55, LO - 0.08), (0.85, LO)),
                  ((1.1, LO + 0.05), (1.38, 2.3), (1.55, 2.45)),
                  ((1.72, 2.3), (1.95, LO - 0.05), (2.25, LO)),
                  ((2.55, LO + 0.08), (2.8, 2.6), (2.95, HI)),
                  ((3.01, HI + 0.07), (3.15, HI + 0.07), (3.25, HI + 0.0)))]

def X():
    return [entre(0.3), vag((0.3, HI), (2.0, 0.8), 0.06), flick(2.0, 0.8, 0.45),
            vag((2.3, HI), (0.3, LO), -0.06)]

def Y():
    return [entre(0.3),
            kedja((0.3, HI), ((0.35, 2.5), (0.8, 1.95), (1.25, 1.95))),
            kedja((2.25, HI), ((2.2, 2.5), (1.6, 2.0), (1.28, 1.6)),
                  ((1.2, 1.3), (1.25, 1.0), (1.25, 0.85))),
            snirkel(1.25, 0.85)]

def Z():
    return [kedja((0.12, HI - 0.1), ((0.18, HI + 0.06), (0.6, HI + 0.12), (1.2, HI)),
                  ((1.7, HI - 0.08), (2.25, HI + 0.02), (2.12, HI - 0.3)),
                  ((1.6, 2.6), (0.9, 1.3), (0.45, 0.55)),
                  ((0.3, 0.28), (0.4, LO - 0.02), (0.72, LO)),
                  ((1.3, LO + 0.1), (1.7, LO - 0.1), (2.05, LO - 0.05)),
                  ((2.22, LO - 0.03), (2.3, LO + 0.0), (2.35, LO + 0.06)))]

PRICK_Y = VERSAL + 0.62   # prickarnas och ringens mitt ovanför versalhöjden
PRICK_R = 0.42            # ytterradie: prickar och ring är lika stora (samma form i produktionen)
PRICK_DX = 0.55
RING_HALV = 0.12                 # ringens halva tjocklek
RING_R = PRICK_R - RING_HALV     # ringens mittlinje, så att ytterkanten = prickens
RING_Y = PRICK_Y                 # samma höjd som prickarna


def ring(cx, cy):
    return [ellips(cx, cy, RING_R, RING_R)]


VERSALER = {"A": A, "B": B, "C": C, "D": D, "E": E, "F": F, "G": G, "H": H, "I": I, "J": J_, "K": K_,
            "M": M, "N": N, "O": O, "P": P, "Q": Q, "R": R_, "S": S, "T": T, "U": U, "V": V, "W": W,
            "X": X, "Y": Y, "Z": Z}
# Å, Ä, Ö: A/O med ring eller prickar (prickarna läggs till som separata delar i 3D)
DIAKRIT = {"Å": ("A", "ring", 1.35), "Ä": ("A", "prickar", 1.35), "Ö": ("O", "prickar", 1.4)}


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


def bygg_alla(mapp=None):
    ut = {}
    if mapp:
        ut["L"] = L_mask(mapp)
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
    if n == "L" and "L" in ut:
        rita_mask(ax, *ut["L"], dx=dx)
        return
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
            ax.add_patch(plt.Circle((cx + sx + K * PRICK_Y + dx, PRICK_Y), PRICK_R, color="k"))


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ut = bygg_alla(sys.argv[1] if len(sys.argv) > 1 else None)
    pickle.dump(ut, open("versaler.pkl", "wb"))
    ordning = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ")
    fig, axs = plt.subplots(3, 10, figsize=(20, 10), dpi=100)
    for ax, n in zip(axs.ravel(), ordning):
        if n == "L":
            pass
        rita_versal(ax, ut, n)
        for y in (0, 2, 4):
            ax.axhline(y, color="#9ab", lw=0.5)
        ax.set_xlim(-0.9, 4.6); ax.set_ylim(-0.4, 5.8); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(n)
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
            bredd = (ut[n][0].shape[1] * RUT + ut[n][1]) 
            for p in polys:
                for j, r in enumerate(p):
                    ax.fill(r[:, 0] + bredd + 0.2, r[:, 1], color="k" if j == 0 else "white", lw=0)
            for y, st in ((0, "-"), (2, "-"), (4, "-"), (-2.1, "--")):
                ax.axhline(y, color="#9ab", lw=0.5, ls=st)
            ax.set_xlim(-0.9, 7.3); ax.set_ylim(-2.4, 5.0); ax.set_aspect("equal"); ax.axis("off")
        for ax in axs.ravel()[len(par):]:
            ax.axis("off")
        plt.subplots_adjust(wspace=0.02, hspace=0.02)
        plt.savefig("versaler_par.png", bbox_inches="tight", facecolor="white")
    print("ok")
