# CLAY-FIX detail on the high-res formed mesh (pre-decimation):
# (a) F5: concave-side unsharp along normals (EDEN-3D-01 recipe) — only troughs deepen, cords untouched.
# (b) F3: gnarl (low-freq knots along horn) + left-horn secondary prong grown by gaussian pull of its own vertices.
import bpy,bmesh,sys,math
import numpy as np
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; K=float(a[1]); PASSES=int(a[2])
o=bpy.data.objects['clean']; me=o.data; nv=len(me.vertices)
E=np.empty(len(me.edges)*2,np.int32); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
deg=np.bincount(E.ravel(),minlength=nv).astype(np.float64)
def lap_smooth(P,it):
    S=P.copy()
    for _ in range(it):
        acc=np.zeros_like(S); np.add.at(acc,E[:,0],S[E[:,1]]); np.add.at(acc,E[:,1],S[E[:,0]])
        S=0.5*S+0.5*acc/np.maximum(deg,1)[:,None]
    return S
P=np.empty(nv*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
z=P[:,2]; bodymask=(z>0.20)  # keep feet zone out of the vein pass (feet handled separately)
for p in range(PASSES):
    me.vertices.foreach_set('co',P.ravel()); me.update()
    N=np.empty(nv*3); me.vertices.foreach_get('normal',N); N=N.reshape(-1,3)
    S=lap_smooth(P,14)
    d=np.einsum('ij,ij->i',P-S,N)          # signed depth vs smoothed surface
    conc=np.minimum(d,0.0)                  # concave side only
    conc=lap_smooth(conc[:,None],3)[:,0]    # diffuse so the groove floor is clean, not speckled
    w=bodymask*np.clip((z-0.20)/0.06,0,1)
    P=P+N*(K*conc*w)[:,None]
    print('PASS',p,'mean conc',round(float(conc.mean()),5),'min',round(float(conc.min()),4))
me.vertices.foreach_set('co',P.ravel()); me.update()
V=me.vertices
# (b0) horn thicken (same base-weighted taper as clay delivery, now on high-res mesh)
SXY,SZ=2.0,1.45
for side in (-1,1):
    cand=[v for v in V if v.co.x*side>0.05]
    tip=max(cand,key=lambda v:v.co.z).co.copy()
    # walk down: horn base = height where the slice around the tip axis gets wide
    zb=None; ax=Vector((tip.x,tip.y))
    for k in range(1,60):
        z=tip.z-k*0.005
        sl=[v for v in V if abs(v.co.z-z)<0.004 and (Vector((v.co.x,v.co.y))-ax).length<0.12]
        if sl:
            c=sum((Vector((v.co.x,v.co.y)) for v in sl),Vector((0,0)))/len(sl); w=max((Vector((v.co.x,v.co.y))-c).length for v in sl)
            ax=c
            if w>0.075: zb=z; break
    print('HORN',side,'tip',tuple(round(x,3) for x in tip),'base z',zb,'axis',tuple(round(x,3) for x in ax))
    if zb is None: continue
    for v in V:
        d=(Vector((v.co.x,v.co.y))-ax).length
        if v.co.z>zb-0.03 and d<0.10:
            t=min(1,max(0,(v.co.z-(zb-0.03))/0.05))*(1-min(1,max(0,(d-0.07)/0.03)))
            off=Vector((v.co.x,v.co.y))-ax
            h=min(1,max(0,(v.co.z-zb)/(tip.z-zb))); n=ax+off*(1+(SXY-1)*t*(1-h)**0.8); v.co.x,v.co.y=n.x,n.y
            v.co.z=v.co.z+(v.co.z-zb)*(SZ-1)*t if v.co.z>zb else v.co.z
me.update()
TIPS={}
for side in (-1,1):
    cand=[v for v in V if v.co.x*side>0.05 and v.co.y>0.0]
    TIPS[side]=max(cand,key=lambda v:v.co.z).co.copy()
# (b1) gnarl: low-frequency knots, amplitude scaled to local horn radius; (b2) left secondary prong
for side in (-1,1):
    tip=TIPS[side]; zb=0.87; ax=Vector((tip.x,tip.y)); L=tip.z-zb
    hv=[v for v in V if v.co.z>zb and (Vector((v.co.x,v.co.y))-ax).length<0.12]
    for v in hv:
        h=(v.co.z-zb)/L; off=Vector((v.co.x-ax.x,v.co.y-ax.y,0)); r=off.length
        if r<1e-6: continue
        th=math.atan2(off.y,off.x)
        knot=r*0.22*(math.sin(h*8.5+th*1.0+side)*0.7+0.5*math.sin(h*13-th*2))*math.sin(min(1,h)*math.pi)
        v.co+=off.normalized()*knot
    if side==-1:
        c=Vector((ax.x-0.03,ax.y,zb+0.32*L)); dirv=Vector((-0.6,0.15,0.78)).normalized()
        n=0
        for v in hv:
            dv=v.co-c; r=dv.length
            if r<0.06 and (v.co.x-ax.x)< 0.0:
                f=math.exp(-(r/0.026)**2); v.co+=dirv*0.11*f; n+=1
        print('PRONG verts',n)
    print('HORN',side,'verts',len(hv),'tip',tuple(round(x,3) for x in tip))
me.update(); bpy.ops.wm.save_as_mainfile(filepath=out)
