import numpy as np, trimesh, manifold3d as mf, fast_simplification as fs
from scipy import ndimage
from skimage.morphology import skeletonize
r = 0.25
def falt(p, pad=3):
    b = trimesh.load(p); b.apply_scale(61.0); b.apply_translation(-b.bounds[0])
    xs = np.arange(-pad, b.extents[0] + pad, r); ys = np.arange(-pad, b.extents[1] + pad, r); X, Y = np.meshgrid(xs, ys); N = X.size
    o = np.column_stack([X.ravel(), Y.ravel(), np.full(N, b.extents[2] + 5)])
    l, ri, _ = b.ray.intersects_location(o, np.tile([0, 0, -1.], (N, 1)), multiple_hits=False)
    T = np.zeros(N); T[ri] = l[:, 2]; return T.reshape(X.shape), X, Y
def profil(T):
    m = T > 0.05; D = ndimage.distance_transform_edt(m) * r
    bins = np.arange(0, D.max() + r, r); i = np.digitize(D[m], bins)
    h = np.array([np.median(T[m][i == k]) if (i == k).any() else np.nan for k in range(1, len(bins))])
    h = np.maximum.accumulate(np.nan_to_num(h)); return bins[:-1], h
def hojd(mask, prof, slapp=3.0):
    """Mjuk kant: signerat avstånd (utjämnat) -> höjd. Utanför går ytan ner med släppvinkeln,
    så att kanten hamnar mellan rutorna (inga trappsteg)."""
    sd = ndimage.distance_transform_edt(mask) * r - ndimage.distance_transform_edt(~mask) * r
    sd = ndimage.gaussian_filter(sd, 0.8 / r)
    Z = np.where(sd > 0, np.interp(sd, *prof), sd / np.tan(np.radians(slapp)))
    return np.maximum(Z, -1.0)
def bygg(T, X, Y, dst, SLAPP=3.0, mjuk=False):
    T = T if mjuk else np.where(T > 0.05, T, -50.0)
    k = 1 / np.tan(np.radians(SLAPP)); R = int(np.ceil(T.max() / k / r)) + 1
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; d = np.hypot(xx, yy) * r
    Z = np.maximum(ndimage.grey_dilation(T, structure=np.where(d <= R * r, -k * d, -1e3)), -1.0)
    h, w = Z.shape; idx = np.arange(h * w).reshape(h, w)
    V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    a, b1, c, e = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    F = np.vstack([np.column_stack([a, b1, c]), np.column_stack([a, c, e])])
    kant = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])
    nb = len(V); V = np.vstack([V, V[kant] * [1, 1, 0] + [0, 0, -2]]); m = len(kant); i = np.arange(m); j = (i + 1) % m
    F = np.vstack([F, np.column_stack([kant[j], kant[i], nb + i]), np.column_stack([kant[j], nb + i, nb + j])])
    mid = nb + np.arange(1, m - 1); F = np.vstack([F, np.column_stack([np.full(m - 2, nb), mid + 1, mid])])
    M = mf.Manifold(mf.Mesh(V.astype(np.float32), F.astype(np.uint32))).trim_by_plane([0, 0, 1], 0.0).to_mesh()
    v0, f0 = np.asarray(M.vert_properties)[:, :3].astype(np.float32), np.asarray(M.tri_verts).astype(np.int64)
    for agg in (7, 3, 1):
        v, f = fs.simplify(v0, f0, target_reduction=0.8, agg=agg); ut = trimesh.Trimesh(v, f)
        if ut.is_watertight: break
    ut.apply_scale(1 / 61.0); ut.export(dst); print(dst, 'vattentät', ut.is_watertight, len(ut.split()), 'kropp')
def stig(sk, X, Y):
    """Längsta vägen genom skelettet som punktlista (mm)."""
    import networkx as nx
    yy, xx = np.nonzero(sk); G = nx.Graph(); P = set(zip(yy, xx))
    for p in P:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                q = (p[0] + dy, p[1] + dx)
                if q != p and q in P: G.add_edge(p, q, weight=np.hypot(dy, dx))
    a = max(nx.single_source_dijkstra_path_length(G, next(iter(P))).items(), key=lambda t: t[1])[0]
    L, V = nx.single_source_dijkstra(G, a); b = max(L, key=L.get)
    return np.array([(X[p], Y[p]) for p in V[b]])
def jamna(pts, s=40.0, n=600):
    from scipy.interpolate import splprep, splev
    tck, _ = splprep(pts[::4].T, s=s); return np.array(splev(np.linspace(0, 1, n), tck)).T
def raster(geom, X, Y):
    from shapely import contains_xy
    return contains_xy(geom, X, Y)
