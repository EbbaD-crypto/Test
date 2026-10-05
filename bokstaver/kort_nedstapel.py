"""Kortar nedstapeln (descendern) på t.ex. p och q: delen under baslinjen flyttas
upp längs lutningen. Bara stapelns raka bitar (ZONER) trycks ihop; fot och
tvärstreck flyttas oförändrade, så tjocklek och form behålls.

    python3 kort_nedstapel.py in.stl ut.stl <hur mycket kortare> [zoner, t.ex. -0.1:-0.3,-1.05:-1.65]
"""
import sys
import numpy as np
import trimesh
from scipy import ndimage

K = np.tan(np.radians(10))


def korta(m, d, zoner=((-0.1, -1.6),)):
    """Vikten w(y) går från 0 (ovanför) till 1 (under sista zonen) och ökar bara
    inne i zonerna, jämnt fördelat efter zonernas längd."""
    ys = np.linspace(0.5, -2.5, 3001)
    rho = np.zeros_like(ys)
    for a, b in zoner:
        rho[(ys <= a) & (ys >= b)] = 1.0
    rho = ndimage.gaussian_filter1d(rho, 40)          # mjuka övergångar (~0,04)
    w = np.cumsum(rho); w /= w[-1]
    total = sum(a - b for a, b in zoner)
    if d > 0.7 * total:
        print("varning: stapeln trycks ihop mycket")
    m = m.copy()
    dy = d * np.interp(-m.vertices[:, 1], -ys, w)
    m.vertices[:, 1] += dy
    m.vertices[:, 0] += K * dy
    return m


if __name__ == "__main__":
    zoner = ((-0.1, -1.6),)
    if len(sys.argv) > 4:
        zoner = tuple(tuple(float(v) for v in z.split(":")) for z in sys.argv[4].split(","))
    m = korta(trimesh.load(sys.argv[1]), float(sys.argv[3]), zoner)
    m.export(sys.argv[2])
    print("vattentät", m.is_watertight, "nederst", round(m.bounds[0, 1], 3))
