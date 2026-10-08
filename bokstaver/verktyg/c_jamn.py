import sys, numpy as np; sys.path.insert(0, sys.argv[1]); from lib import *
from shapely.geometry import LineString
T, X, Y = falt('plan/c1.stl'); m = T > 0.05
D = ndimage.distance_transform_edt(m) * r; sk = skeletonize(m)
p = stig(sk, X, Y); W = float(np.median(2 * D[sk])) if len(sys.argv) < 3 else float(sys.argv[2])
c = jamna(p, s=float(sys.argv[3]) if len(sys.argv) > 3 else 60)
ny = raster(LineString(c).buffer(W / 2, quad_segs=32), X, Y)
Z = hojd(ny, profil(T)); print('bredd', W, 'höjd före %.1f efter %.1f' % (T.max(), Z.max()))
np.savez('an/c_ny.npz', Z=Z, c=c)
bygg(Z, X, Y, 'plan/c_jamn.stl')
