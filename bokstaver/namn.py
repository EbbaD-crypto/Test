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

from versaler import bygg_alla, gemen_polygoner, GEMENER, DIAKRIT, PRICK_Y, PRICK_DX, PRICK_R, K, RUT

YMIN, YMAX = -2.6, 5.6
H = int(round((YMAX - YMIN) / RUT))
MELLAN = 0.32
NAMN = ["Ebba", "Åsa", "Örjan", "Maja", "Sven", "Greta", "Hugo", "Ida", "Kalle", "Nils",
        "Tove", "Wilma", "Felix", "Juno", "Rut", "Vera", "Bo", "Cecilia", "Pia", "Yrsa",
        "Leo", "Ulla", "Theo", "Olle", "Zelda", "Xenia", "Quinn", "Dan"]


def tom(bredd):
    return np.zeros((H, int(np.ceil(bredd / RUT)) + 1), bool)


def versal(ut, n, mapp):
    if n == "L":
        return gemen("L", mapp)
    m, x0, y0 = ut[n]
    lager = [(m, x0, y0)] + ([ut[n + "-ring"]] if n + "-ring" in ut else [])
    xmin = min(l[1] for l in lager)
    xmax = max(l[1] + l[0].shape[1] * RUT for l in lager)
    if n in ("Ä", "Ö"):
        cx = DIAKRIT[n][2]
        xmax = max(xmax, cx + PRICK_DX + K * PRICK_Y + PRICK_R)
    g = tom(xmax - xmin)
    for mm, xx, yy in lager:
        r0 = int(round((yy - YMIN) / RUT)); c0 = int(round((xx - xmin) / RUT))
        g[r0:r0 + mm.shape[0], c0:c0 + mm.shape[1]] |= mm
    if n in ("Ä", "Ö"):
        yy, xx = np.mgrid[0:H, 0:g.shape[1]]
        X, Y = xx * RUT + xmin, yy * RUT + YMIN
        cx = DIAKRIT[n][2]
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


def satt_ihop(glyfer):
    rad = glyfer[0]
    for g in glyfer[1:]:
        hoger = np.where(rad.any(1), rad.shape[1] - 1 - np.argmax(rad[:, ::-1], 1), -10 ** 6)
        vanster = np.where(g.any(1), np.argmax(g, 1), 10 ** 6)
        gap = int(MELLAN / RUT)
        # förskjutning så att minsta avståndet blir gap
        skift = int(np.max(hoger - vanster)) + gap + 1
        ny = np.zeros((H, max(rad.shape[1], skift + g.shape[1])), bool)
        ny[:, :rad.shape[1]] |= rad
        ny[:, skift:skift + g.shape[1]] |= g
        rad = ny
    return rad


def main():
    mapp, ut_fil = sys.argv[1:3]
    ut = bygg_alla()
    cache = {}
    def glyf(c):
        if c not in cache:
            cache[c] = versal(ut, c, mapp) if c.isupper() else gemen(GEMENER[c], mapp)
        return cache[c]
    ord_ = [satt_ihop([glyf(c) for c in n]) for n in NAMN]
    kol = 4
    rader = (len(ord_) + kol - 1) // kol
    fig, axs = plt.subplots(rader, kol, figsize=(5 * kol, 2.3 * rader), dpi=100)
    for ax, o, n in zip(axs.ravel(), ord_, NAMN):
        ax.imshow(np.ma.masked_where(~o, o), cmap="Greys", vmin=0, vmax=1, origin="lower",
                  extent=(0, o.shape[1] * RUT, YMIN, YMAX), interpolation="bilinear")
        ax.set_xlim(-0.3, 16); ax.set_ylim(-2.4, 5.4); ax.set_aspect("equal"); ax.axis("off")
    for ax in axs.ravel()[len(ord_):]:
        ax.axis("off")
    plt.subplots_adjust(wspace=0.02, hspace=0.02)
    plt.savefig(ut_fil, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
