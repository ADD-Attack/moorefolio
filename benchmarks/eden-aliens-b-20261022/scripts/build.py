# EDEN-3D-01 build: segment the approved Hunyuan c1-wholebody-s42 formed mesh into animatable nodes (Decision 35: from the formed mesh, no primitives)
import bpy,bmesh,sys,mathutils
args=sys.argv[sys.argv.index('--')+1:]; glb,outdir=args[0],args[1]
BB,BM=(int(args[2]),int(args[3])) if len(args)>3 else (20000,12000)
VOX=float(args[4]) if len(args)>4 else 0.004
DEEP=float(args[5]) if len(args)>5 else 0.0
SMI=int(args[6]) if len(args)>6 else 20
TS=float(args[7]) if len(args)>7 else 0.0
RD=float(args[12]) if len(args)>12 else 0.018
RW=0.0055
CAPV=[]
RAMP=0.06
NR=5
DN=int(args[13]) if len(args)>13 else 0
PADK=0.9
TR=[]
TDK=float(args[11]) if len(args)>11 else 1.0
TL=float(args[8]) if len(args)>8 else 1.0
NS=float(args[9]) if len(args)>9 else 1.0
NL=float(args[10]) if len(args)>10 else 1.0
XT0=-0.56
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
src=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
src.data.transform(src.matrix_world); src.matrix_world=mathutils.Matrix()
bm=bmesh.new(); bm.from_mesh(src.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
# 1 strip baked ground slab (z<-0.505); feet get capped later
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<-0.505],context='VERTS')
# keep largest connected island only (drop stray slab fragments)
bm.verts.ensure_lookup_table(); seen=set(); isl=[]
for v in bm.verts:
    if v in seen: continue
    st=[v]; comp=[]; seen.add(v)
    while st:
        a=st.pop(); comp.append(a)
        for e in a.link_edges:
            b=e.other_vert(a)
            if b not in seen: seen.add(b); st.append(b)
    isl.append(comp)
