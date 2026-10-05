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
MIN_MARGINAL = 10.0   # får den inte plats krymper kanten, men aldrig under detta
BADD = 256.0          # Bambu Lab A1: 256 x 256 mm
SAKERHET = 2.0
VAGG = 2.5            # lådväggens tjocklek
GIPS = 40.0           # gipsets tjocklek (lådans höjd över plattan), som i dina former
PLATTA_FRAM = 3.0
PLATTA_BAK = 7.0      # tjockare, så att groparna får plats
VAGG_SLAPP = 1.5      # grader
TRATT_HALS = 19.0     # smala änden (mot bokstaven)
TRATT_TOPP = 50.0     # breda änden
KON_OVER = 3.0        # konen sticker upp så mycket över gipset
KANT = 6.0            # minst så mycket gips mellan trattens hals och bokstavens kant
TAPP_D, TAPP_H = 15.0, 5.0
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


def lada(bx, by, platta):
    """Platta + väggar. Insidan lutar VAGG_SLAPP grader utåt uppåt."""
    ut = mf.Manifold.cube([bx + 2 * VAGG, by + 2 * VAGG, platta + GIPS]).translate([-VAGG, -VAGG, 0])
    d = GIPS * np.tan(np.radians(VAGG_SLAPP))
    # extrude skalar runt origo -> centrera först
    inner = (mf.Manifold.extrude(mf.CrossSection([[(-bx / 2, -by / 2), (bx / 2, -by / 2), (bx / 2, by / 2), (-bx / 2, by / 2)]]),
                                 GIPS + 1, scale_top=((bx + 2 * d) / bx, (by + 2 * d) / by))
             .translate([bx / 2, by / 2, platta]))
    return ut - inner


def fotavtryck(m):
    """Bokstavens kontur uppifrån som mask (RUT mm)."""
    x0, y0 = m.bounds[0, :2]
    xs, ys = np.arange(x0, m.bounds[1, 0], RUT), np.arange(y0, m.bounds[1, 1], RUT)
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, m.bounds[1, 2] + 1)])
    _, ri, _ = m.ray.intersects_location(o, np.tile([0, 0, -1.0], (X.size, 1)), multiple_hits=False)
    mask = np.zeros(X.size, bool); mask[ri] = True
    return mask.reshape(X.shape), X, Y


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


def tratt_platser(m):
    mask, X, Y = fotavtryck(m)
    d = ndimage.distance_transform_edt(mask) * RUT
    ok = d >= TRATT_HALS / 2 + KANT
    P = np.column_stack([X[ok], Y[ok]])
    if len(P) < 2:
        raise SystemExit(f"strecken är för smala för {TRATT_HALS} mm trattar")
    # de två platserna längst isär
    from scipy.spatial import ConvexHull
    H = P[ConvexHull(P).vertices]
    D = np.linalg.norm(H[:, None] - H[None], axis=2)
    i, j = np.unravel_index(D.argmax(), D.shape)
    return [H[i], H[j]], d.max()


def main():
    fil, ut = sys.argv[1:3]
    namn = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(os.path.basename(fil))[0]
    os.makedirs(ut, exist_ok=True)
    b = trimesh.load(fil)
    b.apply_scale(SKALA)
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
    g = symbol_form(trimesh.load(fil))
    mask, X, Y = fotavtryck(b)
    hinder = unary_union([Point(x, y).buffer(RUT) for x, y in zip(X[mask][::7], Y[mask][::7])]).buffer(4)
    hinder = unary_union([hinder] + [Point(x, y).buffer(TAPP_D / 2 + 3) for x, y in tappar]
                         + [Point(x, y).buffer(TRATT_HALS / 2 + 3) for x, y in platser])
    sx, sy = symbol_plats(g, b, bx, by, hinder)
    gs = affinity.scale(g, -1, 1, origin=(0, 0))
    bak = bak + trappa(gs, SYMBOL_DJUP, SYMBOL_SLAPP, PLATTA_BAK - 0.01).translate([bx - sx, sy, 0])
    print(f"märke vid ({sx:.0f}, {sy:.0f}) mm")
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
