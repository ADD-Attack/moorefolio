# Stage 2: X-squash correction, decimate to budget, split root feet into rigid nodes, save assembled.blend
import bpy,bmesh,math,sys,random
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; TARGET=int(a[1]) if len(a)>1 else 42000
o=bpy.data.objects['clean']; me=o.data
CX,CY=-0.008,-0.062
for v in me.vertices: v.co.x=CX+(v.co.x-CX)*1.12
bpy.context.view_layer.objects.active=o; o.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
d=o.modifiers.new('d','DECIMATE'); d.ratio=TARGET/len(me.polygons); bpy.ops.object.modifier_apply(modifier='d')
bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=80); bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
print('BOUNDARY LEFT',sum(1 for e in bm.edges if e.is_boundary))
def thr(z): return 0.36+0.55*z
foot=set(f for f in bm.faces if (lambda c:(c.z<0.21 and math.hypot((c.x-CX)/1.12,c.y-CY)>thr(c.z)))(f.calc_center_median()))
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
comps=[c for c in comps if len(c)>=400]; comps.sort(key=lambda c:-len(c))
print('FOOT COMPS',[len(c) for c in comps])
def ang(c):
    p=sum((f.calc_center_median() for f in c),c[0].calc_center_median()*0)/len(c); return math.degrees(math.atan2(p.y-CY,p.x-CX))%360
items=sorted(((ang(c),c) for c in comps),key=lambda t:t[0])
geo={}
for i,(an,c) in enumerate(items): geo['foot_%02d'%(i+1)]=(an,c)
def rr(f):
    c=f.calc_center_median(); return c.z,math.hypot((c.x-CX)/1.12,c.y-CY)
def az(f):
    c=f.calc_center_median(); return math.degrees(math.atan2(c.y-CY,c.x-CX))%360
CUT_B,CUT_F=0.06,0.015   # body keeps stub up to thr+CUT_B; foot starts at thr+CUT_F (overlap band)
def grow(c):
    A=[az(f) for f in c]; a0=A[0]; D=[((x-a0+180)%360)-180 for x in A]; lo,hi=min(D)-3,max(D)+3
    cs=set(c); fr=list(c)
    while fr:
        g=fr.pop()
        for e in g.edges:
            for h in e.link_faces:
                if h in cs: continue
                z,r=rr(h); dd=((az(h)-a0+180)%360)-180
                if z<0.24 and r>thr(z)+CUT_F and lo<=dd<=hi: cs.add(h); fr.append(h)
    return list(cs)
geo={n:(an,grow(c)) for n,(an,c) in geo.items()}
footfaces=set(f for _,c in geo.values() for f in c if (lambda zr: zr[1]>thr(zr[0])+CUT_B)(rr(f)))
def make(name,faces):
    nb=bmesh.new(); vm={}
    for f in faces:
        vs=[]
        for v in f.verts:
            if v not in vm: vm[v]=nb.verts.new(v.co)
            vs.append(vm[v])
        nb.faces.new(vs)
    if name=='body':
        bmesh.ops.holes_fill(nb,edges=[e for e in nb.edges if e.is_boundary],sides=200)
    else:
        nb.normal_update()
        for v in nb.verts:
            z=v.co.z; r=math.hypot((v.co.x-CX)/1.12,v.co.y-CY)
            if r<thr(z)+CUT_B+0.01: v.co+=v.normal*0.002
    bmesh.ops.triangulate(nb,faces=[f for f in nb.faces if len(f.verts)>3])
    m=bpy.data.meshes.new(name); nb.to_mesh(m); ob=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(ob); return ob
body=make('body',[f for f in bm.faces if f not in footfaces])
feet=[]
for n,(an,c) in geo.items():
    f=make(n,c); feet.append(f); print(n,round(an),len(f.data.polygons))
bpy.data.objects.remove(o)
root=bpy.data.objects.new('aliens_node',None); bpy.context.scene.collection.objects.link(root)
body.parent=root
for f in feet:
    # pivot at the root's inner end (nearest point to body axis) for rigid shuffle
    vs=[v.co for v in f.data.vertices]; p=min(vs,key=lambda v:math.hypot(v.x-CX,v.y-CY)+v.z).copy()
    for v in f.data.vertices: v.co-=p
    f.location=p; f.parent=body
print('TRIS', sum(len(x.data.polygons) for x in [body]+feet), 'NODES',1+len(feet))
for i,x in enumerate([body]+feet): x.color=(random.random(),random.random(),random.random(),1) if i else (0.8,0.8,0.8,1)
bpy.ops.wm.save_as_mainfile(filepath=out)
