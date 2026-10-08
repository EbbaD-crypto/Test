"""c: ytterkanten exakt som originalet, innerkanten flyttas så att bredden blir jämn.
Varje snitt (från c:ts mitt och utåt) skalas mot ytterkanten -> ändarna behåller form och vinkel."""
import sys, numpy as np; sys.path.insert(0, sys.argv[1]); from lib import *
T, X, Y = falt('plan/c1.stl'); m = T > 0.05
sk = skeletonize(m); P = np.column_stack([X[sk], Y[sk]])
A = np.column_stack([2 * P, np.ones(len(P))]); cx, cy, _ = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
R = np.hypot(X - cx, Y - cy); TH = np.arctan2(Y - cy, X - cx)
nb = 720; bi = ((TH + np.pi) / (2 * np.pi) * nb).astype(int) % nb
rut = np.full(nb, np.nan); rin = np.full(nb, np.nan)
for k in range(nb):
    s = (bi == k) & m
    if s.sum() > 3: rut[k] = R[s].max(); rin[k] = R[s].min()
w = rut - rin
# kroppen = vinklar där snittet är helt (inte ändarnas rundning)
med = np.nanmedian(w); kropp = w > 0.8 * med
W = float(np.median(w[kropp])) if len(sys.argv) < 3 else float(sys.argv[2])
ws = np.where(kropp, w, np.nan); idx = np.arange(nb)
ok = ~np.isnan(ws); ws = np.interp(idx, idx[ok], ws[ok], period=nb)   # ändarna: närmaste kroppens bredd
ws = ndimage.gaussian_filter1d(ws, 6, mode='wrap'); s = W / ws
# ändarna (och en övergång in i kroppen) lämnas exakt som originalet
vikt = ndimage.gaussian_filter1d(ndimage.binary_erosion(kropp, iterations=25).astype(float), 10, mode='wrap')
s = 1 + (s - 1) * vikt
print('bredd före %.1f–%.1f, nu %.1f' % (np.nanmin(w[kropp]), np.nanmax(w[kropp]), W))
ro = np.where(np.isnan(rut), 0, rut)[bi]
src = ro - (ro - R) / s[bi]
jx = np.clip(np.round((cx + src * np.cos(TH) - X[0, 0]) / r).astype(int), 0, X.shape[1] - 1)
jy = np.clip(np.round((cy + src * np.sin(TH) - Y[0, 0]) / r).astype(int), 0, X.shape[0] - 1)
ny = m[jy, jx] & (src > 0)
ny = ndimage.gaussian_filter(np.pad(ny, 40).astype(float), 0.75 / r)[40:-40, 40:-40] > 0.5
Z = hojd(ny, profil(T)); bygg(Z, X, Y, 'plan/c_jamn.stl')
