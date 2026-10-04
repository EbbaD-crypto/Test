"""Ger h:ets stam samma sväng som stammarna i b och k.

Stammens vänsterkant mäts i många höjder för b, k och h. h:ets kant flyttas
så att den får samma form som medelvärdet av b:s och k:s (relativt sitt eget
medelläge). Bara stamsidan påverkas; bågen och högra benet ligger kvar.
Foten och toppen flyttas med som helheter så att de behåller sin form.

    python3 h_stam.py slutlig
"""
import os
import sys
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter1d

from justera import ramp, slapp_i_hal
from gemensam_sving import laga, kantprofil
from rata_stam import kant

BAS = {"h": -0.06, "b": -10.00, "k": -0.09}


def main():
    mapp = sys.argv[1]
    t = np.linspace(0.55, 3.5, 70)  # toppen ovanför 3,5 och foten under 0,55 flyttas med oförändrade
    prof = {n: kantprofil(trimesh.load(os.path.join(mapp, f"{n}.stl")), BAS[n], "V", t, None) for n in BAS}
    form = np.mean([prof[n] - prof[n].mean() for n in ("b", "k")], axis=0)
    fil = os.path.join(mapp, "h.stl")
    h = trimesh.load(fil)
    mal = prof["h"].mean() + form
    dx = gaussian_filter1d(mal - prof["h"], 2, mode="nearest")
    v = h.vertices.copy()
    y = v[:, 1] - BAS["h"]
    d = np.interp(y, t, dx)
    xs = kant(h, BAS["h"] + 1.0, "V")
    # stamsidan: allt vänster om stammens högerkant (+ marginal), mätt per höjd längs stammen
    stam_h = np.interp(y, t, prof["h"]) + 0.8
    v[:, 0] += d * (1 - ramp(v[:, 0], stam_h, stam_h + 0.25))
    ny = laga(trimesh.Trimesh(v, h.faces, process=False))
    ny, _ = slapp_i_hal(ny); ny = laga(ny)
    efter = kantprofil(ny, BAS["h"], "V", t, None)
    g = lambda x, a, b: np.degrees(np.arctan(np.polyfit(t[(t > a) & (t < b)], x[(t > a) & (t < b)], 1)[0]))
    for n, x in (("h före", prof["h"]), ("h nu", efter), ("b", prof["b"]), ("k", prof["k"])):
        print(f"{n:6s} stam upptill {g(x, 2.4, 3.6):5.1f}°, nedtill {g(x, 0.4, 1.6):5.1f}°")
    print(f"vattentät {ny.is_watertight}")
    ny.export(fil)


if __name__ == "__main__":
    main()
