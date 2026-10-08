import sys, numpy as np; sys.path.insert(0, sys.argv[1]); from lib import *
from skimage.morphology import disk
f, rc, namn = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
z = np.load('an/g_falt.npz'); T, X, Y = z['T'], z['X'], z['Y']; m = T > 0.05
sk = skeletonize(m); D = ndimage.distance_transform_edt(m) * r
J = np.array([127.0, 222.0])
ora = sk & (X > J[0]) & (Y > J[1] - 1)
_, (iy, ix) = ndimage.distance_transform_edt(~sk, return_indices=True)
bort = ora[iy, ix] & (X > J[0] - 2)            # pixlar som hör till örat
ny = m & ~bort
yy, xx = np.nonzero(ora)
for y0, x0 in zip(yy, xx):
    p = J + f * (np.array([X[y0, x0], Y[y0, x0]]) - J)
    ny |= np.hypot(X - p[0], Y - p[1]) <= D[y0, x0]
ny |= np.hypot(X - J[0], Y - J[1]) <= D[np.argmin(np.abs(Y[:, 0] - J[1])), np.argmin(np.abs(X[0] - J[0]))]
if rc > 0:
    st = ndimage.binary_closing(np.pad(ny, 100), disk(int(rc / r)))[100:-100, 100:-100]
    hal = ndimage.binary_dilation(ndimage.binary_fill_holes(m) & ~m, disk(8))
    ny |= st & (Y > 205) & (X > 85) & ~hal
ny = ndimage.binary_opening(ny, disk(2))
sig = float(sys.argv[5]) if len(sys.argv) > 5 else 0
if sig:
    hal = ndimage.binary_dilation(ndimage.binary_fill_holes(m) & ~m, disk(8))
    sl = ndimage.gaussian_filter(np.pad(ny, 100).astype(float), sig / r)[100:-100, 100:-100] > 0.5
    omr = (Y > 200) & (X > 95) & ~hal
    ny = np.where(omr, sl, ny)
Z = hojd(ny, profil(T)); np.save(f'an/{namn}.npy', Z)
bygg(Z, X, Y, f'plan/{namn}.stl')
