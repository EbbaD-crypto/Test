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


OGLOR = os.environ.get("OGLOR", "nej") == "ja"  # skrivstilsögla nere till vänster på alla staplar (avstängd)


def ogla(x, y0=0.8):
    """Skrivstilsögla som på H: stapeln går ner, svänger runt åt vänster i en
    rund ögla och tillbaka upp genom stapeln, där den slutar."""
    return kedja((x, y0), ((x - 0.04, 0.35), (x - 0.32, LO - 0.08), (x - 0.67, LO - 0.06)),
                 ((x - 1.14, LO - 0.04), (x - 1.47, 0.5), (x - 1.3, 1.0)),
                 ((x - 1.14, 1.48), (x - 0.57, 1.6), (x - 0.02, 1.64)),
                 ((x + 0.1, 1.65), (x + 0.17, 1.63), (x + 0.2, 1.6)))


def kort_snirkel(x, y0=0.8):
    if OGLOR:
        return ogla(x, y0)
    return _kort_snirkel(x, y0)


def _kort_snirkel(x, y0=0.8):
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
    ben = kedja((0.5, 0.55), ((0.78, 1.7), (0.95, HI + 0.02), (1.42, HI + 0.02)),
                ((1.9, HI + 0.02), (2.2, 1.9), (2.3, 0.8)))
    y = 1.6
    i = np.where(np.diff(np.sign(ben[:, 1] - y)))[0]
    x0, x1 = ben[i[0], 0], ben[i[-1], 0]
    if OGLOR:
        # öglan nere till vänster fortsätter upp och blir tvärstrecket, som på H
        ogl = kedja((0.5, 0.55), ((0.42, 0.28), (0.18, LO - 0.06), (-0.12, LO - 0.05)),
                    ((-0.58, LO - 0.03), (-0.88, 0.5), (-0.74, 0.95)),
                    ((-0.6, 1.38), (-0.05, 1.52), (x0, y)),
                    ((x0 + 0.5, y + 0.03), (x1 - 0.4, y + 0.06), (x1, y + 0.08)))
        return [ben, svans(2.3, 0.8, 0.05), ogl]
    ben = np.vstack([kedja((-0.02, LO + 0.1), ((0.05, LO - 0.04), (0.3, LO - 0.04), (0.5, 0.55))), ben])
    return [ben, svans(2.3, 0.8, 0.05), vag((x0, y), (x1, y + 0.08), 0.03)]

def B():
    return stapel(0.35, fot="snirkel") + [
            kedja((0.35, HI), ((1.3, HI + 0.12), (1.95, HI - 0.05), (1.9, 2.95)),
                  ((1.85, 2.35), (1.2, 2.08), (0.5, 2.08))),
            kedja((0.5, 2.08), ((1.5, 2.1), (2.2, 1.85), (2.15, 1.15)),
                  ((2.1, 0.45), (1.4, LO - 0.08), (0.35, LO)))]

def C():
    """C som lilla c: ryggen lutar mer och buktar ut längre ner, övre armen
    sveper långt fram åt höger, som om bokstaven drogs med i en vind."""
    bana = kedja((2.6, 3.3), ((2.55, 3.62), (2.1, HI + OV), (1.6, HI + OV)),
                 ((0.85, HI + OV), (0.32, 2.65), (0.25, 1.65)),
                 ((0.2, 0.75), (0.75, LO - OV), (1.4, LO - OV)),
                 ((1.95, LO - OV), (2.35, 0.42), (2.55, 0.8)))
    return [bana]


def D():
    return stapel(0.35, fot="snirkel") + [
            kedja((0.35, HI), ((1.8, HI + 0.12), (2.6, 3.3), (2.6, 2.0)),
                  ((2.6, 0.6), (1.7, LO - 0.1), (0.35, LO)))]

def spiral(cx, cy, rx, ry, v0, v1, s0, s1, n=80):
    """Ellipsbåge vars radie ändras från s0 till s1 (rullar in sig mjukt)."""
    v = np.radians(np.linspace(v0, v1, n)); s = np.linspace(s0, s1, n)
    return np.column_stack([cx + rx * s * np.cos(v), cy + ry * s * np.sin(v)])


