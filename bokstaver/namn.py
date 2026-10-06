"""Sätter ihop namn med versal + gemener för att se hur typsnittet fungerar i ord.

Mellanrummet räknas optiskt: varje bokstav flyttas så att det minsta avståndet
till föregående bokstav (rad för rad) blir MELLAN.

    python3 namn.py <mapp med gemenerna (slutlig)> namn.png
"""
import sys
import numpy as np
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from versaler import bygg_alla, prick_x, gemen_polygoner, GEMENER, DIAKRIT, PRICK_Y, PRICK_DX, PRICK_R, K, RUT

YMIN, YMAX = -2.6, 5.6
H = int(round((YMAX - YMIN) / RUT))
MELLAN = 1.05  # optiskt medelavstånd (över hela höjden)
MINST = 0.75   # minsta tillåtna avstånd (t.ex. P:s båge till i-pricken, F:s arm till e)
DJUP = 0.5     # djupa öppningar räknas bara så här mycket djupare än MELLAN
ARMPAR = {"f", "t"}   # f och t: armarna får komma nära varandra (som en ligatur)
MINST_ARM = 0.5
NAMN = ["Ebba", "Åsa", "Örjan", "Maja", "Sven", "Greta", "Hugo", "Ida", "Kalle", "Nils",
        "Tove", "Wilma", "Felix", "Juno", "Rut", "Vera", "Bo", "Cecilia", "Pia", "Yrsa",
        "Leo", "Ulla", "Theo", "Olle", "Zelda", "Xenia", "Quinn", "Dan",
        "Hanna", "Hedda", "Hilma", "Hjalmar"]


def tom(bredd):
    return np.zeros((H, int(np.ceil(bredd / RUT)) + 1), bool)


def versal(ut, n, mapp):
    m, x0, y0 = ut[n]
    lager = [(m, x0, y0)] + ([ut[n + "-ring"]] if n + "-ring" in ut else [])
    xmin = min(l[1] for l in lager)
    xmax = max(l[1] + l[0].shape[1] * RUT for l in lager)
    if n in ("Ä", "Ö"):
        cx = prick_x(n)
        xmax = max(xmax, cx + PRICK_DX + K * PRICK_Y + PRICK_R)
    g = tom(xmax - xmin)
    for mm, xx, yy in lager:
        r0 = int(round((yy - YMIN) / RUT)); c0 = int(round((xx - xmin) / RUT))
        g[r0:r0 + mm.shape[0], c0:c0 + mm.shape[1]] |= mm
    if n in ("Ä", "Ö"):
        yy, xx = np.mgrid[0:H, 0:g.shape[1]]
        X, Y = xx * RUT + xmin, yy * RUT + YMIN
        cx = prick_x(n)
        for sx in (-PRICK_DX, PRICK_DX):
            g |= (X - (cx + sx + K * PRICK_Y)) ** 2 + (Y - PRICK_Y) ** 2 <= PRICK_R ** 2
    return g


def gemen(fil, mapp):
    polys, bredd = gemen_polygoner(mapp, fil)
    xmin = min(r[:, 0].min() for p in polys for r in p)
    xmax = max(r[:, 0].max() for p in polys for r in p)
    g = tom(xmax - xmin)
    bild = Image.new("1", (g.shape[1], H), 0)
    d = ImageDraw.Draw(bild)
    pix = lambda r: [((x - xmin) / RUT, (y - YMIN) / RUT) for x, y in r]
    for p in polys:
        d.polygon(pix(p[0]), fill=1)
        for hal in p[1:]:
            d.polygon(pix(hal), fill=0)
    return np.array(bild, bool)


def kanter_rad(g):
    hoger = np.where(g.any(1), g.shape[1] - 1 - np.argmax(g[:, ::-1], 1), -10 ** 6)
    vanster = np.where(g.any(1), np.argmax(g, 1), 10 ** 6)
    return hoger, vanster


def utstick(kant, tecken):
    """Rader där en arm sticker ut (mer än 0,2 utanför bokstavens vanliga kant)."""
    giltig = abs(kant) < 10 ** 5
    med = np.median(kant[giltig])
    return giltig & (abs(kant - med) > 0.2 / RUT)


def avstand(forra, nasta, minst=MINST, armar=(False, False)):
    """Hur långt nästa bokstav ska flyttas (i rutor) från föregående bokstavs vänsterkant.

    Optiskt avstånd par för par: på varje rad (över hela höjden, inte bara
    x-höjden) där båda bokstäverna har färg mäts luckan. Djupa öppningar (som
    i C eller under armen på F/T och bågen på P) räknas bara till ett visst
    djup. Medelluckan ska bli MELLAN och ingenstans får det vara mindre än MINST."""
    h1, _ = kanter_rad(forra)
    _, v2 = kanter_rad(nasta)
    rader = slice(int((-0.1 - YMIN) / RUT), int((4.1 - YMIN) / RUT))
    b = (h1[rader] > -10 ** 5) & (v2[rader] < 10 ** 5)
    b_med = b.copy()                          # f/t: armarna räknas inte i medelluckan
    if armar[0]:
        b_med &= ~utstick(h1[rader], 0)
    if armar[1]:
        b_med &= ~utstick(v2[rader], 0)
    h1, v2 = h1[rader][b], v2[rader][b]
    hard = int(np.max(h1 - v2)) + int(minst / RUT)
    djup = (MELLAN + DJUP) / RUT
    lo, hi = hard, hard + int(4 / RUT)
    while hi - lo > 1:                        # minsta skift där medelluckan >= MELLAN
        mitt = (lo + hi) // 2
        lucka = np.minimum(mitt + v2 - h1, djup)
        if any(armar):
            lucka = lucka[b_med[b]]
        if lucka.mean() * RUT >= MELLAN:
            hi = mitt
        else:
            lo = mitt
    return hi


