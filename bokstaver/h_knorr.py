"""Lilla h får en knorr på vänstra benet nedtill, likadan som knorren högst upp.

Toppen av h:ets uppstapel (med knorren) klipps ut, speglas upp-och-ner längs
lutningen (så att den lutar 10° som resten) och sätts nederst på vänstra benet,
där den ersätter den gamla rundade foten. Fogen jämnas ut mjukt.

    python3 h_knorr.py <mapp med slutlig/> forhand.png      # 2D före/efter
    python3 h_knorr.py <mapp> forhand.png ny_h.stl          # även 3D
"""
import sys
import numpy as np
import trimesh

LADA = (0.5, 0.6)          # knorrens utklipp ur b (x < 0.5, y < 0.6 från b:s vänsterkant/baslinje)


def lokal(m, bas):
    return np.array([m.bounds[0, 0], bas])


def vanster_kant(m, bas, y):
    z0, z1 = m.bounds[:, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4))
    P = np.vstack([np.array(q.exterior.coords) for q in p.polygons_full]) - lokal(m, bas)
    return P[abs(P[:, 1] - y) < 0.03, 0].min()


def forskjutning(h, b, hbas, bbas):
    dx = np.mean([vanster_kant(h, hbas, y) - vanster_kant(b, bbas, y) for y in (0.7, 0.8, 0.9)])
    return lokal(h, hbas) - lokal(b, bbas) + [dx, 0]


# knorrens mittlinje (från h:ets vänsterkant/baslinje) och radie längs den
KNORR = np.array([(0.40, 0.42), (0.27, 0.2), (0.12, 0.11), (-0.02, 0.12), (-0.12, 0.2), (-0.16, 0.32)])
KNORR_R = (0.2, 0.12)


def knorr_bana(n=60):
    from scipy.interpolate import splprep, splev
    tck, _ = splprep(KNORR.T, s=0.0005, k=3)
    t = np.linspace(0, 1, n)
    x, y = splev(t, tck)
    return np.column_stack([x, y]), KNORR_R[0] + (KNORR_R[1] - KNORR_R[0]) * t


def knorr_poly(x0, bas):
    from shapely.geometry import Point
    from shapely.ops import unary_union
    p, r = knorr_bana()
    return unary_union([Point(x + x0, y + bas).buffer(rr, 32) for (x, y), rr in zip(p, r)])


K = np.tan(np.radians(10))
KULA_FRAN = 3.45           # knorrens kula: delen av uppstapeln ovanför denna höjd
KULA_TOPP_TILL = 0.62      # kulans (speglade) överkant hamnar här på benet
BEN_X = 1.05               # vänstra benet ligger till vänster om detta (från h:ets vänsterkant)


def kanter(poly, x0, y, sida="v"):
    """Vänstra (sida="v") eller högra (sida="h") benets vänster- och högerkant
    på höjden y (från h:ets vänsterkant)."""
    from shapely.geometry import LineString
    hoger = x0 + (BEN_X + 0.4 if sida == "v" else 5)
    snitt = poly.intersection(LineString([(x0 - 1, y), (hoger, y)]))
    delar = sorted(getattr(snitt, "geoms", [snitt]), key=lambda g: g.bounds[0])
    return np.array(delar[0 if sida == "v" else -1].bounds)[[0, 2]] - x0


SENAST = {}               # transformerna från senaste speglad_knorr (används för 3D)
BIT_FRAN = 2.9            # knorren + stapeln ovanför denna höjd speglas
SKALA = 1.05              # ger jämn tjocklek i benet (ca 0,6 hela vägen ner)
RUNDA = 0.08              # rundar av knorrens kula en aning
OVERLAPP = 0.25           # biten går så här långt upp i benet så att fogen inte syns
HOGER_KNORR = True        # samma knorr på högra benet (vänd utåt åt höger)


def mittlinje(poly, x0, y0, y1, sida="v"):
    """Benets mittpunkt på två höjder (absoluta koordinater)."""
    p0, p1 = [np.array([kanter(poly, x0, y, sida).mean() + x0, y]) for y in (y0, y1)]
    return p0, p1


