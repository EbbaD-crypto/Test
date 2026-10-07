"""Ställer toppen på bokstäverna i x-höjd på rätt linje: 2,00 för raka former,
2,02 för runda (de ska sticka ut en aning för att se lika höga ut).

Bara mittpartiet (0,3–1,7 över baslinjen) sträcks/trycks ihop längs lutningen,
så baslinjen, toppens form och alla detaljer behålls. Hålen får släppet
kontrollerat igen efteråt.

    python3 rata_xhojd.py <mapp med slutlig/>   (en kopia av originalen sparas i <mapp>/fore_xhojd/)
"""
import os
import shutil
import sys
import trimesh

from finputs import langs_lutning, spara
from kolla_hojder import BAS, RUNDA

MAL = {"c1": 2.02, "c2": 2.02, "o": 2.02, "q1": 2.02, "e2": 2.02, "e3": 2.02, "e8": 2.02,
       "s2": 2.02, "s3": 2.02, "s4": 2.02, "s5": 2.02,
       "r": 2.0, "u": 2.0, "v": 2.0, "w1": 2.0, "w2": 2.0, "x": 2.0}
HAL = {"o", "q1", "e2", "e3", "e8"}   # bokstäver med hål (släppet görs om)


def main():
    mapp = sys.argv[1]
    spar = os.path.join(mapp, "fore_xhojd"); os.makedirs(spar, exist_ok=True)
    for n, mal in MAL.items():
        fil = os.path.join(mapp, f"{n}.stl")
        if not os.path.exists(os.path.join(spar, f"{n}.stl")):
            shutil.copy(fil, spar)
        m = trimesh.load(os.path.join(spar, f"{n}.stl"))
        bas = BAS.get(n, m.bounds[0, 1])
        d = mal - (m.bounds[1, 1] - bas)
        ny = spara(langs_lutning(m, bas, 0.3, 1.7, d), fil, hal=n in HAL)
        print(f"{n:3s} topp {m.bounds[1, 1] - bas:.3f} -> {ny.bounds[1, 1] - bas:.3f}  botten {ny.bounds[0, 1] - bas:+.3f}  vattentät {ny.is_watertight}")


if __name__ == "__main__":
    main()