isl.sort(key=len); print('ISLANDS',[len(i) for i in isl[-5:]])
bmesh.ops.delete(bm,geom=[v for c in isl[:-1] for v in c],context='VERTS')
# fill native Hunyuan seam pinholes + slab-strip foot holes (loops <=120 edges); large natural openings untouched
bd=[e for e in bm.edges if e.is_boundary]; print('RAW_BOUNDARY',len(bd))
bmesh.ops.holes_fill(bm,edges=bd,sides=120); print('RAW_BOUNDARY_AFTER',sum(1 for e in bm.edges if e.is_boundary))
bmesh.ops.triangulate(bm,faces=bm.faces)
# voxel remesh the formed mesh into a clean manifold surface (shell is near-closed here); same form, no double walls
if VOX>0:
    # FIX-PASS retopo: inward solidify closes the open shell, then voxel remesh -> clean manifold on c1's outer surface
    from mathutils.bvhtree import BVHTree
    ref_bvh=BVHTree.FromBMesh(bm)
    bm.to_mesh(src.data); bm.free()
    so=src.modifiers.new('so','SOLIDIFY'); so.thickness=0.006; so.offset=-1.0; so.use_even_offset=True
    rm=src.modifiers.new('rm','REMESH'); rm.mode='VOXEL'; rm.voxel_size=VOX; rm.use_smooth_shade=True
    bpy.context.view_layer.objects.active=src; bpy.ops.object.modifier_apply(modifier='so'); bpy.ops.object.modifier_apply(modifier='rm')
    bm=bmesh.new(); bm.from_mesh(src.data); bmesh.ops.triangulate(bm,faces=bm.faces)
    isl2=[]; seen=set()
    for v in bm.verts:
        if v in seen: continue
        st=[v]; comp=[]; seen.add(v)
        while st:
            x=st.pop(); comp.append(x)
            for e in x.link_edges:
                y=e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y)
        isl2.append(comp)
    isl2.sort(key=len); print('REMESH_ISLANDS',[len(i) for i in isl2[-4:]])
    bmesh.ops.delete(bm,geom=[v for c in isl2[:-1] for v in c],context='VERTS')
    inner=[f for f in bm.faces if ref_bvh.find_nearest(f.calc_center_median())[3]>0.003]
    print('INNER_WALL_DELETED',len(inner),'of',len(bm.faces)); bmesh.ops.delete(bm,geom=inner,context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    # throat: cap the open tube end (boundary loops in the mouth zone) and pull the cap centre back -> concave cup
    bd=[e for e in bm.edges if e.is_boundary and min(v.co.x for v in e.verts)>0.12]
    r=bmesh.ops.holes_fill(bm,edges=bd,sides=0); caps=r['faces']
    print('THROAT_CAPS',len(caps),[len(f.verts) for f in caps][:6])
    for f in caps:
        if len(f.verts)<40: continue
        pk=bmesh.ops.poke(bm,faces=[f]); cv=pk['verts'][0]; cv.co.x-=0.12; CAPV.extend(set(v for fc in pk['faces'] for v in fc.verts))
if TS>0:
    # TAIL-PASS (Decision 46): exaggerate c1's tail on the clay. Radial displacement from the tail's own axis (per-slice centroids),
    # x-stretch from the socket, carved transverse ring grooves with bulging pads; all pre-cut so the chain stays aligned
    import math as _m
    tv=[v for v in bm.verts if v.co.x<XT0+RAMP and abs(v.co.y)<0.16 and -0.36<v.co.z<-0.02]
    core=[v for v in tv if v.co.x<XT0-0.005]
    bins={}
    for v in core: bins.setdefault(round(v.co.x*100),[]).append(v.co)
    cen={k:(sum(c.y for c in L)/len(L),sum(c.z for c in L)/len(L)) for k,L in bins.items()}
    keys=sorted(cen)
    def axis(x):
        k=round(x*100); k=min(max(k,keys[0]),keys[-1])
        while k not in cen: k+=1
        return cen[k]
    tip0=min(v.co.x for v in core); span=XT0-tip0
    orig=[(v,v.co.copy()) for v in tv]
    for v,c in orig:
        cy,cz=axis(min(c.x,XT0-0.006)); r=mathutils.Vector((0,c.y-cy,c.z-cz))
        if r.length<1e-6: continue
        rd=r.normalized(); t=min(1.0,max(0.0,(XT0+RAMP-c.x)/RAMP))**1.5; u=min(1.0,max(0.0,(XT0-c.x)/span))
        x=XT0+(c.x-XT0)*TL if c.x<XT0 else c.x
        off=TS*t*(1.3-0.6*u)
        if c.x<XT0:
            sp=span*TL/NR; ph=(XT0-x)/sp
            g=_m.exp(-((ph-round(ph))*sp/RW)**2) if round(ph)>=1 else 0.0
            pad=abs(_m.sin(_m.pi*ph))**0.35
            off+= -RD*g + RD*PADK*pad
        v.co=mathutils.Vector((x,c.y,c.z))+rd*off
    sp=span*TL/NR; rings=[XT0-sp*k for k in range(1,NR+1)]; TR[:]=[rings[0],rings[2]]
    tvs=[v for v,c in orig if c.x<XT0+0.02]
    for _ in range(3): bmesh.ops.smooth_vert(bm,verts=tvs,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    print('TAIL_EXAGGERATED',len(tv),TS,TL,'rings',[round(r,3) for r in rings])
if DEEP>0:
    # GATE-RETRY detail: denoise base (DN light iters) then deepen grooves vs a wide smoothed reference (SMI iters), concave side only
    capset=set(CAPV); keep={v.index:v.co.copy() for v in capset} if capset else {}
    bm.verts.index_update(); keep={v.index:v.co.copy() for v in capset}
    bm.normal_update(); base=bm.copy(); sm=bm.copy()
    for _ in range(DN): bmesh.ops.smooth_vert(base,verts=base.verts,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    for _ in range(SMI): bmesh.ops.smooth_vert(sm,verts=sm.verts,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    base.verts.ensure_lookup_table(); sm.verts.ensure_lookup_table(); bm.verts.ensure_lookup_table(); nd=0
    for v,bv,w in zip(bm.verts,base.verts,sm.verts):
        d=(bv.co-w.co).dot(v.normal); v.co=bv.co.copy()
        if d<0: v.co+=v.normal*d*(DEEP*TDK if v.co.x<XT0 else (DEEP*0.7 if v.co.x>0.15 else DEEP)); nd+=1
    for v in bm.verts:
        if v.index in keep: v.co=keep[v.index]
    base.free(); sm.free(); print('CUP_PROTECTED',len(keep)); print('DEEPENED',nd,'DN',DN,'SMI',SMI,'DEEP',DEEP)
print('REMESH tris',len(bm.faces),'boundary',sum(1 for e in bm.edges if e.is_boundary),'nonman',sum(1 for e in bm.edges if not e.is_manifold))
XT,XM,ZL,XC=-0.56,0.40,-0.34,0.05
T1,T2=(TR[0],TR[1]) if TR else (XT-0.065*TL,XT-0.115*TL)
def cut(co,no):
    g=bm.verts[:]+bm.edges[:]+bm.faces[:]
    bmesh.ops.bisect_plane(bm,geom=g,plane_co=co,plane_no=no,dist=1e-6)
cut((XT,0,0),(1,0,0)); cut((T1,0,0),(1,0,0)); cut((T2,0,0),(1,0,0)); cut((XM,0,0),(1,0,0))
# leg cut plane only within leg columns: bisect globally, region test restricts
cut((0,0,ZL),(0,0,1))
def region(c):
    if c.x<XT: return 'tail_01' if c.x>T1 else ('tail_02' if c.x>T2 else 'tail_03')
    if c.x>XM: return 'mouth'
    if c.z<ZL: return 'leg_'+('F' if c.x>XC else 'B')+('L' if c.y>0 else 'R')
    return 'body'
groups={}
for f in bm.faces: groups.setdefault(region(f.calc_center_median()),[]).append(f.index)
budget={'body':BB,'mouth':BM,'leg_FL':1500,'leg_FR':1500,'leg_BL':1500,'leg_BR':1500,'tail_01':2400,'tail_02':1900,'tail_03':1400}
bm.faces.ensure_lookup_table()
clay=bpy.data.materials.new('clay'); clay.diffuse_color=(0.62,0.6,0.57,1)
objs={}
for name,idx in groups.items():
    b2=bm.copy(); b2.faces.ensure_lookup_table(); keep=set(idx)
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.index not in keep],context='FACES')
    bmesh.ops.delete(b2,geom=[v for v in b2.verts if not v.link_faces],context='VERTS')
    def oncut(v): return any(abs(v.co.x-q)<1e-4 for q in (XT,T1,T2)) or abs(v.co.z-ZL)<1e-4
    ce=[e for e in b2.edges if e.is_boundary and oncut(e.verts[0]) and oncut(e.verts[1])]
    if ce: bmesh.ops.holes_fill(b2,edges=ce,sides=0)
    bmesh.ops.triangulate(b2,faces=b2.faces)
    bmesh.ops.split_edges(b2,edges=[e for e in b2.edges if len(e.link_faces)>2])
    me=bpy.data.meshes.new(name); b2.to_mesh(me); b2.free()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); objs[name]=o
    o.data.materials.append(clay)
    n=len(me.polygons); r=min(1.0,budget[name]/n)
    m=o.modifiers.new('dec','DECIMATE'); m.ratio=r; m.use_collapse_triangulate=True; m.use_symmetry=False
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier='dec')
    b3=bmesh.new(); b3.from_mesh(o.data)
    bmesh.ops.remove_doubles(b3,verts=b3.verts,dist=0.001)
    bmesh.ops.holes_fill(b3,edges=[e for e in b3.edges if e.is_boundary],sides=40)
    bmesh.ops.triangulate(b3,faces=b3.faces)
    b3.to_mesh(o.data); b3.free()
    for p in o.data.polygons: p.use_smooth=True
    print('NODE',name,'raw',n,'->',len(o.data.polygons))
