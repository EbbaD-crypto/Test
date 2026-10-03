"""Ger originalbokstäverna en diskret snirklig touch.

Utgår från förhandsbilden (original.jpg) och lägger till små, avsmalnande
svängar i några ändar, i stil med svansen på ett handskrivet a. Fogarna
jämnas ut så att tilläggen flyter ihop med originalformen. Resultatet sparas
som original_touch.png (höjd = 297 mm) som bygg.py kan göra 3D av:

    python3 touch.py && python3 bygg.py original_touch.png
"""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

UPPLOSNING = 0.25   # mm per pixel
SIDA_MM = 297.0
EXTRA_BREDD = 25.0  # mm luft till höger så att a:ets svans och flyttade r får plats
R_FLYTT = 15.0      # mm, r flyttas åt höger så att e:ts svans inte nuddar den


def bezier(p0, p1, p2, p3, n=300):
    p = np.array([p0, p1, p2, p3], float)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]


# Svängar: (Bézierkurva i mm från originalets ände och utåt, radie i början, radie i slutet)
SVANGAR = {
    # a: foten nere till höger svänger upp i en liten svans
    "a": (bezier((187, 157), (196, 149), (206, 151), (209, 164)), 9.0, 7.0),
    # e: svansen svänger ut åt höger och lite uppåt
    "e": (bezier((88, 85), (95, 86), (101, 90), (104, 99)), 9.5, 7.5),
    # v: högra armen planar ut i en liten utåtsväng
    "v": (bezier((93, 277), (100, 283), (108, 286), (115, 285)), 10.0, 7.5),
    # r: armens ände får en liten droppe nedåt (foten lämnas orörd)
    "r": (bezier((183 + R_FLYTT, 99), (191 + R_FLYTT, 99), (197 + R_FLYTT, 94), (197 + R_FLYTT, 85)), 10.5, 8.0),
}


def original_mask():
    img = Image.open("original.jpg").convert("L")
    skala = SIDA_MM / img.height / UPPLOSNING
    stor = img.resize((round(img.width * skala), round(img.height * skala)), Image.BICUBIC)
    stor = stor.filter(ImageFilter.GaussianBlur(2))
    m = (np.array(stor) < 128)[::-1]  # y uppåt
    etiketter, n = ndimage.label(m)
    storlek = ndimage.sum(m, etiketter, range(1, n + 1))
    m = np.isin(etiketter, np.argsort(storlek)[::-1][:4] + 1)
    # Fyll igen prickarna (upphängningshålen), behåll hålen i a och e
    hal, nh = ndimage.label(ndimage.binary_fill_holes(m) & ~m)
    hs = ndimage.sum(np.ones_like(m), hal, range(1, nh + 1))
    m |= np.isin(hal, [i + 1 for i, a in enumerate(hs) if a * UPPLOSNING ** 2 < 150])
    m = np.pad(m, ((0, 0), (0, round(EXTRA_BREDD / UPPLOSNING))))
    # Flytta r (nedre raden, högra bokstaven) åt höger
    etiketter, _ = ndimage.label(m)
    r_lab = etiketter[round(30 / UPPLOSNING), round(125 / UPPLOSNING)]
    r_mask = etiketter == r_lab
    m[r_mask] = False
    m |= np.roll(r_mask, round(R_FLYTT / UPPLOSNING), axis=1)
    return m


def svep(form, bana, r0, r1):
    """Lägg till en avsmalnande linje längs banan (mm)."""
    yy, xx = np.mgrid[:form.shape[0], :form.shape[1]]
    for (x, y), r in zip(bana, np.linspace(r0, r1, len(bana))):
        cx, cy, rp = x / UPPLOSNING, y / UPPLOSNING, r / UPPLOSNING
        y0, y1 = int(cy - rp - 2), int(cy + rp + 3)
        x0, x1 = int(cx - rp - 2), int(cx + rp + 3)
        sub = (yy[y0:y1, x0:x1] - cy) ** 2 + (xx[y0:y1, x0:x1] - cx) ** 2 <= rp ** 2
        form[y0:y1, x0:x1] |= sub


def main():
    form = original_mask()
    ny = form.copy()
    for bana, r0, r1 in SVANGAR.values():
        svep(ny, bana, r0, r1)
    # Mjuka fogar: utjämna bara runt tilläggen så att resten är orört
    tillagg = ndimage.binary_dilation(ny & ~form, iterations=round(6 / UPPLOSNING))
    mjuk = ndimage.gaussian_filter(ny.astype(float), 2.5 / UPPLOSNING) > 0.5
    ny = np.where(tillagg, mjuk, form)
    Image.fromarray(np.where(ny[::-1], 0, 255).astype(np.uint8)).save("original_touch.png")

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 9), dpi=100)
    for ax, bild, titel in zip(axs, (form, ny), ("Original", "Med snirklig touch")):
        ax.imshow(bild, cmap="Greys", origin="lower")
        ax.set_title(titel); ax.set_axis_off()
    plt.savefig("touch_jamforelse.png", bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    main()
