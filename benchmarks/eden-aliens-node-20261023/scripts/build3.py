# CLAY-FIX assembly: X-squash fix, decimate, planar-bisect foot split (clean joint rings), root-weighted foot thickening.
import bpy,bmesh,math,sys,random
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; TARGET=int(a[1]); THICK=float(a[2])
o=bpy.data.objects['clean']; me=o.data
CX,CY=-0.008,-0.062
for v in me.vertices: v.co.x=CX+(v.co.x-CX)*1.12
bpy.context.view_layer.objects.active=o; o.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
d=o.modifiers.new('d','DECIMATE'); d.ratio=TARGET/len(me.polygons); bpy.ops.object.modifier_apply(modifier='d')
bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=80); bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
def thr(z): return 0.36+0.55*z
def rz(p): return p.z,math.hypot((p.x-CX)/1.12,p.y-CY)
def az(p): return math.degrees(math.atan2(p.y-CY,p.x-CX))%360
foot=set(f for f in bm.faces if (lambda c:(c.z<0.21 and rz(c)[1]>thr(c.z)))(f.calc_center_median()))
comps=[]; seen=set()
for f in foot:
    if f in seen: continue
    st=[f]; c=[]; seen.add(f)
    while st:
        g=st.pop(); c.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h in foot and h not in seen: seen.add(h); st.append(h)
    comps.append(c)
comps=[c for c in comps if len(c)>=400]
print('COMPS',len(comps))
feet=[]
for c in comps:
    tipf=max(c,key=lambda f:rz(f.calc_center_median())[1]); tip=tipf.calc_center_median().copy()
    A=[az(f.calc_center_median()) for f in c]; a0=az(tip)
    D=[((x-a0+180)%360)-180 for x in A]; lo,hi=min(D)-6,max(D)+6
    u=Vector((tip.x-CX,tip.y-CY,0)).normalized()
    # plane through the root just outside the body: at radius thr(z)+0.03 along u, at the root's mean height
    band=[f.calc_center_median() for f in c if thr(f.calc_center_median().z)+0.02<rz(f.calc_center_median())[1]<thr(f.calc_center_median().z)+0.05]
    p0=sum(band,Vector())/len(band) if band else tip
    feet.append((a0,lo,hi,u,p0,tip))
# bisect each foot root with its plane (only within its sector, low zone), then flood from tip on the outer side
ftags={}; ZTOP=0.24
for i,(a0,lo,hi,u,p0,tip) in enumerate(feet):
    reg=[f for f in bm.faces if f.is_valid and f.calc_center_median().z<0.30 and lo<=((az(f.calc_center_median())-a0+180)%360)-180<=hi]
    geom=list(set(reg)|set(e for f in reg for e in f.edges)|set(v for f in reg for v in f.verts))
    bmesh.ops.bisect_plane(bm,geom=geom,plane_co=p0,plane_no=u,clear_inner=False,clear_outer=False)
    reg=[f for f in bm.faces if f.is_valid and f.calc_center_median().z<0.30 and lo<=((az(f.calc_center_median())-a0+180)%360)-180<=hi]
    geom=list(set(reg)|set(e for f in reg for e in f.edges)|set(v for f in reg for v in f.verts))
    bmesh.ops.bisect_plane(bm,geom=geom,plane_co=Vector((0,0,ZTOP)),plane_no=Vector((0,0,1)),clear_inner=False,clear_outer=False)
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
    outer=lambda f:(f.calc_center_median()-p0).dot(u)>0 and f.calc_center_median().z<ZTOP and lo<=((az(f.calc_center_median())-a0+180)%360)-180<=hi
    start=min((f for f in bm.faces if f not in ftags),key=lambda f:(f.calc_center_median()-tip).length)
    st=[start]; got={start}
    while st:
        g=st.pop()
        for e in g.edges:
            for h in e.link_faces:
                if h not in got and h not in ftags and outer(h): got.add(h); st.append(h)
    for f in got: ftags[f]=i
    print('FOOT',i,round(a0),'faces',len(got))
def make(name,faces,plane=None):
    nb=bmesh.new(); vm={}
    for f in faces:
        vs=[]
        for v in f.verts:
            if v not in vm: vm[v]=nb.verts.new(v.co)
            vs.append(vm[v])
        nb.faces.new(vs)
    bmesh.ops.holes_fill(nb,edges=[e for e in nb.edges if e.is_boundary],sides=0)
    bmesh.ops.triangulate(nb,faces=[f for f in nb.faces if len(f.verts)>3])
    if plane:
        u,p0=plane; nb.normal_update()
        for v in nb.verts:
            dd=(v.co-p0).dot(u)
            if dd>0.002 and not v.is_boundary:
                k=min(1,dd/0.05); knob=1+0.35*math.sin(v.co.x*90)*math.sin(v.co.y*90)
                v.co+=v.normal*THICK*k*knob
    m=bpy.data.meshes.new(name); nb.to_mesh(m); ob=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(ob); return ob
order=sorted(range(len(feet)),key=lambda i:feet[i][0])
body=make('body',[f for f in bm.faces if f not in ftags])
fobs=[]
for k,i in enumerate(order):
    fobs.append(make('foot_%02d'%(k+1),[f for f,j in ftags.items() if j==i],(feet[i][3],feet[i][4])))
bpy.data.objects.remove(o)
root=bpy.data.objects.new('aliens_node',None); bpy.context.scene.collection.objects.link(root); body.parent=root
for k,f in enumerate(fobs):
    i=order[k]; p=feet[i][4].copy()
    for v in f.data.vertices: v.co-=p
    f.location=p; f.parent=body
print('TRIS',sum(len(x.data.polygons) for x in [body]+fobs),'NODES',1+len(fobs),'BODY BOUNDARY',sum(1 for e in body.data.edges if False))
bpy.ops.wm.save_as_mainfile(filepath=out)
