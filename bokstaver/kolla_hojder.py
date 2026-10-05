"""Kontrollerar att gemenerna håller linjerna: x-höjd (2,0), uppstaplar (4,0)
och nedstaplar (-2,1) räknat från varje bokstavs baslinje.

    python3 kolla_hojder.py <mapp med slutlig/>
"""
import sys
import numpy as np
import trimesh

XHOJD, UPP, NED = 2.0, 4.0, 2.1
# baslinjer (från originalfilen, se justera.py); övriga: bokstavens underkant
BAS = {"b": -10.00, "d1": -10.01, "h": -0.06, "k": -0.09, "l": -19.96, "t1": -20.04, "t2": -20.05,
       "f": -20.0, "g": 0.0, "y": 0.0, "j": 0.0, "p": 0.0, "q1": 0.0, "q2": 0.0, "i": -19.95}
XGRUPP = ["a1", "a2", "c1", "c2", "c3", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "i", "m", "n",
          "o", "r", "s1", "s2", "s3", "s4", "s5", "u", "v", "w1", "w2", "x", "z"]
UPPGRUPP = ["b", "d1", "h", "k", "l", "t1", "t2"]
NEDGRUPP = ["g", "j", "p", "q1", "q2", "y", "f"]
RUNDA = {"a1", "a2", "c1", "c2", "c3", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "o", "s1", "s2",
         "s3", "s4", "s5", "g", "q1", "q2"}


def main():
    mapp = sys.argv[1]
    rader = []
    for n in XGRUPP + UPPGRUPP + NEDGRUPP:
        m = trimesh.load(f"{mapp}/{n}.stl")
        bas = BAS.get(n, m.bounds[0, 1])
        topp, botten = m.bounds[1, 1] - bas, m.bounds[0, 1] - bas
        rader.append((n, topp, botten))
    tol = 0.035
    print("X-HÖJD (mål 2,00; runda former får sticka ut ~0,03)")
    for n, t, b in rader:
        if n in XGRUPP:
            mal = XHOJD + (0.02 if n in RUNDA else 0)
            print(f"  {n:4s} topp {t:5.2f}  {'OK' if abs(t - mal) <= tol else 'AVVIKER'}")
    print("UPPSTAPLAR (mål 4,00)")
    for n, t, b in rader:
        if n in UPPGRUPP:
            print(f"  {n:4s} topp {t:5.2f}  {'OK' if abs(t - UPP) <= tol else 'AVVIKER'}")
    print("NEDSTAPLAR (mål -2,10) och deras x-höjd")
    for n, t, b in rader:
        if n in NEDGRUPP:
            print(f"  {n:4s} botten {b:5.2f} {'OK' if abs(b + NED) <= tol else 'AVVIKER'}   topp {t:5.2f}")


if __name__ == "__main__":
    main()
