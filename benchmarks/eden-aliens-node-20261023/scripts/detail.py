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
# (b) HORNS-FIX: taller jagged crooked spikes with real gnarl + defined left prong, deforming the horns' own vertices.
import random
CFG={-1:dict(tipz=1.34,Sb=1.9,lean=0.07,ph=0.3,g=1.0,j=0.22),1:dict(tipz=1.27,Sb=2.1,lean=0.06,ph=1.7,g=1.7,j=0.40)}
for side in (-1,1):
    cfg=CFG[side]
    cand=[v for v in V if v.co.x*side>0.05 and v.co.y>0.0]
    tip=max(cand,key=lambda v:v.co.z).co.copy()
    zb=None; ax=Vector((tip.x,tip.y))
    for k in range(1,60):
        z=tip.z-k*0.005
        sl=[v for v in V if abs(v.co.z-z)<0.004 and (Vector((v.co.x,v.co.y))-ax).length<0.12]
        if sl:
            c=sum((Vector((v.co.x,v.co.y)) for v in sl),Vector((0,0)))/len(sl); w=max((Vector((v.co.x,v.co.y))-c).length for v in sl)
            ax=c
            if w>0.075: zb=z; break
    L=tip.z-zb; S=(cfg['tipz']-zb)/L
    hv=[v for v in V if v.co.z>zb-0.03 and (Vector((v.co.x,v.co.y))-ax).length<0.10]
    for v in hv:
        d=(Vector((v.co.x,v.co.y))-ax).length
        t=min(1,max(0,(v.co.z-(zb-0.03))/0.05))*(1-min(1,max(0,(d-0.07)/0.03)))
        if t<=0: continue
        h=min(1,max(0,(v.co.z-zb)/L))
        off=Vector((v.co.x-ax.x,v.co.y-ax.y)); th=math.atan2(off.y,off.x)
        saw=((h*4.5+cfg['ph'])%1.0)                       # jagged stepped taper
        gn=cfg['g']*0.20*math.sin(h*15+th*2+cfg['ph'])+cfg['g']*0.12*math.sin(h*27-th*3)
        rad=(1+(cfg['Sb']-1)*(1-h)**1.2)*(1+cfg['j']*(saw-0.5)*math.sin(h*math.pi))*(1+gn*math.sin(min(1,h*1.3)*math.pi))
        crook=Vector((side*cfg['lean']*h**1.4+0.025*math.sin(h*6+cfg['ph']), 0.03*math.sin(h*5+side), 0))
        n=ax+off*(1+(rad-1)*t)+crook.xy*t
        nz=v.co.z if v.co.z<=zb else zb+(v.co.z-zb)*(1+(S-1)*t)
        v.co.x,v.co.y,v.co.z=n.x,n.y,nz
    me.update()
    if side==-1:
        # secondary prong: pull the outer-flank band at 30-50% height into a long upward-outward spur
        H=cfg['tipz']-zb
        c=Vector((ax.x-0.035,ax.y,zb+0.38*H)); dirv=Vector((-0.55,0.1,0.83)).normalized()
        n=0
        for v in hv:
            dv=v.co-c; r=dv.length
            if r<0.07 and (v.co.x-ax.x)<-0.005:
                f=math.exp(-(r/0.022)**2); v.co+=dirv*0.17*f; n+=1
        print('PRONG verts',n)
    print('HORN',side,'zb',round(zb,3),'S',round(S,2),'verts',len(hv))
me.update(); bpy.ops.wm.save_as_mainfile(filepath=out)