# --- jämn spacing med sidmarginaler (som i typsnittsprogram) -------------------
# Varje bokstav får egna marginaler, räknade i x-höjdszonen och längs lutningen:
# den vita ytan vid sidan om bokstaven (ner till högst SB_DJUP in) ska bli lika
# stor för alla. Raka staplar får då mer marginal, runda och öppna sidor mindre.
SB_ZON = (0.0, 2.0)
SB_DJUP = 0.4
SB_MAL = None          # sätts i kalibrera() så att l–l blir som tidigare
SB_KROCK = 0.35        # bläck får aldrig komma närmare än så (armar, krokar)


def marginaler(g):
    r0, r1 = int((SB_ZON[0] - YMIN) / RUT), int((SB_ZON[1] - YMIN) / RUT)
    rad = np.arange(r0, r1)
    y = rad * RUT + YMIN
    h, v = kanter_rad(g)
    h, v = h[rad].astype(float), v[rad].astype(float)
    bl = (h > -10 ** 5) & (v < 10 ** 5)
    skift = K * y / RUT                       # rätas ut längs lutningen
    vx, hx = v - skift, h - skift
    L, R = vx[bl].min(), hx[bl].max()
    mv = np.where(bl, np.minimum(vx - L, SB_DJUP / RUT), SB_DJUP / RUT).mean() * RUT
    mh = np.where(bl, np.minimum(R - hx, SB_DJUP / RUT), SB_DJUP / RUT).mean() * RUT
    return L, R, mv, mh


def satt_ihop_sb(glyfer, tecken=None):
    """Bokstäverna placeras efter sina marginaler; sedan kontroll att inget krockar."""
    rad, pos = glyfer[0], 0
    L0, R0, _, mh0 = marginaler(glyfer[0])
    forra, f_R, f_mh = glyfer[0], R0, mh0
    for g in glyfer[1:]:
        L, R, mv, mh = marginaler(g)
        luft = (SB_MAL - f_mh) + (SB_MAL - mv)
        skift = int(round(pos + f_R + luft / RUT - L))
        # krockkontroll på hela höjden (riktiga, lutande rader)
        h1, _ = kanter_rad(forra); _, v2 = kanter_rad(g)
        b = (h1 > -10 ** 5) & (v2 < 10 ** 5)
        if b.any():
            minsta = int(np.max(pos + h1[b] - v2[b])) + int(SB_KROCK / RUT)
            skift = max(skift, minsta)
        ny = np.zeros((H, max(rad.shape[1], skift + g.shape[1])), bool)
        ny[:, :rad.shape[1]] |= rad
        ny[:, skift:skift + g.shape[1]] |= g
        rad, forra, pos, f_R, f_mh = ny, g, skift, R, mh
    return rad


def kalibrera(l_glyf):
    """SB_MAL så att avståndet l–l blir som med den gamla metoden."""
    global SB_MAL
    L, R, mv, mh = marginaler(l_glyf)
    gammal = avstand(l_glyf, l_glyf)          # i rutor, från vänsterkant till vänsterkant
    luft = (gammal + L - R) * RUT             # luft mellan rätade kanter
    SB_MAL = (luft + mv + mh) / 2


def satt_ihop(glyfer, tecken=None):
    rad = glyfer[0]
    forra, pos = glyfer[0], 0
    for i, g in enumerate(glyfer[1:], 1):
        armar = (bool(tecken) and tecken[i - 1] in ARMPAR, bool(tecken) and tecken[i] in ARMPAR)
        minst = MINST_ARM if any(armar) else MINST
        skift = pos + avstand(forra, g, minst, armar)
        ny = np.zeros((H, max(rad.shape[1], skift + g.shape[1])), bool)
        ny[:, :rad.shape[1]] |= rad
        ny[:, skift:skift + g.shape[1]] |= g
        rad, forra, pos = ny, g, skift
    return rad


def main():
    mapp, ut_fil = sys.argv[1:3]
    ut = bygg_alla(mapp)
    cache = {}
    def glyf(c):
        if c not in cache:
            cache[c] = versal(ut, c, mapp) if c.isupper() else gemen(GEMENER[c], mapp)
        return cache[c]
    kalibrera(glyf("l"))
    ord_ = [satt_ihop_sb([glyf(c) for c in n], n) for n in NAMN]
    kol = 4
    rader = (len(ord_) + kol - 1) // kol
    fig, axs = plt.subplots(rader, kol, figsize=(5 * kol, 2.3 * rader), dpi=100)
    for ax, o, n in zip(axs.ravel(), ord_, NAMN):
        ax.imshow(np.ma.masked_where(~o, o), cmap="Greys", vmin=0, vmax=1, origin="lower",
                  extent=(0, o.shape[1] * RUT, YMIN, YMAX), interpolation="bilinear")
        ax.set_xlim(-0.8, 19.5); ax.set_ylim(-2.4, 5.4); ax.set_aspect("equal"); ax.axis("off")
    for ax in axs.ravel()[len(ord_):]:
        ax.axis("off")
    plt.subplots_adjust(wspace=0.02, hspace=0.02)
    plt.savefig(ut_fil, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