def en_knorr(hp, x0, bas, sida):
    """Toppknorren (+ en bit stapel) vänds och vrids så att stapelbiten får benets
    exakta lutning och placeras nederst på benet. sida="v": vänd upp-och-ner
    (knorren pekar åt vänster). sida="h": vriden ett halvt varv (pekar åt höger)."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    from shapely import affinity
    bit = hp.intersection(box(x0 - 1, bas + BIT_FRAN - OVERLAPP, x0 + BEN_X + 0.6, bas + 5))
    s0, s1 = mittlinje(hp, x0, bas + BIT_FRAN + 0.35, bas + BIT_FRAN + 0.05)
    sx = 1 if sida == "v" else -1
    sp = affinity.scale(bit, sx, -1, origin=(0, 0))
    a0, a1 = s0 * [sx, -1], s1 * [sx, -1]
    vinkel_sp = np.degrees(np.arctan2(*(a0 - a1)[::-1]))
    y_fog = 1.0
    for _ in range(3):
        y_ovre = y_fog + 0.35 if sida == "v" else min(y_fog + 0.35, 1.1)   # högra benet går in i bågen ovanför ~1,2
        b0, b1 = mittlinje(hp, x0, bas + y_ovre, bas + y_fog, sida)
        if sida == "h" and y_ovre - y_fog < 0.2:
            b0, b1 = mittlinje(hp, x0, bas + 1.1, bas + 0.7, sida)
            b1 = b0 + (b1 - b0) * (1.1 - y_fog) / 0.4
        vinkel_ben = np.degrees(np.arctan2(*(b1 - b0)[::-1]))
        skala = SKALA
        k = affinity.rotate(sp, vinkel_ben - vinkel_sp, origin=tuple(a1))
        k = affinity.scale(k, skala, skala, origin=tuple(a1))
        k = affinity.translate(k, *(b1 - a1))
        y_fog += (bas - 0.03) - k.bounds[1]
    print(sida, "vridning", round(vinkel_ben - vinkel_sp, 1), "fog", round(y_fog, 3))
    k = unary_union([k.buffer(-RUNDA).buffer(RUNDA), k.intersection(box(x0 - 2, bas + y_fog - 0.3, x0 + 6, bas + 5))])
    k = k.intersection(box(x0 - 2, bas - 1, x0 + 6, bas + y_fog + 0.13))
    kb = kanter(hp, x0, bas + y_fog - 0.25, sida)
    mitt_x = kb.mean()
    if sida == "v":
        bort = unary_union([box(x0 - 1, bas - 1, x0 + mitt_x, bas + y_fog - 0.25),
                            box(x0 - 1, bas - 1, x0 + BEN_X, bas + 0.3)])
    else:
        # hela benet under fogen ersätts (benet smalnar av nedtill och skulle ge ett hack)
        bort = box(x0 + kb[0] - 0.3, bas - 1, x0 + 6, bas + y_fog - 0.25)
    return k, bort, dict(vinkel=vinkel_ben - vinkel_sp, a1=np.array(a1), skala=skala, t=np.array(b1 - a1),
                         sx=sx, knorr=k, y_fog=y_fog)


def speglad_knorr(hp, x0, bas):
    """h med toppknorren speglad ner till vänstra benet (och, om HOGER_KNORR,
    vriden ner till högra benet så att den pekar åt höger)."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    sidor = ["v", "h"] if HOGER_KNORR else ["v"]
    delar = [en_knorr(hp, x0, bas, s) for s in sidor]
    utan_fot = hp
    for _, bort, _ in delar:
        utan_fot = utan_fot.difference(bort)
    SENAST.clear()
    SENAST.update(utan_fot=utan_fot, knorrar=[d for _, _, d in delar])
    ny = unary_union([utan_fot] + [k for k, _, _ in delar]).buffer(0.05).buffer(-0.05)
    # mjukare hack under knopparna (bara nedtill)
    y_lag = min(d["y_fog"] for _, _, d in delar) - 0.3
    lag = box(x0 - 2, bas - 1, x0 + 6, bas + y_lag)
    mjuk = ny.buffer(0.12).buffer(-0.12).buffer(-0.1).buffer(0.1).intersection(lag)
    return unary_union([ny.difference(lag), mjuk]).buffer(0.005).buffer(-0.005)


