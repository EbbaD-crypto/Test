"""Formpar för tömningsgjutning (3D-printas, gips hälls i, mastern smälts ur).

Samma princip som dina s- och t-former: två printade lådor.
  * Framsida: bokstaven (platt baksida ner) står på en bottenplatta inne i en
    låda. Gipset blir den främre formhalvan med bokstavens hålighet.
  * Baksida: bottenplatta med två koner. I gipset blir de trattar från
    bokstavens baksida ut genom gipset. Där fylls och töms leran.
Ändringar mot s/t-formerna (som vi pratade om):
  * trattarnas smala ände TRATT_HALS mm (inte 11,5), så halsen inte slammar igen
    när godset växer till ~4 mm
  * konerna är KON_OVER mm högre än lådväggen, så trattarna är öppna baktill
  * trattarna placeras automatiskt så långt isär som möjligt i strecken (nära
    ändarna), med minst KANT mm gips mellan halsen och bokstavens kant
  * tapparna är knopp och grop: framsidans platta har knoppar, baksidans
    platta gropar på speglade platser -> gipshalvorna låser mot varandra.
    Tre tappar osymmetriskt, så halvorna bara passar ihop på ett sätt.
  * lådans innerväggar lutar VAGG_SLAPP grader utåt så gipset släpper.
Baksidan är spegelvänd så att allt hamnar rätt när gipsbiten vänds mot framsidan.

    python3 form.py <bokstav.stl> <utmapp> [namn]
Mått i mm (Bambu Studio läser STL i mm).
"""
import os
import sys
import numpy as np
import trimesh
import manifold3d as mf
from scipy import ndimage

SKALA = float(os.environ.get("SKALA", 61.0))   # mm per enhet: x-höjd ca 122 mm (din nuvarande storlek)
MARGINAL = 22.0       # gips mellan bokstaven och lådväggen (som ditt t)
MIN_MARGINAL = 6.0    # får den inte plats krymper kanten, men aldrig under detta
BADD = 256.0          # Bambu Lab A1: 256 x 256 mm
SAKERHET = 10.0      # lådan blir högst 246 mm, lite luft runt om på bädden
VAGG = 1.0            # lådväggens tjocklek (2 varv; dina gamla lådor hade ca 0,5 mm)
GIPS = 40.0           # gipsets tjocklek (lådans höjd över plattan), som i dina former
PLATTA_FRAM = 1.0
PLATTA_BAK = 3.0      # lite tjockare, så att groparna får plats
VAGG_SLAPP = 3.0      # grader (gipset släpper lättare)
HORN_R = 8.0          # rundade innerhörn (skarpa hörn låser gipset)
TEXT_H = 9.0          # texthöjd på väggarnas insida (mm)
TEXT_DJUP = 0.6       # så mycket står texten ut från väggen (blir gravyr i gipset)
TEXT_Z = 11.0         # textens mitt över plattan
TRATT_HALS = 19.0     # smala änden (mot bokstaven)
TRATT_TOPP = 50.0     # breda änden
KON_OVER = 3.0        # konen sticker upp så mycket över gipset
KANT = 6.0            # minst så mycket gips mellan trattens hals och bokstavens kant
TAPP_D, TAPP_H = 14.0, 2.2
SANK = 0.3            # bokstaven sänks ner så mycket i plattan (sammanfogning)
RUT = 0.5             # mm, för att hitta tratt-platser
SYMBOL_H = 18.0       # märket: bokstaven i liten storlek (höjd i mm)
SYMBOL_DJUP = 1.5     # så djupt sitter märket i baksidans gips
SYMBOL_SPEL = 0.4     # fri kant runt märket vid placeringen
SYMBOL_SLAPP = 0.4    # märket smalnar av så mycket ut mot toppen (ca 15° släpp)


def till_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def till_tm(man):
    g = man.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts))


def kalott(x, y, z):
    """Sfärisk kalott (diameter TAPP_D, höjd TAPP_H) med platt sida på höjden z."""
    r, h = TAPP_D / 2, TAPP_H
    R = (r * r + h * h) / (2 * h)
    klot = mf.Manifold.sphere(R, 96).translate([x, y, z + h - R])
    return klot ^ mf.Manifold.cube([4 * R, 4 * R, h + 1]).translate([x - 2 * R, y - 2 * R, z])