def E():
    """Runt E som en spegelvänd trea (Ɛ): två runda bågar, den nedre lite
    bredare, som möts i mitten med en kort tunga. Båda ändarna rullar in sig
    i en liten mjuk krok. Lutar 10° som resten."""
    mitt = 2.15
    ry1 = (HI + OV - mitt) / 2; ry2 = (mitt - (LO - OV)) / 2
    c1 = (1.3, mitt + ry1); c2 = (1.38, mitt - ry2)
    krok1 = spiral(*c1, 0.8, ry1, 8, 38, 0.86, 1.0)             # övre änden rullar in lite nedåt
    ovre = bage_ellips(*c1, 0.8, ry1, 38, 270)
    nedre = bage_ellips(*c2, 1.02, ry2, 90, 328)
    krok2 = spiral(*c2, 1.02, ry2, 328, 360, 1.0, 0.86)        # nedre änden rullar in lite uppåt
    tunga = (1.42, mitt)
    return [np.vstack([krok1, ovre, [tunga]]), np.vstack([[tunga], nedre, krok2])]

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
    """J som ditt lilla j: rak stapel med liten insväng upptill och en bred,
    mjuk båge nedtill som slutar uppåt åt vänster."""
    stam = kedja((1.8, HI), ((1.85, 2.8), (1.8, 1.8), (1.78, 1.0)))
    return [entre(1.8), stam, bage_ellips(1.03, 1.0, 0.75, 0.7, 0, -178)]


def K_():
    return stapel(0.35, fot="snirkel") + [
            kedja((2.6, HI - 0.02), ((2.3, HI + 0.12), (1.85, 3.4), (1.45, 2.65)),
                  ((1.15, 2.1), (0.75, 1.88), (0.4, 1.85))),
            kedja((0.95, 1.95), ((1.45, 2.0), (1.85, 1.45), (2.05, 0.8))), flick(2.05, 0.8, 0.2)]

def L_varp_param(polys):
    """Mät fotens undersida på ditt L och räkna ut vridning och sänkning."""
    P = np.vstack([p[0] for p in polys])
    xs = np.arange(0.4, 2.25, 0.1)
    under = np.array([P[(abs(P[:, 0] - x) < 0.05) & (P[:, 1] < 1.2), 1].min() for x in xs])
    lutn = np.polyfit(xs, under, 1)[0]
    vinkel = -np.arctan(lutn)                              # vrid så att undersidan blir vågrät
    # vridpunkt: stammens mitt där den möter foten
    mitt = lambda y: (lambda r: (r[:, 0].min() + r[:, 0].max()) / 2)(P[abs(P[:, 1] - y) < 0.03])
    pivot = np.array([mitt(1.05), 0.6])
    lut = (mitt(2.2) - mitt(1.2)) / 1.0                      # stammens lutning dx/dy
    return vinkel, pivot, lut


def L_varp(p, vinkel, pivot, sank, y_hel=0.7, y_noll=2.0, lut=0.0):
    """Räta upp foten (allt under y_hel) och sänk den. Punkterna flyttas bara i
    höjdled, så stammen behåller sin lutning; mjuk övergång upp till y_noll.
    Allt ovanför y_noll är orört."""
    p = np.asarray(p, float)
    t = np.clip((y_noll - p[:, 1]) / (y_noll - y_hel), 0, 1)
    w = t * t * (3 - 2 * t)                                 # mjuk ramp
    ut = p.copy()
    ut[:, 1] += w * (np.tan(vinkel) * (p[:, 0] - pivot[0]) - sank)
    ut[:, 0] -= w * sank * lut          # sänkningen sker längs stammens lutning
    return ut


def L_mask(mapp, under_baslinjen=0.04, vind=0.0):
    """Ditt original-L, med foten vriden så att undersidan ligger i linje med
    baslinjen och benet sänkt lite (foten får gå något under baslinjen)."""
    from PIL import Image, ImageDraw
    polys, _ = gemen_polygoner(mapp, "L")
    vinkel, pivot, lut = L_varp_param(polys)
    # sänkning: vriden undersida (medel) hamnar under_baslinjen under baslinjen
    P = L_varp(np.vstack([p[0] for p in polys]), vinkel, pivot, 0.0, lut=lut)
    xs = np.arange(0.4, 2.25, 0.1)
    under = np.mean([P[(abs(P[:, 0] - x) < 0.05) & (P[:, 1] < 1.2), 1].min() for x in xs])
    sank = under + under_baslinjen
    polys = [[L_varp(r, vinkel, pivot, sank, lut=lut) for r in p] for p in polys]
    polys = [[r + np.column_stack([vind * (r[:, 1] - 2.0), 0 * r[:, 1]]) for r in p] for p in polys]
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
    return ndimage.gaussian_filter(np.array(bild, float), 2) > 0.5, x0, y0


