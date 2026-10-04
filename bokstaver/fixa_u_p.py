"""Rättar u och p så att de lutar som resten av typsnittet.

u: varje arm skjuvas för sig så att armens ytterkant lutar LUTNING grader
   (vänster arm: vänsterkanten, höger arm: högerkanten). Bågen nertill rörs inte.
p: stammens vänsterkant får LUTNING grader hela vägen (som q:s stam; valfritt
   med en andel av svängen i g, j och y). Skålen rörs inte.

    LUTNING=10 python3 fixa_u_p.py slutlig
"""
import os
import sys
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter1d

from justera import ramp, integral, slapp_i_hal
from gemensam_sving import laga, kantprofil, sving
from rata_stam import kant

LUTNING = float(os.environ.get("LUTNING", 10.0))
K = np.tan(np.radians(LUTNING))


def kantlutning(m, y0, y1, sida):
    ys = np.linspace(y0, y1, 15)
    return np.polyfit(ys, [kant(m, y, sida) for y in ys], 1)[0]


def fixa_u(fil):
    u = trimesh.load(fil)
    (x0, y0, _), (x1, y1, _) = u.bounds
    h = y1 - y0
    zc = (u.bounds[0, 2] + u.bounds[1, 2]) / 2
    s = u.section(plane_origin=[0, y1 - 0.4 * h, zc], plane_normal=[0, 1, 0])
    bit = sorted((d[:, 0].min(), d[:, 0].max()) for d in s.discrete)
    mitt = (bit[0][1] + bit[-1][0]) / 2
    a, b = y0 + 0.35 * h, y1 - 0.1 * h
    kv, kh = kantlutning(u, a, b, "V"), kantlutning(u, a, b, "H")
    v = u.vertices.copy()
    t = np.linspace(y0 - 0.01, y1 + 0.01, 4000)
    w = ramp(t, y0 + 0.2 * h, y0 + 0.45 * h)
    S = np.interp(v[:, 1], t, np.concatenate([[0], np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(t))]))
    wl = 1 - ramp(v[:, 0], mitt - 0.1, mitt + 0.1)
    v[:, 0] += ((K - kv) * wl + (K - kh) * (1 - wl)) * S
    ny = trimesh.Trimesh(v, u.faces, process=False)
    kv2, kh2 = kantlutning(ny, a, b, "V"), kantlutning(ny, a, b, "H")
    ny = laga(ny)
    g = lambda k: np.degrees(np.arctan(k))
    print(f"u: vänster arm {g(kv):.1f}° → {g(kv2):.1f}°, höger arm {g(kh):.1f}° → {g(kh2):.1f}°, vattentät {ny.is_watertight}")
    ny.export(fil)


def fixa_p(mapp, sving_andel=0.0):
    zon = (-1.5, 1.6)
    t = np.linspace(*zon, 60)
    # gemensam nedstapelsväng från g, j och y (deras stamkant på högersidan)
    sv = [sving(t, kantprofil(trimesh.load(os.path.join(mapp, f"{n}.stl")), 0.0, "H", t, None)) for n in ("g", "j", "y")]
    gemensam = np.mean(sv, axis=0)
    fil = os.path.join(mapp, "p.stl")
    p = trimesh.load(fil)
    xe = kantprofil(p, 0.0, "V", t, None)
    mal = xe.mean() + K * (t - t.mean()) + sving_andel * gemensam
    dx = gaussian_filter1d(mal - xe, 2, mode="nearest")
    v = p.vertices.copy()
    d = np.interp(v[:, 1], t, dx)
    xs = kant(p, 0.8, "V")
    v[:, 0] += d * (1 - ramp(v[:, 0], xs + 0.55, xs + 0.85))
    ny = trimesh.Trimesh(v, p.faces, process=False)
    g = lambda m, a, b: np.degrees(np.arctan(kantlutning(m, a, b, "V")))
    fore = (g(p, 0.3, 1.6), g(p, -1.5, -0.3))
    efter = (g(ny, 0.3, 1.6), g(ny, -1.5, -0.3))
    ny, _ = slapp_i_hal(laga(ny)); ny = laga(ny)
    print(f"p: stam i x-höjden {fore[0]:.1f}° → {efter[0]:.1f}°, nedstapel {fore[1]:.1f}° → {efter[1]:.1f}°, "
          f"vattentät {ny.is_watertight}")
    ny.export(fil)


if __name__ == "__main__":
    mapp = sys.argv[1]
    fixa_u(os.path.join(mapp, "u.stl"))
    fixa_p(mapp)