def rund_rektangel(bx, by, r):
    """Rektangel centrerad i origo med rundade hörn (som CrossSection)."""
    from shapely.geometry import box
    p = box(-bx / 2 + r, -by / 2 + r, bx / 2 - r, by / 2 - r).buffer(r, 32)
    return mf.CrossSection([list(p.exterior.coords)[:-1][::-1] if not p.exterior.is_ccw else list(p.exterior.coords)[:-1]])


def lada(bx, by, platta):
    """Platta + väggar. Väggarna lutar VAGG_SLAPP grader utåt uppåt (lika tjocka hela
    vägen) och innerhörnen är rundade."""
    d = (GIPS + 1) * np.tan(np.radians(VAGG_SLAPP))
    def skal(b): return (b + 2 * d) / b
    ut_b, ut_h = bx + 2 * VAGG, by + 2 * VAGG
    botten = mf.Manifold.extrude(rund_rektangel(ut_b, ut_h, HORN_R + VAGG), platta).translate([bx / 2, by / 2, 0])
    yttre = (mf.Manifold.extrude(rund_rektangel(ut_b, ut_h, HORN_R + VAGG), GIPS, scale_top=(skal(ut_b), skal(ut_h)))
             .translate([bx / 2, by / 2, platta]))
    inre = (mf.Manifold.extrude(rund_rektangel(bx, by, HORN_R), GIPS + 1, scale_top=(skal(bx), skal(by)))
            .translate([bx / 2, by / 2, platta]))
    return botten + (yttre - inre)


