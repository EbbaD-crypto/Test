"""Bygger om en master som höjdfält: ovansidan behålls, baksidan blir helt plan,
och alla väggar får minst 3° släpp -> inga underskärningar."""
import sys, time, numpy as np, trimesh, manifold3d as mf, fast_simplification as fs
from scipy import ndimage
src, dst = sys.argv[1], sys.argv[2]; r = 0.25; SLAPP = 3.0; t0 = time.time()
b = trimesh.load(src); b.apply_scale(61.0); b.apply_translation(-b.bounds[0])
xs = np.arange(-3, b.extents[0] + 3, r); ys = np.arange(-3, b.extents[1] + 3, r)
X, Y = np.meshgrid(xs, ys); N = X.size
o = np.column_stack([X.ravel(), Y.ravel(), np.full(N, b.extents[2] + 5)])
l, ri, _ = b.ray.intersects_location(o, np.tile([0, 0, -1.0], (N, 1)), multiple_hits=False)
T = np.full(N, -50.0); T[ri] = l[:, 2]; T = T.reshape(X.shape)
k = 1 / np.tan(np.radians(SLAPP)); R = int(np.ceil(b.extents[2] / k / r)) + 1
yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; d = np.hypot(xx, yy) * r
St = np.where(d <= R * r, -k * d, -1e3)
Z = np.maximum(ndimage.grey_dilation(T, structure=St), -1.0)
# sluten "kudde": toppyta som grid, botten på z=-1, sedan kapad vid z=0
h, w = Z.shape; idx = np.arange(h * w).reshape(h, w)
V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
a, b1, c, e = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
F = np.vstack([np.column_stack([a, b1, c]), np.column_stack([a, c, e])])
kant = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])
nb = len(V); V = np.vstack([V, V[kant] * [1, 1, 0] + [0, 0, -2]])
m = len(kant); i = np.arange(m); j = (i + 1) % m
F = np.vstack([F, np.column_stack([kant[j], kant[i], nb + i]), np.column_stack([kant[j], nb + i, nb + j])])
mid = nb + np.arange(1, m - 1); F = np.vstack([F, np.column_stack([np.full(m - 2, nb), mid + 1, mid])])
M = mf.Manifold(mf.Mesh(V.astype(np.float32), F.astype(np.uint32)))
M = M.trim_by_plane([0, 0, 1], 0.0)
mm = M.to_mesh(); v, f = np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts)
v0, f0 = v, f
v, f = fs.simplify(v.astype(np.float32), f.astype(np.int64), target_reduction=0.8)
print("före förenkling vattentät", trimesh.Trimesh(v0, f0).is_watertight)
ut = trimesh.Trimesh(v, f)
if not ut.is_watertight:
    v, f = fs.simplify(v0.astype(np.float32), f0.astype(np.int64), target_reduction=0.8, agg=3)
ut = trimesh.Trimesh(v, f); ut.apply_scale(1 / 61.0)
ut.export(dst)
print(dst, 'vattentät', ut.is_watertight, 'kroppar', len(ut.split()), 'trianglar', len(f), '%.0fs' % (time.time() - t0))