def tillbaka(P, kn):
    """Var i originalet en punkt i en speglad knorr kommer ifrån."""
    v = np.radians(-kn["vinkel"]); a1 = kn["a1"]
    q = (P - kn["t"] - a1) / kn["skala"]
    q = np.column_stack([np.cos(v) * q[:, 0] - np.sin(v) * q[:, 1], np.sin(v) * q[:, 0] + np.cos(v) * q[:, 1]]) + a1
    return q * [kn["sx"], -1]


def h_3d(h, rut=0.01):
    """Nytt h i 3D: din egen ovansida (höjdfält från originalet) överallt; i
    knorren hämtas höjden från toppknorren via samma spegling/vridning som i 2D."""
    from shapely.ops import unary_union
    from PIL import Image, ImageDraw
    from skimage import measure
    from scipy import ndimage
    z0, z1 = h.bounds[:, 2]
    s = h.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4)); hp = unary_union(list(p.polygons_full))
    x0 = h.bounds[0, 0]
    ny = speglad_knorr(hp, x0, 0.0)
    gx0, gy0, gx1, gy1 = np.array(ny.bounds) + [-0.1, -0.1, 0.1, 0.1]
    xs, ys = np.arange(gx0, gx1, rut), np.arange(gy0, gy1, rut)
    X, Y = np.meshgrid(xs, ys)
    P = np.column_stack([X.ravel(), Y.ravel()])

    def hojd(Q):
        o = np.column_stack([Q, np.full(len(Q), z1 + 1)])
        loc, ri, _ = h.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(Q), 1)), multiple_hits=False)
        Z = np.zeros(len(Q)); Z[ri] = loc[:, 2] - z0
        return Z

    def rast(g):
        b = Image.new("1", (len(xs), len(ys)), 0); d = ImageDraw.Draw(b)
        for q in getattr(g, "geoms", [g]):
            d.polygon([((x - gx0) / rut, (y - gy0) / rut) for x, y in q.exterior.coords], fill=1)
            for i in q.interiors:
                d.polygon([((x - gx0) / rut, (y - gy0) / rut) for x, y in i.coords], fill=0)
        return np.array(b, bool).ravel()

    i_ny, i_beh = rast(ny), rast(SENAST["utan_fot"])
    # höjd från benet/resten (behållna delen) och från knorrarna (via speglingen)
    Zb = np.zeros(len(P)); Zb[i_beh] = hojd(P[i_beh])
    Zk = np.zeros(len(P)); i_kn = np.zeros(len(P), bool)
    for kn in SENAST["knorrar"]:
        ik = rast(kn["knorr"]); i_kn |= ik
        Zk[ik] = np.maximum(Zk[ik], hojd(tillbaka(P[ik], kn)))
    sh = X.shape
    Zb, Zk = Zb.reshape(sh), Zk.reshape(sh)
    beh, kn, i_ny = i_beh.reshape(sh) & (Zb > 1e-3), i_kn.reshape(sh) & (Zk > 1e-3), i_ny.reshape(sh)
    # mjuk övergång i fogen: vikter efter avstånd in från respektive dels kant
    wb = np.clip(ndimage.distance_transform_edt(beh) * rut / 0.2, 0, 1) ** 2
    wk = np.clip(ndimage.distance_transform_edt(kn) * rut / 0.2, 0, 1) ** 2
    # där bara en del finns gäller den delen helt
    wb = np.where(beh & ~kn, 1.0, wb); wk = np.where(kn & ~beh, 1.0, wk)
    summa = wb + wk
    Z = np.where(summa > 0, (wb * Zb + wk * Zk) / np.maximum(summa, 1e-9), 0.0)
    # fogar/utjämningar som inte finns i någon av delarna: fyll med grannarnas höjd
    saknas = i_ny & (Z < 1e-3)
    if saknas.any():
        idx = ndimage.distance_transform_edt(saknas | ~i_ny, return_distances=False, return_indices=True)
        Z = np.where(saknas, Z[tuple(idx)], Z)
    Z = np.where(i_ny, Z, 0.0)
    # lätt utjämning bara i fogområdet
    fog = ndimage.binary_dilation(beh & kn, iterations=10) | ndimage.binary_dilation(saknas, iterations=4)
    Zs = ndimage.gaussian_filter(Z, 2.0) / np.maximum(ndimage.gaussian_filter(i_ny.astype(float), 2.0), 1e-6)
    vikt = ndimage.gaussian_filter(fog.astype(float), 3.0)
    Z = np.where(i_ny, Z * (1 - vikt) + Zs * vikt, 0.0)
    # höjdfält -> sluten mesh (platt baksida)
    Zp = np.pad(Z, 2)
    zs = -rut + np.arange(int(Z.max() / (rut / 2)) + 4) * (rut / 2)
    falt = np.minimum(Zp[:, :, None] - zs[None, None, :], zs[None, None, :])
    falt = np.where(Zp[:, :, None] > 0.003, falt, -0.05)
    v, f, _, _ = measure.marching_cubes(falt.astype(np.float32), 0.0, spacing=(rut, rut, rut / 2))
    v = np.column_stack([gx0 - 2 * rut + v[:, 1], gy0 - 2 * rut + v[:, 0], z0 + zs[0] + v[:, 2]])
    m = trimesh.Trimesh(v, f[:, ::-1]); m.merge_vertices(); m.update_faces(m.nondegenerate_faces())
    trimesh.smoothing.filter_taubin(m, iterations=8)
    m.vertices[:, 2] = np.maximum(m.vertices[:, 2], z0)
    m.fix_normals()
    m = m.simplify_quadric_decimation(face_count=150000)
    if not m.is_watertight:
        from gemensam_sving import laga
        m = laga(m)
    return m