def text_yta(text, hojd):
    """Textens kontur (shapely) i mm, centrerad i origo, läsbar från betraktaren."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from shapely.geometry import Polygon
    from shapely import affinity
    typsnitt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Jost-600.ttf")   # Futura-liknande
    tp = TextPath((0, 0), text, size=10, prop=FontProperties(fname=typsnitt))
    g = None
    for ring in tp.to_polygons():
        if len(ring) < 3:
            continue
        p = Polygon(ring).buffer(0)
        g = p if g is None else g.symmetric_difference(p)
    x0, y0, x1, y1 = g.bounds
    k = hojd / (y1 - y0)
    g = affinity.scale(g, k, k, origin=(0, 0))
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, -(x0 + x1) / 2, -(y0 + y1) / 2)


def vaggtext(text, bx, by, platta):
    """Texten upphöjd på alla fyra väggarnas insida, läsbar på gipset utifrån.
    Två lager (bredare nedtill) ger sluttande kanter så att gipset släpper."""
    g = text_yta(text, TEXT_H)
    def prisma(yta, w0, w1):
        delar = []
        for q in getattr(yta, "geoms", [yta]):
            ringar = [list(q.exterior.coords)[:-1]] + [list(i.coords)[:-1] for i in q.interiors]
            delar.append(mf.Manifold.extrude(mf.CrossSection(ringar, mf.FillRule.EvenOdd), w1 - w0).translate([0, 0, w0]))
        return mf.Manifold.batch_boolean(delar, mf.OpType.Add)
    # lokalt: x = läsriktning, y = uppåt, z = in i lådan (w)
    lokal = prisma(g.buffer(0.12), -0.5, TEXT_DJUP * 0.5) + prisma(g.buffer(-0.12), -0.5, TEXT_DJUP)
    tan = np.tan(np.radians(VAGG_SLAPP))
    z0 = platta + TEXT_Z
    vaggar = [((bx / 2, 0), (1, 0), (0, 1)), ((bx / 2, by), (-1, 0), (0, -1)),
              ((0, by / 2), (0, -1), (1, 0)), ((bx, by / 2), (0, 1), (-1, 0))]
    ut = []
    for (ox, oy), (ux, uy), (nx, ny) in vaggar:
        def flytta(p, ox=ox, oy=oy, ux=ux, uy=uy, nx=nx, ny=ny):
            u, v, w = p
            z = z0 + v
            w = w - (z - platta) * tan            # följer väggens lutning
            return [ox + u * ux + w * nx, oy + u * uy + w * ny, z]
        w = lokal.warp(flytta)
        if w.volume() < 0:                         # spegelvänd bas -> vänd trianglarna
            tm = till_tm(w); tm.invert(); w = till_mf(tm)
        ut.append(w)
    return mf.Manifold.batch_boolean(ut, mf.OpType.Add)


def fotavtryck(m):
    """Bokstavens kontur uppifrån som mask (RUT mm)."""
    x0, y0 = m.bounds[0, :2]
    xs, ys = np.arange(x0, m.bounds[1, 0], RUT), np.arange(y0, m.bounds[1, 1], RUT)
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, m.bounds[1, 2] + 1)])
    _, ri, _ = m.ray.intersects_location(o, np.tile([0, 0, -1.0], (X.size, 1)), multiple_hits=False)
    mask = np.zeros(X.size, bool); mask[ri] = True
    return mask.reshape(X.shape), X, Y


def kontur_poly(m):
    """Bokstavens kontur uppifrån (snitt nära baksidan) som shapely-yta."""
    from shapely.ops import unary_union
    z0, z1 = m.bounds[:, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.05 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4))
    return unary_union(list(p.polygons_full))


def symbol_form(m):
    """Bokstavens kontur uppifrån, skalad till SYMBOL_H hög, centrerad i origo."""
    from shapely.ops import unary_union
    from shapely import affinity
    z0, z1 = m.bounds[:, 2]
    s = m.section(plane_origin=[0, 0, z0 + 0.15 * (z1 - z0)], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.eye(4))
    g = unary_union(list(p.polygons_full))
    k = SYMBOL_H / (g.bounds[3] - g.bounds[1])
    g = affinity.scale(g, k, k, origin=g.centroid)
    return affinity.translate(g, -g.centroid.x, -g.centroid.y)


def trappa(g, hojd, smalnar, z0, upp=True):
    """Märket som tunna lager som smalnar av (släpp). upp=False: smalast nedtill
    (för gropen i baksidans platta)."""
    from shapely.geometry import Polygon
    n = 6
    delar = []
    for i in range(n):
        lager = g.buffer(-smalnar * (i + 0.5) / n, join_style=1)
        if lager.is_empty:
            continue
        ytor = []
        for q in getattr(lager, "geoms", [lager]):
            ytor.append(list(q.exterior.coords)[:-1][::1 if q.exterior.is_ccw else -1])
            for h in q.interiors:
                ytor.append(list(h.coords)[:-1][::-1 if h.is_ccw else 1])
        # inkapslade prismor från basen (inga sammanfallande sidoytor)
        hi = (i + 1) * hojd / n
        # nedåt (grop): prismorna går 1 mm upp ovanför plattan så att snittet blir rent
        z = z0 if upp else z0 - hi
        delar.append(mf.Manifold.extrude(mf.CrossSection(ytor), hi + (0 if upp else 1)).translate([0, 0, z]))
    return mf.Manifold.batch_boolean(delar, mf.OpType.Add)


def symbol_plats(g, b, bx, by, hinder):
    """Mittpunkt för märket: i ett hörn, fritt från bokstaven, tapparna och trattarna."""
    from shapely import affinity
    from shapely.geometry import box
    lada_in = box(3, 3, bx - 3, by - 3)
    kand = [(x, y) for y in np.arange(by - 3, 3, -1.0) for x in np.arange(3, bx - 3, 1.0)]
    kand.sort(key=lambda p: np.hypot(p[0], by - p[1]))   # närmast övre vänstra hörnet först
    for x, y in kand:
        s = affinity.translate(g.buffer(SYMBOL_SPEL), x, y)
        if lada_in.contains(s) and not s.intersects(hinder):
            return x, y
    raise SystemExit("hittar ingen plats för märket")


PRICK_AVSTAND = 15.0  # gips mellan pricken och bokstaven / väggen
HORN = 32.0           # hörnen hålls fria för tapparna


def placera_prickar(b, prickar, bx, by):
    """Prickarna läggs på en ledig plats i lådan (läget spelar ingen roll, de gjuts
    som egna bitar). Finns ingen plats görs lådan större åt det håll som ryms."""
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    upptaget = kontur_poly(b).buffer(PRICK_AVSTAND)
    maxsida = BADD - SAKERHET - 2 * VAGG
    delar = [b]
    for p in prickar:
        r = p.extents[:2].max() / 2
        for forsok in range(3):
            horn = unary_union([box(x - HORN, y - HORN, x + HORN, y + HORN) for x in (0, bx) for y in (0, by)])
            fri = box(0, 0, bx, by).buffer(-(PRICK_AVSTAND + r)).difference(upptaget.buffer(r)).difference(horn.buffer(r))
            if not fri.is_empty and fri.area > 1:
                c = fri.representative_point()
                # så långt från bokstaven som möjligt inom den fria ytan
                from shapely import prepared
                fp = prepared.prep(fri)
                kand = [c] + [Point(x, y) for x in np.arange(0, bx, 4) for y in np.arange(0, by, 4) if fp.contains(Point(x, y))]
                c = max(kand, key=lambda q: min(upptaget.distance(q), 30))
                break
            # gör lådan större
            if bx + 2 * r + PRICK_AVSTAND <= maxsida and (bx <= by or by + 2 * r + PRICK_AVSTAND > maxsida):
                bx += 2 * r + PRICK_AVSTAND
            elif by + 2 * r + PRICK_AVSTAND <= maxsida:
                by += 2 * r + PRICK_AVSTAND
            else:
                raise SystemExit("ingen plats för pricken")
        else:
            raise SystemExit("ingen plats för pricken")
        q = p.copy()
        q.apply_translation([c.x - q.bounds[:, 0].mean(), c.y - q.bounds[:, 1].mean(), b.bounds[0, 2] - q.bounds[0, 2]])
        delar.append(q)
        upptaget = upptaget.union(Point(c.x, c.y).buffer(r + PRICK_AVSTAND))
        print(f"prick vid ({c.x:.0f}, {c.y:.0f}) mm, låda {bx:.0f} x {by:.0f}")
    return bx, by, trimesh.util.concatenate(delar)


def tratt_platser(m):
    """Två trattar i bokstaven (så långt isär som möjligt) och en mitt i varje prick."""
    from scipy.spatial import ConvexHull
    mask, X, Y = fotavtryck(m)
    delar, n = ndimage.label(mask)
    storlek = ndimage.sum(mask, delar, range(1, n + 1))
    platser, maxd = [], 0
    for i in np.argsort(storlek)[::-1]:
        if storlek[i] * RUT ** 2 < 100:          # smulor
            continue
        d = ndimage.distance_transform_edt(delar == i + 1) * RUT
        maxd = max(maxd, d.max())
        ok = d >= TRATT_HALS / 2 + KANT
        if not platser:                          # själva bokstaven
            P = np.column_stack([X[ok], Y[ok]])
            if len(P) < 2:
                raise SystemExit(f"strecken är för smala för {TRATT_HALS} mm trattar")
            H = P[ConvexHull(P).vertices]
            D = np.linalg.norm(H[:, None] - H[None], axis=2)
            i0, j0 = np.unravel_index(D.argmax(), D.shape)
            platser += [H[i0], H[j0]]
        else:                                    # prick: en tratt mitt i
            if not ok.any():
                raise SystemExit("pricken är för liten för en tratt")
            k = d.argmax()
            platser.append(np.array([X.ravel()[k], Y.ravel()[k]]))
    return platser, maxd


def main():
    fil, ut = sys.argv[1:3]
    namn = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(os.path.basename(fil.split(',')[0]))[0]
    os.makedirs(ut, exist_ok=True)
    filer = fil.split(",")          # t.ex. j.stl,j-prick.stl: prickar gjuts i samma form
    original = trimesh.load(filer[0])
    b = original.copy()
    b.apply_scale(SKALA)
    prickar = [trimesh.load(f).apply_scale(SKALA) for f in filer[1:]]
    # får lådan inte plats rakt vrids bokstaven (diagonalt) så att lådan blir minst
    plats = BADD - SAKERHET - 2 * (MARGINAL + VAGG)
    if b.extents[:2].max() > plats:
        from scipy.spatial import ConvexHull
        P = b.vertices[:, :2]; H = P[ConvexHull(P).vertices]
        def sida(a):
            c, s = np.cos(a), np.sin(a)
            return np.ptp(H @ np.array([[c, -s], [s, c]]).T, 0).max()
        a = min(np.radians(np.arange(0, 180, 0.5)), key=sida)
        b.apply_transform(trimesh.transformations.rotation_matrix(a, [0, 0, 1]))
        print(f"vriden {np.degrees(a):.1f}° för att få plats")
    # kanten krymper (bara där det behövs) så att lådan ryms på bädden
    mx, my = [min(MARGINAL, (BADD - SAKERHET - e) / 2 - VAGG) for e in b.extents[:2]]
    if min(mx, my) < MIN_MARGINAL:
        raise SystemExit(f"får inte plats på bädden: {b.extents[:2].max():.1f} mm bokstav")
    if min(mx, my) < MARGINAL:
        print(f"smalare kant: {mx:.1f} mm (sidled), {my:.1f} mm (höjdled)")
    bx = b.extents[0] + 2 * mx
    by = b.extents[1] + 2 * my
    b.apply_translation([mx - b.bounds[0, 0], my - b.bounds[0, 1], PLATTA_FRAM - SANK - b.bounds[0, 2]])
    if prickar:
        bx, by, b = placera_prickar(b, prickar, bx, by)

    tappar = [(15, 15), (bx - 15, 15), (bx - 15, by - 15)]   # tre hörn, osymmetriskt
    # framsida
    fram = lada(bx, by, PLATTA_FRAM) + till_mf(b)
    for x, y in tappar:
        fram = fram + kalott(x, y, PLATTA_FRAM - 0.01)
    # baksida: speglad i x (gipsbiten vänds runt y-axeln mot framsidan)
    platser, maxd = tratt_platser(b)
    bak = lada(bx, by, PLATTA_BAK)
    h = GIPS + KON_OVER
    for x, y in platser:
        kon = mf.Manifold.cylinder(h + 0.01, TRATT_HALS / 2, TRATT_TOPP / 2, 128).translate([bx - x, y, PLATTA_BAK - 0.01])
        bak = bak + kon
    for x, y in tappar:
        bak = bak - kalott(0, 0, 0).mirror([0, 0, 1]).translate([bx - x, y, PLATTA_BAK + 0.01])   # grop: platt sida uppåt
    # märke: bokstaven nedsänkt i baksidans gips (läses rättvänt där). Ett upphöjt
    # märke skulle kräva en grop i framsidan för att halvorna ska sluta tätt.
    # Bokstaven är osymmetrisk, så märket visar också hur halvorna ska vändas.
    from shapely.geometry import Point
    from shapely.ops import unary_union
    from shapely import affinity
    g = symbol_form(original)
    hinder = kontur_poly(b).buffer(4)
    hinder = unary_union([hinder] + [Point(x, y).buffer(TAPP_D / 2 + 3) for x, y in tappar]
                         + [Point(x, y).buffer(TRATT_HALS / 2 + 3) for x, y in platser])
    sx, sy = symbol_plats(g, b, bx, by, hinder)
    gs = affinity.scale(g, -1, 1, origin=(0, 0))
    bak = bak + trappa(gs, SYMBOL_DJUP, SYMBOL_SLAPP, PLATTA_BAK - 0.01).translate([bx - sx, sy, 0])
    print(f"märke vid ({sx:.0f}, {sy:.0f}) mm")
    fram = fram + vaggtext(f"{namn} framsida", bx, by, PLATTA_FRAM)
    bak = bak + vaggtext(f"{namn} baksida", bx, by, PLATTA_BAK)
    for del_, n in ((fram, "framsida"), (bak, "baksida")):
        t = till_tm(del_)
        t.merge_vertices()
        t.update_faces(t.nondegenerate_faces())
        if not t.is_watertight:
            from gemensam_sving import laga
            t = laga(t)
        t.fix_normals()
        t.export(os.path.join(ut, f"form_{namn}_{n}.stl"))
        print(f"{n}: {t.extents.round(1)} mm, vattentät {t.is_watertight}, delar {len(t.split(only_watertight=False))}")
    print("trattar (framsidans koordinater):", [tuple(np.round(p, 1)) for p in platser],
          f"bredaste stället i strecket {2 * maxd:.1f} mm")
    print(f"gips över bokstaven: {GIPS - (b.bounds[1, 2] - PLATTA_FRAM):.1f} mm")


if __name__ == "__main__":
    main()