# FIX-PASS F5: whole tail chain scaled as one unit about tail_01's root (segments stay aligned)
if NS!=1.0 or NL!=1.0:
    tvs=[v.co for v in objs['tail_01'].data.vertices]; P=mathutils.Vector((XT,0,sum(c.z for c in tvs)/len(tvs)))
    M=mathutils.Matrix.Translation(P)@mathutils.Matrix.Diagonal((NL,NS,NS,1.0))@mathutils.Matrix.Translation(-P)
    for tn in ('tail_01','tail_02','tail_03'): objs[tn].data.transform(M)
    T1s,T2s=XT+(T1-XT)*NL,XT+(T2-XT)*NL
    print('TAIL_CHAIN_SCALED',NS,NL)
else: T1s,T2s=T1,T2
# pivots: legs at hip-cut centre, tail segs at root, mouth at cut centre
def set_origin(o,pt):
    o.data.transform(mathutils.Matrix.Translation(-pt)); o.location=pt
for name,o in objs.items():
    vs=[v.co for v in o.data.vertices]
    if name.startswith('leg'): pt=mathutils.Vector((sum(v.x for v in vs)/len(vs),sum(v.y for v in vs)/len(vs),ZL))
    elif name=='mouth': pt=mathutils.Vector((XM,0,sum(v.z for v in vs)/len(vs)))
    elif name.startswith('tail'): pt=mathutils.Vector(({'tail_01':XT,'tail_02':T1s,'tail_03':T2s}[name],0,sum(v.z for v in vs)/len(vs)))
    else: pt=mathutils.Vector((0,0,0))
    set_origin(o,pt)
bpy.context.view_layer.update()
def parent(c,p):
    w=c.matrix_world.copy(); c.parent=p; c.matrix_world=w
for n in objs:
    if n!='body' and not n.startswith('tail_0') or n=='tail_01': parent(objs[n],objs['body'])
parent(objs['tail_02'],objs['tail_01']); parent(objs['tail_03'],objs['tail_02'])
bpy.data.objects.remove(src)
objs['body'].name='aliens_b_body'
# provisional UVs so glTF tangents export (contract: tangents ON); material phase re-UVs
for o in objs.values():
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=0.003); bpy.ops.object.mode_set(mode='OBJECT')
print('TOTAL_TRIS',sum(len(o.data.polygons) for o in objs.values()))
bpy.ops.wm.save_as_mainfile(filepath=outdir+'\\aliens_b_clay.blend')
bpy.ops.export_scene.gltf(filepath=outdir+'\\aliens_b_clay.glb',export_format='GLB',export_yup=True,export_apply=True,export_tangents=True,export_draco_mesh_compression_enable=False)
