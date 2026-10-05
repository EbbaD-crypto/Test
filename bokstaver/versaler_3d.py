"""Bygger versalerna (A–Ö) i 3D från 2D-formerna i versaler.py.

Varje versal får samma välvda profil som dina egna bokstäver (uppmätt på ditt
l: nästan lodrät kant längst ner som sedan välver sig upp mot mitten), platt
baksida och 10° lutning (finns redan i 2D-formen). Hålen (A, B, D, O, P, Q, R …)
får minst SLAPP_HAL grader släpp så att leran släpper ur gipsformen.
Prickarna över Å, Ä och Ö blir egna delar, som pricken på ditt i.

    python3 versaler_3d.py <mapp med dina gemener (slutlig)> <utmapp>
"""
import os
import sys
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

from versaler import bygg_alla, mask, prick_x, DIAKRIT, PRICK_Y, PRICK_DX, PRICK_R, K, RUT as RUT2D

# Din profil (uppmätt på l): bredd på olika höjder -> hur långt in från kanten
# varje höjd ligger. HOJD = bokstavens tjocklek.
HOJD = 0.403
PROFIL_F = np.array([0.0, 0.02, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 1.0])
PROFIL_B = np.array([0.564, 0.564, 0.56, 0.551, 0.539, 0.521, 0.498, 0.467, 0.425, 0.365, 0.322,
                     0.265, 0.176, 0.093, 0.0])
PROFIL_D = (PROFIL_B[0] - PROFIL_B) / 2          # avstånd in från kanten
RUT = 0.02                                       # 3D-upplösning
SLAPP_HAL = 15.0
YTOR = 60000        # antal trianglar per bokstav (lagom fil-storlek, slät yta)
TJOCKLEK = 0.41     # samma tjocklek som dina gemener
MARGINAL = 8.0      # extra grader: ytan blir lite brantare när höjdfältet görs om till mesh


def hojd_fran_kant(d):
    """Höjd över baksidan som funktion av avståndet in från kanten."""
    return HOJD * np.interp(d, PROFIL_D, PROFIL_F)


def ner(m2d):
    """2D-masken (RUT2D) ner till 3D-upplösningen (RUT)."""
    f = int(round(RUT / RUT2D))
    h, w = (m2d.shape[0] // f) * f, (m2d.shape[1] // f) * f
    return m2d[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3)) > 0.5


def hojdfalt(m):
    d = ndimage.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1] * RUT
    d = np.where(m, d - RUT / 2, 0)
    Z = np.where(m, hojd_fran_kant(d), 0.0)
    return ndimage.gaussian_filter(Z, 0.7) * m


def slapp(Z, m):
    """Minst SLAPP_HAL graders släpp i hålen: väggarna runt varje hål får
    luta minst så mycket (som slapp_i_hal i justera.py, men direkt i höjdfältet)."""
    hal = ndimage.binary_fill_holes(m) & ~m
    if hal.sum() * RUT ** 2 < 0.005:
        return Z, m
    cot = 1 / np.tan(np.radians(SLAPP_HAL + MARGINAL))
    r = int(np.ceil(HOJD / cot / RUT)) + 1
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    dist = np.hypot(yy, xx) * RUT
    struktur = np.where(dist <= r * RUT, -dist * cot, -1e3)
    Zd = ndimage.grey_dilation(Z, structure=struktur)
    omrade = ndimage.binary_dilation(hal, iterations=int(0.25 / RUT)) & ndimage.binary_fill_holes(m)
    Z2 = np.where(omrade, np.maximum(Z, Zd - 0.003), Z)
    return Z2, m | (omrade & (Z2 > 0.004))


def till_mesh(Z, x0, y0):
    """Höjdfält -> sluten mesh med platt baksida (z = 0)."""
    Z = np.pad(Z, 2)
    nz = int(HOJD / (RUT / 2)) + 4
    zs = -RUT + np.arange(nz) * (RUT / 2)
    falt = np.minimum(Z[:, :, None] - zs[None, None, :], zs[None, None, :] - 0.0)
    falt = np.where(Z[:, :, None] > 0.003, falt, -0.05)
    v, f, _, _ = measure.marching_cubes(falt.astype(np.float32), 0.0, spacing=(RUT, RUT, RUT / 2))
    v = np.column_stack([x0 - 2 * RUT + v[:, 1], y0 - 2 * RUT + v[:, 0], zs[0] + v[:, 2]])
    m = trimesh.Trimesh(v, f[:, ::-1])
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    trimesh.smoothing.filter_taubin(m, iterations=12)
    m.vertices[:, 2] = np.maximum(m.vertices[:, 2], 0.0)
    m.fix_normals()
    return m


