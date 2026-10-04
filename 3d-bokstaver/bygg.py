"""Gör om bokstäver i en bild till 3D-original för gipsgjutning.

Konturerna tas från förhandsbilden (A4, stående). Varje bokstav byggs som en
höjdkarta ovanpå en platt botten: platt baksida mot byggplattan och en mjukt
rundad ovansida där varje stapel får samma kupolform, skalad efter sin bredd.
Eftersom ovansidan är en höjdkarta finns inga underskärningar, och
lutningen begränsas så att alla väggar har minst SLAPPVINKEL grader släpp.
Gipset kan då lyftas rakt upp. Tjockleken följer proportionen 16 rutor hög
ger 4 rutor tjock, och är densamma för alla bokstäver. Prickarna fylls igen
så bokstäverna blir helt solida.

    python3 bygg.py original_jamn.png 310
    python3 bygg.py abcd.png --sida 200 --namn a1 a2 b c d --ut abcd
"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from skimage import measure
from skimage.morphology import skeletonize
import trimesh
import manifold3d

import argparse
arg = argparse.ArgumentParser(description="Gör gjutbara 3D-original av bokstäverna i en bild.")
arg.add_argument("bild", nargs="?", default="original.jpg")
arg.add_argument("sida", nargs="?", type=float, default=297.0, help="bildens höjd i mm")
arg.add_argument("--sida", dest="sida_flagga", type=float, help="bildens höjd i mm")
arg.add_argument("--namn", nargs="+", help="bokstävernas namn från vänster till höger (en rad)")
arg.add_argument("--ut", default=".", help="mapp för STL/GLB-filerna")
argv = arg.parse_args()

BILD = argv.bild
DJUP = 29.0              # mm, samma tjocklek för alla bokstäver (x-höjd ca 116 mm / 4)
SLAPPVINKEL = 5.0        # grader, minsta släppvinkel mot lodrätt
FYLLIGHET = 2.5          # tvärsnittets form: 2 = ellips, högre = fylligare axlar
MIN_HALVBREDD = 8.0      # mm, används för att hålla släppvinkeln även i smala delar
UPPLOSNING = 0.25        # mm per voxel
SIDA_MM = argv.sida_flagga or argv.sida

img = Image.open(BILD).convert("L")
mm_per_px = SIDA_MM / img.height
skala = mm_per_px / UPPLOSNING
stor = img.resize((round(img.width * skala), round(img.height * skala)), Image.BICUBIC)
stor = stor.filter(ImageFilter.GaussianBlur(2 / UPPLOSNING * 0.25))
mask = np.array(stor) < 128
mask = mask[::-1]  # y uppåt

namn = argv.namn or ["V", "a", "e", "r"]
etiketter, n = ndimage.label(mask)
storlek = ndimage.sum(mask, etiketter, range(1, n + 1))
bokstaver = [i + 1 for i in np.argsort(storlek)[::-1][:len(namn)]]
def ordning(i):
    ys, xs = np.nonzero(etiketter == i)
    if argv.namn:
        return (0, xs.mean())  # en rad, vänster till höger
    # Vaer: V, a (översta raden), e, r (nedersta raden)
    return (ys.mean() < mask.shape[0] / 2, xs.mean())
bokstaver.sort(key=ordning)
print(f"tjocklek {DJUP:.1f} mm, släppvinkel {SLAPPVINKEL}°")

# Profil över stapelns tvärsnitt: t = 0 vid kanten, t = 1 mitt på stapeln.
# Varje stapel får samma mjuka kupol, skalad efter sin egen bredd, så att
# alla bokstäver blir lika runda. Lutningen begränsas för släppvinkeln
# (med 1° marginal för utjämning och mesh-brus).
max_lutning = 1 / np.tan(np.radians(SLAPPVINKEL + 1))
t = np.linspace(0, 1, 4001)
rå = (1 - (1 - np.clip(t, 0, 1 - 1e-9)) ** FYLLIGHET) ** (1 / FYLLIGHET)
rå_lutning = np.gradient(rå, t)
tak = max_lutning * MIN_HALVBREDD / DJUP
def profil_for(k):
    lut = np.minimum(k * rå_lutning, tak)
    return np.concatenate([[0], np.cumsum((lut[1:] + lut[:-1]) / 2 * np.diff(t))])
lo, hi = 1.0, 100.0  # välj k så att profilen når exakt 1 mitt på stapeln
for _ in range(60):
    k = (lo + hi) / 2
    lo, hi = (k, hi) if profil_for(k)[-1] < 1 else (lo, k)
profil = profil_for(hi)

def kupol(tt):
    return np.interp(tt, t, profil)

def halvbredd(sub, d):
    """Stapelns halvbredd (mm) i varje punkt: avståndet till kanten på
    närmaste punkt på mittlinjen, utjämnat längs bokstaven."""
    mitt = skeletonize(sub)
    _, (iy, ix) = ndimage.distance_transform_edt(~mitt, return_indices=True)
    w = d[iy, ix]
    vikt = ndimage.gaussian_filter(sub.astype(float), 3 / UPPLOSNING)
    w = ndimage.gaussian_filter(np.where(sub, w, 0), 3 / UPPLOSNING) / np.maximum(vikt, 1e-6)
    return np.maximum(w, d)

meshes = {}
for bok, lab in zip(namn, bokstaver):
    m = etiketter == lab
    # Fyll igen prickarna (små upphängningshål); behåll riktiga hål som i a och e
    fylld = ndimage.binary_fill_holes(m)
    hal, nh = ndimage.label(fylld & ~m)
    hal_storlek = ndimage.sum(np.ones_like(m), hal, range(1, nh + 1))
    prickar = np.isin(hal, [i + 1 for i, a in enumerate(hal_storlek) if a * UPPLOSNING**2 < 150])
    m = m | prickar

    ys, xs = np.nonzero(m)
    pad = 24
    y0, y1 = ys.min() - pad, ys.max() + pad
    x0, x1 = xs.min() - pad, xs.max() + pad
    sub = np.pad(m, pad)[y0 + pad:y1 + pad, x0 + pad:x1 + pad]

    # Avstånd in från kanten (mm), utjämnat för en mjuk yta
    d = ndimage.distance_transform_edt(sub) - ndimage.distance_transform_edt(~sub)
    d = ndimage.gaussian_filter(d * UPPLOSNING, 1.0)
    # Utanför bokstaven fortsätter väggen nedåt med samma lutning; den kapas vid z = 0
    w = halvbredd(sub, np.maximum(d, 0))
    z = np.where(d > 0, DJUP * kupol(np.maximum(d, 0) / np.maximum(w, 1e-6)), d * max_lutning)
    z = ndimage.gaussian_filter(z, 0.6)

    # Solid = {0 < höjd < z(x, y)}; nivåfält normerat med ytans lutning
    gy, gx = np.gradient(z, UPPLOSNING)
    norm = np.sqrt(1 + gx**2 + gy**2)
    nz = int(np.ceil(DJUP / UPPLOSNING)) + 4
    zz = (np.arange(-8, nz - 1) + 0.5) * UPPLOSNING
    falt = np.maximum((zz[None, None, :] - z[:, :, None]) / norm[:, :, None], zz[0] + UPPLOSNING - zz[None, None, :])
    v, f, _, _ = measure.marching_cubes(falt + 1e-4, 0.0, spacing=(UPPLOSNING,) * 3)
    v = np.column_stack([v[:, 1] + x0 * UPPLOSNING, v[:, 0] + y0 * UPPLOSNING, v[:, 2] + zz[0]])
    mesh = trimesh.Trimesh(v, f[:, ::-1])
    mesh.update_faces(mesh.nondegenerate_faces()); mesh.merge_vertices()
    mesh = mesh.simplify_quadric_decimation(face_count=150000) if len(mesh.faces) > 150000 else mesh
    # Kapa vid z = 0: helt platt botten och skarp kant mot byggplattan
    kropp = manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(mesh.vertices, np.float32), tri_verts=np.asarray(mesh.faces, np.uint32)))
    kapad = kropp.trim_by_plane((0.0, 0.0, 1.0), 0.0).to_mesh()
    mesh = trimesh.Trimesh(kapad.vert_properties[:, :3], kapad.tri_verts)
    mesh.fix_normals()
    meshes[bok] = mesh

    # Kontroll: varje yta ska antingen vara botten eller luta utåt uppåt
    nzs = mesh.face_normals[:, 2]
    botten = nzs < -0.99
    vinkel = np.degrees(np.arcsin(np.clip(nzs[~botten], -1, 1)))
    yta = mesh.area_faces[~botten]
    under = yta[vinkel < SLAPPVINKEL - 1].sum() / yta.sum() * 100
    print(f"{bok}: vattentät {mesh.is_watertight}, mått {np.round(mesh.extents, 1)} mm, "
          f"minsta släpp {np.percentile(vinkel, 0.1):.1f}° (0,1-percentil), "
          f"yta under {SLAPPVINKEL - 1:.0f}°: {under:.2f} %, underskärning: {(vinkel < 0).sum()} trianglar")

import os
os.makedirs(argv.ut, exist_ok=True)
for bok, mesh in meshes.items():
    mesh.export(os.path.join(argv.ut, f"bokstav_{bok}.stl"))
prefix = "".join(namn) if argv.namn else "Vaer"
alla = trimesh.util.concatenate(list(meshes.values()))
alla.export(os.path.join(argv.ut, f"{prefix}_alla.stl"))
alla.export(os.path.join(argv.ut, f"{prefix}_alla.glb"))