def main():
    mapp, bild = sys.argv[1:3]
    h = trimesh.load(f"{mapp}/h.stl"); b = trimesh.load(f"{mapp}/b.stl")
    hbas, bbas = 0.0, -10.0
    d = forskjutning(h, b, hbas, bbas)
    print("flytt", d.round(3))
    # 2D
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from shapely.geometry import Polygon, box
    from shapely import affinity
    from shapely.ops import unary_union
    def poly(m):
        z0, z1 = m.bounds[:, 2]
        s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
        p, _ = s.to_2D(to_2D=np.eye(4))
        return unary_union(list(p.polygons_full))
    hp, bp = poly(h), poly(b)
    bx0 = b.bounds[0, 0]
    ny = speglad_knorr(hp, h.bounds[0, 0], hbas)
    fig, axs = plt.subplots(1, 2, figsize=(10, 5.5))
    for ax, g, t, f in ((axs[0], hp, "h nu", "#555"), (axs[1], ny, "h med knorr", "k")):
        for q in getattr(g, "geoms", [g]):
            x, y = q.exterior.xy; ax.fill(np.array(x) - h.bounds[0, 0], y, color=f, lw=0)
            for i in q.interiors:
                x, y = i.xy; ax.fill(np.array(x) - h.bounds[0, 0], y, color="white", lw=0)
        ax.axhline(0, color="#4a7be0", lw=0.6); ax.axhline(2, color="#4a7be0", lw=0.6); ax.axhline(4, color="#4a7be0", lw=0.6)
        ax.set_xlim(-0.5, 2.6); ax.set_ylim(-0.3, 4.3); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t)
    plt.savefig(bild, bbox_inches="tight", facecolor="white")
    if len(sys.argv) > 3:
        import manifold3d as mf
        from gemensam_sving import laga
        from justera import slapp_i_hal
        bx0, bz0 = b.bounds[0, 0], b.bounds[0, 2]
        lada = trimesh.creation.box(bounds=[[bx0 - 1, bbas - 1, bz0 - 1], [bx0 + LADA[0], bbas + LADA[1], bz0 + 2]])
        bit = b.intersection(lada, engine="manifold")
        bit.apply_translation([d[0], d[1], h.bounds[0, 2] - b.bounds[0, 2]])
        ny3 = laga(trimesh.boolean.union([h, bit], engine="manifold"))
        ny3, _ = slapp_i_hal(ny3)
        ny3 = laga(ny3)
        print("vattentät", ny3.is_watertight)
        ny3.export(sys.argv[3])


if __name__ == "__main__":
    main()