def M():
    """Symmetriskt M med en liten knorr överst på båda sidor; brett, som M ska
    vara (ca 1,25 x O). Diagonalerna går över topparna och ut i knorrarna."""
    v, h = 0.55, 3.3
    dal = (v + h) / 2
    over = kedja((v - 0.38, HI - 0.1), ((v - 0.3, HI + 0.04), (v - 0.12, HI + 0.04), (v, HI)),
                 ((v + 0.45, HI - 0.02), (dal - 0.35, 1.9), (dal, 1.2)),
                 ((dal + 0.35, 1.9), (h - 0.45, HI - 0.02), (h, HI)),
                 ((h + 0.12, HI + 0.04), (h + 0.3, HI + 0.04), (h + 0.38, HI - 0.1)))
    vstam = kedja((v, HI), ((0.52, 2.7), (0.62, 1.5), (0.52, 0.8)))
    hstam = kedja((h, HI), ((h + 0.03, 2.7), (h - 0.07, 1.5), (h + 0.03, 0.8)))
    return [over, vstam, hstam, kort_snirkel(0.52, 0.8), svans(h + 0.03, 0.8)]


def N():
    """N som M: insvängen går över toppen och ner i diagonalen."""
    v, h = 0.55, 2.5
    over = kedja((v - 0.38, HI - 0.1), ((v - 0.3, HI + 0.04), (v - 0.12, HI + 0.04), (v, HI)),
                 ((0.85, HI - 0.15), (1.9, 0.9), (2.22, LO + 0.06)),       # rakare diagonal
                 ((2.34, LO - 0.06), (h, 0.12), (h, 0.6)),                  # kort, stram vändning nere
                 ((h, 1.6), (h + 0.02, 2.8), (h, HI - 0.02)),                # rak högerstapel
                 ((h + 0.03, HI + 0.04), (h + 0.2, HI + 0.04), (h + 0.36, HI - 0.05)))
    stam = kedja((v, HI), ((0.52, 2.7), (0.62, 1.5), (0.52, 0.8)))
    return [over, stam, kort_snirkel(0.52, 0.8)]


def superellips(cx, cy, rx, ry, n=2.5, antal=400):
    """Mellan ellips (n=2) och rektangel: rundare, mindre spetsiga ändar."""
    v = np.linspace(0, 2 * np.pi, antal)
    c, s_ = np.cos(v), np.sin(v)
    return np.column_stack([cx + rx * np.sign(c) * np.abs(c) ** (2 / n),
                            cy + ry * np.sign(s_) * np.abs(s_) ** (2 / n)])


def O():
    """O med fylligare topp och botten (superellips) så att de inte blir spetsiga."""
    return [superellips(1.4, 2.0, 1.15, HI - 2.0 + OV, 2.25)]

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
                  ((1.75, HI - 0.06), (2.2, HI - 0.04), (2.5, HI + 0.05))),
            linje((1.3, HI), (1.3, 0.85), 0.1), snirkel(1.3, 0.85)]


def U():
    """U som ditt lilla u: vänster stapel går ner i en rund botten som går upp
    i en egen rak högerstapel; högerstapeln går ner till baslinjen med en liten fot."""
    return [entre(0.35),
            kedja((0.35, HI), ((0.35, 2.4), (0.35, 1.6), (0.38, 1.1)),
                  ((0.45, 0.4), (0.82, LO - OV), (1.2, LO - OV)),
                  ((1.6, LO - OV), (1.98, 0.55), (2.12, 1.6))),
            kedja((2.3, HI), ((2.33, 2.7), (2.26, 1.5), (2.3, 0.75))),
            svans(2.3, 0.75)]

def V():
    return [entre(0.3),
            kedja((0.3, HI), ((0.45, 2.3), (0.85, LO - 0.08), (1.2, LO)),
                  ((1.55, LO + 0.1), (2.0, 2.5), (2.3, HI)),
                  ((2.36, HI + 0.07), (2.5, HI + 0.07), (2.6, HI + 0.0)))]

def W():
    """Brett W (bredast av versalerna, som typografin säger)."""
    return [entre(0.25),
            kedja((0.25, HI), ((0.37, 2.0), (0.62, LO - 0.08), (0.97, LO)),
                  ((1.25, LO + 0.05), (1.58, 2.3), (1.78, 2.45)),
                  ((1.98, 2.3), (2.25, LO - 0.05), (2.6, LO)),
                  ((2.95, LO + 0.08), (3.22, 2.6), (3.4, HI)),
                  ((3.46, HI + 0.07), (3.6, HI + 0.07), (3.7, HI + 0.0)))]


