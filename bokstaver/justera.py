"""Gör alfabetet från Nomad konsekvent och lättare att gjuta.

Utgår från a-z.30.sep.stl (alla bokstäver i en fil) och ändrar så lite som
möjligt:

1. Uppstaplar (b, d, f, h, k, l, t, L, !) blir 2 × x-höjden och lutar 3°.
2. Nedstaplar (g, j, p, q, y, f) blir 1,05 × x-höjden djupa och lutar 15°.
   Bara stapelns raka del sträcks; krokar och ändar flyttas oförändrade.
   Lutningen ändras bara i upp-/nedstapeln, med en mjuk övergång.
3. Alla hål (a, b, d, e, g, o, p, q) får minst SLAPP_HAL grader släppvinkel
   hela vägen ner till den platta baksidan. Material läggs bara till i
   hålets nedre kant; resten av ytan är exakt som originalet.

Bokstäver som inte behöver ändras sparas exakt som de är.

    python3 justera.py a-z.30.sep.stl justerade
"""
import os
import sys
import numpy as np
import trimesh
import manifold3d
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure

XHOJD = 2.0          # x-höjden i filens enheter
UPP = 2.0 * XHOJD    # uppstaplarnas höjd över baslinjen
NED = 1.05 * XHOJD   # nedstaplarnas djup under baslinjen
UPP_VINKEL = 3.0     # grader, lutning åt höger
NED_VINKEL = 15.0
SLAPP_HAL = 15.0     # minsta släppvinkel i hålen (grader från lodrätt)
RUT = 0.005          # rutnät för hålens släppkant (filens enheter)

# Bokstäverna identifieras på sitt läge i filen (nedre vänstra hörnet, x, y).
# baslinje = y för baslinjen. upp/ned: band (relativt baslinjen) där stapeln
# är rak och får sträckas, angivet som (änden närmast x-höjd/baslinje, bortre
# änden); bortom bandet flyttas formen oförändrad.
BOKSTAVER = {
    (-23.04, -10.00): dict(namn="b", bas=-10.00, upp=(2.3, 3.5)),
    (-17.99, -10.01): dict(namn="d1", bas=-10.01, upp=(2.3, 3.5)),
    (-16.85, -5.48): dict(namn="d2", bas=-5.48, upp=(2.3, 3.5)),
    (-10.76, -6.58): dict(namn="d3", bas=-6.58, upp=(2.3, 3.6)),
    (-19.07, -15.22): dict(namn="d4", bas=-15.22, upp=(2.3, 3.5)),
    (-15.06, -15.00): dict(namn="d5", bas=-15.00, upp=(2.3, 3.5)),
    (19.65, -0.06): dict(namn="h", bas=-0.06, upp=(2.3, 3.5)),
    (22.52, -0.09): dict(namn="k", bas=-0.09, upp=(2.3, 3.5)),
    (2.75, -19.96): dict(namn="l", bas=-19.96, upp=(1.0, 3.5)),
    (-3.77, -20.04): dict(namn="t1", bas=-20.04, upp=(2.3, 3.5)),
    (-1.72, -20.05): dict(namn="t2", bas=-20.05, upp=(2.3, 3.5)),
    (-26.68, -20.16): dict(namn="L", bas=-20.10, upp=(1.0, 3.5)),
    (-14.71, 1.31): dict(namn="utropstecken", bas=0.0, upp=(1.6, 3.6)),
    (12.35, -21.82): dict(namn="f", bas=-20.00, upp=(1.45, 1.95), ned=(-0.3, -1.3)),
    (-44.68, -1.73): dict(namn="g", bas=0.0, ned=(-0.1, -0.9)),
    (-32.76, -2.16): dict(namn="y", bas=0.0, ned=(-0.2, -1.2)),
    (-29.51, -2.15): dict(namn="j", bas=0.0, ned=(-0.2, -1.2)),
    (-27.42, -2.06): dict(namn="p", bas=0.0, ned=(-0.2, -1.6)),
    (-0.70, -2.45): dict(namn="q1", bas=0.0, ned=(-1.0, -2.1)),
    (1.76, -2.16): dict(namn="q2", bas=0.0, ned=(-1.0, -1.9)),
}
OVRIGA = {  # namn på bokstäver som inte har upp-/nedstaplar
    (-28.73, 8.74): "e1", (-26.38, 9.03): "e2", (-50.70, -0.09): "e3",
    (-40.03, -0.00): "s1", (-38.16, -0.04): "s2", (-30.01, -0.07): "s3",
    (-9.76, -0.04): "w1", (4.09, -0.06): "z", (6.37, -0.01): "x", (8.99, -0.01): "m",
    (-27.77, 2.15): "j-prick", (-14.84, 0.11): "utropstecken-prick", (3.66, -4.26): "punkt",
    (-21.27, -6.05): "c1", (-19.09, -5.97): "c2", (1.38, -9.06): "w2",
    (-28.31, -10.01): "a1", (-25.71, -10.02): "a2", (-20.28, -9.98): "c3",
    (-14.52, -9.97): "e4", (-11.90, -10.00): "e5", (-9.33, -10.04): "e6", (-5.18, -9.98): "e7",
    (-12.14, -13.31): "e8", (-32.71, -13.58): "bage", (-16.69, -13.54): "prick",
    (-16.48, -19.21): "s4", (-14.57, -19.17): "n", (-12.25, -19.25): "s5",
    (9.19, -17.67): "i-prick", (-6.02, -20.04): "r", (4.08, -20.00): "o",
    (6.35, -19.99): "v", (8.92, -19.95): "i", (-556.76, -1211.16): "langt-bort",
}


