import sys, os, numpy as np, trimesh
sys.path.insert(0,'/home/user/Test/bokstaver')
import versaler_3d as v3
from fixa_under import nedat
from under import analys
UT='/tmp/claude-0/-home-user-Test/c8738e90-5590-5d0d-88bf-c392bb155a12/scratchpad/az/utan_under/'
r=float(sys.argv[2]) if len(sys.argv)>2 else 0.006
for f in sys.argv[1].split(','):
    m=trimesh.load(f); b=m.bounds; zb=b[0,2]
    xs=np.arange(b[0,0]-2*r,b[1,0]+2*r,r); ys=np.arange(b[0,1]-2*r,b[1,1]+2*r,r); X,Y=np.meshgrid(xs,ys)
    o=np.column_stack([X.ravel(),Y.ravel(),np.full(X.size,b[1,2]+1)])
    loc,ri,_=m.ray.intersects_location(o,np.tile([0,0,-1.],(X.size,1)),multiple_hits=False)
    Z=np.zeros(X.size); Z[ri]=loc[:,2]-zb; Z=Z.reshape(X.shape)
    v3.RUT=r; v3.HOJD=float(Z.max())+r
    ny=v3.till_mesh(Z,xs[0],ys[0])
    ny.apply_translation([0,0,zb])
    if ny.volume<0: ny.invert()
    if not ny.is_watertight:
        from gemensam_sving import laga
        l=laga(ny)
        if l.is_watertight and np.allclose(l.bounds,ny.bounds,atol=0.01): ny=l
    namn=os.path.basename(f); ny.export(UT+namn)
    # avvikelse mot originalets ovansida
    loc2,ri2,_=ny.ray.intersects_location(o,np.tile([0,0,-1.],(X.size,1)),multiple_hits=False)
    Z2=np.zeros(X.size); Z2[ri2]=loc2[:,2]-zb; Z2=Z2.reshape(X.shape)
    inne=(Z>0.05)&(Z2>0.05)
    fl,ly,wt=analys(UT+namn)
    print(namn,'nedåtvänd före %.0f efter %.0f mm2'%(nedat(m),nedat(ny)),'| överhäng %.0f ej plan %.0f tät %s'%(fl,ly,ny.is_watertight),
          '| ytavvikelse median %.2f max95 %.2f mm'%(np.median(abs(Z-Z2)[inne])*61,np.percentile(abs(Z-Z2)[inne],95)*61), 'vol %+.1f%%'%(100*(ny.volume/m.volume-1)),flush=True)
