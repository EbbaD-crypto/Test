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


def kanter(poly, x0, y):
    """Vänstra benets/stapelns vänster- och högerkant på höjden y (från h:ets vänsterkant)."""
    from shapely.geometry import LineString
    snitt = poly.intersection(LineString([(x0 - 1, y), (x0 + BEN_X + 0.4, y)]))
    delar = sorted(getattr(snitt, "geoms", [snitt]), key=lambda g: g.bounds[0])
    return np.array(delar[0].bounds)[[0, 2]] - x0


BIT_FRAN = 2.9            # knorren + stapeln ovanför denna höjd speglas
SKALA = 1.05              # ger jämn tjocklek i benet (ca 0,6 hela vägen ner)
RUNDA = 0.08              # rundar av knorrens kula en aning
OVERLAPP = 0.25           # biten går så här långt upp i benet så att fogen inte syns


def mittlinje(poly, x0, y0, y1):
    """Stapelns/benets mittpunkt på två höjder (absoluta koordinater)."""
    p0, p1 = [np.array([kanter(poly, x0, y).mean() + x0, y]) for y in (y0, y1)]
    return p0, p1


def speglad_knorr(hp, x0, bas):
    """Knorren + en bit stapel speglas upp-och-ner och VRIDS sedan så att
    stapelbiten får exakt benets lutning (vridning, inte snedning, så att
    kulan behåller sin runda form). Biten skalas till benets tjocklek och
    placeras så att knorrens nederkant hamnar strax under baslinjen."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    from shapely import affinity
    bit = hp.intersection(box(x0 - 1, bas + BIT_FRAN - OVERLAPP, x0 + BEN_X + 0.6, bas + 5))
    # stapelbitens axel (uppifrån och ned) och benets axel
    s0, s1 = mittlinje(hp, x0, bas + BIT_FRAN + 0.35, bas + BIT_FRAN + 0.05)
    bredd_st = np.diff(kanter(hp, x0, bas + BIT_FRAN + 0.05))[0]
    # spegla kring y = 0 (upp-och-ner)
    sp = affinity.scale(bit, 1, -1, origin=(0, 0))
    a0, a1 = s0 * [1, -1], s1 * [1, -1]           # stapelns axel i den speglade biten (a1 = fogen)
    vinkel_sp = np.degrees(np.arctan2(*(a0 - a1)[::-1]))    # bitens riktning nedåt från fogen
    y_fog = 1.0
    for _ in range(3):
        b0, b1 = mittlinje(hp, x0, bas + y_fog + 0.35, bas + y_fog)
        vinkel_ben = np.degrees(np.arctan2(*(b1 - b0)[::-1]))   # benets riktning nedåt vid fogen
        bredd_ben = np.diff(kanter(hp, x0, bas + y_fog))[0]
        skala = SKALA if SKALA else bredd_ben / bredd_st
        k = affinity.rotate(sp, vinkel_ben - vinkel_sp, origin=tuple(a1))
        k = affinity.scale(k, skala, skala, origin=tuple(a1))
        k = affinity.translate(k, *(b1 - a1))
        y_fog += (bas - 0.03) - k.bounds[1]        # justera så att nederkanten hamnar på -0.03
    print("vridning", round(vinkel_ben - vinkel_sp, 1), "skala", round(skala, 3), "fog", round(y_fog, 3))
    # pyttelite rundare kula (bara nedtill, så att fogen mot benet inte påverkas)
    k = unary_union([k.buffer(-RUNDA).buffer(RUNDA), k.intersection(box(x0 - 1, bas + y_fog - 0.3, x0 + BEN_X + 1, bas + 5))])
    k = k.intersection(box(x0 - 1, bas - 1, x0 + BEN_X + 1, bas + y_fog + 0.13))   # ingen kant som sticker ut ovanför fogen
    # bara benets vänstra del tas bort (där knorren sitter); högerkanten går ner i kulan
    mitt_x = kanter(hp, x0, bas + y_fog - 0.25).mean()
    utan_fot = hp.difference(box(x0 - 1, bas - 1, x0 + mitt_x, bas + y_fog - 0.25)).difference(
        box(x0 - 1, bas - 1, x0 + BEN_X, bas + 0.3))   # nedersta delen av benet ersätts helt av kulan
    ny = unary_union([utan_fot, k]).buffer(0.05).buffer(-0.05)
    # mjukare hack under knoppen (bara nedtill)
    lag = box(x0 - 1, bas - 1, x0 + BEN_X, bas + y_fog - 0.3)
    mjuk = ny.buffer(0.12).buffer(-0.12).buffer(-0.06).buffer(0.06).intersection(lag)
    return unary_union([ny.difference(lag), mjuk]).buffer(0.005).buffer(-0.005)


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