def X():
    """X med samma sväng på båda strecken: båda börjar med en liten insväng
    upptill och slutar med en liten mjuk fot, speglade mot varandra.
    Fötterna fortsätter diagonalernas riktning så att det inte blir någon knyck."""
    hogerin = kedja((2.3 + 0.38, HI - 0.1), ((2.3 + 0.3, HI + 0.04), (2.3 + 0.12, HI + 0.04), (2.3, HI)))
    # streck 1: uppe till vänster ner till höger, mjuk fot åt höger
    s1 = kedja((0.3, HI), ((0.75, 2.9), (1.55, 1.6), (1.95, 0.75)),
               ((2.08, 0.45), (2.15, LO - 0.02), (2.35, LO - 0.02)),
               ((2.47, LO - 0.02), (2.55, LO + 0.03), (2.6, LO + 0.1)))
    # streck 2: speglat (uppe till höger ner till vänster), mjuk fot åt vänster
    s2 = kedja((2.3, HI), ((1.85, 2.9), (1.05, 1.6), (0.65, 0.75)),
               ((0.52, 0.45), (0.45, LO - 0.02), (0.25, LO - 0.02)),
               ((0.13, LO - 0.02), (0.05, LO + 0.03), (0.0, LO + 0.1)))
    return [entre(0.3), s1, hogerin, s2]

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

PRICK_Y = VERSAL + 0.88   # prickarnas och ringens mitt ovanför versalhöjden
PRICK_R = 0.42            # ytterradie: prickar och ring är lika stora (samma form i produktionen)
PRICK_DX = 0.55
RING_HALV = 0.12                 # ringens halva tjocklek
RING_R = PRICK_R - RING_HALV     # ringens mittlinje, så att ytterkanten = prickens
RING_Y = PRICK_Y                 # samma höjd som prickarna


def ring(cx, cy):
    return [ellips(cx, cy, RING_R, RING_R)]


VERSALER = {"A": A, "B": B, "C": C, "D": D, "E": E, "F": F, "G": G, "H": H if OGLOR else H_enkel, "I": I, "J": J_, "K": K_,
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


# "Vind": extra lutning (ca 6°) som får bokstaven att se ut att dras framåt, som lilla c.
# VIND=runda: bara de runda versalerna (staplarna behåller gemenernas 10°)
# VIND=alla:  alla versaler
VIND = 0.1
VIND_LAGE = os.environ.get("VIND", "runda")
RUNDA = {"C", "G", "O", "Q", "S"}


def har_vind(n):
    bas = DIAKRIT[n][0] if n in DIAKRIT else n
    return VIND_LAGE == "alla" or bas in RUNDA


def vind(banor):
    ut = []
    for b in banor:
        b = np.array(b, float); b[:, 0] += VIND * (b[:, 1] - 2.0); ut.append(b)
    return ut


def prick_x(n):
    """Mitten (rak, före lutning) mellan prickarna/ringen över n."""
    cx = DIAKRIT[n][2]
    return cx + (VIND * (HI - 2.0) if har_vind(n) else 0.0)   # mitt över bokstavens topp


def bygg_alla(mapp=None):
    ut = {}
    if mapp:
        ut["L"] = L_mask(mapp, vind=VIND if VIND_LAGE == "alla" else 0.0)
    for n, f in VERSALER.items():
        ut[n] = mask(vind(f()) if har_vind(n) else f())
    for n, (bas, typ, cx) in DIAKRIT.items():
        banor = VERSALER[bas]()
        ut[n] = mask(vind(banor) if har_vind(n) else banor)  # ring och prickar är egna delar
        if typ == "ring":
            # ringen är fylld: en rund prick, lika stor som prickarna på Ä och Ö
            cx = prick_x(n)
            ut[n + "-ring"] = mask([np.array([[cx, RING_Y], [cx + 0.001, RING_Y]])], halv=PRICK_R)
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
        cx = prick_x(n)
        for sx in (-PRICK_DX, PRICK_DX):
            ax.add_patch(plt.Circle((cx + sx + K * PRICK_Y + dx, PRICK_Y), PRICK_R, color="k"))


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ut = bygg_alla(sys.argv[1] if len(sys.argv) > 1 else None)
    pickle.dump(ut, open("versaler.pkl", "wb"))
    ordning = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ")
    fig, axs = plt.subplots(3, 10, figsize=(24, 10), dpi=100)
    for ax, n in zip(axs.ravel(), ordning):
        if n == "L":
            pass
        rita_versal(ax, ut, n)
        for y in (0, 2, 4):
            ax.axhline(y, color="#9ab", lw=0.5)
        ax.set_xlim(-1.3, 4.6); ax.set_ylim(-0.5, 5.8); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(n)
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