def hitta(tabell, p):
    for (x, y), v in tabell.items():
        if abs(p.bounds[0, 0] - x) < 0.03 and abs(p.bounds[0, 1] - y) < 0.03:
            return v
    return None


def ramp(t, a, b):
    """0 vid a, 1 vid b (mjuk), fungerar även om a > b."""
    s = np.clip((t - a) / (b - a), 0, 1)
    return s * s * (3 - 2 * s)


def integral(f, y, ref, n=4000):
    """∫_ref^y f(t) dt för varje y (tabellerat)."""
    lo, hi = min(y.min(), ref) - 1e-6, max(y.max(), ref) + 1e-6
    t = np.linspace(lo, hi, n)
    F = np.concatenate([[0], np.cumsum((f(t[1:]) + f(t[:-1])) / 2 * np.diff(t))])
    F -= np.interp(ref, t, F)
    return np.interp(y, t, F)


def mittlinje_lutning(v, faces, ylo, yhi):
    """Lutning (tan) för mittlinjen sett uppifrån mellan ylo och yhi."""
    m = trimesh.Trimesh(v, faces, process=False)
    ys = np.linspace(ylo, yhi, 25)
    xs, yy = [], []
    for y in ys:
        sek = m.section(plane_origin=[0, y, (m.bounds[0, 2] + m.bounds[1, 2]) / 2], plane_normal=[0, 1, 0])
        if sek is None:
            continue
        x = sek.vertices[:, 0]
        if np.ptp(x) > 0.9:  # mer än en stapel i snittet
            continue
        xs.append((x.min() + x.max()) / 2); yy.append(y)
    return np.polyfit(yy, xs, 1)[0] if len(yy) > 5 else None


def stapel(v, faces, bas, band, mal, upp):
    """Sträck stapeln i bandet så att änden hamnar på mal, och ändra lutningen."""
    y = v[:, 1] - bas
    a, b = band  # a närmast x-höjd/baslinje, b närmast änden
    ande = y.max() if upp else y.min()
    delta = mal - ande
    # Sträckning: vikten är 1 inne i bandet och tonas ut mot kanterna
    m = 0.15 * (b - a)
    w = lambda t: ramp(t, a, a + m) * ramp(t, b, b - m)
    langd = integral(w, np.array([b]), a)[0]
    dy = delta / langd * integral(w, y, a)
    ny = v.copy(); ny[:, 1] += dy
    # Lutning: mät stapelns raka del efter sträckningen och skjuv mot målet
    yb = ny[:, 1] - bas
    lo, hi = sorted((a, b + delta))  # bandet efter sträckningen
    k_nu = mittlinje_lutning(ny, faces, bas + lo, bas + hi)
    if k_nu is not None:
        k_mal = np.tan(np.radians(UPP_VINKEL if upp else NED_VINKEL))
        start = a - 0.4 if upp else a + 0.4
        wl = lambda t: ramp(t, start, a + (0.3 if upp else -0.3))
        ny[:, 0] += (k_mal - k_nu) * integral(wl, yb, start)
    return ny, delta, k_nu


def topphojd(mesh, x0, y0, nx, ny):
    """Översta ytans höjd i ett rutnät (strålar uppifrån). z0 - 1 där inget träffas."""
    xs = x0 + (np.arange(nx) + 0.5) * RUT
    ys = y0 + (np.arange(ny) + 0.5) * RUT
    X, Y = np.meshgrid(xs, ys)
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, mesh.bounds[1, 2] + 1)])
    loc, idx, _ = mesh.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(o), 1)), multiple_hits=False)
    Z = np.full(X.size, mesh.bounds[0, 2] - 1.0)
    Z[idx] = loc[:, 2]
    return Z.reshape(ny, nx), xs, ys


