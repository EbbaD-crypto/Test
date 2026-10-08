"""c: originalets kontur behålls; bara innerkantens punkter flyttas, radiellt från c:ts mitt,
så att bredden blir jämn. Ändarna (rundningarna) rörs inte, övergången är mjuk."""
import sys, numpy as np; sys.path.insert(0, sys.argv[1]); from lib import *
from shapely.geometry import Polygon; from skimage import measure
T, X, Y = falt('plan/c1.stl'); m = T > 0.05
cs = max(measure.find_contours(m.astype(float), 0.5), key=len)
P = np.column_stack([X[0, 0] + cs[:, 1] * r, Y[0, 0] + cs[:, 0] * r])[:-1]
sk = skeletonize(m); S = np.column_stack([X[sk], Y[sk]])
A = np.column_stack([2 * S, np.ones(len(S))]); cx, cy, _ = np.linalg.lstsq(A, (S ** 2).sum(1), rcond=None)[0]
R0 = np.median(np.hypot(S[:, 0] - cx, S[:, 1] - cy))
rad = np.hypot(P[:, 0] - cx, P[:, 1] - cy); th = np.arctan2(P[:, 1] - cy, P[:, 0] - cx)
# vinkel räknad från c:ts öppning (åt höger) så att den är sammanhängande
gap = np.arctan2(np.mean(P[:, 1]) - cy, np.mean(P[:, 0]) - cx) + np.pi
th = np.mod(th - gap, 2 * np.pi)
inre = rad < R0
o = ~inre; so = np.argsort(th[o]); r_ut = lambda t: np.interp(t, th[o][so], rad[o][so])
ti = th[inre]; t0, t1 = ti.min(), ti.max()
ramp = np.radians(float(sys.argv[2]) if len(sys.argv) > 2 else 35)
v = np.clip(np.minimum(ti - t0, t1 - ti) / ramp, 0, 1); v = v * v * (3 - 2 * v)
bredd = r_ut(ti) - rad[inre]
kant = (v > 0.98) & (v < 1.0) | (np.abs(v - 1) < 1e-9) & False
W = float(np.median(bredd[(v > 0.95)])) if len(sys.argv) < 4 else float(sys.argv[3])
# bredd vid övergångarna -> W, så att inget hack uppstår
ov = np.abs(v - 0.999) < 0.05
print('bredd i kroppen %.1f–%.1f, vid övergång %.1f, W %.1f' % (bredd[v > .95].min(), bredd[v > .95].max(), np.median(bredd[(v > 0.9) & (v < 1)]), W))
ny_r = rad[inre] + (r_ut(ti) - W - rad[inre]) * v
Q = P.copy(); Q[inre, 0] = cx + ny_r * np.cos(np.arctan2(P[inre, 1] - cy, P[inre, 0] - cx)); Q[inre, 1] = cy + ny_r * np.sin(np.arctan2(P[inre, 1] - cy, P[inre, 0] - cx))
from scipy.ndimage import gaussian_filter1d
Qs = np.column_stack([gaussian_filter1d(Q[:, 0], 12, mode='wrap'), gaussian_filter1d(Q[:, 1], 12, mode='wrap')])
Q = np.where(inre[:, None], Qs, Q)
ny = Polygon(Q).buffer(0)
mask = raster(ny, X, Y)
Z = hojd(mask, profil(T)); bygg(Z, X, Y, mjuk=True, dst='plan/c_jamn.stl')
