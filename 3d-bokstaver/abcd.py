"""a, a, b, c, d från Abcd_.stl, ritade om med jämn tjocklek och kortare uppstaplar.

Mittlinjerna är spårade efter bokstäverna i Abcd_.stl (skalade så att
x-höjden blir ca 108 mm, samma som "Vaer"). Uppstaplarna på b och d är
förkortade till 1,5 × x-höjden (originalet hade 2 ×). Alla linjer sveps med
samma radie som i jamn.py så att hela alfabetet får samma tjocklek.

    python3 abcd.py && python3 bygg.py abcd.png --sida 200 --namn a1 a2 b c d --ut abcd
"""
import numpy as np
from PIL import Image
from scipy import ndimage

from jamn import HALVBREDD, kedja

UPPLOSNING = 0.25   # mm per pixel
BASLINJE = 12.0     # mm, bokstävernas underkant
XHOJD = 108.0       # mm, från baslinjen till x-höjdens överkant
UPPSTAPEL = 1.5     # uppstaplarnas höjd i förhållande till x-höjden
SIDA_H, SIDA_B = 200.0, 720.0

# Mittlinjens övre ände på b och d: överkanten ska hamna på 1,5 × x-höjden
TOPP = BASLINJE + UPPSTAPEL * XHOJD - HALVBREDD

MITTLINJER = {
    "a1": [
        # skålen svänger mjukt in i stapeln så att hålet blir ovalt
        kedja((91, 88), ((88, 100), (75, 104), (60, 103)),
              ((40, 102), (27, 85), (28, 62)),
              ((29, 40), (42, 29), (60, 29)),
              ((75, 29), (88, 36), (90, 50))),
        kedja((101, 109), ((95, 104), (91, 100), (91, 90)),
              ((91, 70), (91, 50), (90, 37)),
              ((95, 33), (104, 30), (105, 23))),
    ],
    "a2": [
        kedja((235, 88), ((232, 100), (218, 104), (204, 103)),
              ((184, 102), (171, 85), (172, 62)),
              ((173, 40), (186, 28), (204, 28)),
              ((219, 28), (232, 35), (234, 50))),
        kedja((246, 108), ((240, 104), (236, 100), (235, 92)),
              ((235, 70), (235, 50), (234, 37)),
              ((240, 32), (246, 29), (249, 25))),
    ],
    "b": [
        # uppstapel med originalets krok åt vänster överst, ned till foten
        kedja((331, TOPP), ((337, TOPP - 4), (340, TOPP - 12), (340, TOPP - 22)),
              ((340, 125), (338, 112), (338, 103)),
              ((336, 80), (330, 60), (328, 36)),
              ((322, 32), (316, 28), (314, 22))),
        # skålen
        kedja((337, 90), ((342, 101), (355, 104), (368, 104)),
              ((385, 104), (397, 85), (396, 65)),
              ((395, 40), (380, 28), (363, 28)),
              ((348, 28), (336, 34), (331, 45))),
    ],
    "c": [
        kedja((522, 103), ((510, 105), (495, 103), (484, 97)),
              ((470, 88), (469, 70), (470, 60)),
              ((471, 40), (485, 28), (503, 28)),
              ((515, 28), (527, 33), (536, 46))),
    ],
    "d": [
        kedja((658, 88), ((655, 100), (642, 104), (627, 103)),
              ((607, 102), (595, 85), (596, 62)),
              ((597, 40), (610, 29), (627, 29)),
              ((642, 29), (655, 35), (657, 50))),
        # lutande uppstapel som svänger åt höger överst, och svansen nertill
        kedja((657, 37), ((658, 60), (658, 90), (658, 103)),
              ((660, 120), (663, TOPP - 14), (667, TOPP - 5)),
              ((670, TOPP), (674, TOPP + 1), (678, TOPP))),
        kedja((657, 37), ((663, 32), (672, 28), (678, 24))),
    ],
}


def rendera():
    h, b = round(SIDA_H / UPPLOSNING), round(SIDA_B / UPPLOSNING)
    linjer = np.zeros((h, b), bool)
    for banor in MITTLINJER.values():
        for bana in banor:
            langd = np.r_[0, np.cumsum(np.hypot(*np.diff(bana, axis=0).T))]
            t = np.arange(0, langd[-1], UPPLOSNING / 2)
            x = np.interp(t, langd, bana[:, 0])
            y = np.interp(t, langd, bana[:, 1])
            linjer[np.round((SIDA_H - y) / UPPLOSNING).astype(int), np.round(x / UPPLOSNING).astype(int)] = True
    form = ndimage.distance_transform_edt(~linjer) * UPPLOSNING <= HALVBREDD
    Image.fromarray(np.where(form, 0, 255).astype(np.uint8)).save("abcd.png")

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fore = np.array(Image.open("abcd_original.png").convert("L")) < 128
    fig, axs = plt.subplots(2, 1, figsize=(14, 9.5), dpi=100)
    hf = fore.shape[0] * UPPLOSNING
    axs[0].imshow(fore, cmap="Greys", extent=(0, fore.shape[1] * UPPLOSNING, 0, hf))
    axs[0].set_title("Före: uppstaplar 2 × x-höjden")
    axs[1].imshow(form, cmap="Greys", extent=(0, SIDA_B, 0, SIDA_H))
    for banor in MITTLINJER.values():
        for bana in banor:
            axs[1].plot(bana[:, 0], bana[:, 1], color="#e0604a", lw=1)
    axs[1].set_title("Efter: uppstaplar 1,5 × x-höjden, samma linjetjocklek som Vaer")
    for ax in axs:
        ax.set_xlim(0, SIDA_B); ax.set_ylim(0, max(hf, SIDA_H))
        for y, f in ((BASLINJE, "baslinje"), (BASLINJE + XHOJD, "x-höjd"),
                     (BASLINJE + UPPSTAPEL * XHOJD, "1,5 ×"), (BASLINJE + 2 * XHOJD, "2 ×")):
            ax.axhline(y, color="#4a7be0", lw=0.6, ls="--")
            ax.text(SIDA_B + 3, y, f, va="center", fontsize=7, color="#4a7be0")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    plt.savefig("abcd_jamforelse.png", bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    rendera()
