"""Ritar "vaer" i snirklig skrivstil med jämn linjetjocklek.

Varje bokstav definieras som mittlinjer (kubiska Bézierkurvor) i mm, med
x-höjd XHOJD. Mittlinjerna sveps med en cirkel med radien HALVBREDD, så att
alla bokstäver får exakt samma linjetjocklek och runda ändar. Resultatet
sparas som en bild (snirkliga.png) där bildens höjd motsvarar 297 mm, så
att bygg.py kan göra 3D-modeller av den:

    python3 snirkliga.py && python3 bygg.py snirkliga.png
"""
import numpy as np
from PIL import Image
from scipy import ndimage

XHOJD = 110.0       # mm, bokstävernas höjd inklusive linjetjocklek
HALVBREDD = 12.5    # mm, halva linjetjockleken
SIDA_H, SIDA_B = 297.0, 280.0  # mm
UPPLOSNING = 0.1    # mm per pixel

# Mittlinjen löper mellan LAG och TOPP i höjdled
LAG, TOPP = HALVBREDD, XHOJD - HALVBREDD


def bezier(*p, n=400):
    p = np.array(p, float)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]


def kedja(start, *segment):
    """Sammanhängande Bézierkedja: varje segment är (c1, c2, slut)."""
    punkter, p0 = [], start
    for c1, c2, p3 in segment:
        punkter.append(bezier(p0, c1, c2, p3))
        p0 = p3
    return np.vstack(punkter)


def ellips(cx, cy, rx, ry, fran, till, n=600):
    v = np.radians(np.linspace(fran, till, n))
    return np.column_stack([cx + rx * np.cos(v), cy + ry * np.sin(v)])


# --- Bokstäverna (mm, x-höjd 0..XHOJD) --------------------------------------
def v():
    # Snirklig ingång uppe till vänster, spets nere i mitten, utgång som
    # svänger ut åt höger överst.
    return [kedja((4, 78),
                  ((6, 100), (22, 102), (28, 92)),
                  ((34, 80), (42, 30), (50, LAG + 2)),
                  ((58, 30), (66, 80), (74, 92)),
                  ((80, 101), (94, 100), (100, 88)))]


def a():
    # Rund skål och en stapel som slutar i en uppåtsvängd svans (som skissen).
    skal = ellips(41, 54, 31, 41, 0, 360)
    stapel = kedja((72, TOPP),
                   ((72, 70), (70, 40), (72, 26)),
                   ((75, 8), (96, 6), (104, 26)))
    return [skal, stapel]


def e():
    # Ögla med tvärstreck, rund rygg och en svans som svänger upp åt höger.
    return [kedja((16, 50),
                  ((40, 51), (82, 52), (89, 68)),
                  ((95, 90), (66, TOPP + 1), (48, TOPP)),
                  ((22, 96), (LAG + 1, 76), (LAG + 1, 50)),
                  ((LAG + 1, 26), (32, LAG), (54, LAG)),
                  ((74, LAG), (90, 22), (100, 36)))]


def r():
    # Ingångssnirkel uppe till vänster, rak stapel, båge som slutar i en krok,
    # och en liten utgång åt höger nertill.
    stapel = kedja((6, 80),
                   ((8, 100), (26, 102), (28, 88)),
                   ((30, 60), (28, 30), (30, LAG + 4)),
                   ((32, 6), (46, 8), (52, 20)))
    bage = kedja((29, 66),
                 ((38, 92), (60, 102), (78, 94)),
                 ((90, 88), (94, 76), (86, 70)))
    return [stapel, bage]


BOKSTAVER = {"v": v, "a": a, "e": e, "r": r}
# Placering på sidan (mm, nedre vänstra hörnet), två rader som originalet
PLACERING = {"v": (16, 168), "a": (150, 168), "e": (16, 22), "r": (150, 22)}


def rendera():
    h, b = round(SIDA_H / UPPLOSNING), round(SIDA_B / UPPLOSNING)
    linjer = np.zeros((h, b), bool)
    for namn, funk in BOKSTAVER.items():
        ox, oy = PLACERING[namn]
        for bana in funk():
            # tät sampling så att svepet blir sammanhängande
            langd = np.r_[0, np.cumsum(np.hypot(*np.diff(bana, axis=0).T))]
            t = np.arange(0, langd[-1], UPPLOSNING / 2)
            x = np.interp(t, langd, bana[:, 0]) + ox
            y = np.interp(t, langd, bana[:, 1]) + oy
            kol = np.round(x / UPPLOSNING).astype(int)
            rad = np.round((SIDA_H - y) / UPPLOSNING).astype(int)
            linjer[rad, kol] = True
    fylld = ndimage.distance_transform_edt(~linjer) <= HALVBREDD / UPPLOSNING
    Image.fromarray(np.where(fylld, 0, 255).astype(np.uint8)).save("snirkliga.png")

    # Förhandsvisning med mittlinjer
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 8.5), dpi=110)
    ax.imshow(fylld, cmap="Greys", extent=(0, SIDA_B, 0, SIDA_H))
    for namn, funk in BOKSTAVER.items():
        ox, oy = PLACERING[namn]
        for bana in funk():
            ax.plot(bana[:, 0] + ox, bana[:, 1] + oy, color="#e0604a", lw=1)
    ax.set_axis_off()
    plt.savefig("snirkliga_skiss.png", bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    rendera()
