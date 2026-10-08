import sys, numpy as np; sys.path.insert(0, sys.argv[1]); from lib import *
from shapely.geometry import LineString
T, X, Y = falt('plan/c1.stl'); m = T > 0.05
D = ndimage.distance_transform_edt(m) * r; sk = skeletonize(m)
p = stig(sk, X, Y); W = float(np.median(2 * D[sk]))
c = jamna(p, s=8.0)
ny = raster(LineString(c).buffer(W / 2, cap_style='flat'), X, Y)
# ändarna: originalets form (och vinkel) bortom linjens slut, skalad tvärs linjen till bredden W
for ande, inre in ((c[0], c[12]), (c[-1], c[-13])):
    t = (ande - inre) / np.linalg.norm(ande - inre); n = np.array([-t[1], t[0]])
    iy, ix = np.argmin(np.abs(Y[:, 0] - ande[1])), np.argmin(np.abs(X[0] - ande[0])); h = D[iy, ix]
    P = np.column_stack([X.ravel() - ande[0], Y.ravel() - ande[1]])
    u, v = P @ t, P @ n
    # punkt (u, v) i nya ändan <- (u, v * h / (W/2)) i originalet
    src = ande + np.outer(u, t) + np.outer(v * h / (W / 2), n)
    jx = np.clip(np.round((src[:, 0] - X[0, 0]) / r).astype(int), 0, X.shape[1] - 1)
    jy = np.clip(np.round((src[:, 1] - Y[0, 0]) / r).astype(int), 0, X.shape[0] - 1)
    nara = (u > -0.5) & (u < 2.5 * h) & (np.abs(v) < W)
    ny |= (nara & m[jy, jx]).reshape(m.shape)
ny = ndimage.gaussian_filter(np.pad(ny, 40).astype(float), 2.0 / r)[40:-40, 40:-40] > 0.5
Z = hojd(ny, profil(T)); print('bredd %.1f' % W)
bygg(Z, X, Y, 'plan/c_jamn.stl')