def rata_u(fil, varv=2, sving=0.0, amplitud=None):
    """Gör u:ets armar raka och parallella. Varje arm flyttas höjd för höjd så
    att dess mittlinje blir en rak linje med LUTNING grader, och får samma
    bredd hela vägen (armens medianbredd), så att båda kanterna blir raka.
    De rundade topparna flyttas med utan att ändra form, och bågen nertill
    tonas ut. Båda armarna får samma mjuka böj: vänster arms ursprungliga
    mittlinjesväng (armarna böjer annars åt motsatta håll eftersom u är ett
    vänt n), skalad med sving eller till en given amplitud."""
    mal = None
    for _ in range(varv):
        u = trimesh.load(fil)
        (x0, y0, _), (x1, y1, _) = u.bounds
        h = y1 - y0
        zc = (u.bounds[0, 2] + u.bounds[1, 2]) / 2

        def armar(y):
            s = u.section(plane_origin=[0, y, zc], plane_normal=[0, 1, 0])
            return sorted((d[:, 0].min(), d[:, 0].max()) for d in s.discrete)

        ys = np.linspace(y0 + 0.4 * h, y0 + 0.9 * h, 50)
        bitar = [armar(y) for y in ys]
        mitt = np.median([(b[0][1] + b[-1][0]) / 2 for b in bitar if len(b) >= 2])
        v = u.vertices.copy()
        ok = np.array([len(b) >= 2 for b in bitar])
        cw = {arm: (np.array([(b[arm][0] + b[arm][1]) / 2 for b, o in zip(bitar, ok) if o]),
                    np.array([b[arm][1] - b[arm][0] for b, o in zip(bitar, ok) if o])) for arm in (0, -1)}
        yk = ys[ok]
        if mal is None:
            # mål bestäms en gång från originalet: rak 10°-linje + gemensam sväng
            avvik = []
            for arm in (0, -1):
                k, c0 = np.polyfit(yk, cw[arm][0], 1)
                avvik.append(cw[arm][0] - (k * yk + c0))
            gem = gaussian_filter1d(avvik[0], 3, mode="nearest")
            if amplitud is not None:
                gem = gem * amplitud / np.ptp(gem)
                sving = 1.0
            mal = {arm: (yk.copy(), cw[arm][0].mean() + K * (yk - yk.mean()) + sving * gem, np.median(cw[arm][1]))
                   for arm in (0, -1)}
        for arm in (0, -1):
            c, w = cw[arm]
            ct = np.interp(yk, mal[arm][0], mal[arm][1])
            wt = mal[arm][2]
            dx = gaussian_filter1d(ct - c, 2, mode="nearest")
            sk = gaussian_filter1d(wt / w, 2, mode="nearest")
            # full verkan i armen, ingen skalning i topparna, uttoning mot bågen
            yv = v[:, 1]
            hel = ramp(yv, y0 + 0.30 * h, y0 + 0.52 * h)
            skalvikt = hel * ramp(yv, y0 + 0.92 * h, y0 + 0.82 * h)
            d = np.interp(yv, yk, dx) * hel
            skal = 1 + (np.interp(yv, yk, sk) - 1) * skalvikt
            cy = np.interp(yv, yk, c)
            sidovikt = 1 - ramp(v[:, 0], mitt - 0.1, mitt + 0.1) if arm == 0 else ramp(v[:, 0], mitt - 0.1, mitt + 0.1)
            nyx = cy + (v[:, 0] - cy) * skal + d
            v[:, 0] = v[:, 0] + (nyx - v[:, 0]) * sidovikt
        ny = laga(trimesh.Trimesh(v, u.faces, process=False))
        ny.export(fil)
    u = ny
    ys = np.linspace(y0 + 0.38 * h, y0 + 0.85 * h, 30)
    kanter = np.array([[k for b in [armar(y)] for k in (b[0][0], b[0][1], b[-1][0], b[-1][1])] for y in ys])
    for i, namn in enumerate(("vänster arm ytterkant", "vänster arm innerkant", "höger arm innerkant", "höger arm ytterkant")):
        k, c0 = np.polyfit(ys, kanter[:, i], 1)
        print(f"u {namn}: {np.degrees(np.arctan(k)):.1f}°, sväng (avvikelse från rak linje) {np.abs(kanter[:, i] - (k * ys + c0)).max():.3f}")
    print(f"u vattentät {ny.is_watertight}")



def p_som_f(mapp):
    """Ger p:s nedstapel samma sväng som f:s nedstapel. Stammen i x-höjden
    och skålen rörs inte; svängen tonas in strax under baslinjen."""
    t = np.linspace(-1.9, -0.1, 50)
    f = trimesh.load(os.path.join(mapp, "f.stl"))
    xf = kantprofil(f, -20.0, "V", t, None)
    kf, cf = np.polyfit(t, xf, 1)
    sv_f = gaussian_filter1d(xf - (kf * t + cf), 2, mode="nearest")
    fil = os.path.join(mapp, "p.stl")
    p = trimesh.load(fil)
    xp = kantprofil(p, 0.0, "V", t, None)
    malx = xp.mean() + K * (t - t.mean()) + sv_f
    dx = gaussian_filter1d(malx - xp, 2, mode="nearest")
    dx -= dx[-1]  # ingen förflyttning vid baslinjen
    v = p.vertices.copy()
    d = np.interp(v[:, 1], t, dx) * ramp(v[:, 1], 0.0, -0.4)
    xs = kant(p, -0.8, "V")
    v[:, 0] += d * (1 - ramp(v[:, 0], xs + 0.55, xs + 0.85))
    ny = laga(trimesh.Trimesh(v, p.faces, process=False))
    ny, _ = slapp_i_hal(ny); ny = laga(ny)
    xn = kantprofil(ny, 0.0, "V", t, None)
    kn, cn = np.polyfit(t, xn, 1)
    print(f"p: nedstapelns sväng {np.ptp(xp - np.polyval(np.polyfit(t, xp, 1), t)):.3f} → {np.ptp(xn - (kn * t + cn)):.3f} "
          f"(f:s {np.ptp(sv_f):.3f}), lutning {np.degrees(np.arctan(kn)):.1f}°, vattentät {ny.is_watertight}")
    ny.export(fil)