def slapp_i_hal(mesh):
    """Lägg till material i hålens nedre kant så att väggarna får minst SLAPP_HAL."""
    z0, z1 = mesh.bounds[0, 2], mesh.bounds[1, 2]
    pad = 0.05
    x0, y0 = mesh.bounds[0, 0] - pad, mesh.bounds[0, 1] - pad
    nx = int((mesh.extents[0] + 2 * pad) / RUT) + 1
    ny = int((mesh.extents[1] + 2 * pad) / RUT) + 1
    Z, xs, ys = topphojd(mesh, x0, y0, nx, ny)
    fot = Z > z0 + 1e-4
    hal = ndimage.binary_fill_holes(fot) & ~fot
    hal = ndimage.binary_opening(hal, iterations=2)
    if hal.sum() * RUT ** 2 < 0.01:
        return mesh, False
    cot = 1 / np.tan(np.radians(SLAPP_HAL + 1))  # 1° marginal
    r = int(np.ceil((z1 - z0) / cot / RUT)) + 1
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    dist = np.hypot(yy, xx) * RUT
    struktur = np.where(dist <= r * RUT, -dist * cot, -1e3)
    Zd = ndimage.grey_dilation(np.maximum(Z, z0), structure=struktur)
    # Bara runt hålen; i hålets mitt (fortfarande öppet) blir det inget material
    omrade = ndimage.binary_dilation(hal, iterations=int(0.15 / RUT))
    Zf = np.where(omrade, Zd - 0.003, z0 - 1.0)
    if not (Zf > Z + 1e-3).any():
        return mesh, False
    # Solid för tillägget: {z0 <= z <= Zf(x, y)}, byggs med marching cubes
    nz = int((z1 - z0) / RUT) + 3
    zs = z0 - RUT + np.arange(nz) * RUT
    falt = np.maximum(zs[None, None, :] - Zf[:, :, None], (z0 - 0.002) - zs[None, None, :])
    falt = np.maximum(falt, -0.05)
    v, f, _, _ = measure.marching_cubes(falt.astype(np.float32), 0.0, spacing=(RUT, RUT, RUT))
    v = np.column_stack([xs[0] + v[:, 1], ys[0] + v[:, 0], zs[0] + v[:, 2]])
    till = trimesh.Trimesh(v, f[:, ::-1])
    till.update_faces(till.nondegenerate_faces()); till.merge_vertices()
    till.fix_normals()
    till = till.simplify_quadric_decimation(face_count=min(len(till.faces), 60000))
    M = lambda m: manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    ihop = (M(mesh) + M(till)).trim_by_plane((0.0, 0.0, 1.0), float(z0)).to_mesh()
    ut = trimesh.Trimesh(ihop.vert_properties[:, :3], ihop.tri_verts)
    ut.fix_normals()
    return ut, True


def main():
    kalla, utmapp = sys.argv[1], sys.argv[2]
    os.makedirs(utmapp, exist_ok=True)
    alla = trimesh.load(kalla, force="mesh")
    delar = [p for p in alla.split(only_watertight=False) if len(p.faces) > 3000]
    print(f"{len(delar)} bokstäver/delar")
    rapport = []
    for p in delar:
        info = hitta(BOKSTAVER, p)
        namn = info["namn"] if info else hitta(OVRIGA, p) or f"okand_{p.bounds[0,0]:.1f}_{p.bounds[0,1]:.1f}"
        v = p.vertices.copy()
        andrat = []
        if info and "upp" in info:
            v, d, k = stapel(v, p.faces, info["bas"], info["upp"], UPP, True)
            andrat.append(f"upp {d:+.2f}, lutning {np.degrees(np.arctan(k)) if k is not None else float('nan'):.1f}°→{UPP_VINKEL}°")
        if info and "ned" in info:
            v, d, k = stapel(v, p.faces, info["bas"], info["ned"], -NED, False)
            andrat.append(f"ned {d:+.2f}, lutning {np.degrees(np.arctan(k)) if k is not None else float('nan'):.1f}°→{NED_VINKEL}°")
        m = trimesh.Trimesh(v, p.faces, process=False)
        m, hal = slapp_i_hal(m)
        if hal:
            andrat.append(f"släpp i hål ≥{SLAPP_HAL}°")
        m.export(os.path.join(utmapp, f"{namn}.stl"))
        rapport.append((namn, andrat, m.is_watertight))
        print(f"{namn:20s} {'; '.join(andrat) or 'oförändrad'}  vattentät {m.is_watertight}")


if __name__ == "__main__":
    main()