def hojdfalt_fint(m2d):
    """Höjden räknas på det fina 2D-rutnätet (jämnare yta) och tas sedan ner."""
    d = ndimage.distance_transform_edt(np.pad(m2d, 1))[1:-1, 1:-1] * RUT2D
    Zf = np.where(m2d, hojd_fran_kant(np.maximum(d - RUT2D / 2, 0)), 0.0)
    Zf = ndimage.gaussian_filter(Zf, 2.0) * m2d
    f = int(round(RUT / RUT2D))
    h, w = (m2d.shape[0] // f) * f, (m2d.shape[1] // f) * f
    return Zf[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3))


def bygg(m2d, x0, y0, rut2d=RUT2D):
    m = ner(m2d)
    Z = hojdfalt_fint(m2d) * m
    Z, m = slapp(Z, m)
    mesh = till_mesh(Z, x0, y0)
    if len(mesh.faces) > YTOR:
        mesh = mesh.simplify_quadric_decimation(face_count=YTOR)
    if not mesh.is_watertight:
        from gemensam_sving import laga
        mesh = laga(mesh)
    return mesh


def prick(cx, cy):
    """En rund prick (lika stor för Å, Ä och Ö), lutad som resten."""
    m, x0, y0 = mask([np.array([[cx, cy], [cx + 0.001, cy]])], halv=PRICK_R)
    return bygg(m, x0, y0)


def gemen_med_prickar(mapp, bok, bas, antal, ut, fil):
    """Gemena å, ä, ö: din a/o-fil + din egen i-prick (lika stor) ovanför,
    på samma höjd som pricken på i."""
    from versaler import gemen_polygoner
    m = trimesh.load(os.path.join(mapp, f"{bok}.stl"))
    pr = trimesh.load(os.path.join(mapp, "i-prick.stl"))
    pr_bas = -19.95                                   # i:ets baslinje
    pr_mitt = pr.bounds.mean(0)
    hojd = pr_mitt[1] - pr_bas                         # prickens mitt över baslinjen
    polys, _ = gemen_polygoner(mapp, bok)
    P = np.vstack([p[0] for p in polys])
    topp = P[P[:, 1] > 1.6]
    cx = m.bounds[0, 0] + topp[:, 0].mean() + K * (hojd - topp[:, 1].mean())
    m.export(os.path.join(ut, f"{fil}.stl"))
    dx = 0.42
    platser = [cx] if antal == 1 else [cx - dx, cx + dx]
    for i, x in enumerate(platser):
        p = pr.copy()
        p.apply_translation([x - pr_mitt[0], bas + hojd - pr_mitt[1], m.bounds[0, 2] - pr.bounds[0, 2]])
        p.export(os.path.join(ut, f"{fil}_prick{i + 1}.stl"))


def main():
    mapp, ut = sys.argv[1:3]
    os.makedirs(ut, exist_ok=True)
    alla = bygg_alla(mapp)
    namn = {"Å": "AA", "Ä": "AE", "Ö": "OE"}
    for n, (m2d, x0, y0) in alla.items():
        if n.endswith("-ring") or n == "L":
            continue
        mesh = bygg(m2d, x0, y0)
        fil = namn.get(n, n)
        mesh.export(os.path.join(ut, f"versal_{fil}.stl"))
        rad = f"{n}: {len(mesh.faces)} ytor, vattentät {mesh.is_watertight}, tjocklek {mesh.extents[2]:.3f}"
        if n in DIAKRIT:
            cx = prick_x(n)
            delar = [(cx, PRICK_Y)] if DIAKRIT[n][1] == "ring" else [(cx - PRICK_DX, PRICK_Y), (cx + PRICK_DX, PRICK_Y)]
            for i, (px, py) in enumerate(delar):
                prick(px, py).export(os.path.join(ut, f"versal_{fil}_prick{i + 1}.stl"))
            rad += f", {len(delar)} prick(ar)"
        print(rad, flush=True)
    # ditt L: foten uppriktad, tjockleken som de andra bokstäverna
    from versaler import L_3d
    L, _ = L_3d(mapp)
    z0 = L.bounds[0, 2]
    L.vertices[:, 2] = z0 + (L.vertices[:, 2] - z0) * TJOCKLEK / L.extents[2]
    L.export(os.path.join(ut, "versal_L.stl"))
    print(f"L: vattentät {L.is_watertight}, tjocklek {L.extents[2]:.3f}", flush=True)
    # lilla h med knorr
    import h_knorr
    h = h_knorr.h_3d(trimesh.load(os.path.join(mapp, "h.stl")))
    h.export(os.path.join(ut, "h.stl"))
    print(f"h: vattentät {h.is_watertight}, tjocklek {h.extents[2]:.3f}", flush=True)
    # gemena å, ä, ö
    gemen_med_prickar(mapp, "a1", -10.0, 1, ut, "gemen_aa")
    gemen_med_prickar(mapp, "a1", -10.0, 2, ut, "gemen_ae")
    gemen_med_prickar(mapp, "o", -20.0, 2, ut, "gemen_oe")
    print("å, ä, ö klara", flush=True)


if __name__ == "__main__":
    main()
