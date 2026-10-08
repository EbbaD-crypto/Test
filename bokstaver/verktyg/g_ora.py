"""g_ny: örat (knorren) kortas längs sin egen riktning, bredd och form behålls; gropen upptill finns kvar."""
import sys, numpy as np; sys.path.insert(0, sys.argv[1]); from lib import *
f, namn = float(sys.argv[2]), sys.argv[3]
z = np.load('an/g_falt.npz'); T, X, Y = z['T'], z['X'], z['Y']; m = T > 0.05
sk = skeletonize(m); J = np.array([127.0, 222.0])
ora = sk & (X > J[0]) & (Y > J[1] - 1)
_, (iy, ix) = ndimage.distance_transform_edt(~sk, return_indices=True)
E = ora[iy, ix] & m
P = np.column_stack([X[ora], Y[ora]]); tip = P[np.argmax(np.hypot(*(P - J).T))]
d = (tip - J) / np.linalg.norm(tip - J); n = np.array([-d[1], d[0]])
u = (X - J[0]) * d[0] + (Y - J[1]) * d[1]; v = (X - J[0]) * n[0] + (Y - J[1]) * n[1]
qx = J[0] + d[0] * np.where(u > 0, u / f, u) + n[0] * v; qy = J[1] + d[1] * np.where(u > 0, u / f, u) + n[1] * v
jx = np.clip(np.round((qx - X[0, 0]) / r).astype(int), 0, X.shape[1] - 1); jy = np.clip(np.round((qy - Y[0, 0]) / r).astype(int), 0, X.shape[0] - 1)
ny = (m & ~E) | E[jy, jx]
# stapelns högerkant och skarven under örat jämnas (inte överkanten med gropen)
sl = ndimage.gaussian_filter(np.pad(ny, 100).astype(float), 5 / r)[100:-100, 100:-100] > 0.5
ny = np.where((Y > 60) & (Y < J[1] + 6) & (X > 112), sl, ny)
sl = ndimage.gaussian_filter(np.pad(ny, 100).astype(float), 3 / r)[100:-100, 100:-100] > 0.5
ny = np.where((Y > J[1]) & (X > J[0] - 12) & (X < J[0] + 18), sl, ny)   # mjuk grop, ingen skarv
ny = ndimage.gaussian_filter(np.pad(ny, 40).astype(float), 0.75 / r)[40:-40, 40:-40] > 0.5
Z = hojd(ny, profil(T)); bygg(Z, X, Y, f'plan/{namn}.stl')
