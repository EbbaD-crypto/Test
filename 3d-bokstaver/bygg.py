"""Gör om bokstäverna "Vaer" (från Keynote-filen) till 3D-original för gipsgjutning.

Konturerna tas från förhandsbilden (A4, stående). Varje bokstav byggs som en
höjdkarta ovanpå en platt botten: platt baksida mot byggplattan och en rundad
ovansida. Eftersom ovansidan är en höjdkarta finns inga underskärningar, och
lutningen begränsas så att alla väggar har minst SLAPPVINKEL grader släpp.
Gipset kan då lyftas rakt upp. Tjockleken följer proportionen 16 rutor hög
ger 4 rutor tjock. Prickarna fylls igen så
bokstäverna blir helt solida.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from skimage import measure
import trimesh
import manifold3d

BILD = sys.argv[1] if len(sys.argv) > 1 else "original.jpg"
HOJD_PER_DJUP = 16 / 4   # 16 rutor hög -> 4 rutor tjock
SLAPPVINKEL = 5.0        # grader, minsta släppvinkel mot lodrätt
RUNDNING = 14.0          # mm in från kanten där ovansidan når full höjd
UPPLOSNING = 0.25        # mm per voxel
SIDA_MM = 297.0          # bildens höjd = A4

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
# Läsordning: V, a (översta raden), e, r (nedersta raden)
def ordning(i):
    ys, xs = np.nonzero(etiketter == i)
    return (ys.mean() < mask.shape[0] / 2, xs.mean())
bokstaver.sort(key=ordning)
namn = ["V", "a", "e", "r"]

hojder = [np.ptp(np.nonzero(etiketter == lab)[0]) * UPPLOSNING for lab in bokstaver]
DJUP = float(np.mean(hojder)) / HOJD_PER_DJUP
print(f"medelhöjd {np.mean(hojder):.1f} mm -> tjocklek {DJUP:.1f} mm, släppvinkel {SLAPPVINKEL}°")

# Profil: kvartsellips från kanten till RUNDNING mm in, med lutningen
# begränsad till max_lutning så att väggarna aldrig blir lodräta.
# Byggs med 1° marginal så att utjämning och mesh-brus inte går under SLAPPVINKEL.
max_lutning = 1 / np.tan(np.radians(SLAPPVINKEL + 1))
s = np.linspace(0, RUNDNING, 4001)
u = np.clip(1 - s / RUNDNING, 0, 1 - 1e-12)
ellips = u / np.sqrt(1 - u**2) / RUNDNING  # lutning för höjd 1
def profil_for(k):
    lut = np.minimum(k * DJUP * ellips, max_lutning)
    return np.concatenate([[0], np.cumsum((lut[1:] + lut[:-1]) / 2 * np.diff(s))])
lo, hi = 1.0, 100.0  # välj k så att profilen når exakt DJUP
for _ in range(60):
    k = (lo + hi) / 2
    lo, hi = (k, hi) if profil_for(k)[-1] < DJUP else (lo, k)
profil = profil_for(hi)

def hojd(d):
    return np.interp(d, s, profil)

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
    z = np.where(d > 0, hojd(np.maximum(d, 0)), d * max_lutning)
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

for bok, mesh in meshes.items():
    mesh.export(f"bokstav_{bok}.stl")
alla = trimesh.util.concatenate(list(meshes.values()))
alla.export("Vaer_alla.stl")
alla.export("Vaer_alla.glb")
