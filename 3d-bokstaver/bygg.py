"""Gör om bokstäverna "Vaer" (från Keynote-filen) till 3D-modeller med rundade kanter.

Konturerna tas från förhandsbilden (A4, stående). Varje bokstav får ett
2D-avståndsfält som sedan extruderas med avrundade kanter och blir ett
mesh via marching cubes. Hålen i bokstäverna behålls som genomgående hål.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from skimage import measure
import trimesh

BILD = sys.argv[1] if len(sys.argv) > 1 else "preview.jpg"
DJUP = 15.0       # mm, bokstävernas tjocklek
RADIE = 4.0       # mm, kantradie
UPPLOSNING = 0.25  # mm per voxel
SIDA_MM = 297.0   # bildens höjd = A4

img = Image.open(BILD).convert("L")
mm_per_px = SIDA_MM / img.height
skala = mm_per_px / UPPLOSNING
stor = img.resize((round(img.width * skala), round(img.height * skala)), Image.BICUBIC)
stor = stor.filter(ImageFilter.GaussianBlur(2 / UPPLOSNING * 0.25))
mask = np.array(stor) < 128
mask = mask[::-1]  # y uppåt

etiketter, n = ndimage.label(mask)
storlek = ndimage.sum(mask, etiketter, range(1, n + 1))
bokstaver = [i + 1 for i in np.argsort(storlek)[::-1][:4]]
# Sortera i läsordning: V, a (översta raden), e, r (nedersta raden)
def ordning(i):
    ys, xs = np.nonzero(etiketter == i)
    return (-round(ys.mean() / (mask.shape[0] / 2)), xs.mean())
bokstaver.sort(key=ordning)
namn = ["V", "a", "e", "r"]

meshes = {}
for bok, lab in zip(namn, bokstaver):
    m = etiketter == lab
    ys, xs = np.nonzero(m)
    pad = int(3 * RADIE / UPPLOSNING)
    y0, y1 = ys.min() - pad, ys.max() + pad
    x0, x1 = xs.min() - pad, xs.max() + pad
    sub = np.pad(m, pad)[y0 + pad:y1 + pad, x0 + pad:x1 + pad]
    # Signerat avstånd i mm (negativt inuti)
    d2 = (ndimage.distance_transform_edt(~sub) - ndimage.distance_transform_edt(sub)) * UPPLOSNING
    d2 = ndimage.gaussian_filter(d2, 1.0)
    nz = int((DJUP / 2 + 2) / UPPLOSNING)
    z = np.arange(-nz, nz + 1) * UPPLOSNING
    # Rundad extrudering: q = (d2 + r, |z| - h/2 + r)
    qx = d2[:, :, None] + RADIE
    qz = np.abs(z)[None, None, :] - DJUP / 2 + RADIE
    sdf = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0) - RADIE
    v, f, _, _ = measure.marching_cubes(sdf + 1e-4, 0.0, spacing=(UPPLOSNING,) * 3)
    # (rad=y, kol=x, z) -> (x, y, z) i mm, i sidans koordinater
    v = np.column_stack([v[:, 1] + x0 * UPPLOSNING, v[:, 0] + y0 * UPPLOSNING, v[:, 2] - nz * UPPLOSNING])
    mesh = trimesh.Trimesh(v, f[:, ::-1])
    mesh.update_faces(mesh.nondegenerate_faces()); mesh.merge_vertices()
    mesh = mesh.simplify_quadric_decimation(face_count=60000) if len(mesh.faces) > 60000 else mesh
    mesh.fix_normals()
    meshes[bok] = mesh
    print(bok, "vattentät:", mesh.is_watertight, "mått (mm):", np.round(mesh.extents, 1), "trianglar:", len(mesh.faces))

for bok, mesh in meshes.items():
    mesh.export(f"bokstav_{bok}.stl")
alla = trimesh.util.concatenate(list(meshes.values()))
alla.export("Vaer_alla.stl")
alla.export("Vaer_alla.glb")
