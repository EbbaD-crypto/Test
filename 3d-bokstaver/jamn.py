"""Originalbokstäverna med touch, ritade om med exakt samma linjetjocklek.

Mittlinjerna är spårade efter originalbokstävernas mitt (se touch.py för
svängarna) som mjuka Bézierkurvor och sveps med en och samma radie. Formerna
följer originalet men tjockleken blir jämn överallt. Koordinater i mm på
samma sida som original_touch.png (r flyttat 15 mm åt höger), men sidan är
310 mm hög.

    python3 jamn.py && python3 bygg.py original_jamn.png 310
"""
import numpy as np
from PIL import Image
from scipy import ndimage

HALVBREDD = 15.5    # mm, halva linjetjockleken för alla bokstäver
SIDA_H, SIDA_B = 310.0, 235.0  # lite högre än A4 så att v:ts sväng får plats
UPPLOSNING = 0.25   # mm per pixel


def kedja(start, *segment):
    """Sammanhängande kubisk Bézierkedja: varje segment är (c1, c2, slut)."""
    t = np.linspace(0, 1, 300)[:, None]
    punkter, p0 = [], np.array(start, float)
    for c1, c2, p3 in segment:
        c1, c2, p3 = (np.array(c, float) for c in (c1, c2, p3))
        punkter.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p3)
        p0 = p3
    return np.vstack(punkter)


MITTLINJER = {
    "v": [
        # vänster arm ned till spetsen
        kedja((20, 277), ((30, 260), (45, 215), (55, 195))),
        # höger arm upp, med den lilla utåtsvängen överst
        kedja((55, 195), ((68, 222), (88, 264), (103, 280)),
              ((107, 284), (112, 285), (116, 284))),
    ],
    "a": [
        # skålen, från stapelns topp moturs runt till stapeln nertill
        kedja((180, 236), ((160, 240), (123, 236), (119, 202)),
              ((116, 174), (138, 165), (157, 167)),
              ((171, 169), (179, 178), (180, 190))),
        # stapeln ned och svansen som svänger upp
        kedja((186, 244), ((182, 225), (180, 200), (180, 182)),
              ((181, 162), (198, 152), (208, 166))),
    ],
    "e": [
        # tvärstreck, rygg runt ögat, ned och ut i svansen
        kedja((27, 112), ((45, 111), (70, 111), (82, 121)),
              ((88, 141), (75, 159), (57, 159)),
              ((38, 159), (28, 141), (27, 112)),
              ((26, 85), (42, 75), (62, 75)),
              ((84, 75), (100, 80), (108, 90))),
    ],
    "r": [
        # stapeln, med originalets lilla ingång uppe till vänster
        kedja((138, 22), ((146, 45), (150, 70), (150, 96)),
              ((150, 101), (146, 104), (141, 107))),
        # armen och droppen nedåt i änden
        kedja((150, 97), ((165, 102), (185, 104), (200, 99)),
              ((208, 96), (212, 90), (211, 84))),
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
    Image.fromarray(np.where(form, 0, 255).astype(np.uint8)).save("original_jamn.png")

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fore = np.array(Image.open("original_touch.png").convert("L")) < 128  # 297 mm hög
    fore = np.pad(fore, ((h - fore.shape[0], 0), (0, max(0, b - fore.shape[1]))))[:, :b]
    fig, axs = plt.subplots(1, 2, figsize=(13, 9), dpi=100)
    axs[0].imshow(fore, cmap="Greys", extent=(0, SIDA_B, 0, SIDA_H))
    axs[0].set_title("Före: olika tjocklek")
    axs[1].imshow(form, cmap="Greys", extent=(0, SIDA_B, 0, SIDA_H))
    for banor in MITTLINJER.values():
        for bana in banor:
            axs[1].plot(bana[:, 0], bana[:, 1], color="#e0604a", lw=1)
    axs[1].set_title("Efter: samma tjocklek överallt")
    for ax in axs:
        ax.set_axis_off()
    plt.savefig("jamn_jamforelse.png", bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    rendera()
