# Refine F3 on the formed mesh: thicken/lengthen each horn about its own base (soft falloff), no new geometry.
import bpy,math,sys
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; SXY,SZ=float(a[1]),float(a[2])
b=bpy.data.objects['body']; V=b.data.vertices
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
b.data.update(); bpy.ops.wm.save_as_mainfile(filepath=out)
